import json
import boto3
import math

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
s3vectors = boto3.client('s3vectors', region_name='us-east-1')

# Configuration
VECTOR_BUCKET_NAME = "product-chat-vectors"
INDEX_NAME = "products"
SIMILARITY_THRESHOLD = 0.5
NOVA_MODEL_ID = "us.amazon.nova-lite-v1:0"

def lambda_handler(event, context):
    """Product chat API handler with Nova Lite"""
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        body = json.loads(event.get('body', '{}'))
        question = body.get('question', '').strip()
        
        if not question:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Question is required'})
            }
        
        # Search S3 Vectors for similar products
        user_embedding = get_embedding(question)
        best_match = find_best_match(user_embedding)
        
        if best_match['similarity'] >= SIMILARITY_THRESHOLD:
            response_text = generate_product_response(question, best_match)
            result = {
                'answer': response_text,
                'confidence': round(best_match['similarity'], 2),
                'product': {
                    'name': best_match['name'],
                    'category': best_match['category'],
                    'price': best_match['price']
                },
                'found_product': True
            }
        else:
            response_text = generate_no_match_response(question)
            result = {
                'answer': response_text,
                'confidence': round(best_match['similarity'], 2),
                'found_product': False
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e), 'type': type(e).__name__})
        }

def find_best_match(user_embedding):
    """Find most similar product using S3 Vectors"""
    try:
        # Convert to float32
        query_vector_float32 = [float(x) for x in user_embedding]
        
        response = s3vectors.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=INDEX_NAME,
            topK=1,
            queryVector={'float32': query_vector_float32},
            returnMetadata=True,
            returnDistance=True
        )
        
        if response['vectors']:
            result = response['vectors'][0]
            metadata = result.get('metadata', {})
            distance = result.get('distance', 0.0)
            
            # Convert distance to similarity (for cosine: similarity = 1 - distance)
            similarity = 1.0 - distance if distance else 1.0
            
            return {
                'name': metadata.get('name', ''),
                'description': metadata.get('description', ''),
                'category': metadata.get('category', ''),
                'price': float(metadata.get('price', 0)),
                'features': metadata.get('features', '').split('|') if metadata.get('features') else [],
                'similarity': similarity
            }
        
        return {'name': '', 'description': '', 'similarity': 0.0}
        
    except Exception as e:
        print(f"S3 Vectors query error: {e}")
        return {'name': '', 'description': '', 'similarity': 0.0}

def get_embedding(text):
    """Generate embedding using Titan"""
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=json.dumps({"inputText": text})
    )
    return json.loads(response['body'].read())['embedding']

def generate_product_response(question, product):
    """Generate product response with Nova Lite"""
    prompt = f"""You are a helpful product assistant. Answer the customer's question about this product.

Customer Question: {question}

Product Information:
- Name: {product['name']}
- Category: {product['category']}
- Price: ${product['price']}
- Description: {product['description']}
- Features: {', '.join(product['features'])}

Provide a helpful, friendly response about this product. Be concise and focus on what the customer asked."""

    try:
        response = bedrock.invoke_model(
            modelId=NOVA_MODEL_ID,
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"max_new_tokens": 200, "temperature": 0.7}
            })
        )
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text']
    except Exception as e:
        return f"Here's what I found about {product['name']}: {product['description']} It's priced at ${product['price']}."

def generate_no_match_response(question):
    """Generate response when no product matches"""
    prompt = f"""A customer asked: "{question}"

You couldn't find a matching product in the catalog. Politely let them know and suggest they browse categories or contact support. Be helpful and friendly."""

    try:
        response = bedrock.invoke_model(
            modelId=NOVA_MODEL_ID,
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"max_new_tokens": 150, "temperature": 0.7}
            })
        )
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text']
    except:
        return "I couldn't find a specific product matching your query. Please browse our categories or contact support for assistance."