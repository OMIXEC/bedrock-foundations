import json
import boto3
import base64
import datetime
import re  # Added this import

client_bedrock = boto3.client('bedrock-runtime')
client_s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Everything below here must be indented by 4 spaces
    input_prompt = event.get('prompt', 'default prompt')
    
    # Bedrock Call
    response_bedrock = client_bedrock.invoke_model(
        contentType='application/json', 
        accept='application/json',
        modelId='amazon.titan-image-generator-v2:0',
        body=json.dumps({
            "taskType": "TEXT_IMAGE", 
            "textToImageParams": {"text": input_prompt}
        })
    )
    
    response_bedrock_byte = json.loads(response_bedrock['body'].read())
    response_bedrock_base64 = response_bedrock_byte['images'][0]
    response_bedrock_finalimage = base64.b64decode(response_bedrock_base64)
    
    # FIX: Clean naming logic (Indented 4 spaces)
    # 1. Get the prompt from the event (ensure it's not empty)
    input_prompt = event.get('prompt', 'generated_image')

    # 2. Create a dynamic slug: 
    # This takes the first 25 characters, removes weird symbols, and replaces spaces with '_'
    dynamic_slug = re.sub(r'[^a-zA-Z0-9\s]', '', input_prompt[:25]) # Remove special chars
    dynamic_slug = dynamic_slug.strip().replace(' ', '_').lower()   # Spaces to underscores

    # 3. Add a precise timestamp (including microseconds to prevent collisions)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')

    # 4. Final unique filename
    poster_name = f"posters/{dynamic_slug}_{timestamp}.png"
    
    # S3 Upload
    client_s3.put_object( 
        Bucket='gen-movie-descriptions-12143f23',
        Body=response_bedrock_finalimage,
        ContentType='image/png',
        Key=poster_name
    )

    # Pre-Signed URL
    generate_presigned_url = client_s3.generate_presigned_url(
        'get_object', 
        Params={'Bucket': 'gen-movie-descriptions-12143f23', 'Key': poster_name}, 
        ExpiresIn=3600
    )
    
    return {
        'statusCode': 200,
        'body': generate_presigned_url
    }
