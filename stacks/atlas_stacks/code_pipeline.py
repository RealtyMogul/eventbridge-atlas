from os import name
from aws_cdk import (
    Stack, CfnOutput,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    aws_secretsmanager as secrets,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions
)
from aws_cdk.aws_ecr import Repository
from constructs import Construct

class CICDPipeline(Stack):

    def __init__(self, scope: Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpcid = ssm.StringParameter.value_from_lookup(self, parameter_name=('VPC-ID'))
        imported_vpc = ec2.Vpc.from_lookup(self, "importedvpc", vpc_id=vpcid)
        github_connection_arn = secrets.Secret.from_secret_name_v2(self, "github_arn", secret_name='github_arn').secret_value.to_string()    

        ecr_repo:Repository = props['ecr_repo']      
        repo_name = ecr_repo.repository_name  

        pipeline = codepipeline.Pipeline(self, f"-EventBridgeAtlasBuildPipeline",
            pipeline_name="EventBridgeAtlasBuildPipeline",
            cross_account_keys=False)

        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name="GitHub_Source",
            owner="RealtyMogul",
            repo=props['gitrepo'],
            branch=props['gitbranch'],
            connection_arn=github_connection_arn,
            output=source_output
        )

        source_stage = pipeline.add_stage(
            stage_name='Source',
            actions=[source_action]
        )

        build_output = codepipeline.Artifact()
        buildProject = codebuild.PipelineProject(self, f"{props['environment']}-EventBridgeAtlasBuildProject",
            vpc=imported_vpc,
            subnet_selection=ec2.SubnetSelection(subnet_group_name="Application"),
            environment={
                "privileged": True},
            project_name="EventBridgeAtlasBuild",
            environment_variables={
                "ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                    value=props['accountID']
                ),
                "REPO_NAME": codebuild.BuildEnvironmentVariable(
                    value=repo_name
                )
            }
        )

        ecr_repo.grant_pull_push(buildProject)

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build",
            input=source_output,
            project=buildProject,
            outputs=[build_output]
        )

        build_stage = pipeline.add_stage(
            stage_name='Build',
            actions=[build_action]
        )

        deploy_stage = pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                codepipeline_actions.EcsDeployAction(
                    action_name="EventBridgeAtlasDeployment",
                    service=props['ecs_service'],
                    image_file=build_output.at_path("imagedefinitions.json")
                ),
            ]
        )

        self.output_props = props.copy()
        self.output_props['pipeline'] = pipeline
    
    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props