import json
import base64
import boto3
import os
import uuid

FOLDER = "image/"

BUCKET = 'fullsize-images-67'
REGION = 'us-east-1'
s3 = boto3.client('s3', region_name=REGION)


# format :   {file:"xxxxxxxxxbase64","username":" ","name":"123.jpg"}
def lambda_handler(event, context):
    try:
        data = json.loads(event['body'])
        image = data["file"]
        user_email = data["user_email"]
        name = data['name']

        _, suffix = os.path.splitext(name)
        id = uuid.uuid1()

        # key for normal image
        key = user_email + "/" + str(id.hex) + suffix

        # read image
        decoded = base64.b64decode(image)

        # save into s3
        s3.put_object(Bucket=BUCKET, Key=key, Body=decoded,
                      ContentType='mimetype', ContentDisposition='inline', ACL='public-read')

        return {
            'statusCode': 200,
            'body': json.dumps("Image upload success"),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            }
        }

    except s3.exceptions.NoSuchBucket as e:
        return {
            'statusCode': 404,
            'body': json.dumps(f"Bucket {BUCKET} does not exist"),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred: {str(e)}"),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            }

        }
