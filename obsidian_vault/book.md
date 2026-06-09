# Book Service

**Overview**: Main functionality for the book module.

## Key Components
- [[book_main.py]] **(main)**
- [[book_test_new_service.py]] **(service)**

## Database
- [[book_book_v4_pb2_grpc.py_BookService]] (model)
- [[book_book_v4_pb2_grpc.py_BookServiceServicer]] (model)
- [[book_book_v4_pb2_grpc.py_BookServiceStub]] (model)
- [[book_config.py_Config]] (model)
- [[book_config.py_Settings]] (sql_model)
- [[book_database.py_Database]] (model)
- [[book_grpc_client.py_RAGServiceGRPCClient]] (model)
- [[book_grpc_server.py_BookService]] (model)
- [[book_models_author.py_AuthorBio]] (sql_model)
- [[book_models_author.py_AuthorProfile]] (sql_model)
- [[book_models_author.py_AuthorStats]] (sql_model)
- [[book_models_author.py_AuthorStyleProfile]] (sql_model)

## Related Services
- [[AuthorProfile]]
- [[BookProfile]]
- [[FastAPI]]
- [[IndexBookPayload]]
- [[SeriesProfile]]
- [[root]]
- [[table:authorbios]]
- [[table:authorprofiles]]
