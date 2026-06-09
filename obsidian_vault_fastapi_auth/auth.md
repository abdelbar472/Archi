# Auth Service

**Overview**: Main functionality for the auth module.

## Key Components
- [[auth_main.py]] **(main)**
- [[auth_routers.py]] **(router)**
- [[auth_services.py]] **(service)**

## Database
- [[auth_config.py_Settings]] (sql_model)
- [[auth_grpc_server.py_AuthServicer]] (model)
- [[auth_models.py]] (model)
- [[auth_models.py_RefreshToken]] (sql_model)
- [[auth_models.py_User]] (sql_model)
- [[auth_schemas.py]] (model)
- [[auth_schemas.py_LoginRequest]] (sql_model)
- [[auth_schemas.py_RefreshTokenRequest]] (sql_model)
- [[auth_schemas.py_Token]] (sql_model)
- [[auth_schemas.py_TokenData]] (sql_model)
- [[auth_schemas.py_UserBase]] (sql_model)
- [[auth_schemas.py_UserCreate]] (sql_model)

## Related Services
- [[AsyncSession]]
- [[FastAPI]]
- [[HTTPAuthorizationCredentials]]
- [[LoginRequest]]
- [[RefreshToken]]
- [[RefreshTokenRequest]]
- [[Request]]
- [[User]]
