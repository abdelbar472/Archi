# Galileo Service

**Overview**: Main functionality for the galileo module.

## Key Components
- [[galileo_chat_services_redis_service.py]] **(service)**

## Database
- [[galileo_chat_apps.py_ChatConfig]] (model)
- [[galileo_chat_consumers.py_ChatConsumer]] (model)
- [[galileo_chat_management_commands_setup_scylladb.py_Command]] (sql_model)
- [[galileo_chat_middleware.py_JWTAuthMiddleware]] (sql_model)
- [[galileo_chat_models.py]] (model)
- [[galileo_chat_models.py_ChatRoom]] (model)
- [[galileo_chat_models.py_ChatRoomMembership]] (model)
- [[galileo_chat_models.py_MessageScylla]] (model)
- [[galileo_chat_models.py_Meta]] (model)
- [[galileo_chat_permissions.py_HasSpaceAccess]] (sql_model)
- [[galileo_chat_permissions.py_IsChatRoomMember]] (sql_model)
- [[galileo_chat_serializers.py_ChatRoomMembershipSerializer]] (model)

## Related Services
- [[root]]
- [[table:commands]]
- [[table:customusermanagers]]
- [[table:hasspaceaccesss]]
- [[table:hasworkspaceaccesss]]
- [[table:ischatroommembers]]
- [[table:isspacemembers]]
- [[table:isspaceowneroradmins]]
