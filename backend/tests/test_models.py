from sqlalchemy.orm import configure_mappers

from app.db.base import Base


def test_all_model_mappers_can_be_configured() -> None:
    assert Base.metadata.tables
    configure_mappers()
