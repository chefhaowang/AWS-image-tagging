import json
import boto3

REGION = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table('user-image-tags')


def lambda_handler(event, context):
    try:
        # Parse the request body
        request_data = json.loads(event['body'])
        # Extract the user ID
        user_id = request_data.get('user_id')
        # Extract the thumbnail URLs, default to an empty list
        thumbnail_urls = request_data.get('thumbnail_url', [])
        # Extract the request type, default to adding tags
        request_type = request_data.get('type', 1)
        # Extract the tags list, default to an empty list
        tags_list = request_data.get('tags', [])

        # Ensure that tags_list is always a list
        if not isinstance(tags_list, list):
            tags_list = []

        # Convert the tags list to a dictionary where each tag points to a number (default 1)
        tags = {tag: 1 for tag in tags_list}

        # Determine whether to add or remove tags based on the request type
        if request_type == 1:  # Adding tags
            for thumbnail_url in thumbnail_urls:
                # Retrieve image tag information using user ID and thumbnail URL
                response = table.get_item(
                    Key={
                        'user_id': user_id,
                        'thumbnail_url': thumbnail_url
                    }
                )
                # Update image tag information
                if 'Item' in response:
                    existing_tags = response['Item'].get('tags', {})
                    for tag, count in tags.items():
                        # Update tag count
                        existing_tags[tag] = count
                    # Write back to the database
                    table.update_item(
                        Key={
                            'user_id': user_id,
                            'thumbnail_url': thumbnail_url
                        },
                        UpdateExpression='SET tags = :tags',
                        ExpressionAttributeValues={
                            ':tags': existing_tags
                        }
                    )
                else:
                    # If image information does not exist, create new image information and add tags
                    table.put_item(
                        Item={
                            'user_id': user_id,
                            'thumbnail_url': thumbnail_url,
                            'tags': tags
                        }
                    )
        elif request_type == 0:  # Removing tags
            for thumbnail_url in thumbnail_urls:
                # Retrieve image tag information using user ID and thumbnail URL
                response = table.get_item(
                    Key={
                        'user_id': user_id,
                        'thumbnail_url': thumbnail_url
                    }
                )
                if 'Item' in response:
                    existing_tags = response['Item'].get('tags', {})
                    # Remove the target tags from the existing tags
                    for tag in tags.keys():
                        existing_tags.pop(tag, None)
                    # Write back to the database
                    table.update_item(
                        Key={
                            'user_id': user_id,
                            'thumbnail_url': thumbnail_url
                        },
                        UpdateExpression='SET tags = :tags',
                        ExpressionAttributeValues={
                            ':tags': existing_tags
                        }
                    )

        # Return a successful response
        return {
            'statusCode': 200,
            'body': json.dumps("Tags updated successfully"),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            }
        }

    except Exception as e:
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
