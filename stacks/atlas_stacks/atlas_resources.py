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
from aws_cdk.aws_applicationautoscaling import Schedule
import aws_cdk
from constructs import Construct


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
        repository = ecr.Repository(self, "Repository",
            repository_name=f"{props['environment'].lower()}-adminpanelrepo")
        s3bucket = s3.Bucket(
            self,
            f"{props['project']}-{props['environment']}-bucket",
            removal_policy=RemovalPolicy.DESTROY,
        )
        fargate_task = aws_cdk.aws_ecs_patterns.ScheduledFargateTask(
            self,
            "EventBridgeAtlasFargate",
            schedule=Schedule.cron(hour=12, minute=0),
            vpc=importedVPC,
            scheduled_fargate_task_image_options=ecs_patterns.ScheduledFargateTaskImageOptions(
                image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
                container_name=f"{props['environment'].lower()}-eventbridgeatlas",
                environment={
                    "EVENT_BUS_NAME": f"{props['environment']}-EventCentral",
                    "SCHEMA_REGISTRY_NAME": "discovered-schemas",
                    "REGION": props["targetenv"]["region"],
                    "BUCKET_NAME": s3bucket.bucket_name
                },
            ),
        )

        s3bucket.grant_read_write(fargate_task)

        self.output_props = props.copy()
        self.output_props['ecr_repo'] = repository
        self.output_props['ecs_task']=fargate_task.task

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
