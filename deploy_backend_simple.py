#!/usr/bin/env python3
"""
Simple Backend Deployment Script for Product Chat
"""

import boto3
import json
import zipfile
import os
import time

# AWS clients
s3 = boto3.client('s3', region_name='us-east-1')
s3vectors = boto3.client('s3vectors', region_name='us-east-1')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')
apigateway = boto3.client('apigateway', region_name='us-east-1')

# Configuration
BUCKET_NAME = "product-chat-data"
VECTOR_BUCKET_NAME = "product-chat-vectors"
FUNCTION_NAME = "product-chat-api"
ROLE_NAME = "product-chat-lambda-role"
API_NAME = "product-chat-api"

def deploy_backend():
    print("Starting backend deployment...")
    
    # Step 1: S3 bucket
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"Created S3 bucket: {BUCKET_NAME}")
    except Exception as e:
        if 'BucketAlreadyExists' in str(e):
            print(f"S3 bucket already exists: {BUCKET_NAME}")
    
    # Upload products
    products = [
        {"id": "1", "name": "Wireless Bluetooth Headphones", "category": "Electronics", "price": 89.99, "description": "Premium wireless headphones with noise cancellation and 30-hour battery life", "features": ["Noise Cancellation", "30hr Battery", "Bluetooth 5.0", "Quick Charge"]},
        {"id": "2", "name": "Smart Fitness Watch", "category": "Wearables", "price": 199.99, "description": "Advanced fitness tracker with heart rate monitoring and GPS", "features": ["Heart Rate Monitor", "GPS Tracking", "Water Resistant", "Sleep Tracking"]},
        {"id": "3", "name": "Portable Phone Charger", "category": "Accessories", "price": 29.99, "description": "High-capacity power bank with fast charging support", "features": ["10000mAh Capacity", "Fast Charging", "USB-C", "LED Display"]},
        {"id": "4", "name": "Wireless Gaming Mouse", "category": "Gaming", "price": 79.99, "description": "High-precision gaming mouse with RGB lighting", "features": ["RGB Lighting", "12000 DPI", "Wireless", "Programmable Buttons"]},
        {"id": "5", "name": "Smart Home Speaker", "category": "Smart Home", "price": 129.99, "description": "Voice-controlled smart speaker with premium sound quality", "features": ["Voice Control", "Premium Sound", "Smart Home Hub", "Multi-room Audio"]}
    ]
    
    s3.put_object(Bucket=BUCKET_NAME, Key='products.json', Body=json.dumps({"products": products}, indent=2), ContentType='application/json')
    print("Uploaded sample products")
    
    # Step 2: S3 Vectors
    try:
        s3vectors.create_vector_bucket(vectorBucketName=VECTOR_BUCKET_NAME)
        print(f"Created S3 Vectors bucket: {VECTOR_BUCKET_NAME}")
    except Exception as e:
        if 'VectorBucketAlreadyExists' in str(e):
            print(f"S3 Vectors bucket already exists: {VECTOR_BUCKET_NAME}")
    
    try:
        s3vectors.create_index(vectorBucketName=VECTOR_BUCKET_NAME, indexName="products", dataType="float32", dimension=1536, distanceMetric="cosine")
        print("Created S3 Vectors index")
    except Exception as e:
        if 'IndexAlreadyExists' in str(e):
            print("S3 Vectors index already exists")
    
    # Generate embeddings
    obj = s3.get_object(Bucket=BUCKET_NAME, Key='products.json')
    products_data = json.loads(obj['Body'].read().decode('utf-8'))
    
    vectors_to_put = []
    for product in products_data['products']:
        text = f"{product['name']} {product['description']} {' '.join(product['features'])}"
        response = bedrock.invoke_model(modelId="amazon.titan-embed-text-v1", body=json.dumps({"inputText": text}))
        embedding = json.loads(response['body'].read())['embedding']
        
        vectors_to_put.append({
            'key': f"product_{product['id']}",
            'data': {'float32': [float(x) for x in embedding]},
            'metadata': {
                'name': product['name'],
                'description': product['description'],
                'category': product['category'],
                'price': str(product['price']),
                'features': '|'.join(product['features'])
            }
        })
    
    s3vectors.put_vectors(vectorBucketName=VECTOR_BUCKET_NAME, indexName="products", vectors=vectors_to_put)
    print("Generated and stored product embeddings")
    
    # Step 3: Lambda
    trust_policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    
    try:
        iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust_policy), Description='Role for product chat Lambda function')
        print(f"Created IAM role: {ROLE_NAME}")
    except Exception as e:
        if 'EntityAlreadyExists' in str(e):
            print(f"IAM role already exists: {ROLE_NAME}")
    
    # Attach policies
    policies = ['arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole', 'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess', 'arn:aws:iam::aws:policy/AmazonBedrockFullAccess']
    for policy in policies:
        try:
            iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy)
        except:
            pass
    
    # S3 Vectors permissions
    s3vectors_policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": ["s3vectors:QueryVectors", "s3vectors:GetVectors", "s3vectors:ListVectorStores"], "Resource": "*"}]}
    try:
        iam.put_role_policy(RoleName=ROLE_NAME, PolicyName='S3VectorsAccess', PolicyDocument=json.dumps(s3vectors_policy))
        print("Added S3 Vectors permissions")
    except:
        pass
    
    role_response = iam.get_role(RoleName=ROLE_NAME)
    role_arn = role_response['Role']['Arn']
    
    # Lambda code
    lambda_code = f'''import json
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
s3vectors = boto3.client('s3vectors', region_name='us-east-1')

def lambda_handler(event, context):
    headers = {{
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }}
    
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {{'statusCode': 200, 'headers': headers, 'body': ''}}
        
        body = json.loads(event.get('body', '{{}}'))
        question = body.get('question', '').strip()
        
        if not question:
            return {{'statusCode': 400, 'headers': headers, 'body': json.dumps({{'error': 'Question is required'}})}}
        
        # Get embedding
        response = bedrock.invoke_model(modelId="amazon.titan-embed-text-v1", body=json.dumps({{"inputText": question}}))
        user_embedding = json.loads(response['body'].read())['embedding']
        
        # Query S3 Vectors
        query_vector_float32 = [float(x) for x in user_embedding]
        response = s3vectors.query_vectors(
            vectorBucketName="{VECTOR_BUCKET_NAME}",
            indexName="products",
            topK=1,
            queryVector={{'float32': query_vector_float32}},
            returnMetadata=True,
            returnDistance=True
        )
        
        if response['vectors']:
            result = response['vectors'][0]
            metadata = result.get('metadata', {{}})
            distance = result.get('distance', 0.0)
            similarity = 1.0 - distance if distance else 1.0
            
            if similarity >= 0.5:
                # Generate response with Nova Lite
                prompt = f"""You are a helpful product assistant. Answer the customer's question about this product.

Customer Question: {{question}}

Product Information:
- Name: {{metadata.get('name', '')}}
- Category: {{metadata.get('category', '')}}
- Price: ${{metadata.get('price', '')}}
- Description: {{metadata.get('description', '')}}
- Features: {{metadata.get('features', '').replace('|', ', ')}}

Provide a helpful, friendly response about this product. Be concise and focus on what the customer asked."""

                try:
                    nova_response = bedrock.invoke_model(
                        modelId="us.amazon.nova-lite-v1:0",
                        body=json.dumps({{
                            "messages": [{{"role": "user", "content": [{{"text": prompt}}]}}],
                            "inferenceConfig": {{"max_new_tokens": 200, "temperature": 0.7}}
                        }})
                    )
                    nova_result = json.loads(nova_response['body'].read())
                    answer = nova_result['output']['message']['content'][0]['text']
                except:
                    answer = f"Here's what I found about {{metadata.get('name', '')}}: {{metadata.get('description', '')}} It's priced at ${{metadata.get('price', '')}}."
                
                return {{
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({{
                        'answer': answer,
                        'confidence': round(similarity, 2),
                        'product': {{
                            'name': metadata.get('name', ''),
                            'category': metadata.get('category', ''),
                            'price': float(metadata.get('price', 0))
                        }},
                        'found_product': True
                    }})
                }}
        
        # No match found
        try:
            nova_response = bedrock.invoke_model(
                modelId="us.amazon.nova-lite-v1:0",
                body=json.dumps({{
                    "messages": [{{"role": "user", "content": [{{"text": f"A customer asked: '{{question}}'. You couldn't find a matching product. Politely let them know and suggest they browse categories or contact support."}}]}}],
                    "inferenceConfig": {{"max_new_tokens": 150, "temperature": 0.7}}
                }})
            )
            nova_result = json.loads(nova_response['body'].read())
            answer = nova_result['output']['message']['content'][0]['text']
        except:
            answer = "I couldn't find a specific product matching your query. Please browse our categories or contact support for assistance."
        
        return {{
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({{
                'answer': answer,
                'confidence': 0.0,
                'found_product': False
            }})
        }}
        
    except Exception as e:
        return {{'statusCode': 500, 'headers': headers, 'body': json.dumps({{'error': str(e)}})}}
'''
    
    # Create deployment package
    with zipfile.ZipFile('lambda_deployment.zip', 'w') as zip_file:
        zip_file.writestr('lambda_function.py', lambda_code)
    
    with open('lambda_deployment.zip', 'rb') as f:
        zip_content = f.read()
    
    time.sleep(10)  # Wait for role
    
    try:
        lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='Product chat API with S3 Vectors and Nova Lite',
            Timeout=30,
            MemorySize=512
        )
        print(f"Created Lambda function: {FUNCTION_NAME}")
    except Exception as e:
        if 'ResourceConflictException' in str(e):
            lambda_client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zip_content)
            print(f"Updated Lambda function: {FUNCTION_NAME}")
    
    os.remove('lambda_deployment.zip')
    
    # Step 4: API Gateway
    api = apigateway.create_rest_api(name=API_NAME, description='Product Chat API with S3 Vectors and Nova Lite')
    api_id = api['id']
    print(f"Created API Gateway: {api_id}")
    
    resources = apigateway.get_resources(restApiId=api_id)
    root_id = resources['items'][0]['id']
    
    chat_resource = apigateway.create_resource(restApiId=api_id, parentId=root_id, pathPart='chat')
    resource_id = chat_resource['id']
    
    apigateway.put_method(restApiId=api_id, resourceId=resource_id, httpMethod='POST', authorizationType='NONE')
    apigateway.put_method(restApiId=api_id, resourceId=resource_id, httpMethod='OPTIONS', authorizationType='NONE')
    
    lambda_response = lambda_client.get_function(FunctionName=FUNCTION_NAME)
    lambda_arn = lambda_response['Configuration']['FunctionArn']
    
    apigateway.put_integration(restApiId=api_id, resourceId=resource_id, httpMethod='POST', type='AWS_PROXY', integrationHttpMethod='POST', uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations')
    apigateway.put_integration(restApiId=api_id, resourceId=resource_id, httpMethod='OPTIONS', type='MOCK', requestTemplates={'application/json': '{"statusCode": 200}'})
    
    apigateway.put_method_response(restApiId=api_id, resourceId=resource_id, httpMethod='OPTIONS', statusCode='200', responseParameters={'method.response.header.Access-Control-Allow-Headers': False, 'method.response.header.Access-Control-Allow-Methods': False, 'method.response.header.Access-Control-Allow-Origin': False})
    apigateway.put_integration_response(restApiId=api_id, resourceId=resource_id, httpMethod='OPTIONS', statusCode='200', responseParameters={'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'", 'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'", 'method.response.header.Access-Control-Allow-Origin': "'*'"})
    
    account_id = boto3.client('sts').get_caller_identity()['Account']
    try:
        lambda_client.add_permission(FunctionName=FUNCTION_NAME, StatementId='api-gateway-invoke', Action='lambda:InvokeFunction', Principal='apigateway.amazonaws.com', SourceArn=f'arn:aws:execute-api:us-east-1:{account_id}:{api_id}/*/*')
        print("Added Lambda permission")
    except:
        pass
    
    apigateway.create_deployment(restApiId=api_id, stageName='prod')
    
    api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/chat"
    print(f"API Gateway deployed: {api_url}")
    
    print("=" * 60)
    print("BACKEND DEPLOYMENT COMPLETE!")
    print(f"API URL: {api_url}")
    print("Update frontend/src/App.js with this API URL")
    print("=" * 60)
    
    return api_url

if __name__ == "__main__":
    deploy_backend()