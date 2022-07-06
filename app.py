#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import Environment

from lib.config import (ACCOUNT_ID, BASE_URL, DEPLOYMENT, DEV, GIT_BRANCH,
                        LEGACY, PROD, PROJECT, QA, REGION, REPO, SANDBOX,
                        VPN_CIDR, VPN_IP, VPN_SG_ID, get_all_configurations,
                        get_logical_id_prefix)
from lib.tagging import tag
from stacks.atlas_stack import accountStacks

# Specify which deployment environments a pipeline should be created for
# Adding stages to this list will allow for a deployment pipeline to be
# set up in the associated account/environment.
deploy_environments = [SANDBOX, 
                        # DEV, 
                        # QA, 
                        #PROD, 
                        # LEGACY
                        ]

app = cdk.App()
# Map values from lib/config.py into placeholders
raw_mappings = get_all_configurations()
deployment_account = raw_mappings[DEPLOYMENT][ACCOUNT_ID]
deployment_region = raw_mappings[DEPLOYMENT][REGION]
deployment_aws_env = {
    'account': deployment_account,
    'region': deployment_region
}
logical_id_prefix = get_logical_id_prefix()
gitrepo=REPO

# Create prop dictionaries for each environment, then deploy a pipeline
# for that environment
env_props = {}
for de in deploy_environments:

    target_environment = de
    target_account = raw_mappings[de][ACCOUNT_ID]
    target_region = raw_mappings[de][REGION]
    target_branch = raw_mappings[de][GIT_BRANCH]
    base_url = raw_mappings[de][BASE_URL]
    target_aws_env = {
        'account': target_account,
        'region': target_region,
    }

    # SET ALL NAMESPACE AND OTHER PROPERTIES HERE.  THEY WILL BE
    # ACCESSIBLE THROUGHOUT THE STACKS AND APPLICATION
    prop = {'namespace': 'rm',
             'gitrepo': gitrepo,
             'gitbranch': target_branch,
             'targetenv': target_aws_env,
             'environment': de.upper(),
             'accountID': target_account,
             'project' : PROJECT,
             'baseURL' : base_url,
             'vpnIP' : VPN_IP
    }
    env_props[de] = prop

    deploymentStack = accountStacks(app, 
        f"{prop['project']}-{prop['environment']}",
        env=Environment(
            account=deployment_aws_env['account'], 
            region=deployment_aws_env['region']
            ),
        props=prop
    )
    tag(deploymentStack, de)

app.synth()
