import json
import boto3
import urllib.parse

REGION = 'us-east-1'
BUCKET_FULLSIZE_NAME = 'fullsize-images-67'
BUCKET_THUMBNAIL_NAME = 'thumbnails-images-67'

s3 = boto3.client('s3', region_name=REGION)  # S3 client
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table('user-image-tags')


def extract_key_from_url(url):
    parsed_url = urllib.parse.urlparse(url)
    return urllib.parse.unquote(parsed_url.path.lstrip('/'))


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Parse the request body
        request_data = json.loads(event['body'])
        print("Parsed request data:", request_data)

        # Extract the user ID
        user_id = request_data.get('user_id')
        print("Extracted user ID:", user_id)

        # Extract the thumbnail URLs, default to an empty list
        thumbnail_urls = request_data.get('thumbnail_urls', [])
        print("Extracted thumbnail URLs:", thumbnail_urls)

        for thumbnail_url in thumbnail_urls:
            print(f"Processing thumbnail URL: {thumbnail_url}")

            # Retrieve image information from DynamoDB using user ID and thumbnail URL
            print(f"Retrieving image information from DynamoDB for user {
                  user_id} and thumbnail {thumbnail_url}")
            response = table.get_item(
                Key={
                    'user_id': user_id,
                    'thumbnail_url': thumbnail_url
                }
            )
            print("DynamoDB get_item response:", response)

            if 'Item' in response:
                # Extract S3 keys from URLs
                full_image_url = response['Item'].get('image_url')
                thumbnail_key = extract_key_from_url(thumbnail_url)
                full_image_key = extract_key_from_url(
                    full_image_url) if full_image_url else None

                # Delete the full image from S3 if exists
                if full_image_key:
                    print(f"Deleting full image from S3 bucket {
                          BUCKET_FULLSIZE_NAME} with key {full_image_key}")
                    s3.delete_object(
                        Bucket=BUCKET_FULLSIZE_NAME, Key=full_image_key)

                # Delete the thumbnail from S3
                print(f"Deleting thumbnail from S3 bucket {
                      BUCKET_THUMBNAIL_NAME} with key {thumbnail_key}")
                s3.delete_object(Bucket=BUCKET_THUMBNAIL_NAME,
                                 Key=thumbnail_key)

                # Delete the entry from DynamoDB
                print(f"Deleting item from DynamoDB for user {
                      user_id} and thumbnail {thumbnail_url}")
                table.delete_item(
                    Key={
                        'user_id': user_id,
                        'thumbnail_url': thumbnail_url
                    }
                )
            else:
                print(f"No item found in DynamoDB for user {
                      user_id} and thumbnail {thumbnail_url}")

        print("All specified images and thumbnails deleted successfully")

        # Return a successful response
        return {
            'statusCode': 200,
            'body': json.dumps("Images and thumbnails deleted successfully from DynamoDB and bucket"),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            }
        }

    except Exception as e:
        print(f"An error occurred: {str(e)}")

        # Return an error response
        return {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred: {str(e)}"),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            }
        }
