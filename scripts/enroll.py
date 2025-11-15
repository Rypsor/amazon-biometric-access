import boto3
import os

def enroll_employees(bucket_name, collection_id, table_name):
    """
    Enrolls employees by indexing their faces from S3 into a Rekognition collection
    and storing the metadata in a DynamoDB table.

    :param bucket_name: Name of the S3 bucket containing employee photos.
    :param collection_id: ID of the Rekognition collection.
    :param table_name: Name of the DynamoDB table.
    """
    rekognition_client = boto3.client('rekognition')
    dynamodb_resource = boto3.resource('dynamodb')
    s3_resource = boto3.resource('s3')
    table = dynamodb_resource.Table(table_name)

    bucket = s3_resource.Bucket(bucket_name)

    for obj in bucket.objects.all():
        employee_id, _ = os.path.splitext(obj.key)

        print(f"Enrolling employee: {employee_id}")

        response = rekognition_client.index_faces(
            CollectionId=collection_id,
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': obj.key
                }
            },
            ExternalImageId=employee_id,
            DetectionAttributes=['ALL']
        )

        if response['FaceRecords']:
            face_record = response['FaceRecords'][0]
            face_id = face_record['Face']['FaceId']

            table.put_item(
                Item={
                    'FaceId': face_id,
                    'employee_id': employee_id,
                    'full_name': employee_id.replace('_', ' ').title()
                }
            )
            print(f"Successfully enrolled {employee_id} with FaceId: {face_id}")
        else:
            print(f"Could not enroll {employee_id}. No faces detected.")

if __name__ == '__main__':
    # Replace with your actual bucket, collection, and table names
    S3_BUCKET = "your-s3-bucket-name"
    REKOGNITION_COLLECTION = "employees"
    DYNAMODB_TABLE = "employees"

    enroll_employees(S3_BUCKET, REKOGNITION_COLLECTION, DYNAMODB_TABLE)
