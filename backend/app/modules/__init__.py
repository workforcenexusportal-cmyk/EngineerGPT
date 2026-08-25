"""Platform modules. Each module is a self-contained clean-architecture package.

Contract per module:
- ``schemas.py``  Pydantic request/response models (the module's public data types)
- ``service.py``  Domain logic; depends only on core + ai + pipeline abstractions
- ``router.py``   FastAPI wiring; thin, delegates to the service
"""
