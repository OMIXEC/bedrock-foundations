This `README.md` is crafted for a high-impact GitHub repository. It focuses on the serverless "End-to-End" nature of the project and provides clear, actionable steps for other developers to replicate your success.

---

# ✍️ Serverless AI Blog Generator

### AWS Bedrock | AWS Lambda | API Gateway | Amazon S3

A fully serverless, end-to-end Generative AI pipeline that automates blog creation. Using **Amazon Bedrock (LLaMA 3)**, this project takes a simple topic via a REST API and transforms it into a structured, professional blog post stored automatically in **Amazon S3**.

---

## 🏗️ Architecture Overview

1. **Trigger:** A `POST` request is sent to **API Gateway** with a JSON body.
2. **Compute:** **AWS Lambda** processes the request and constructs a prompt.
3. **Intelligence:** **Amazon Bedrock (Meta LLaMA 3)** generates a 300-500 word blog.
4. **Storage:** The final text is saved as a `.txt` file in an **S3 Bucket** with a unique timestamp.

---

## 🚀 Key Features

* **Prompt Engineering:** Arofessional formatting (5 subtopics + conclusion).
* **Serverless Scaling:** No servers to manage; pays only for what you use.
* **Custom Lambda Layers:** Deployment strategy for utilizing the latest `boto3` SDK.
* **Persistent Storage:** Organized S3 folder structure for output management.

---

## 🛠️ Setup Instructions

### 1. Amazon Bedrock Access

* Navigate to **Amazon Bedrock** in `ap-south-1` (or your preferred region).
* Go to **Model Access** and ensure **Meta LLaMA 3** (or Titan) is granted.

### 2. S3 Bucket Setup

* Create a bucket (e.g., `aws-bedrock-blog-output`).
* Ensure the Lambda IAM Role has `s3:PutObject` permissions for this bucket.

### 3. Lambda Configuration & Layer

Amazon Bedrock requires an updated `boto3` version not available in standard Lambda runtimes.

* **Create the Layer:**
```bash
mkdir python
pip install boto3 -t python/
zip -r boto3_layer.zip python

```


* **Upload:** Creatnew Lambda Layer in the console and attach it to your function.
* **Timeout:** Set timeout to **1 minute** (LLMs take time to think!).

### 4. API Gateway Setup

* **Type:** HTTP API.
* **Route:** `POST /blog-generation`.
* **Integration:** Lambda Proxy Integration.

---

## 📂 Code Implementation

```python
import boto3
import json
from datetime import datetime

# Initialize clients
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
s3 = boto3.client('s3')

def lambda_handler(event, context):
    body = json.loads(event['body'])
    topic = body['blog_topic']
    
    # Bedrock Payload
    prompt = f"Write a professional blog about {topic} with 5 subtopics and a conclusion."
    payload = {
        "prompt": prompt,
        "max_gen_len": 600,
        "temperature": 0.5
    }
    
    # Invoke Model
    response = bedrock.invoke_model(
        body=json.dumps(payload),
        modelId="meta.llama3-8b-instruct-v1:0"
    )
    
    # Parse & Save
    result = json.loads(response.get('body'read())
    blog_content = result['generation']
    
    file_name = f"blog-output/{datetime.now().strftime('%H%M%S')}.txt"
    s3.put_object(Bucket='YOUR_BUCKET_NAME', Key=file_name, Body=blog_content)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Blog Generation Completed and Saved to S3')
    }

```

---

## 🧪 Testing with ReqBin / Postman

* **Method:** `POST`
* **Endpoint:** `https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev/blog-generation`
* **Body:**
```json
{
  "blog_topic": "The Future of Serverless AI in 2026"
}

```



---

## 🎯 Project Takeaways

* Learned to handle **LLM Inference** via API.
* Mastered **Lambda Layers** for dependency management.
* Implemented **Serverless Integration** patterns between API Gateway, Compute, and Storage.

---

**Author:** [OMIXEC]

