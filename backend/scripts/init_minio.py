import json
import sys

import boto3
from botocore.exceptions import ClientError

sys.path.append("/app")

from app.core.config import settings


def init_minio():
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )

    try:
        s3_client.head_bucket(Bucket=settings.S3_BUCKET)
        print(f"✓ Bucket '{settings.S3_BUCKET}' already exists")
    except ClientError as e:
        # Check if the error is because bucket doesn't exist
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404':
            s3_client.create_bucket(Bucket=settings.S3_BUCKET)

            # Restricted bucket policy - only authenticated users can access
            # For public access, set Principal to {"AWS": "*"}
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{settings.S3_ACCESS_KEY}:root"},
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject"
                        ],
                        "Resource": f"arn:aws:s3:::{settings.S3_BUCKET}/*",
                    }
                ],
            }

            s3_client.put_bucket_policy(
                Bucket=settings.S3_BUCKET,
                Policy=json.dumps(bucket_policy),
            )

            print(f"✓ Bucket '{settings.S3_BUCKET}' created successfully with restricted access")
        else:
            # Re-raise if it's a different error
            print(f"❌ Error accessing bucket: {error_code} - {e}")
            raise


if __name__ == "__main__":
    init_minio()
