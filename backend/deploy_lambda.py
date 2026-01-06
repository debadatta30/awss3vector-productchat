import boto3
import zipfile
import json
import os

lambda_client = boto3.client('lambda', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')

FUNCTION_NAME = 'product-chat-api'
ROLE_NAME = 'product-chat-lambda-role'

def create_lambda_role():
    """Create IAM role for Lambda"""
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        role = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for product chat Lambda function'
        )
        print(f"Created role: {ROLE_NAME}")
    except Exception as e:
        if 'EntityAlreadyExists' in str(e):
            print(f"Role {ROLE_NAME} already exists")
        else:
            print(f"Error creating role: {e}")
            return None
    
    # Attach policies
    policies = [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess',
        'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
    ]
    
    for policy in policies:
        try:
            iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy)
        except Exception as e:
            print(f"Policy attach error: {e}")
    
    # Add S3 Vectors permissions
    s3vectors_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3vectors:QueryVectors",
                    "s3vectors:GetVectors",
                    "s3vectors:ListVectorStores"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        iam.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName='S3VectorsAccess',
            PolicyDocument=json.dumps(s3vectors_policy)
        )
        print("Added S3 Vectors permissions")
    except Exception as e:
        print(f"S3 Vectors policy error: {e}")
    
    # Get role ARN
    role_response = iam.get_role(RoleName=ROLE_NAME)
    return role_response['Role']['Arn']

def create_deployment_package():
    """Create Lambda deployment package"""
    
    print("Creating deployment package...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lambda_file = os.path.join(script_dir, 'product_chat_lambda.py')
    
    with zipfile.ZipFile('product_chat_lambda.zip', 'w') as zip_file:
        zip_file.write(lambda_file, 'lambda_function.py')
    
    print("Deployment package created")
    return 'product_chat_lambda.zip'

def deploy_lambda():
    """Deploy Lambda function"""
    
    role_arn = create_lambda_role()
    if not role_arn:
        return
    
    zip_file = create_deployment_package()
    
    try:
        with open(zip_file, 'rb') as f:
            zip_content = f.read()
        
        # Create or update function
        try:
            response = lambda_client.create_function(
                FunctionName=FUNCTION_NAME,
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='Product chat API with Nova Lite',
                Timeout=30,
                MemorySize=512
            )
            print(f"Created Lambda function: {FUNCTION_NAME}")
        except Exception as e:
            if 'ResourceConflictException' in str(e):
                response = lambda_client.update_function_code(
                    FunctionName=FUNCTION_NAME,
                    ZipFile=zip_content
                )
                print(f"Updated Lambda function: {FUNCTION_NAME}")
            else:
                print(f"Error deploying function: {e}")
                return
        
        print(f"Function ARN: {response['FunctionArn']}")
        
    except Exception as e:
        print(f"Deployment error: {e}")
    finally:
        if os.path.exists(zip_file):
            os.remove(zip_file)

if __name__ == "__main__":
    deploy_lambda()