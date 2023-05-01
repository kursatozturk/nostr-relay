import os
from pathlib import Path

import pytest

pytest_plugins = [
    "tests.plugins.db_initer",
    "pytest_asyncio"
]
