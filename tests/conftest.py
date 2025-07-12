import pytest
from app import app
from app.pump_repository import clear_pump_repository

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database state"""
    clear_pump_repository()
    yield 