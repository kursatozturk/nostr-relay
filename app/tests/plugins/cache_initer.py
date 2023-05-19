from dotenv import load_dotenv
from pytest import Session


def pytest_sessionstart(session: Session):
    load_dotenv("cache/.env")  # load cache credentials
