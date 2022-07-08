from os import path

from aws_cdk import (
    BundlingOptions,
    CfnOutput,
    Duration,
    Fn,
    RemovalPolicy,
    Stack,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
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

        s3bucket = s3.Bucket(
            self,
            f"{props['project']}-{props['environment']}-bucket",
            removal_policy=RemovalPolicy.DESTROY,
        )
        fargate_task = aws_cdk.aws_ecs_patterns.ScheduledFargateTask(
            self,
            "EventBridgeAtlasFargate",
            schedule=Schedule.cron(day='*',month='*',hour='*', minute='0'),
            cluster=props['cluster'],
            scheduled_fargate_task_image_options=ecs_patterns.ScheduledFargateTaskImageOptions(
                image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
                environment={
                    "EVENT_BUS_NAME": f"{props['environment']}-EventCentral",
                    "SCHEMA_REGISTRY_NAME": "discovered-schemas",
                    "REGION": props["targetenv"]["region"],
                    "BUCKET_NAME": s3bucket.bucket_name
                },
            ),
        )
        #granting permisions
        fargate_task.task_definition.execution_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEC2ContainerRegistryPowerUser'))
        # fargate_task.task_definition.execution_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonECSTaskExecutionRolePolicy'))
        s3bucket.grant_read_write(fargate_task.task_definition.execution_role)
        
        #taking fargate task definition and making a service
        fargate_service = ecs.FargateService(self, 'EventBridgeAtlasFargateService', task_definition=fargate_task.task_definition,cluster=props['cluster'])
        self.output_props = props.copy()
        self.output_props['ecs_service']=fargate_service

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
