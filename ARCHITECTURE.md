# Product Chat Architecture Flow

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │    │                 │
│   React App     │───▶│   API Gateway   │───▶│   Lambda        │───▶│   S3 Vectors    │
│   (Frontend)    │    │   (REST API)    │    │   (Backend)     │    │   (Embeddings)  │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │ S3      │             │ CORS    │             │ Nova    │             │ Cosine  │
    │ Website │             │ Headers │             │ Lite    │             │ Search  │
    └─────────┘             └─────────┘             └─────────┘             └─────────┘
```

## 🔄 Data Flow

### 1. Setup Phase
```
Products Data → Titan Embed → S3 Vectors Index
     │              │              │
     ▼              ▼              ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│ JSON    │   │ 1536-D  │   │ Vector  │
│ Format  │   │ Vectors │   │ Storage │
└─────────┘   └─────────┘   └─────────┘
```

### 2. Query Phase
```
User Query → Titan Embed → S3 Vectors Query → Product Match → Nova Lite → Response
     │           │              │                 │            │           │
     ▼           ▼              ▼                 ▼            ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ "wireless│ │ Vector  │ │ Cosine      │ │ Best Match  │ │ AI      │ │ Natural │
│ headph." │ │ [1536]  │ │ Similarity  │ │ Product     │ │ Response│ │ Language│
└─────────┘ └─────────┘ └─────────────┘ └─────────────┘ └─────────┘ └─────────┘
```

## 🏛️ AWS Services Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                AWS Cloud                                        │
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │             │    │             │    │             │    │             │     │
│  │     S3      │    │ API Gateway │    │   Lambda    │    │ S3 Vectors  │     │
│  │  (Website)  │    │             │    │             │    │             │     │
│  │             │    │             │    │             │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘     │
│                              │                  │                             │
│                              │                  │                             │
│                              ▼                  ▼                             │
│                     ┌─────────────┐    ┌─────────────┐                       │
│                     │             │    │             │                       │
│                     │ CloudWatch  │    │   Bedrock   │                       │
│                     │   (Logs)    │    │ (Nova Lite) │                       │
│                     │             │    │ (Titan Emb) │                       │
│                     └─────────────┘    └─────────────┘                       │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔧 Component Details

### Frontend (React App)
- **Location**: S3 Static Website
- **Purpose**: User interface for product chat
- **Features**: Chat interface, product cards, suggestions
- **Communication**: HTTPS requests to API Gateway

### API Gateway
- **Purpose**: REST API endpoint with CORS
- **Endpoint**: `/prod/chat`
- **Methods**: POST (queries), OPTIONS (CORS)
- **Security**: Public access with CORS headers

### Lambda Function
- **Runtime**: Python 3.9
- **Purpose**: Process queries and generate responses
- **Integrations**: 
  - Bedrock (Nova Lite + Titan Embed)
  - S3 Vectors (similarity search)
- **Memory**: 512MB, Timeout: 30s

### S3 Vectors
- **Purpose**: Vector similarity search
- **Index**: Products index with 1536 dimensions
- **Distance**: Cosine similarity
- **Data**: Product embeddings with metadata

### Bedrock Models
- **Titan Embed**: Generate 1536-dimensional embeddings
- **Nova Lite**: Generate natural language responses
- **Region**: us-east-1

## 📊 Request Flow Diagram

```
1. User types query
        │
        ▼
2. React sends POST to API Gateway
        │
        ▼
3. API Gateway triggers Lambda
        │
        ▼
4. Lambda gets embedding from Titan
        │
        ▼
5. Lambda queries S3 Vectors
        │
        ▼
6. S3 Vectors returns similar products
        │
        ▼
7. Lambda generates response with Nova Lite
        │
        ▼
8. Response sent back through API Gateway
        │
        ▼
9. React displays chat response with product card
```

## 🔐 Security & Permissions

### IAM Roles & Policies
```
Lambda Execution Role:
├── AWSLambdaBasicExecutionRole
├── AmazonS3ReadOnlyAccess
├── AmazonBedrockFullAccess
└── S3VectorsAccess (Custom Policy)
    ├── s3vectors:QueryVectors
    ├── s3vectors:GetVectors
    └── s3vectors:ListVectorStores
```

### S3 Bucket Policies
```
Website Bucket: Public read access
Data Bucket: Lambda read access only
Vector Bucket: Lambda query access only
```

## 📈 Scalability Considerations

- **Lambda**: Auto-scales based on requests
- **S3 Vectors**: Handles high-throughput queries
- **API Gateway**: Built-in rate limiting and caching
- **Bedrock**: Managed service with auto-scaling
- **S3 Website**: Global CDN distribution available

## 💰 Cost Optimization

- **Lambda**: Pay per request and execution time
- **S3 Vectors**: Pay per query and storage
- **Bedrock**: Pay per token processed
- **S3**: Minimal storage costs
- **API Gateway**: Pay per API call

## 🔄 Data Lifecycle

1. **Setup**: Products → Embeddings → S3 Vectors Index
2. **Runtime**: Query → Embedding → Search → Match → Response
3. **Updates**: New products require re-embedding and index update
4. **Cleanup**: All resources can be deleted via cleanup script