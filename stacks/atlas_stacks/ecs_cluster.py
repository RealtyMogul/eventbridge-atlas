from importlib import resources
import json
import os
from os import name
import this
from aws_cdk import (
    Stack, CfnOutput, Duration, Fn,
    aws_ecs as ecs,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    aws_ecr as ecr
)
from aws_cdk.aws_secretsmanager import ResourcePolicy
from constructs import Construct

class ecsCluster(Stack):

    def __init__(self, scope: Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Perform various lookups and imports for required existing resources
        # -----------------------------
        vpcid = ssm.StringParameter.value_from_lookup(self, parameter_name="VPC-ID")
        importedVPC = ec2.Vpc.from_lookup(self, "importedvpc", vpc_id=vpcid)
        # -----------------------------

        cluster= ecs.Cluster(self, "EventBridgeAtlasCluster",
            vpc=importedVPC)
        repository = ecr.Repository(self, "Repository",
            repository_name=f"{props['environment'].lower()}-eventbridge-atlas-repo")

        self.output_props = props.copy()
        self.output_props['cluster'] = cluster
        self.output_props['ecr_repo'] = repository

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props