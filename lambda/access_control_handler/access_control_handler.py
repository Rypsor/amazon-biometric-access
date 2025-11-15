import boto3
import json
import base64

def access_control_handler(event, context):
    """
    Handles access control by searching for a face in a Rekognition collection.

    :param event: The event object from API Gateway.
    :param context: The context object.
    :return: A dictionary with a status code and a message.
    """
    rekognition_client = boto3.client('rekognition')
    dynamodb_resource = boto3.resource('dynamodb')
    table = dynamodb_resource.Table('employees')

    image_bytes = base64.b64decode(event['body'])

    try:
        response = rekognition_client.search_faces_by_image(
            CollectionId='employees',
            Image={'Bytes': image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=95
        )

        if response['FaceMatches']:
            face_match = response['FaceMatches'][0]
            face_id = face_match['Face']['FaceId']

            dynamodb_response = table.get_item(Key={'FaceId': face_id})

            if 'Item' in dynamodb_response:
                employee = dynamodb_response['Item']
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': f"Access Granted for {employee['full_name']} (Employee ID: {employee['employee_id']})"
                    })
                }

        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Access Denied: Face not recognized.'})
        }

    except rekognition_client.exceptions.InvalidParameterException as e:
        if "no faces detected" in str(e).lower():
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Access Denied: No face detected in the image.'})
            }
        raise e
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal Server Error'})
        }
