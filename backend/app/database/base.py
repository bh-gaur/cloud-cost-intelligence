"""
Database Declarative Base and Model Registry
Imports all models to guarantee full table metadata registration on Base.metadata.create_all().
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all application models so Base.metadata is fully populated
def import_all_models():
    import app.models.user  # noqa: F401
    import app.models.organization  # noqa: F401
    import app.models.session  # noqa: F401
    import app.models.invitation  # noqa: F401
    import app.models.account  # noqa: F401
    import app.models.cost  # noqa: F401
    import app.models.alert  # noqa: F401
    import app.models.optimization  # noqa: F401
    import app.models.report  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.audit  # noqa: F401


import_all_models()
