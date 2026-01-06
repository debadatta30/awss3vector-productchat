import boto3
import os
import json
import subprocess
from pathlib import Path

s3 = boto3.client('s3', region_name='us-east-1')

BUCKET_NAME = 'product-chat-website'
FRONTEND_PATH = '.'

def create_s3_bucket():
    """Create S3 bucket for static website"""
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"Created bucket: {BUCKET_NAME}")
    except Exception as e:
        if 'BucketAlreadyOwnedByYou' in str(e):
            print(f"Bucket {BUCKET_NAME} already exists")
        else:
            print(f"Error creating bucket: {e}")
            return False
    
    # Configure bucket for static website hosting
    try:
        s3.put_bucket_website(
            Bucket=BUCKET_NAME,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}
            }
        )
        print("Configured static website hosting")
    except Exception as e:
        print(f"Website config error: {e}")
    
    # Try to disable Block Public Access and set bucket policy
    try:
        # Disable Block Public Access
        s3.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        print("Disabled Block Public Access")
        
        # Set bucket policy for public read
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
                }
            ]
        }
        
        s3.put_bucket_policy(
            Bucket=BUCKET_NAME,
            Policy=json.dumps(bucket_policy)
        )
        print("Set public read policy")
        
    except Exception as e:
        print(f"⚠️ Public access setup failed: {e}")
        print("Files uploaded but may not be publicly accessible")
    return True

def build_react_app():
    """Build React app for production"""
    print("Installing dependencies...")
    
    try:
        # Install dependencies
        result = subprocess.run(
            ['npm.cmd', 'install'],
            cwd=FRONTEND_PATH,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            print(f"Install failed: {result.stderr}")
            return False
        
        print("Building React app...")
        
        # Build the app
        result = subprocess.run(
            ['npm.cmd', 'run', 'build'],
            cwd=FRONTEND_PATH,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print("React app built successfully")
            return True
        else:
            print(f"Build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error building app: {e}")
        return False

def upload_to_s3():
    """Upload build files to S3"""
    print("Uploading files to S3...")
    
    build_path = Path(FRONTEND_PATH) / 'build'
    
    if not build_path.exists():
        print("Build directory not found")
        return False
    
    # Upload all files
    for file_path in build_path.rglob('*'):
        if file_path.is_file():
            # Get relative path for S3 key
            s3_key = str(file_path.relative_to(build_path)).replace('\\', '/')
            
            # Determine content type
            content_type = 'text/html'
            if file_path.suffix == '.css':
                content_type = 'text/css'
            elif file_path.suffix == '.js':
                content_type = 'application/javascript'
            elif file_path.suffix == '.json':
                content_type = 'application/json'
            elif file_path.suffix in ['.png', '.jpg', '.jpeg']:
                content_type = f'image/{file_path.suffix[1:]}'
            
            # Upload file
            extra_args = {'ContentType': content_type}
            
            # Add cache control for static assets
            if file_path.suffix in ['.css', '.js']:
                extra_args['CacheControl'] = 'no-cache, must-revalidate'
            
            s3.upload_file(
                str(file_path),
                BUCKET_NAME,
                s3_key,
                ExtraArgs=extra_args
            )
            
            print(f"Uploaded: {s3_key}")
    
    return True

def main():
    print("Deploying Product Chat frontend to S3...")
    
    # Create S3 bucket
    if not create_s3_bucket():
        return
    
    # Build React app
    if not build_react_app():
        return
    
    # Upload to S3
    if not upload_to_s3():
        return
    
    # Get website URL
    website_url = f"http://{BUCKET_NAME}.s3-website-us-east-1.amazonaws.com"
    
    print(f"\nDeployment complete!")
    print(f"Website URL: {website_url}")
    print(f"Your product chat is now live!")
    print(f"\nDon't forget to update the API_URL in App.js with your actual API Gateway URL")

if __name__ == "__main__":
    main()