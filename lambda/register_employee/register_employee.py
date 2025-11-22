import json
import boto3
import base64
import os
import uuid
import re

# Initialize clients
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
cloudwatch_client = boto3.client('cloudwatch')

# Environment variables
TABLE_NAME = os.environ.get('EMPLOYEES_TABLE')
COLLECTION_ID = os.environ.get('REKOGNITION_COLLECTION_ID', 'employees')

def register_employee(event, context):
    print("Received event: " + json.dumps(event))

    try:
        # Parse input
        body = json.loads(event['body'])
        image_base64 = body.get('image')
        first_name = body.get('firstName')
        last_name = body.get('lastName')
        cedula = body.get('cedula')
        city = body.get('city')

        # Basic validation
        if not all([image_base64, first_name, last_name, cedula, city]):
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'Missing required fields'})
            }

        # Sanitize Cedula for ExternalImageId
        # Rekognition allows: [a-zA-Z0-9_.\-:]
        # Remove any invalid characters from cedula
        external_image_id = re.sub(r'[^a-zA-Z0-9_.\-:]', '', cedula)

        if not external_image_id:
             return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'Invalid characters in ID (Cedula)'})
            }

        # Decode image
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            print(f"Error decoding image: {e}")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'Invalid image format'})
            }

        # Index face in Rekognition
        try:
            rek_response = rekognition.index_faces(
                CollectionId=COLLECTION_ID,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_image_id,
                DetectionAttributes=['ALL'],
                MaxFaces=1,
                QualityFilter="AUTO"
            )
        except rekognition.exceptions.ResourceNotFoundException:
             return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': f'Rekognition collection {COLLECTION_ID} not found'})
            }

        # Check if a face was actually indexed
        if not rek_response['FaceRecords']:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'No face detected in the image'})
            }

        face_id = rek_response['FaceRecords'][0]['Face']['FaceId']
        print(f"Face indexed successfully. FaceId: {face_id}")

        # Save to DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        item = {
            'FaceId': face_id,
            'FirstName': first_name,
            'LastName': last_name,
            'Cedula': cedula,
            'City': city,
            'CreatedAt': str(uuid.uuid4()) # Or timestamp
        }

        table.put_item(Item=item)
        print(f"Employee saved to DynamoDB: {item}")

        # Publish CloudWatch Metric
        cloudwatch_client.put_metric_data(
            Namespace='BiometricAccessControl',
            MetricData=[
                {
                    'MetricName': 'EmployeeRegistrations',
                    'Value': 1,
                    'Unit': 'Count'
                },
            ]
        )

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Employee registered successfully',
                'faceId': face_id,
                'cedula': cedula
            })
        }

    except Exception as e:
        print(f"Internal Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': f'Internal Server Error: {str(e)}'})
        }
