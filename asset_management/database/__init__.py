# Marks database as a Python package.


def import_models():
    """
    Import all models to ensure they are registered with SQLAlchemy.
    This function should be called before creating any sessions.
    """
    # Import all models here to avoid circular imports
    from asset_management.app.user import models as user_models  # noqa: F401
    from asset_management.app.club import models as club_models  # noqa: F401
    from asset_management.app.assets import models as asset_models  # noqa: F401
    from asset_management.app.schedule import models as schedule_models  # noqa: F401
    from asset_management.app.favorite import models as favorite_models  # noqa: F401
    from asset_management.app.picture import models as picture_models  # noqa: F401
    from asset_management.app.category import models as category_models  # noqa: F401
