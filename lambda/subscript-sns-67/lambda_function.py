import boto3
import json

snsClient = boto3.client('sns')


def lambda_handler(event, context):

    try:
        print("Received event:", json.dumps(event))

        # Parse the request body
        request_data = json.loads(event['body'])
        print("Parsed request data:", request_data)

        # Extract the user email and keys
        user_email = request_data.get('user_email')

        # creating Topic and if it already created with the specified name, that topic's ARN is returned without creating a new topic.
        snsArn = 'arn:aws:sns:us-east-1:064005534643:tagsdetecting'
        # crearting a subscriber for the specified SNS Toic
        snsEndpointSusbcribe(snsArn, user_email)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('email subscripted successfully')
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


# Function to create SNS Subscriber for that Topic
def snsEndpointSusbcribe(snsArn, emailId):
    response = snsClient.subscribe(
        TopicArn=snsArn,
        Protocol='email',
        Endpoint=emailId,
    )
