from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.observability.health import check_database
from app.storage.database import Base


def test_check_database_healthy():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    result = check_database(session)

    assert result.healthy is True
    session.close()
    engine.dispose()


def test_check_database_unhealthy_when_query_fails():
    class FailingSession:
        def execute(self, _query):
            raise RuntimeError("database unavailable")

    result = check_database(FailingSession())

    assert result.healthy is False
    assert result.detail == "Database health check failed"
    assert "database unavailable" not in result.detail