import pytest
from app.parser import extract_imports


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

    assert "line 4" in str(exc_info.value) or "line" in str(exc_info.value).lower()
