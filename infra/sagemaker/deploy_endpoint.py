"""Deploy OpenAI gpt-oss-20b to a SageMaker real-time endpoint using AWS's vLLM container.

Run from your laptop (needs admin-ish AWS credentials via `aws configure`):

    pip install boto3
    python infra/sagemaker/deploy_endpoint.py --role-arn arn:aws:iam::<ACCOUNT_ID>:role/clinical-ai-sagemaker-role

Takes ~10-20 minutes (instance boot + ~13 GB model download from Hugging Face + vLLM warm-up).
BILLING STARTS when the endpoint is InService. Delete it with delete_endpoint.py when you stop.

Image + AMI values follow AWS's vLLM DLC guide:
https://aws.github.io/deep-learning-containers/vllm/deployment/sagemaker/
If a newer image tag is listed there, pass it with --image-tag.
"""
import argparse
import time

import boto3

DLC_ACCOUNT = "763104351884"  # AWS Deep Learning Containers registry account


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--role-arn", required=True, help="SageMaker execution role ARN")
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--endpoint-name", default="clinical-ai-gptoss-20b")
    p.add_argument("--instance-type", default="ml.g5.2xlarge")
    p.add_argument("--image-tag", default="server-sagemaker-cuda-v2.8")
    p.add_argument("--ami-version", default="al2-ami-sagemaker-inference-gpu-3-1")
    p.add_argument("--max-model-len", default="16384", help="Context window to allocate KV cache for")
    args = p.parse_args()

    sm = boto3.client("sagemaker", region_name=args.region)
    suffix = time.strftime("%Y%m%d-%H%M%S")
    model_name = f"{args.endpoint_name}-model-{suffix}"
    config_name = f"{args.endpoint_name}-config-{suffix}"
    image = f"{DLC_ACCOUNT}.dkr.ecr.{args.region}.amazonaws.com/vllm:{args.image_tag}"

    print(f"Image:    {image}")
    print(f"Instance: {args.instance_type}")

    # 1) Model = container image + environment (which HF model vLLM should load).
    sm.create_model(
        ModelName=model_name,
        ExecutionRoleArn=args.role_arn,
        PrimaryContainer={
            "Image": image,
            "Environment": {
                "SM_VLLM_MODEL": "openai/gpt-oss-20b",            # -> --model openai/gpt-oss-20b
                "SM_VLLM_MAX_MODEL_LEN": args.max_model_len,       # -> --max-model-len 16384
            },
        },
    )
    print(f"Created model           {model_name}")

    # 2) Endpoint config = which model, on what hardware, how many instances.
    sm.create_endpoint_config(
        EndpointConfigName=config_name,
        ProductionVariants=[{
            "VariantName": "AllTraffic",
            "ModelName": model_name,
            "InstanceType": args.instance_type,
            "InitialInstanceCount": 1,
            "InferenceAmiVersion": args.ami_version,
            # The model downloads at startup; give the health check time before SageMaker gives up.
            "ContainerStartupHealthCheckTimeoutInSeconds": 1800,
        }],
    )
    print(f"Created endpoint config {config_name}")

    # 3) Endpoint = the HTTPS URL your backend invokes. Update in place if it already exists.
    existing = [e["EndpointName"] for e in sm.list_endpoints(NameContains=args.endpoint_name)["Endpoints"]]
    if args.endpoint_name in existing:
        sm.update_endpoint(EndpointName=args.endpoint_name, EndpointConfigName=config_name)
        print(f"Updating endpoint       {args.endpoint_name}")
    else:
        sm.create_endpoint(EndpointName=args.endpoint_name, EndpointConfigName=config_name)
        print(f"Creating endpoint       {args.endpoint_name}")

    print("Waiting for InService (10-20 min). Follow progress in SageMaker console > Endpoints > Logs.")
    start = time.time()
    sm.get_waiter("endpoint_in_service").wait(
        EndpointName=args.endpoint_name, WaiterConfig={"Delay": 30, "MaxAttempts": 80}
    )
    print(f"InService after {int(time.time() - start) // 60} min. Next: python infra/sagemaker/test_endpoint.py")


if __name__ == "__main__":
    main()
