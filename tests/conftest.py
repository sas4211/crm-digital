"""
Shared fixtures for Exercise 1.2 prototype tests.
"""

import pytest
from src.core_loop_prototype import IncomingMessage


@pytest.fixture
def make_msg():
    """Factory fixture to create IncomingMessage quickly."""
    def _make(channel="email", body="", name="Test User", email="test@example.com", subject=""):
        return IncomingMessage(
            channel=channel,
            body=body,
            sender_name=name,
            sender_email=email,
            subject=subject or f"{channel.title()} inquiry",
        )
    return _make


@pytest.fixture
def email_msg(make_msg):
    def _make(**kwargs):
        defaults = {"channel": "email", "email": "sarah@example.com"}
        return make_msg(**{**defaults, **kwargs})
    return _make


@pytest.fixture
def whatsapp_msg(make_msg):
    def _make(**kwargs):
        defaults = {"channel": "whatsapp", "name": "", "email": "whatsapp-user@placeholder.com"}
        return make_msg(**{**defaults, **kwargs})
    return _make


@pytest.fixture
def webform_msg(make_msg):
    def _make(**kwargs):
        defaults = {"channel": "web_form", "email": "webform@example.com"}
        return make_msg(**{**defaults, **kwargs})
    return _make
