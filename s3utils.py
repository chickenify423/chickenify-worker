import os, boto3

S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION")
S3_KEY = os.getenv("S3_KEY")
S3_SECRET = os.getenv("S3_SECRET")

s3 = boto3.client("s3",
    region_name=S3_REGION,
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET) if all([S3_BUCKET, S3_REGION, S3_KEY, S3_SECRET]) else None

def put_input_bytes(user_id: int, job_id: int, content: bytes) -> str:
    if not s3:
        raise ValueError("S3 not configured")
    key = f"inputs/{user_id}/{job_id}.wav"
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=content, ContentType="audio/wav")
    return key

def output_url(key: str) -> str:
    return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"
