# -*- coding: utf-8 -*-
"""
Unit tests for database functionality

@author: dduong
"""

import pytest
import os
from unittest.mock import Mock, patch
from database.db_utils import DatabaseManager
from database.schema import Base

# Test database URL (will be overridden by CI)
TEST_DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:test@localhost:5432/test_db")

@pytest.fixture
def db_manager():
    """Create a test database manager"""
    return DatabaseManager(TEST_DB_URL, "normalized")

def test_database_manager_init(db_manager):
    """Test DatabaseManager initialization"""
    assert db_manager.approach == "normalized"
    assert db_manager.engine is not None

def test_database_manager_invalid_approach():
    """Test DatabaseManager with invalid approach"""
    with pytest.raises(ValueError):
        DatabaseManager(TEST_DB_URL, "invalid_approach")

def test_validate_car_data():
    """Test car data validation"""
    from data.save_data import validate_car_data
    
    # Valid car data
    valid_data = {
        "item": {
            "reference": "E123456789",
            "price": 15000,
            "mileage": 50000,
            "year": 2020,
            "vehicle": {
                "make": "PEUGEOT",
                "model": "308"
            },
            "dealer": {
                "customerReference": "D123"
            }
        },
        "url": "https://example.com/car"
    }
    
    assert validate_car_data(valid_data) == True
    
    # Invalid car data (missing required field)
    invalid_data = {
        "item": {
            "reference": "E123456789",
            "price": 15000
            # Missing mileage, year, vehicle, dealer
        },
        "url": "https://example.com/car"
    }
    
    assert validate_car_data(invalid_data) == False
