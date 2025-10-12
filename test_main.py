from httpx import patch
import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from main import ImageTextboxApp
from test_config import test_config_ini  # Assuming the main application is in main.py


@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def app(root):
    with patch("main.genai.Client"):
        app = ImageTextboxApp(root, test_config_ini)
        yield app
    return app
