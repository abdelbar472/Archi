# Follow Service

**Overview**: Main functionality for the follow module.

## Key Components
- [[follow_main.py]] **(main)**
- [[follow_routers.py]] **(router)**
- [[follow_services.py]] **(service)**

## Database
- [[follow_config.py_Settings]] (sql_model)
- [[follow_grpc_server.py_FollowServicer]] (model)
- [[follow_models.py]] (model)
- [[follow_models.py_Follow]] (sql_model)
- [[follow_schemas.py]] (model)
- [[follow_schemas.py_FollowListResponse]] (sql_model)
- [[follow_schemas.py_FollowResponse]] (sql_model)
- [[follow_schemas.py_FollowStats]] (sql_model)
- [[follow_schemas.py_FollowerEntry]] (sql_model)

## Related Services
- [[AsyncSession]]
- [[AuthServiceStub]]
- [[FastAPI]]
- [[Follow]]
- [[FollowServiceStub]]
- [[GetFollowListResponse]]
- [[GetFollowStatsResponse]]
- [[HTTPAuthorizationCredentials]]
