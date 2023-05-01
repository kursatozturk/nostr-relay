import os

from dotenv import load_dotenv
from pytest import Session


def pytest_sessionstart(session: Session):
    load_dotenv("db/.env")  # load db credentials
