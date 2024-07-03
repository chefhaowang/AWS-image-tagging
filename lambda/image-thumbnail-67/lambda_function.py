import json
import boto3
from PIL import Image
import io
import urllib.parse
import urllib.request

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Set your target bucket for thumbnails
# Replace with the name of your target bucket for thumbnails
TARGET_BUCKET = 'thumbnails-images-67'


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Get the S3 bucket and object key from the event
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        print("Processing file from bucket:", source_bucket, "key:", key)

        # Decode the URL-encoded key
        key = urllib.parse.unquote(key)
        print("Decoded key:", key)

        # Extract user email from the key
        if '/' in key:
            user_email, image_filename = key.split('/', 1)
            print("Extracted user email:", user_email)
        else:
            print("Key format is incorrect, cannot extract user email.")
            raise ValueError(
                "Key format is incorrect, cannot extract user email.")

        # Construct the basic URL for the original image
        original_url = f"https://{source_bucket}.s3.amazonaws.com/{key}"
        print("Constructed URL for original image:", original_url)

        # Download the original image using the constructed URL
        response = urllib.request.urlopen(original_url)
        image_data = response.read()

        # Create a thumbnail
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail((128, 128))
        thumbnail_buffer = io.BytesIO()
        image.save(thumbnail_buffer, format='JPEG')
        thumbnail_buffer.seek(0)
        print("Thumbnail created successfully")

        # Save the thumbnail to the target S3 bucket in the same directory and with the same file name
        thumbnail_key = key
        s3.put_object(Bucket=TARGET_BUCKET, Key=thumbnail_key,
                      Body=thumbnail_buffer, ContentType='image/jpeg', ACL='public-read')
        print("Thumbnail uploaded to bucket:",
              TARGET_BUCKET, "key:", thumbnail_key)

        # Construct the basic URL for the thumbnail image
        thumbnail_url = f"https://{TARGET_BUCKET}.s3.amazonaws.com/{thumbnail_key}"
        print("Constructed URL for thumbnail image:", thumbnail_url)

        # Prepare the response
        response_payload = {
            'user_email': user_email,
            'image_key': key,
            'original_url': original_url,
            'thumbnail_url': thumbnail_url
        }

        # Invoke the second Lambda function with the URLs
        lambda_client.invoke(
            # Replace with your second Lambda function's name
            FunctionName='object-detection-67',
            InvocationType='Event',
            Payload=json.dumps(response_payload)
        )
        print("Second Lambda function invoked with payload:",
              json.dumps(response_payload))

        return {
            'statusCode': 200,
            'body': json.dumps(response_payload),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }

    except Exception as e:
        print("Error processing file:", str(e))
        raise e
