import boto3
import json
import base64
import os
from datetime import datetime

def access_control_handler(event, context):
    """
    Handles access control by detecting the number of faces and then searching
    for a recognized face in a Rekognition collection.

    Returns one of three states:
    - "Access Granted": If exactly one face is detected and it's a known employee.
    - "Access Denied": If exactly one face is detected but it's not a known employee.
    - "Unknown": If zero or more than one face is detected.
    """
    rekognition_client = boto3.client('rekognition')
    dynamodb_resource = boto3.resource('dynamodb')
    s3_client = boto3.client('s3')
    sns_client = boto3.client('sns')

    table = dynamodb_resource.Table('employees')
    unrecognized_faces_bucket = os.environ['UNRECOGNIZED_FACES_BUCKET']
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']

    image_bytes = base64.b64decode(event['body'])

    try:
        # Step 1: Detect and count faces in the image
        detect_response = rekognition_client.detect_faces(Image={'Bytes': image_bytes})

        num_faces = len(detect_response['FaceDetails'])

        # Step 2: Handle cases with 0 faces
        if num_faces == 0:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': "No se detectan caras"
                })
            }

        # Step 3: Handle "Access Granted" or "Access Denied" state (exactly 1 face)
        search_response = rekognition_client.search_faces_by_image(
            CollectionId='employees',
            Image={'Bytes': image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=95
        )

        if search_response['FaceMatches']:
            face_match = search_response['FaceMatches'][0]
            face_id = face_match['Face']['FaceId']

            dynamodb_response = table.get_item(Key={'FaceId': face_id})

            if 'Item' in dynamodb_response:
                employee = dynamodb_response['Item']
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'Access Granted',
                        'message': f"Welcome, {employee['full_name']} (Employee ID: {employee['employee_id']})"
                    })
                }

        # If no match was found in the collection, upload image to S3 and send SNS alert
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
        s3_key = f"unrecognized-face-{timestamp}.jpg"

        s3_client.put_object(
            Bucket=unrecognized_faces_bucket,
            Key=s3_key,
            Body=image_bytes,
            ContentType='image/jpeg'
        )

        s3_url = f"https://{unrecognized_faces_bucket}.s3.amazonaws.com/{s3_key}"

        response = sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject="ALERTA: Acceso Biométrico",
            Message=f"Se detectó un desconocido. Se niega su acceso.\n\nFoto: {s3_url}"
        )
        print(f"SNS Alert sent to topic: {sns_topic_arn}, MessageId: {response.get('MessageId')}")

        return {
            'statusCode': 401,
            'body': json.dumps({
                'status': 'Access Denied',
                'message': 'Face not recognized.'
            })
        }

    except rekognition_client.exceptions.InvalidParameterException as e:
        # This can happen if the image format is invalid
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'Error',
                'message': f'Invalid image format or parameter: {str(e)}'
            })
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'Error',
                'message': 'Internal Server Error'
            })
        }
