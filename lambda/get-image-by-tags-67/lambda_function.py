import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('user-image-tags')


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        if 'body' in event:
            body = json.loads(event['body'])
            user_id = body.get('user_id')
            tags = body.get('tags', {})
            print(f"we have got tags: {tags}")
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps('Bad Request: Missing user_id in the request')
                }
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps('Bad Request: Missing body in the request')
            }

        print(f"Received user_id: {user_id}, tags: {tags}")

       # Perform DynamoDB query with filter expressions
        filter_expression = Key('user_id').eq(user_id)
        for tag, min_count in tags.items():
            condition = Attr(f'tags.{tag}').gte(min_count)
            if filter_expression is None:
                filter_expression = condition
            else:
                filter_expression = filter_expression & condition

        response = table.scan(
            FilterExpression=filter_expression
        )

        items = response['Items']
        print(f"Found items: {items}")

        # Collect the thumbnail URLs
        links = [item['thumbnail_url'] for item in items]

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'links': links})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred: {str(e)}"),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
