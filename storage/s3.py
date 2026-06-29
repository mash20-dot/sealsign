import boto3
from botocore.client import Config
import os

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('CLOUDFLARE_R2_ENDPOINT'),
        aws_access_key_id=os.getenv('CLOUDFLARE_R2_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('CLOUDFLARE_R2_SECRET_KEY'),
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def upload_file(file_bytes, key, content_type):
    client = get_s3_client()
    bucket = os.getenv('CLOUDFLARE_R2_BUCKET')
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_bytes,
        ContentType=content_type
    )
    return key

def delete_file(key):
    client = get_s3_client()
    bucket = os.getenv('CLOUDFLARE_R2_BUCKET')
    client.delete_object(Bucket=bucket, Key=key)

def get_presigned_url(key, expires_in=3600):
    client = get_s3_client()
    bucket = os.getenv('CLOUDFLARE_R2_BUCKET')
    url = client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expires_in
    )
    return url