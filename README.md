# Product Chat with S3 Vectors & Nova Lite

An AI-powered product chat application that uses Amazon S3 Vectors for semantic search and Nova Lite for natural language responses.

## 🏗️ Architecture


- **Frontend**: React app deployed to S3 static website
- **Backend**: Lambda function using S3 Vectors for semantic search and Nova Lite for AI responses
- **Data**: Product embeddings stored in S3 Vectors for fast similarity search
- **API**: API Gateway for REST endpoints with CORS support

## 📁 Project Structure

```
├── backend/
│   ├── deploy_lambda.py            # Deploy Lambda function
│   ├── generate_product_embeddings.py # Generate S3 Vector embeddings
│   ├── product_chat_lambda.py      # Main Lambda function code
│   ├── setup_api_gateway.py        # Create API Gateway
│   └── setup_product_s3.py         # Setup S3 bucket with products
├── frontend/
│   ├── src/
│   │   ├── App.js                  # Main React component
│   │   ├── App.css                 # Styling
│   │   └── index.js                # React entry point
│   ├── public/
│   │   └── index.html              # HTML template
│   ├── package.json                # Dependencies
│   └── deploy_frontend.py          # Deploy React app to S3
├── deploy_backend_simple.py        # One-step backend deployment
├── cleanup_aws_resources.py        # Clean up all AWS resources
├── .gitignore                      # Git ignore file
└── README.md                       # This file
```

## 🚀 Quick Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.9+
- Node.js and npm (for frontend)
- Access to Amazon Bedrock (Nova Lite and Titan Embed models)

### Step 1: Deploy Backend
```bash
python deploy_backend_simple.py
```

This will:
1. Create S3 bucket with sample products
2. Create S3 Vectors bucket and index
3. Generate embeddings using Titan Embed
4. Deploy Lambda function with S3 Vectors integration
5. Create API Gateway with CORS
6. Output the API URL

### Step 2: Update Frontend API URL
Copy the API URL from Step 1 output and update `frontend/src/App.js`:
```javascript
const API_URL = 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat';
```

### Step 3: Deploy Frontend
```bash
cd frontend
python deploy_frontend.py
```

This will:
1. Create S3 website bucket
2. Install npm dependencies
3. Build React app
4. Upload files to S3
5. Configure static website hosting
6. Output the website URL

## 🧪 Testing

### Test Backend API
```bash
python -c "import requests; print(requests.post('YOUR_API_URL', json={'question': 'wireless headphones'}).json())"
```

### Test Frontend
Visit the website URL and try these queries:
- "I need wireless headphones"
- "Show me a fitness tracker"
- "Gaming mouse with RGB"
- "Do you have phone chargers?"
- "What smart speakers are available?"

## 🛠️ Manual Deployment (Alternative)

If you prefer step-by-step deployment:

### Backend Components
```bash
# Setup S3 bucket with products
cd backend
python setup_product_s3.py

# Generate embeddings for S3 Vectors
python generate_product_embeddings.py

# Deploy Lambda function
python deploy_lambda.py

# Setup API Gateway
python setup_api_gateway.py
```

### Frontend Components
```bash
# Deploy React app
cd frontend
python deploy_frontend.py
```

## 🧹 Cleanup

To remove all AWS resources:
```bash
python cleanup_aws_resources.py
```

This will delete:
- S3 buckets (data, vectors, website)
- Lambda functions
- IAM roles and policies
- API Gateways
- S3 Vectors buckets and indexes

## 🎯 Features

- **Semantic Search**: Uses S3 Vectors with cosine similarity for intelligent product matching
- **AI Responses**: Nova Lite generates natural, contextual responses
- **Real-time Chat**: Interactive chat interface with typing indicators
- **Product Cards**: Rich product information display with confidence scores
- **Responsive Design**: Works on desktop and mobile devices
- **CORS Enabled**: Proper cross-origin request handling
- **Error Handling**: Graceful error handling and fallback responses

## 📊 Sample Products

The system includes 5 sample products:
1. Wireless Bluetooth Headphones ($89.99)
2. Smart Fitness Watch ($199.99)
3. Portable Phone Charger ($29.99)
4. Wireless Gaming Mouse ($79.99)
5. Smart Home Speaker ($129.99)

## 🔧 Customization

### Adding More Products
1. Edit the products array in `deploy_backend_simple.py`
2. Redeploy backend: `python deploy_backend_simple.py`

### Modifying the Chat Interface
- Edit `frontend/src/App.js` for functionality
- Edit `frontend/src/App.css` for styling
- Redeploy: `cd frontend && python deploy_frontend.py`

### Adjusting Search Sensitivity
Modify `SIMILARITY_THRESHOLD` in the Lambda code (default: 0.5)
- Lower values = stricter matching
- Higher values = more lenient matching


##  Troubleshooting

### Common Issues

1. **Lambda timeout**: Increase timeout in deployment script
2. **CORS errors**: Verify API Gateway CORS configuration
3. **Embedding errors**: Check Bedrock model access permissions
4. **S3 Vectors access denied**: Verify IAM permissions
5. **Frontend 404 errors**: Ensure S3 website hosting is enabled

### Debug Steps
1. Check CloudWatch logs for Lambda errors
2. Test API directly with curl or Python requests
3. Verify S3 Vectors bucket and index exist
4. Ensure API Gateway is properly deployed
5. Check browser console for frontend errors

### Permission Requirements

Ensure your AWS credentials have access to:
- S3 (create buckets, upload objects)
- S3 Vectors (create buckets, indexes, query vectors)
- Lambda (create functions, update code)
- IAM (create roles, attach policies)
- API Gateway (create APIs, deploy stages)
- Bedrock (invoke Nova Lite and Titan Embed models)

## 📝 License

This project is for educational and demonstration purposes. Ensure you comply with AWS service terms and pricing.

## 🤝 Contributing

Feel free to:
- Add more product categories
- Improve the chat interface
- Enhance the embedding strategy
- Add more language support
- Optimize performance

---

**Happy chatting! 🛍️✨**
