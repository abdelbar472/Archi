# Recommendation Service

**Overview**: Main functionality for the recommendation module.

## Key Components
- [[recommendation_main.py]] **(main)**
- [[recommendation_routers.py]] **(router)**
- [[recommendation_service.py]] **(service)**

## Database
- [[recommendation_config.py_Config]] (model)
- [[recommendation_config.py_Settings]] (sql_model)
- [[recommendation_grpc_server.py_GRPCServer]] (model)
- [[recommendation_grpc_server.py_RecommendationServicer]] (model)
- [[recommendation_profile.py_UserProfile]] (model)
- [[recommendation_profile.py_UserProfileBuilder]] (model)
- [[recommendation_routers.py_InteractionEventBody]] (sql_model)
- [[recommendation_routers.py_RecommendationRequestBody]] (sql_model)
- [[recommendation_service.py_RecommendationService]] (model)

## Related Services
- [[FastAPI]]
- [[InteractionEventBody]]
- [[RagServiceStub]]
- [[RecommendationRequestBody]]
- [[Settings]]
- [[UserProfile]]
- [[root]]
- [[table:interactioneventbodys]]
