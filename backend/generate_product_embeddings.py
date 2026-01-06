import json
import boto3
import csv
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
s3vectors = boto3.client('s3vectors', region_name='us-east-1')

BUCKET_NAME = "product-chat-data"
CSV_KEY = "products.csv"
VECTOR_BUCKET_NAME = "product-chat-vectors"
INDEX_NAME = "products"

def generate_embedding(text):
    """Generate embedding using Bedrock Titan"""
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=json.dumps({"inputText": text})
    )
    return json.loads(response['body'].read())['embedding']

def create_vector_bucket():
    """Create S3 Vector Bucket"""
    try:
        response = s3vectors.create_vector_bucket(
            vectorBucketName=VECTOR_BUCKET_NAME
        )
        print(f"Created vector bucket: {VECTOR_BUCKET_NAME}")
        return True
    except Exception as e:
        if 'ConflictException' in str(e):
            print(f"Vector bucket {VECTOR_BUCKET_NAME} already exists")
            return True
        else:
            print(f"Error creating vector bucket: {e}")
            return False

def create_vector_index():
    """Create S3 Vector Index"""
    try:
        response = s3vectors.create_index(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=INDEX_NAME,
            dataType='float32',
            dimension=1536,
            distanceMetric='cosine'
        )
        print(f"Created vector index: {INDEX_NAME}")
        return True
    except Exception as e:
        if 'ConflictException' in str(e):
            print(f"Vector index {INDEX_NAME} already exists")
            return True
        else:
            print(f"Error creating vector index: {e}")
            return False

def generate_product_embeddings():
    """Generate embeddings and store in S3 Vectors"""
    
    print("Setting up S3 Vector Bucket...")
    
    if not create_vector_bucket():
        return
    
    print("Setting up S3 Vector Index...")
    
    if not create_vector_index():
        return
    
    print("Loading products from S3...")
    
    try:
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=CSV_KEY)
        csv_content = obj['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error loading products: {e}")
        return
    
    csv_reader = csv.DictReader(csv_content.splitlines())
    total_products = sum(1 for _ in csv.DictReader(csv_content.splitlines()))
    print(f"Found {total_products} products")
    print("Generating embeddings and storing in S3 Vectors...\n")
    
    csv_reader = csv.DictReader(csv_content.splitlines())
    for i, row in enumerate(csv_reader, 1):
        name = row['name']
        category = row['category']
        price = float(row['price'])
        description = row['description']
        features = row['features'].split('|')
        
        print(f"[{i}/{total_products}] Processing: {name}")
        
        # Create searchable text
        searchable_text = f"{name} {category} {description} {' '.join(features)}"
        
        # Generate vector
        vector = generate_embedding(searchable_text)
        
        # Store in S3 Vectors (batch)
        vector_float32 = [float(x) for x in vector]
        
        metadata = {
            'name': name,
            'category': category,
            'price': str(price),
            'description': description,
            'features': '|'.join(features)
        }
        
        try:
            s3vectors.put_vectors(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=INDEX_NAME,
                vectors=[
                    {
                        'key': f"product_{i}",
                        'data': {
                            'float32': vector_float32
                        },
                        'metadata': metadata
                    }
                ]
            )
        except Exception as e:
            print(f"Error storing vector for {name}: {e}")
    
    print(f"\nDone! Stored {total_products} product vectors in S3 Vectors")
    print(f"Vector Bucket: {VECTOR_BUCKET_NAME}")
    print(f"Vector Index: {INDEX_NAME}")

if __name__ == "__main__":
    generate_product_embeddings()