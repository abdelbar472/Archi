# User Service

**Overview**: Main functionality for the user module.

## Key Components
- [[user_main.py]] **(main)**
- [[user_routers.py]] **(router)**
- [[user_services.py]] **(service)**

## Database
- [[user_config.py_Settings]] (sql_model)
- [[user_grpc_server.py_UserServicer]] (model)
- [[user_models.py]] (model)
- [[user_models.py_UserProfile]] (sql_model)
- [[user_schemas.py]] (model)
- [[user_schemas.py_FollowListResponse]] (sql_model)
- [[user_schemas.py_FollowStatsResponse]] (sql_model)
- [[user_schemas.py_ProfileResponse]] (sql_model)
- [[user_schemas.py_ProfileUpdate]] (sql_model)
- [[user_schemas.py_TokenRefreshRequest]] (sql_model)
- [[user_schemas.py_TokenResponse]] (sql_model)
- [[user_schemas.py_UserPayload]] (sql_model)

## Related Services
- [[AsyncSession]]
- [[AuthServiceStub]]
- [[FastAPI]]
- [[FollowServiceStub]]
- [[GetFollowListResponse]]
- [[GetFollowStatsResponse]]
- [[HTTPAuthorizationCredentials]]
- [[ProfileUpdate]]
