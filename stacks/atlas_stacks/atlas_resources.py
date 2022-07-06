from os import path

from aws_cdk import (
    BundlingOptions,
    CfnOutput,
    Duration,
    Fn,
    RemovalPolicy,
    Stack,
    aws_ecs_patterns as ecs_patterns,
)
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_lambda as aws_lambda
from aws_cdk import aws_logs as aws_logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_ecr_assets import DockerImageAsset
from aws_cdk.aws_applicationautoscaling import Schedule
import aws_cdk
from constructs import Construct
from pathlib import Path


class FargateService(Stack):
    """
    Services created: s3bucket, ecr repo, fargate scheduled task
    """
    def __init__(self, scope: Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.output_props = props.copy()

        # https://eventbus-cdk.workshop.aws/en/04-api-gateway-service-integrations/01-rest-api/rest-apis.html

        vpcid = ssm.StringParameter.value_from_lookup(self, parameter_name="VPC-ID")
        importedVPC = ec2.Vpc.from_lookup(self, "importedvpc", vpc_id=vpcid)
        cluster= ecs.Cluster(self, "EventBridgeAtlasCluster",
            vpc=importedVPC)
        repository = ecr.Repository(self, "Repository",
            repository_name=f"{props['environment'].lower()}-eventbridge-atlas-repo")
        image = DockerImageAsset(self,"EventBridgeAtlasImage",directory= str(Path.cwd().parent.parent))
        s3bucket = s3.Bucket(
            self,
            f"{props['project']}-{props['environment']}-bucket",
            removal_policy=RemovalPolicy.DESTROY,
        )
        fargate_task = aws_cdk.aws_ecs_patterns.ScheduledFargateTask(
            self,
            "EventBridgeAtlasFargate",
            schedule=Schedule.cron(day='*',month='*',hour='*', minute='0'),
            cluster=cluster,
            scheduled_fargate_task_image_options=ecs_patterns.ScheduledFargateTaskImageOptions(
                image=image,
                environment={
                    "EVENT_BUS_NAME": f"{props['environment']}-EventCentral",
                    "SCHEMA_REGISTRY_NAME": "discovered-schemas",
                    "REGION": props["targetenv"]["region"],
                    "BUCKET_NAME": s3bucket.bucket_name
                },
            ),
        )
        fargate_service = ecs.FargateService(self, 'EventBridgeAtlasFargateService', task_definition=fargate_task.task_definition,cluster=cluster)

        s3bucket.grant_read_write(fargate_task.task_definition.execution_role)
        self.output_props = props.copy()
        self.output_props['ecr_repo'] = repository
        self.output_props['ecs_service']=fargate_service
        self.output_props['image']=image

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
