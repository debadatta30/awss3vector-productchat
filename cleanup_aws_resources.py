#!/usr/bin/env python3
"""
Cleanup script to delete all existing Product Chat AWS resources
Run this before the clean setup to start completely fresh.
"""

import boto3
import json
import time

# AWS clients
s3 = boto3.client('s3', region_name='us-east-1')
s3vectors = boto3.client('s3vectors', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')
apigateway = boto3.client('apigateway', region_name='us-east-1')

def delete_s3_bucket(bucket_name):
    """Delete S3 bucket and all its contents"""
    try:
        # Delete all objects first
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            objects = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
        
        # Delete bucket
        s3.delete_bucket(Bucket=bucket_name)
        print(f"✅ Deleted S3 bucket: {bucket_name}")
        return True
    except Exception as e:
        if 'NoSuchBucket' in str(e):
            print(f"ℹ️  S3 bucket doesn't exist: {bucket_name}")
        else:
            print(f"❌ Error deleting S3 bucket {bucket_name}: {e}")
        return False

def delete_s3_vectors_bucket(bucket_name):
    """Delete S3 Vectors bucket"""
    try:
        # First delete all indexes
        indexes = s3vectors.list_indexes(vectorBucketName=bucket_name)
        for index in indexes.get('indexes', []):
            try:
                s3vectors.delete_index(
                    vectorBucketName=bucket_name,
                    indexName=index['indexName']
                )
                print(f"✅ Deleted S3 Vectors index: {index['indexName']}")
            except Exception as e:
                print(f"❌ Error deleting index {index['indexName']}: {e}")
        
        # Delete the vector bucket
        s3vectors.delete_vector_bucket(vectorBucketName=bucket_name)
        print(f"✅ Deleted S3 Vectors bucket: {bucket_name}")
        return True
    except Exception as e:
        if 'VectorBucketNotFound' in str(e):
            print(f"ℹ️  S3 Vectors bucket doesn't exist: {bucket_name}")
        else:
            print(f"❌ Error deleting S3 Vectors bucket {bucket_name}: {e}")
        return False

def delete_lambda_function(function_name):
    """Delete Lambda function"""
    try:
        lambda_client.delete_function(FunctionName=function_name)
        print(f"✅ Deleted Lambda function: {function_name}")
        return True
    except Exception as e:
        if 'ResourceNotFoundException' in str(e):
            print(f"ℹ️  Lambda function doesn't exist: {function_name}")
        else:
            print(f"❌ Error deleting Lambda function {function_name}: {e}")
        return False

def delete_iam_role(role_name):
    """Delete IAM role and its policies"""
    try:
        # Detach managed policies
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)
        for policy in attached_policies['AttachedPolicies']:
            iam.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])
        
        # Delete inline policies
        inline_policies = iam.list_role_policies(RoleName=role_name)
        for policy_name in inline_policies['PolicyNames']:
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        
        # Delete role
        iam.delete_role(RoleName=role_name)
        print(f"✅ Deleted IAM role: {role_name}")
        return True
    except Exception as e:
        if 'NoSuchEntity' in str(e):
            print(f"ℹ️  IAM role doesn't exist: {role_name}")
        else:
            print(f"❌ Error deleting IAM role {role_name}: {e}")
        return False

def delete_api_gateway(api_name):
    """Delete API Gateway"""
    try:
        # Find API by name
        apis = apigateway.get_rest_apis()
        api_id = None
        for api in apis['items']:
            if api['name'] == api_name:
                api_id = api['id']
                break
        
        if api_id:
            apigateway.delete_rest_api(restApiId=api_id)
            print(f"✅ Deleted API Gateway: {api_name} ({api_id})")
            return True
        else:
            print(f"ℹ️  API Gateway doesn't exist: {api_name}")
            return False
    except Exception as e:
        print(f"❌ Error deleting API Gateway {api_name}: {e}")
        return False

def cleanup_all():
    """Clean up all existing resources"""
    print("🧹 Starting cleanup of Product Chat AWS resources...")
    print("=" * 60)
    
    # List of resources to clean up
    resources_to_clean = [
        # Current deployment resources
        ("S3 Bucket", "product-chat-data", lambda: delete_s3_bucket("product-chat-data")),
        ("S3 Vectors Bucket", "product-chat-vectors", lambda: delete_s3_vectors_bucket("product-chat-vectors")),
        ("Website Bucket", "product-chat-website", lambda: delete_s3_bucket("product-chat-website")),
        ("Lambda Function", "product-chat-api", lambda: delete_lambda_function("product-chat-api")),
        ("IAM Role", "product-chat-lambda-role", lambda: delete_iam_role("product-chat-lambda-role")),
        ("API Gateway", "product-chat-api", lambda: delete_api_gateway("product-chat-api")),
    ]
    
    success_count = 0
    total_count = len(resources_to_clean)
    
    for resource_type, resource_name, cleanup_func in resources_to_clean:
        print(f"\n🗑️  Cleaning up {resource_type}: {resource_name}")
        if cleanup_func():
            success_count += 1
        time.sleep(1)  # Small delay between deletions
    
    print("\n" + "=" * 60)
    print(f"🧹 Cleanup Summary: {success_count}/{total_count} resources processed")
    print("=" * 60)
    
    if success_count > 0:
        print("✅ Cleanup completed! You can now run the deployment script.")
        print("\nNext steps:")
        print("1. Run: python deploy_backend_simple.py")
        print("2. Wait for the complete deployment")
        print("3. Test your application")
    else:
        print("ℹ  No resources found to clean up. You can proceed with deployment.")
    
    print("
🚀 Ready for fresh deployment!")

if __name__ == "__main__":
    cleanup_all()