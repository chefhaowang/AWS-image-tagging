import json
import boto3

sns = boto3.client('sns')


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Parse the request body
        request_data = json.loads(event['body'])
        print("Parsed request data:", request_data)

        # Extract the user email
        user_email = request_data.get('user_email')

        if not user_email:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps('Bad Request: Missing user_email')
            }

        # Get the list of tags for the SNS topic
        response = sns.list_tags_for_resource(
            # Replace with your SNS Topic ARN
            ResourceArn='arn:aws:sns:us-east-1:064005534643:tagsdetecting'
        )

        tags = response['Tags']
        print(f"Retrieved tags: {tags}")

        # Filter tags by user_email
        filtered_tags = [tag['Key']
                         for tag in tags if tag['Value'] == user_email]
        print(f"Filtered tags for {user_email}: {filtered_tags}")

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'keys': filtered_tags})
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
