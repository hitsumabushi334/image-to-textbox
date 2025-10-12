from unittest import mock
from httpx import patch
import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from main import ImageTextboxApp
import configparser  # Assuming the main application is in main.py


@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def test_config_ini():
    test_config_ini = mock.Mock()


@pytest.fixture
def app(root):
    with patch("main.genai.Client"):
        app = ImageTextboxApp(root, test_config_ini)
        yield app
    return app
