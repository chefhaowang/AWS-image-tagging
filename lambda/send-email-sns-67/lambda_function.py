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

        # Set up the SNS topic and message
        # Replace with your SNS Topic ARN
        topic_arn = 'arn:aws:sns:us-east-1:064005534643:tagsdetecting'
        subject = 'Hello '
        message = 'This is a test email from AWS Lambda and SNS.'

        # Publish the message to SNS
        response = sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject,
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': user_email
                }
            }
        )

        print("Email sent response:", response)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('Email sent successfully')
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
