# Rag Service

**Overview**: Main functionality for the rag module.

## Key Components
- [[rag_main.py]] **(main)**
- [[rag_routers.py]] **(router)**
- [[rag_services.py]] **(service)**

## Database
- [[rag_config.py_Config]] (model)
- [[rag_config.py_Settings]] (sql_model)
- [[rag_embedding.py_EmbeddingGenerator]] (model)
- [[rag_engine.py_RAGEngine]] (model)
- [[rag_grpc_client.py_BookServiceGRPCClient]] (model)
- [[rag_grpc_server.py_GRPCServer]] (model)
- [[rag_grpc_server.py_RagServicer]] (model)
- [[rag_qdrant_client.py_DatabaseManager]] (model)
- [[rag_routers.py_BookSyncRequest]] (sql_model)
- [[rag_services.py_IndexingService]] (model)
- [[rag_services.py_SearchService]] (model)
- [[rag_vector_store.py_VectorStore]] (model)

## Related Services
- [[BookSyncRequest]]
- [[FastAPI]]
- [[GetBookEmbeddingRequest]]
- [[GetSimilarBooksRequest]]
- [[IndexBooksRequest]]
- [[QdrantClient]]
- [[RetrievalCandidate]]
- [[SemanticSearchRequest]]
