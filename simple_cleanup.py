import boto3

# AWS clients
s3 = boto3.client('s3', region_name='us-east-1')
s3vectors = boto3.client('s3vectors', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')
apigateway = boto3.client('apigateway', region_name='us-east-1')

print("Cleaning up resources...")

# Delete S3 Vectors
try:
    # Delete index first
    s3vectors.delete_index(vectorBucketName="product-chat-vectors", indexName="products")
    print("Deleted S3 Vectors index")
except:
    print("S3 Vectors index not found")

try:
    # Delete vector bucket
    s3vectors.delete_vector_bucket(vectorBucketName="product-chat-vectors")
    print("Deleted S3 Vectors bucket")
except:
    print("S3 Vectors bucket not found")

# Delete regular S3 bucket
try:
    # Delete objects first
    response = s3.list_objects_v2(Bucket="product-chat-data")
    if 'Contents' in response:
        objects = [{'Key': obj['Key']} for obj in response['Contents']]
        s3.delete_objects(Bucket="product-chat-data", Delete={'Objects': objects})
    s3.delete_bucket(Bucket="product-chat-data")
    print("Deleted S3 bucket")
except:
    print("S3 bucket not found")

# Delete Lambda
try:
    lambda_client.delete_function(FunctionName="product-chat-api")
    print("Deleted Lambda function")
except:
    print("Lambda function not found")

# Delete API Gateway
try:
    apis = apigateway.get_rest_apis()
    for api in apis['items']:
        if api['name'] == "product-chat-api":
            apigateway.delete_rest_api(restApiId=api['id'])
            print("Deleted API Gateway")
            break
except:
    print("API Gateway not found")

# Delete IAM role
try:
    # Detach policies
    attached = iam.list_attached_role_policies(RoleName="product-chat-lambda-role")
    for policy in attached['AttachedPolicies']:
        iam.detach_role_policy(RoleName="product-chat-lambda-role", PolicyArn=policy['PolicyArn'])
    
    # Delete inline policies
    inline = iam.list_role_policies(RoleName="product-chat-lambda-role")
    for policy_name in inline['PolicyNames']:
        iam.delete_role_policy(RoleName="product-chat-lambda-role", PolicyName=policy_name)
    
    iam.delete_role(RoleName="product-chat-lambda-role")
    print("Deleted IAM role")
except:
    print("IAM role not found")

print("Complete cleanup done! Now run: python deploy_backend_simple.py")