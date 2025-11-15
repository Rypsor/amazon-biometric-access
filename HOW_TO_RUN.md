# How to Run the Biometric Access Control MVP in AWS Learner Lab

This guide provides step-by-step instructions to deploy and run the Biometric Access Control MVP in your AWS Learner Lab environment.

## Prerequisites

1.  **AWS Learner Lab Access**: Ensure you are logged into your AWS Learner Lab account.
2.  **Sample Employee Photos**: You will need at least one JPG or PNG photo of a person to act as your "employee".
3.  **A Test Photo**: You will need a photo (either of the same "employee" or a different person) to test the access control system.

## Step 1: Set Up Your S3 Bucket and Photos

The system uses an S3 bucket to store the initial employee photos for enrollment.

1.  **Create an S3 Bucket**:
    *   Navigate to the S3 service in the AWS Console.
    *   Create a new, unique S3 bucket (e.g., `your-name-access-control-photos`).
    *   **Important**: Make a note of this bucket name.

2.  **Upload Employee Photos**:
    *   Inside your newly created bucket, upload the sample employee photos.
    *   Name the photo files in the format `FirstName_LastName.jpg` (e.g., `John_Doe.jpg`). The system will use the filename as the employee's name.

## Step 2: Configure the Project

You need to tell the project which S3 bucket to use.

1.  **Create a Configuration File**:
    *   In the root of this repository, create a new file named `config/biometric-cfn-params.json`.
    *   Copy and paste the following content into the file:

    ```json
    {
        "S3BucketNameParameter": "your-s3-bucket-name",
        "AccessControlLambdaSourceS3KeyParameter": "src/access_control_handler.zip"
    }
    ```

2.  **Update the Bucket Name**:
    *   In the `config/biometric-cfn-params.json` file, replace `"your-s3-bucket-name"` with the actual name of the S3 bucket you created in Step 1.

## Step 3: Package and Deploy the Lambda Function

This step bundles the Lambda function code into a zip file and uploads it to your S3 bucket.

1.  **Open the AWS Cloud9 Terminal** (or your local terminal if you have the AWS CLI configured for your Learner Lab).

2.  **Run the following commands** from the root of the repository:

    ```bash
    # Install dependencies (only needs to be done once)
    pip install pynt boto3 opencv-python

    # Clean the build directory
    pynt clean

    # Package the access_control_handler lambda function
    pynt packagelambda[access_control_handler]

    # Deploy the packaged lambda to your S3 bucket
    pynt deploylambda[access_control_handler,cfn_params_path="config/biometric-cfn-params.json"]
    ```

## Step 4: Deploy the AWS Infrastructure

This step uses CloudFormation to create all the necessary AWS resources.

1.  **Run the `createstack` command**:
    *   **If this is the first time you are deploying**, run the `createstack` command:
        ```bash
        pynt createstack[cfn_path="aws-infra/biometric-access-control-cfn.yaml",cfn_params_path="config/biometric-cfn-params.json",global_params_path="config/global-params.json"]
        ```
    *   **If you have already deployed the stack and are updating it**, run the `updatestack` command instead:
        ```bash
        pynt updatestack[cfn_path="aws-infra/biometric-access-control-cfn.yaml",cfn_params_path="config/biometric-cfn-params.json",global_params_path="config/global-params.json"]
        ```

2.  **Wait for Completion**: This process will take a few minutes. You can monitor the status in the AWS CloudFormation console. It is complete when the stack status is `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

## Step 5: Enroll the Employees

Now that the infrastructure is ready, you need to populate the Rekognition collection and DynamoDB table with your employee data.

1.  **Run the `enroll.py` script**:
    *   Use the following command, replacing `<your-s3-bucket-name>` with the name of the bucket you created in Step 1.

    ```bash
    python scripts/enroll.py <your-s3-bucket-name>
    ```

2.  **Verify Enrollment**: You should see success messages in the terminal for each employee photo found in your S3 bucket.

## Step 6: Test the System

Finally, you can test the access control system in real-time using your webcam.

1.  **Get the API Gateway URL**:
    *   Navigate to the **API Gateway** service in the AWS Console.
    *   Find the API named `AccessControlApi`.
    *   Go to the **Stages** section, click on the `dev` stage.
    *   The **Invoke URL** will be displayed at the top. It will look something like `https://xxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev`.
    *   Append `/access` to the end of this URL. The final URL should look like: `https://xxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev/access`.

2.  **Run the Camera Simulator**:
    *   Use the following command, replacing the placeholder with your actual API Gateway URL:

    ```bash
    python scripts/camera_simulator.py "your_api_gateway_url/access"
    ```
    *   A window will open showing your webcam feed with a countdown. Look at the camera!
    *   After 3 seconds, it will automatically take a photo and send it for verification.

3.  **Check the Results**: The terminal will show one of three outcomes:
    *   **Access Granted**: If exactly one face was detected and it belongs to a registered employee.
        ```
        Status Code: 200
        Response: {'status': 'Access Granted', 'message': 'Welcome, John Doe...'}
        ```
    *   **Access Denied**: If exactly one face was detected, but it was not found in the employee database.
        ```
        Status Code: 401
        Response: {'status': 'Access Denied', 'message': 'Face not recognized.'}
        ```
    *   **Unknown**: If zero faces or more than one face were detected in the photo.
        ```
        Status Code: 400
        Response: {'status': 'Unknown', 'message': 'No face detected...'}
        // or {'status': 'Unknown', 'message': 'Multiple faces detected...'}
        ```

Congratulations! You have successfully deployed and tested the Biometric Access Control MVP.
