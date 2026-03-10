This `README.md` is designed to be professional, scannable, and technically complete. It incorporates all the troubleshooting we did (IAM fixes, naming conventions, and model versions) while respecting the original project structure provided.

---

# 🎬 Bedrock Movie Poster Generator

A serverless Generative AI application that transforms text prompts into high-quality movie posters using **Amazon Bedrock** and **AWS Lambda**. The system generates a unique image, stores it in **Amazon S3**, and returns a secure, time-limited **Pre-Signed URL** via **API Gateway**.

## 🚀 Features

* **AI Image Generation:** Leverages Amazon Titan Image Generator v2 (or Stable Diffusion).
* **Dynamic Naming:** Intelligent filename generation using prompt-based "slugs" and high-precision timestamps to prevent file overwrites.
* **Secure Delivery:** Uses S3 Pre-Signed URLs so images remain private while accessible to the user for a limited time.
* **Serverless REST API:** Fully integrated with API Gateway for external trigsupport (e.g., Postman).

---

## 🛠️ Technical Stack

* **Compute:** AWS Lambda (Python 3.11+)
* **AI Engine:** Amazon Bedrock (`amazon.titan-image-generator-v2:0`)
* **Storage:** Amazon S3
* **API:** AWS API Gateway (REST)
* **Permissions:** IAM (Identity and Access Management)

---

## 📋 Prerequisites

* **Boto3 Version:** Ensure your environment uses `boto3 > 1.28.63` to support Bedrock Runtime.
* **Model Access:** You must manually "Request Access" for the **Titan Image Generator** in the AWS Bedrock Console (Region: `us-east-1`).
* **IAM Permissions:** The Lambda execution role requires a specific policy to interact with Bedrock and S3.

---

## 🔧 Setup & Implementation

### 1. Storage (S3)

Create an S3 bucket named `gen-movie-descriptions-12143f23` (or your preferred unique name). This will store the raw `.png` files.

### 2. Permissions (IAM)

The Lambda function needs a custom **Inline Policy** to function. Use the following template:

```json
{
    "Version": "2012-10-17",
    "Statemen      {
            "Sid": "BedrockInvoke",
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-image-generator-v*"
        },
        {
            "Sid": "S3UploadAndSign",
            "Effect": "Allow",
            "Action": ["s3:PutObject", "s3:GetObject"],
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        },
        {
            "Sid": "Logging",
            "Effect": "Allow",
            "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}

```

### 3. Lambda Configuration

* **Runtime:** Python 3.11
* **Timeout:** Increase from 3s to **30s** (Image generation is a heavy process).
* **Memory:** Minimum **512MB** recommended.

### 4. API Gateway Integration

1. Create a **REST API** named `movePosterDesignAPI`.
2. Create a **GET** method.
3. **Mapping Template:** In the "Integration Request", set the `application/json` template to map URL query parameters to the Lambda event:
```json
{
  "prompt" : "$input.params('prompt')"
}

```



---

## 💻 Code Logic (The "Brain")

The Lambda follows an 8-step process:

1. **Extract:** Get `prompt` from the API event.
2. **Generate Name:** Create a slug from the prompt + timestamp (e.g., `israeli_marvel_2026-02-04.png`).
3. **Invoke Bedrock:** Send the prompt to Titan v2.
4. **Parse:** Decode the Base64 image data from the Bedrock response.
5. **Upload:** Store the binary data in S3 with `ContentType='image/png'`.
6. **Sign:** Generate a Pre-Signed URL for the S3 object.
7. **Respond:** Return the URL to the user.

---

## 🧪 Testing

**Test Event (Lambda Console):**

```json
{
  "prompt": "A futuristic spy agent fighting in a snowy Greek city, Aaron Jasinski style"
}

```

**Postman/CURL:**
`GET https://your-api-id.execute-api.us-east-1.amazonaws.com/dev?prompt=your+text+here`

---

## 📝 Author's Note

**OMIXEC**
