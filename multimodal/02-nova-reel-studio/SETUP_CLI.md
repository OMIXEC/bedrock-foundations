# Amazon Bedrock Nova Reel Setup Guide

To use Nova Reel for video generation, you need to configure your AWS environment with the correct permissions and an S3 bucket for output.

## 1. Create an S3 Output Bucket

Nova Reel is asynchronous and writes the generated video to S3.

```bash
# Create a new bucket (replace with your unique name)
aws s3 mb s3://nova-reel-output-yourname --region us-east-1
```

## 2. Set Environment Variable

Update your backend environment or shell to use this bucket.

```bash
export NOVA_REEL_OUTPUT_BUCKET=nova-reel-output-yourname
```

## 3. IAM Policy

Ensure your IAM User/Role has the following policy attached:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetBucketLocation"],
      "Resource": "arn:aws:s3:::nova-reel-output-yourname/*"
    }
  ]
}
```

## 4. Model Access

Ensure you have requested access to **Amazon Nova Reel** in the Bedrock console (region `us-east-1`).
