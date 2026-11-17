"""Stop paying: delete the endpoint plus every endpoint config and model this project created.

    python infra/sagemaker/delete_endpoint.py [--endpoint-name clinical-ai-gptoss-20b] [--region us-east-1]

Re-deploying later is one command (deploy_endpoint.py) and ~15 minutes.
"""
import argparse

import boto3

p = argparse.ArgumentParser()
p.add_argument("--endpoint-name", default="clinical-ai-gptoss-20b")
p.add_argument("--region", default="us-east-1")
args = p.parse_args()

sm = boto3.client("sagemaker", region_name=args.region)
name = args.endpoint_name

try:
    sm.delete_endpoint(EndpointName=name)
    print(f"Deleting endpoint {name} (billing stops once it is gone)")
except sm.exceptions.ClientError as e:
    print(f"Endpoint: {e.response['Error']['Message']}")

for cfg in sm.list_endpoint_configs(NameContains=f"{name}-config")["EndpointConfigs"]:
    sm.delete_endpoint_config(EndpointConfigName=cfg["EndpointConfigName"])
    print(f"Deleted config {cfg['EndpointConfigName']}")

for model in sm.list_models(NameContains=f"{name}-model")["Models"]:
    sm.delete_model(ModelName=model["ModelName"])
    print(f"Deleted model {model['ModelName']}")

print("Done. Check SageMaker console > Inference > Endpoints shows nothing for this project.")
