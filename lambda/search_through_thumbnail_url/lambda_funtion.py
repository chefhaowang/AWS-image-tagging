import json
import boto3

REGION = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table('user-image-tags')


def lambda_handler(event, context):
    try:
        data = json.loads(event['body'])
        user_id = data['user_id']
        thumbnail_url = data['thumbnail_url']

        # Query DynamoDB for the image URL
        response = table.get_item(
            Key={
                'user_id': user_id,
                'thumbnail_url': thumbnail_url
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps("Image URL not found"),
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Headers': '*'
                }
            }

        image_url = response['Item']['image_url']

        return {
            'statusCode': 200,
            'body': json.dumps({"image_url": image_url}),
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
