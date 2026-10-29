from app.parser import extract_imports


def test_basic_import():
    code = "import requests"
    assert extract_imports(code) == ["requests"]


def test_nested_import():
    code = "import os.path"
    assert extract_imports(code) == ["os"]


def test_from_import():
    code = "from urllib.parse import urlparse"
    assert extract_imports(code) == ["urllib"]


def test_multiple_imports():
    code = """
import numpy as np
from fastapi import FastAPI, Depends
"""
    imports = extract_imports(code)
    assert "numpy" in imports
    assert "fastapi" in imports
