# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import re

#GIT REPO
REPO = 'eventbridge-atlas'

#PROJECT
PROJECT = 'Eventbridge-Atlas'

# Environments (targeted at accounts)
DEPLOYMENT = 'Deployment'
SANDBOX = 'Sandbox'
DEV = 'Develop'
QA = 'QA'
PROD = 'Prod'
LEGACY = 'Legacy'

# The following constants are used to map to parameter/secret paths
ENVIRONMENT = 'environment'

# Manual Inputs
GITHUB_REPOSITORY_OWNER_NAME = 'github_repository_owner_name'
GITHUB_REPOSITORY_NAME = 'github_repository_name'
ACCOUNT_ID = 'account_id'
REGION = 'region'
LOGICAL_ID_PREFIX = 'logical_id_prefix'
RESOURCE_NAME_PREFIX = 'resource_name_prefix'
VPC_CIDR = 'vpc_cidr'
GIT_BRANCH = 'git_branch'
BASE_URL = 'base_url'
ENVIRONMENT = 'environment'

# Secrets Manager Inputs
GITHUB_TOKEN = 'github_token'

# Other Environment-Agnostic Constants
VPN_IP = '35.161.109.174/32'
VPN_CIDR = '10.13.32.0/21'
VPN_SG_ID = 'sg-014e44f6b546266be'

def get_local_configuration(environment: str) -> dict:
    """
    Provides manually configured variables that are validated for quality and safety.

    @param: environment str: The environment used to retrieve corresponding configuration
    @raises: Exception: Throws an exception if the resource_name_prefix does not conform
    @raises: Exception: Throws an exception if the requested environment does not exist
    @returns: dict:
    """
    local_mapping = {
        DEPLOYMENT: {
            ACCOUNT_ID: '700154229199',
            REGION: 'us-west-2',
            GITHUB_REPOSITORY_OWNER_NAME: 'RealtyMogul',
            # If you use GitHub / GitHub Enterprise, this will be the organization name
            GITHUB_REPOSITORY_NAME: 'eventbridge-atlas',
            # This is used in the Logical Id of CloudFormation resources
            # We recommend capital case for consistency. e.g. DataLakeCdkBlog
            LOGICAL_ID_PREFIX: 'ea',
            # This is used in resources that must be globally unique!
            # It may only contain alphanumeric characters, hyphens, and cannot contain trailing hyphens
            # E.g. unique-identifier-data-lake
            RESOURCE_NAME_PREFIX: 'rm',
            GIT_BRANCH: 'main'
        },
        SANDBOX: {
            ACCOUNT_ID: '830361487402',
            REGION: 'us-west-2',
            VPC_CIDR: '10.9.0.0/16',
            GIT_BRANCH: 'sandbox',
            BASE_URL: 'sandbox.realtymogul.com',
            ENVIRONMENT: 'Sandbox'
        },
        DEV: {
            ACCOUNT_ID: '894461340758',
            REGION: 'us-west-2',
            VPC_CIDR: '10.10.0.0/16',
            GIT_BRANCH: 'develop',
            BASE_URL: 'develop.realtymogul.com',
            ENVIRONMENT: 'Develop'
        },
        QA: {
            ACCOUNT_ID: '194468182769',
            REGION: 'us-west-2',
            VPC_CIDR: '10.11.0.0/16',
            GIT_BRANCH: 'QA',
            BASE_URL: 'qa.realtymogul.com',
            ENVIRONMENT: 'QA'
        },
        PROD: {
            ACCOUNT_ID: '444695359454',
            REGION: 'us-west-2',
            VPC_CIDR: '10.12.0.0/16',
            GIT_BRANCH: 'prod',
            BASE_URL: 'realtymogul.com',
            ENVIRONMENT: 'Prod'
        },
        LEGACY: {
            ACCOUNT_ID: '804885395568',
            REGION: 'us-west-2',
            VPC_CIDR: '10.1.0.0/16',
            GIT_BRANCH: 'prod',
            BASE_URL: 'realtymogul.com',
            ENVIRONMENT: 'Prod'
        }
    }

    resource_prefix = local_mapping[DEPLOYMENT][RESOURCE_NAME_PREFIX]
    if (
        not re.fullmatch('^[a-z|0-9|-]+', resource_prefix)
        or '-' in resource_prefix[-1:] or '-' in resource_prefix[1]
    ):
        raise Exception('Resource names may only contain lowercase Alphanumeric and hyphens '
                        'and cannot contain leading or trailing hyphens')

    if environment not in local_mapping:
        raise Exception(f'The requested environment: {environment} does not exist in local mappings')

    return local_mapping[environment]


def get_environment_configuration(environment: str) -> dict:
    """
    Provides all configuration values for the given target environment

    @param environment str: The environment used to retrieve corresponding configuration

    @return: dict:
    """
    cloudformation_output_mapping = {
        ENVIRONMENT: environment,
    }

    return {**cloudformation_output_mapping, **get_local_configuration(environment)}


def get_all_configurations() -> dict:
    """
    Returns a dict mapping of configurations for all environments.
    These keys correspond to static values, CloudFormation outputs, and Secrets Manager (passwords only) records.

    @return: dict:
    """
    return {
        DEPLOYMENT: {
            ENVIRONMENT: DEPLOYMENT,
            GITHUB_TOKEN: '/CDKPipelines/GitHubToken',
            **get_local_configuration(DEPLOYMENT),
        },
        DEV: get_environment_configuration(DEV),
        QA: get_environment_configuration(QA),
        PROD: get_environment_configuration(PROD),
        SANDBOX: get_environment_configuration(SANDBOX),
        LEGACY: get_environment_configuration(LEGACY)
    }


def get_logical_id_prefix() -> str:
    """Returns the logical id prefix to apply to all CloudFormation resources

    @return: str:
    """
    return get_local_configuration(DEPLOYMENT)[LOGICAL_ID_PREFIX]


def get_resource_name_prefix() -> str:
    """Returns the resource name prefix to apply to all resources names

    @return: str:
    """
    return get_local_configuration(DEPLOYMENT)[RESOURCE_NAME_PREFIX]
