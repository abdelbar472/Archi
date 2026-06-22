# Language: Python
# Parser Status: Production Ready
# Primary Parser: AST (built-in) + Fallback Regex

## Domain & Main Use Cases
- Web backends & APIs
- Data science / ML pipelines
- CLI tools & automation
- Django & FastAPI heavy projects

## Key Frameworks & Patterns to Recognize
- Django: Views (class-based + function), Models, Serializers, Admin, Signals, Management Commands
- FastAPI: APIRouter, dependencies (@Depends), Pydantic models, endpoints (@app.get, @app.post)
- Flask: Blueprints, routes (@app.route)
- SQLAlchemy: Models (declarative_base), relationships, sessions
- Celery: Tasks (@task, @shared_task)
- Pydantic: BaseModel, validators
- Testing: pytest fixtures, Django TestCase

## Node Types Parser Must Detect
- django_view, django_model, django_serializer, django_admin
- fastapi_endpoint, fastapi_router, pydantic_model
- celery_task
- class, function, method
- cli_command (for management commands)

## What to Skip / Low Priority
- Migrations (alembic / django migrations)
- Very dynamic metaclass magic
- Pure math / numpy heavy code (unless data pipeline)

## Parser Strategy
- Primary: Python AST (very reliable)
- Fallback: Regex for quick wins / when AST misses context
- Goal: Strong cross-file call resolution + framework awareness

## Test Repositories Suggestions
- https://github.com/tiangolo/fastapi (FastAPI)
- https://github.com/django/django (Django)
- https://github.com/pallets/flask (Flask)
- Any internal FastAPI/Django project

---