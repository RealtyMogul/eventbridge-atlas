from aws_cdk import Environment, Stack, Stage, Tags
from aws_cdk import aws_secretsmanager as secrets
from aws_cdk import pipelines as pipelines
from constructs import Construct
from lib.tagging import tag

from stacks.atlas_stacks.atlas_resources import FargateService
from stacks.atlas_stacks.code_pipeline import CICDPipeline


class accountStacks(Stack):

    def __init__(self, scope: Construct, construct_id: str, env=None, props=None) -> None:
        super().__init__(scope, construct_id, env=env)

        github_connection_arn = secrets.Secret.from_secret_name_v2(self, "github_arn", secret_name='github_arn').secret_value.unsafe_unwrap()
        docker_hub_secret = secrets.Secret.from_secret_name_v2(self, "dockerSecret", secret_name='dockerhubSecret')

        GeneralPipeline = pipelines.CodePipeline(self, f"DeploymentPipeline-{props['environment']}",
            cross_account_keys=True,
            pipeline_name=f"{props['environment']}-{props['project']}",
            docker_credentials=[
                pipelines.DockerCredential.docker_hub(docker_hub_secret)
            ],
            synth=pipelines.ShellStep("Synth",
                input=pipelines.CodePipelineSource.connection(f"RealtyMogul/{props['gitrepo']}", f"{props['gitbranch']}",
                    connection_arn=github_connection_arn
                ),
                commands=["pip install -r requirements.txt", 
                          "npm install -g aws-cdk", 
                          "cdk synth"]
            ),
            docker_enabled_for_synth=True
        )

        account_wave = GeneralPipeline.add_wave("Accounts")

        account_wave.add_stage(Stacks(self, f"{props['environment']}",
            env=Environment(
                account= props['targetenv']['account'],
                region= props['targetenv']['region']
            ),
            props=props
        ))

class Stacks(Stage):
    """
    Contains the stacks that will be deployed by a CDK Pipeline.  Each stack should be as atomic as
    is reasonable so that a failed stack update does not affect the operation of the others.  In a worst-case
    scenario a stack will end up in a ROLLBACK_COMPLETE status and can't be updated until it is deleted and
    re-proisioned.  Extra care must be taken for stateful assets (e.g. databases).

    Outputs from each stack are added to the `props` dictionary as the construction proceeds so that individual
    assets can be referenced, imported, and used as necessary.  If one stack depends on the output of another, be sure
    to add it as an explicit dependency.
    """

    def __init__(self, scope, id, *, env=None, props=None, outdir=None):
        super().__init__(scope, id, env=env, outdir=outdir)

        """Stacks"""
        atlas = FargateService(self, f"{props['project']}Task", props)
        build_pipeline=CICDPipeline(self, f"{props['project']}BuildPipeline", atlas.outputs)
        build_pipeline.add_dependency(atlas, "need to create the repo before CICD pipeline executes")


        tag(atlas, props['environment'])
        tag(build_pipeline, props['environment'])
