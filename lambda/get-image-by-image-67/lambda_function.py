import json
import boto3
import base64
import numpy as np
import cv2
import tempfile
import os

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Bucket and keys for YOLO configuration files
YOLO_BUCKET = 'yolo-configs-67'
YOLO_WEIGHTS_KEY = 'yolov3-tiny.weights'
YOLO_CONFIG_KEY = 'yolov3-tiny.cfg'
YOLO_CLASSES_KEY = 'coco.names'
# Replace with your DynamoDB table name
DYNAMODB_TABLE_NAME = 'user-image-tags'


def download_yolo_files():
    yolo_dir = tempfile.gettempdir()
    weights_path = os.path.join(yolo_dir, YOLO_WEIGHTS_KEY)
    config_path = os.path.join(yolo_dir, YOLO_CONFIG_KEY)
    classes_path = os.path.join(yolo_dir, YOLO_CLASSES_KEY)

    print(f"Downloading {YOLO_WEIGHTS_KEY} from bucket {
          YOLO_BUCKET} to {weights_path}")
    s3.download_file(YOLO_BUCKET, YOLO_WEIGHTS_KEY, weights_path)
    print(f"Downloading {YOLO_CONFIG_KEY} from bucket {
          YOLO_BUCKET} to {config_path}")
    s3.download_file(YOLO_BUCKET, YOLO_CONFIG_KEY, config_path)
    print(f"Downloading {YOLO_CLASSES_KEY} from bucket {
          YOLO_BUCKET} to {classes_path}")
    s3.download_file(YOLO_BUCKET, YOLO_CLASSES_KEY, classes_path)

    return weights_path, config_path, classes_path


def load_yolo(weights_path, config_path, classes_path):
    print(f"Loading YOLO model from {weights_path} and {config_path}")
    net = cv2.dnn.readNet(weights_path, config_path)
    print(f"Reading classes from {classes_path}")
    with open(classes_path, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
    return net, classes


def detect_objects(net, classes, image):
    height, width, channels = image.shape
    print(f"Image dimensions: {width}x{height}, Channels: {channels}")
    blob = cv2.dnn.blobFromImage(
        image, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    print("Running forward pass of YOLO model")

    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1]
                     for i in net.getUnconnectedOutLayers()]
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    print("Applying Non-Max Suppression")
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    detected_objects = []
    for i in range(len(boxes)):
        if i in indexes:
            detected_objects.append(str(classes[class_ids[i]]))

    return detected_objects


def query_dynamodb(user_email, detected_tags):
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    filter_expression = " and ".join(
        [f"tags.#tag_{tag} > :min_count" for tag in detected_tags])
    expression_attribute_names = {f"#tag_{tag}": tag for tag in detected_tags}
    expression_attribute_values = {":min_count": 0}

    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )

    items = response.get('Items', [])
    return [item['thumbnail_url'] for item in items if item['user_id'] == user_email]


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        if 'body' not in event:
            print("Error: 'body' key is missing in event")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps('Bad Request: Missing body in the request')
            }

        data = json.loads(event['body'])
        print(f"Received data: {data}")

        image = data["image"]
        user_email = data["user_email"]

        # Read image
        print("Decoding base64 image")
        image_data = base64.b64decode(image)

        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            print("Failed to decode image, image is None")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps('Bad Request: Unable to decode image')
            }

        # Download YOLO configuration files
        print("Downloading YOLO configuration files")
        weights_path, config_path, classes_path = download_yolo_files()

        # Load YOLO model
        print("Loading YOLO model")
        net, classes = load_yolo(weights_path, config_path, classes_path)

        # Detect objects in the image
        print("Detecting objects in the image")
        detected_objects = detect_objects(net, classes, image)
        detected_tags = list(set(detected_objects))  # Remove duplicates

        print(f"Detected objects: {detected_objects}")
        print(f"Unique detected tags: {detected_tags}")

        # Query DynamoDB
        print("Querying DynamoDB")
        matching_thumbnails = query_dynamodb(user_email, detected_tags)

        print(f"Matching thumbnails: {matching_thumbnails}")

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'matching_thumbnails': matching_thumbnails})
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
