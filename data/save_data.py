import os
from datetime import datetime
import json
import threading
from typing import List, Dict, Any

# Note: fcntl import removed as it was unused. Using threading locks instead for cross-platform compatibility.

DATA_DIR = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(DATA_DIR, exist_ok=True)

# Thread lock for concurrent access
_file_locks = {}
_lock = threading.Lock()

def get_file_lock(file_path: str):
    """Get or create a lock for a specific file path"""
    with _lock:
        if file_path not in _file_locks:
            _file_locks[file_path] = threading.Lock()
        return _file_locks[file_path]

# save_raw_data function removed - was unused

# save_bulk_raw_data function removed - was unused

# load_raw_data function removed - was unused

def validate_car_data(car_data: Dict[str, Any]) -> bool:
    """
    Validate that car data has the required structure for PostgreSQL insertion
    
    Args:
        car_data: Car data dictionary
    
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = {
        'item': dict,
        'url': str
    }
    
    required_item_fields = {
        'reference': str,
        'vehicle': dict,
        'price': (int, float)
    }
    
    required_vehicle_fields = {
        'make': str,
        'model': str,
        'year': (int, float)
    }
    
    # Optional vehicle fields (may not be present in all listings)
    optional_vehicle_fields = {
        'vin': str,  # VIN not always provided by LaCentrale
        'detailedModel': str,
        'version': str,
        'trimLevel': str,
        'doors': (int, float),
        'gearbox': str,
        'motorization': str,
        'energy': str,
        'externalColor': str,
        'category': str,
        'family': str,
        'mileage': (int, float)
    }
    
    try:
        # Check top-level fields
        for field, field_type in required_fields.items():
            if field not in car_data:
                print(f"❌ Missing required field: {field}")
                return False
            if not isinstance(car_data[field], field_type):
                print(f"❌ Invalid type for field {field}: expected {field_type}, got {type(car_data[field])}")
                return False
        
        # Check item fields
        item = car_data['item']
        for field, field_type in required_item_fields.items():
            if field not in item:
                print(f"❌ Missing required item field: {field}")
                return False
            if not isinstance(item[field], field_type):
                print(f"❌ Invalid type for item.{field}: expected {field_type}, got {type(item[field])}")
                return False
        
        # Check required vehicle fields
        vehicle = item['vehicle']
        for field, field_type in required_vehicle_fields.items():
            if field not in vehicle:
                print(f"❌ Missing required vehicle field: {field}")
                return False
            if not isinstance(vehicle[field], field_type):
                print(f"❌ Invalid type for vehicle.{field}: expected {field_type}, got {type(vehicle[field])}")
                return False
        
        # Check optional vehicle fields (only validate type if present)
        for field, field_type in optional_vehicle_fields.items():
            if field in vehicle and vehicle[field] is not None:
                if not isinstance(vehicle[field], field_type):
                    print(f"⚠️  Warning: Optional vehicle field {field} has unexpected type: expected {field_type}, got {type(vehicle[field])}")
                    # Don't return False for optional fields, just warn
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating car data: {e}")
        return False

# convert_legacy_json_file function removed - was unused







