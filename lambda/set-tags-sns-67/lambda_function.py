import json
import boto3

sns = boto3.client('sns')


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Parse the request body
        request_data = json.loads(event['body'])
        print("Parsed request data:", request_data)

        # Extract the user email and keys
        user_email = request_data.get('user_email')
        keys = request_data.get('keys', [])

        if not user_email or not keys:
            return {
                'statusCode': 400, 'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps('Bad Request: Missing user_email or keys')
            }

        # Create tags to set
        tags = [{'Key': key, 'Value': user_email} for key in keys]
        print(f"Setting tags: {tags}")

        # Set tags for the SNS topic
        response = sns.tag_resource(
            # Replace with your SNS Topic ARN
            ResourceArn='arn:aws:sns:us-east-1:064005534643:tagsdetecting',
            Tags=tags
        )

        print("Tags set response:", response)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('Tags set successfully')
        }

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(f"An error occurred: {str(e)}")
        }
