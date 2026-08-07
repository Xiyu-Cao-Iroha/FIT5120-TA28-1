import os

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://calmpath:calmpath@localhost:5432/calmpath_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# The test suite must stay deterministic and network-free regardless of
# whatever is in the real .env - force the demo/fallback providers here.
# Tests that specifically want to exercise the Google-backed code paths
# mock httpx.get directly (see test_google_providers.py) rather than
# relying on a real key.
os.environ["GOOGLE_MAPS_API_KEY"] = ""
os.environ["USE_LIVE_PEDESTRIAN_DATA"] = "false"

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app import models  # noqa: E402,F401  (registers tables on Base.metadata)
from app.db import Base  # noqa: E402


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS postgis")
        conn.commit()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
