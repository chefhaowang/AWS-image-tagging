import json
import boto3
import numpy as np
import urllib.request
import tempfile
import os
import cv2

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('user-image-tags')
sns = boto3.client('sns')

# Bucket and keys for YOLO configuration files
YOLO_BUCKET = 'yolo-configs-67'
YOLO_WEIGHTS_KEY = 'yolov3-tiny.weights'
YOLO_CONFIG_KEY = 'yolov3-tiny.cfg'
YOLO_CLASSES_KEY = 'coco.names'

# Bucket for storing detected objects data


def download_yolo_files():
    yolo_dir = tempfile.gettempdir()
    weights_path = os.path.join(yolo_dir, YOLO_WEIGHTS_KEY)
    config_path = os.path.join(yolo_dir, YOLO_CONFIG_KEY)
    classes_path = os.path.join(yolo_dir, YOLO_CLASSES_KEY)

    try:
        print(f"Downloading {YOLO_CONFIG_KEY} from bucket {
              YOLO_BUCKET} to {config_path}")
        s3.download_file(YOLO_BUCKET, YOLO_CONFIG_KEY, config_path)
    except Exception as e:
        print(f"Failed to download {YOLO_CONFIG_KEY}: {e}")
        raise

    try:
        print(f"Downloading {YOLO_CLASSES_KEY} from bucket {
              YOLO_BUCKET} to {classes_path}")
        s3.download_file(YOLO_BUCKET, YOLO_CLASSES_KEY, classes_path)
    except Exception as e:
        print(f"Failed to download {YOLO_CLASSES_KEY}: {e}")
        raise

    try:
        print(f"Downloading {YOLO_WEIGHTS_KEY} from bucket {
              YOLO_BUCKET} to {weights_path}")
        s3.download_file(YOLO_BUCKET, YOLO_WEIGHTS_KEY, weights_path)
    except Exception as e:
        print(f"Failed to download {YOLO_WEIGHTS_KEY}: {e}")
        raise

    return weights_path, config_path, classes_path


def load_yolo(weights_path, config_path, classes_path):
    print(f"Loading YOLO model from {weights_path} and {config_path}")
    net = cv2.dnn.readNet(weights_path, config_path)
    print(f"Reading classes from {classes_path}")
    with open(classes_path, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
    return net, classes


def detect_objects(net, classes, image_url):
    print(f"Downloading image from {image_url}")
    image_path = '/tmp/temp_image.jpg'

    if image_url.startswith("https://"):
        resp = urllib.request.urlopen(image_url)
        with open(image_path, 'wb') as f:
            f.write(resp.read())
    else:
        print(f"Unsupported URL format: {image_url}")
        raise ValueError(f"Unsupported URL format: {image_url}")

    image = cv2.imread(image_path)
    if image is None:
        print("Failed to read the downloaded image")
        raise ValueError("Failed to read the downloaded image")

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


def count_objects(detected_objects):
    object_counts = {}
    for obj in detected_objects:
        if obj in object_counts:
            object_counts[obj] += 1
        else:
            object_counts[obj] = 1
    return object_counts


def get_special_tags(user_email):
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

    return filtered_tags


def is_same_tags(tags_special, detected_objects):

    tags = []

    if len(detected_objects) != 0:
        for item in detected_objects:
            if item in tags_special:
                tags.append(item)

    if len(tags) == 0:
        return False
    else:
        return tags


def send_email(tags, user_email):

    tag_str = ""

    for item in tags:
        tag_str = tag_str + item + ", "

    print("Repeated special tags " + tag_str)

    topic_arn = 'arn:aws:sns:us-east-1:064005534643:tagsdetecting'
    subject = 'Special tags detected'
    message = 'Your images has been detected having special tags: ' + tag_str

    print(f"message for email sending is {message}")

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


def lambda_handler(event, context):
    print("Received event: %s" % json.dumps(event, indent=2))

    user_email = event['user_email']
    image_key = event['image_key']
    original_url = event['original_url']
    thumbnail_url = event['thumbnail_url']

    print(f"Original image URL: {original_url}")
    print(f"Thumbnail image URL: {thumbnail_url}")
    print(f"User email: {user_email}")
    print(f"Image key: {image_key}")

    image_url = original_url

    print("Downloading YOLO configuration files")
    weights_path, config_path, classes_path = download_yolo_files()

    print("Loading YOLO model")
    net, classes = load_yolo(weights_path, config_path, classes_path)

    print("Detecting objects in the image")
    detected_objects = detect_objects(net, classes, image_url)
    print(f"Detected objects: {detected_objects}")

    # email sending if tags in special
    tags_special = get_special_tags(user_email)

    boo = is_same_tags(tags_special, detected_objects)

    if boo == False:
        pass
    else:
        send_email(boo, user_email)

    # Count the detected objects
    object_counts = count_objects(detected_objects)
    print(f"Object counts: {object_counts}")

    # Store the information in DynamoDB
    item = {
        'user_id': user_email,
        'thumbnail_url': thumbnail_url,
        'image_url': original_url,
        'tags': object_counts
    }
    print(f"Stored item in DynamoDB: {item}")

    table.put_item(Item=item)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(detected_objects)
    }
