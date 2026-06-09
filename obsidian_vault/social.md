# Social Service

**Overview**: Main functionality for the social module.

## Key Components
- [[social_main.py]] **(main)**
- [[social_routers.py]] **(router)**
- [[social_services.py]] **(service)**

## Database
- [[social_config.py_Settings]] (sql_model)
- [[social_grpc_server.py_SocialServicer]] (model)
- [[social_models.py]] (model)
- [[social_models.py_BookLike]] (sql_model)
- [[social_models.py_BookRating]] (sql_model)
- [[social_models.py_BookReview]] (sql_model)
- [[social_models.py_ReviewLike]] (sql_model)
- [[social_models.py_Shelf]] (sql_model)
- [[social_models.py_ShelfItem]] (sql_model)
- [[social_schemas.py]] (model)
- [[social_schemas.py_BookSocialStatsResponse]] (sql_model)
- [[social_schemas.py_LikeResponse]] (sql_model)

## Related Services
- [[AsyncSession]]
- [[AuthServiceStub]]
- [[BookLike]]
- [[BookRating]]
- [[BookReview]]
- [[FastAPI]]
- [[HTTPAuthorizationCredentials]]
- [[RatingUpsertRequest]]
