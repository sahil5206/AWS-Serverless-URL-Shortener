# 🏗️ Architecture Diagram

## System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser] --> B[Frontend Interface]
        C[Mobile App] --> D[API Client]
    end
    
    subgraph "CDN Layer"
        E[CloudFront Distribution]
    end
    
    subgraph "API Layer"
        F[API Gateway]
        G[/shorten - POST]
        H[/{shortId} - GET]
    end
    
    subgraph "Compute Layer"
        I[Lambda: createShortener]
        J[Lambda: redirectShortener]
    end
    
    subgraph "Data Layer"
        K[DynamoDB Table]
        L[urlTable]
    end
    
    subgraph "Infrastructure"
        M[Terraform]
        N[IAM Roles]
        O[CloudWatch Logs]
    end
    
    A --> E
    B --> E
    C --> F
    D --> F
    E --> F
    F --> G
    F --> H
    G --> I
    H --> J
    I --> K
    J --> K
    K --> L
    M --> I
    M --> J
    M --> F
    M --> K
    I --> O
    J --> O
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Gateway
    participant L1 as createShortener
    participant L2 as redirectShortener
    participant D as DynamoDB
    
    Note over U,D: URL Shortening Flow
    U->>F: Enter long URL
    F->>A: POST /shorten
    A->>L1: Invoke Lambda
    L1->>D: Store mapping
    D-->>L1: Success
    L1-->>A: Return short URL
    A-->>F: Response
    F-->>U: Display short URL
    
    Note over U,D: URL Redirection Flow
    U->>A: GET /{shortId}
    A->>L2: Invoke Lambda
    L2->>D: Query short ID
    D-->>L2: Return original URL
    L2-->>A: HTTP 302 redirect
    A-->>U: Redirect to original URL
```

## Component Details

### AWS Lambda Functions
- **createShortener**: Handles URL shortening requests
- **redirectShortener**: Manages URL redirection

### Amazon DynamoDB
- **Table**: urlTable
- **Partition Key**: shortId (String)
- **Attributes**: shortId, longUrl, createdAt

### Amazon API Gateway
- **REST API**: RESTful endpoints
- **CORS**: Cross-origin resource sharing
- **Integration**: Lambda proxy integration

### Amazon CloudFront
- **Distribution**: Global CDN
- **Origin**: API Gateway
- **Caching**: Optimized for API responses

### Terraform Infrastructure
- **Provider**: AWS
- **Resources**: Lambda, API Gateway, DynamoDB, CloudFront
- **State**: Remote state management
