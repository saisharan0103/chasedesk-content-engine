import random
from pathlib import Path

import pytest

from src.content_loader import load_knowledge_base

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = REPO_ROOT / "content"


@pytest.fixture(scope="session")
def kb():
    return load_knowledge_base(CONTENT_DIR)


@pytest.fixture
def rng():
    return random.Random(1234)
