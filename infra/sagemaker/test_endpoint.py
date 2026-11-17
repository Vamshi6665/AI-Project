"""Smoke-test the endpoint with the same payload shape the backend sends.

    python infra/sagemaker/test_endpoint.py [--endpoint-name clinical-ai-gptoss-20b] [--region us-east-1]
"""
import argparse
import json
import time

import boto3

p = argparse.ArgumentParser()
p.add_argument("--endpoint-name", default="clinical-ai-gptoss-20b")
p.add_argument("--region", default="us-east-1")
args = p.parse_args()

runtime = boto3.client("sagemaker-runtime", region_name=args.region)
body = {
    "model": "openai/gpt-oss-20b",
    "messages": [
        {"role": "system", "content": "Return only a JSON object."},
        {"role": "user", "content": 'Extract {"name": ..., "dob": ...} from: Patient Jane Roe, born 1980-02-29.'},
    ],
    "max_tokens": 512,
    "temperature": 0,
    "reasoning_effort": "low",
}
start = time.time()
resp = runtime.invoke_endpoint(
    EndpointName=args.endpoint_name, ContentType="application/json", Accept="application/json", Body=json.dumps(body)
)
payload = json.loads(resp["Body"].read())
print(f"Latency: {time.time() - start:.1f}s")
print("Answer :", payload["choices"][0]["message"].get("content"))
print("Usage  :", payload.get("usage"))
