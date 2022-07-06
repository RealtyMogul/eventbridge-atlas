# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as cdk

from .config import (
    get_logical_id_prefix, get_resource_name_prefix,
)
from lib.config import (
    REPO, PROJECT
    )

def tag(stack, target_environment: str):
    """
    Adds a tag to all constructs in the stack

    @param stack: The stack to tag
    @param target_environment: The environment the stack is deployed to
    """

    cdk.Tags.of(stack).add("REPO", REPO)
    cdk.Tags.of(stack).add("PROJECT", PROJECT)
    cdk.Tags.of(stack).add("ENVIRONMENT", target_environment)