import boto3
import json

apigateway = boto3.client('apigateway', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

API_NAME = 'product-chat-api'
FUNCTION_NAME = 'product-chat-api'

def create_api_gateway():
    """Create API Gateway for product chat"""
    
    try:
        # Create REST API
        api = apigateway.create_rest_api(
            name=API_NAME,
            description='Product Chat API with Nova Lite'
        )
        api_id = api['id']
        print(f"Created API: {api_id}")
        
        # Get root resource
        resources = apigateway.get_resources(restApiId=api_id)
        root_id = resources['items'][0]['id']
        
        # Create /chat resource
        chat_resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='chat'
        )
        resource_id = chat_resource['id']
        
        # Create POST method
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            authorizationType='NONE'
        )
        
        # Create OPTIONS method for CORS
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        # Get Lambda function ARN
        lambda_response = lambda_client.get_function(FunctionName=FUNCTION_NAME)
        lambda_arn = lambda_response['Configuration']['FunctionArn']
        
        # Set up Lambda integration for POST
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )
        
        # Set up OPTIONS integration for CORS
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={'application/json': '{"statusCode": 200}'}
        )
        
        # Set up OPTIONS response
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
                'method.response.header.Access-Control-Allow-Origin': False
            }
        )
        
        apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )
        
        # Grant API Gateway permission to invoke Lambda
        try:
            lambda_client.add_permission(
                FunctionName=FUNCTION_NAME,
                StatementId='api-gateway-invoke',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:us-east-1:*:{api_id}/*/*'
            )
        except Exception as e:
            if 'ResourceConflictException' not in str(e):
                print(f"Permission error: {e}")
        
        # Deploy API
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )
        
        api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/chat"
        
        print(f"API Gateway deployed successfully!")
        print(f"API URL: {api_url}")
        
        return api_url
        
    except Exception as e:
        print(f"Error creating API Gateway: {e}")
        return None

if __name__ == "__main__":
    create_api_gateway()