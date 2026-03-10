# Bedrock Foundations - Architecture Diagrams

---

## RAG Pattern Architecture

```mermaid
graph TB
    USER[User Query] --> BEDROCK[Amazon Bedrock]
    
    subgraph "Embedding Generation"
        BEDROCK --> TITAN[Titan Embeddings v2]
        TITAN --> EMBED[Vector Embeddings]
    end
    
    subgraph "Vector Stores"
        EMBED --> FAISS[FAISS Local]
        EMBED --> PINECONE[Pinecone Cloud]
        EMBED --> OPENSEARCH[OpenSearch]
        EMBED --> KENDRA[Amazon Kendra]
    end
    
    subgraph "Retrieval"
        FAISS --> RETRIEVE[Retrieve Top-K]
        PINECONE --> RETRIEVE
        OPENSEARCH --> RETRIEVE
        KENDRA --> RETRIEVE
    end
    
    RETRIEVE --> AUGMENT[Augment Prompt]
    AUGMENT --> LLM[Claude 3 Sonnet]
    LLM --> RESPONSE[Response]
    
    style BEDROCK fill:#ff9900
    style TITAN fill:#4ecdc4
    style LLM fill:#7b68ee
```

---

## Simple Agent Architecture

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Orchestrator
    participant Tool1
    participant Tool2
    participant LLM
    
    User->>Agent: User Input
    Agent->>Orchestrator: Parse Intent
    Orchestrator->>LLM: Determine Action
    LLM-->>Orchestrator: Call Tool1
    Orchestrator->>Tool1: Execute
    Tool1-->>Orchestrator: Result
    Orchestrator->>LLM: Process Result
    LLM-->>Orchestrator: Call Tool2
    Orchestrator->>Tool2: Execute
    Tool2-->>Orchestrator: Result
    Orchestrator->>LLM: Generate Response
    LLM-->>Agent: Final Response
    Agent-->>User: Display Response
```

---

## Bedrock Flows Architecture

```mermaid
graph LR
    START([Start]) --> INPUT[Input Node]
    INPUT --> CONDITION{Condition Node}
    
    CONDITION -->|Path A| PROMPT1[Prompt Node 1]
    CONDITION -->|Path B| PROMPT2[Prompt Node 2]
    
    PROMPT1 --> AGENT1[Agent Node]
    PROMPT2 --> KB[Knowledge Base Node]
    
    AGENT1 --> MERGE[Merge Node]
    KB --> MERGE
    
    MERGE --> OUTPUT[Output Node]
    OUTPUT --> END([End])
    
    style START fill:#4ecdc4
    style CONDITION fill:#ffe66d
    style END fill:#ff6b6b
```

---

## Multimodal Processing

```mermaid
graph TB
    subgraph "Input Types"
        TEXT[Text Input]
        IMAGE[Image Input]
        VIDEO[Video Input]
    end
    
    subgraph "Processing"
        TEXT --> NOVA[Nova Pro]
        IMAGE --> NOVA
        VIDEO --> NOVA
    end
    
    subgraph "Analysis"
        NOVA --> OCR[Text Extraction]
        NOVA --> VISION[Image Analysis]
        NOVA --> SCENE[Scene Detection]
    end
    
    OCR --> COMBINE[Combine Results]
    VISION --> COMBINE
    SCENE --> COMBINE
    
    COMBINE --> RESPONSE[Multimodal Response]
    
    style NOVA fill:#ff9900
    style COMBINE fill:#4ecdc4
```

---

## Embeddings Pipeline

```mermaid
graph LR
    DOCS[Documents] --> CHUNK[Chunk Text<br/>512 tokens]
    CHUNK --> EMBED[Titan Embeddings v2]
    EMBED --> VECTOR[Vector<br/>1024 dimensions]
    VECTOR --> STORE[(Vector Store)]
    
    QUERY[User Query] --> EMBED_Q[Generate Query Embedding]
    EMBED_Q --> SEARCH[Similarity Search]
    STORE --> SEARCH
    SEARCH --> RESULTS[Top-K Results]
    
    style EMBED fill:#ff9900
    style STORE fill:#4ecdc4
    style SEARCH fill:#7b68ee
```

---

## Fine-Tuning Workflow

```mermaid
stateDiagram-v2
    [*] --> PrepareData
    PrepareData --> ValidateFormat
    ValidateFormat --> UploadToS3
    UploadToS3 --> CreateJob
    CreateJob --> Training
    Training --> Validation
    Validation --> ModelReady: Success
    Validation --> Failed: Error
    ModelReady --> Deploy
    Deploy --> [*]
    Failed --> [*]
```

---

## Knowledge Base Integration

```mermaid
graph TB
    subgraph "Data Sources"
        S3[S3 Bucket]
        CONFLUENCE[Confluence]
        SHAREPOINT[SharePoint]
    end
    
    S3 --> SYNC[Data Sync]
    CONFLUENCE --> SYNC
    SHAREPOINT --> SYNC
    
    SYNC --> CHUNK[Chunking Strategy]
    CHUNK --> EMBED[Generate Embeddings]
    EMBED --> VECTOR[(Vector Store)]
    
    subgraph "Query Processing"
        QUERY[User Query] --> KB[Knowledge Base]
        KB --> VECTOR
        VECTOR --> RETRIEVE[Retrieve Context]
        RETRIEVE --> AUGMENT[Augment Prompt]
        AUGMENT --> LLM[LLM]
        LLM --> RESPONSE[Response]
    end
    
    style KB fill:#ff9900
    style VECTOR fill:#4ecdc4
```

---

## Agent with Tools

```mermaid
graph TB
    USER[User Input] --> AGENT[Bedrock Agent]
    
    subgraph "Tool Selection"
        AGENT --> ORCHESTRATOR[Orchestrator]
        ORCHESTRATOR --> TOOL1[Search Tool]
        ORCHESTRATOR --> TOOL2[Calculator Tool]
        ORCHESTRATOR --> TOOL3[API Tool]
    end
    
    subgraph "Execution"
        TOOL1 --> LAMBDA1[Lambda Function 1]
        TOOL2 --> LAMBDA2[Lambda Function 2]
        TOOL3 --> LAMBDA3[Lambda Function 3]
    end
    
    LAMBDA1 --> RESULT[Combine Results]
    LAMBDA2 --> RESULT
    LAMBDA3 --> RESULT
    
    RESULT --> LLM[Generate Response]
    LLM --> USER
    
    style AGENT fill:#ff9900
    style ORCHESTRATOR fill:#7b68ee
```

---

## Complete Learning Path

```mermaid
graph LR
    START([Start Here]) --> RAG[RAG Patterns]
    RAG --> AGENTS[Agents Basics]
    AGENTS --> FLOWS[Flows]
    FLOWS --> MULTI[Multimodal]
    MULTI --> EMBED[Embeddings]
    EMBED --> TUNE[Fine-Tuning]
    TUNE --> END([Production Ready])
    
    style START fill:#4ecdc4
    style END fill:#ff6b6b
```

---

**Last Updated**: 2026-03-09
