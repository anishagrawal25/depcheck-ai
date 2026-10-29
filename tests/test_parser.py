import pytest
from app.parser import extract_imports, to_pypi_name, parse_requirements, IMPORT_TO_PYPI


def test_basic_import():
    code = "import requests"
    assert extract_imports(code) == ["requests"]


def test_nested_import():
    code = "import pydantic.v1"
    assert extract_imports(code) == ["pydantic"]


def test_stdlib_filtered():
    code = """
import os
import sys
from urllib.parse import urlparse
import json
import requests
"""
    assert extract_imports(code) == ["requests"]


def test_relative_imports_filtered():
    code = """
from . import sibling
from ..parent import helper
from ...core.utils import clean
import requests
"""
    assert extract_imports(code) == ["requests"]


def test_deduped_and_sorted():
    code = """
import requests
from requests import get
import boto3
import aiohttp
from boto3.session import Session
"""
    assert extract_imports(code) == ["aiohttp", "boto3", "requests"]


def test_syntax_error_raises_value_error():
    broken_code = """
import requests
def bad_function(
    return 123
"""
    with pytest.raises(ValueError) as exc_info:
        extract_imports(broken_code)

    assert "line" in str(exc_info.value).lower()


def test_to_pypi_name_mappings():
    assert to_pypi_name("cv2") == "opencv-python"
    assert to_pypi_name("PIL") == "Pillow"
    assert to_pypi_name("sklearn") == "scikit-learn"
    assert to_pypi_name("yaml") == "PyYAML"
    assert to_pypi_name("bs4") == "beautifulsoup4"
    assert to_pypi_name("dotenv") == "python-dotenv"
    assert to_pypi_name("requests") == "requests"
    assert to_pypi_name("fastapi") == "fastapi"


def test_imports_inside_functions():
    code = """
def load_data():
    import pandas as pd
    return pd.DataFrame()

async def fetch():
    from httpx import AsyncClient
    return AsyncClient()
"""
    assert extract_imports(code) == ["httpx", "pandas"]


def test_imports_inside_try_except():
    code = """
try:
    import orjson as json
except ImportError:
    import simplejson as json
finally:
    import structlog
"""
    assert extract_imports(code) == ["orjson", "simplejson", "structlog"]


def test_imports_inside_if_blocks():
    code = """
import sys

if sys.platform == "win32":
    import win32api
elif sys.platform == "darwin":
    from appscript import app
else:
    import pyinotify
"""
    assert extract_imports(code) == ["appscript", "pyinotify", "win32api"]


def test_parse_requirements_standard():
    reqs = """
# Core requirements
requests==2.31.0
fastapi>=0.100.0, <1.0.0
pydantic~=2.0
uvicorn # ASGI server

-r base.txt
--extra-index-url https://custom.pypi.org/simple
celery[redis,auth]>=5.2.0
pytest
"""
    parsed = parse_requirements(reqs)
    assert parsed == ["celery", "fastapi", "pydantic", "pytest", "requests", "uvicorn"]


def test_parse_requirements_empty_and_comments():
    reqs = """
# Just comments
# Another comment
"""
    assert parse_requirements(reqs) == []
