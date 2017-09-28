"""Test Example."""
from briefy.reflex import logger
import pytest


@pytest.fixture
def context():
    """Context fixture to be used in other tests."""
    return {
        'full_name': 'Briefy Tech Team',
        'email': 'developers@briefy.co',
        'company': 'Briefy'
    }


test_data = [
    ('full_name', 'Briefy Tech Team'),
    ('email', 'developers@briefy.co'),
    ('company', 'Briefy'),
]


@pytest.mark.parametrize('key,value', test_data)
def test_key_value(context, key, value):
    """Test context values."""
    logger.info('Test')
    assert context[key] == value
