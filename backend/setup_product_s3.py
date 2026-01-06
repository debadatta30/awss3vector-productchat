import boto3
import json
import csv
import io

s3 = boto3.client('s3', region_name='us-east-1')

BUCKET_NAME = "product-chat-data"

def setup_product_bucket():
    """Create S3 bucket and upload sample product data"""
    
    print(f"Creating S3 bucket: {BUCKET_NAME}")
    
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print("Bucket created successfully")
    except Exception as e:
        if "BucketAlreadyOwnedByYou" in str(e):
            print("Bucket already exists")
        else:
            print(f"Error creating bucket: {e}")
            return
    
    # Sample product data
    products = [
        {
            "name": "Wireless Bluetooth Headphones",
            "category": "Electronics",
            "price": 89.99,
            "description": "Premium wireless headphones with noise cancellation and 30-hour battery life",
            "features": ["Noise Cancellation", "30hr Battery", "Bluetooth 5.0", "Quick Charge"]
        },
        {
            "name": "Smart Fitness Watch",
            "category": "Wearables",
            "price": 199.99,
            "description": "Advanced fitness tracker with heart rate monitoring, GPS, and sleep tracking",
            "features": ["Heart Rate Monitor", "GPS Tracking", "Sleep Analysis", "Water Resistant"]
        },
        {
            "name": "Portable Phone Charger",
            "category": "Accessories",
            "price": 29.99,
            "description": "High-capacity power bank with fast charging for smartphones and tablets",
            "features": ["10000mAh Capacity", "Fast Charging", "USB-C", "LED Display"]
        },
        {
            "name": "Wireless Gaming Mouse",
            "category": "Gaming",
            "price": 79.99,
            "description": "High-precision gaming mouse with customizable RGB lighting and programmable buttons",
            "features": ["RGB Lighting", "Programmable Buttons", "High DPI", "Wireless"]
        },
        {
            "name": "Smart Home Speaker",
            "category": "Smart Home",
            "price": 149.99,
            "description": "Voice-controlled smart speaker with premium sound quality and home automation",
            "features": ["Voice Control", "Premium Audio", "Smart Home Hub", "Multi-room Audio"]
        }
    ]
    
    # Convert to CSV format
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=['name', 'category', 'price', 'description', 'features'])
    writer.writeheader()
    
    for product in products:
        product_row = product.copy()
        product_row['features'] = '|'.join(product['features'])  # Join features with |
        writer.writerow(product_row)
    
    # Upload CSV to S3
    print("Uploading product data...")
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key='products.csv',
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )
    
    print(f"Setup complete!")
    print(f"   Bucket: s3://{BUCKET_NAME}")
    print(f"   Products: {len(products)} items")
    print(f"\nNext step: python generate_product_embeddings.py")

if __name__ == "__main__":
    setup_product_bucket()