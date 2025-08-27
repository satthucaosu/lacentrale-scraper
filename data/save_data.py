import os
from datetime import datetime
import json
import threading
from typing import List, Dict, Any

# Import fcntl only on Unix systems (not available on Windows)
try:
    import fcntl  # For file locking on Unix systems
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

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

def save_raw_data(car_data: Dict[str, Any], name_prefix: str = "lacentrale") -> str:
    """
    Save the raw car data to a properly formatted JSON file
    Creates/updates a JSON array format suitable for PostgreSQL insertion
    
    Args:
        car_data: Dictionary containing car information
        name_prefix: Prefix for the filename
    
    Returns:
        str: Path to the saved file
    """
    today = datetime.today().strftime("%Y-%m-%d")
    file_path = os.path.join(DATA_DIR, f"{name_prefix}_{today}.json")
    
    # Use file locking to prevent corruption in concurrent access
    file_lock = get_file_lock(file_path)
    
    with file_lock:
        try:
            # Check if file exists and load existing data
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    
                    # Ensure existing_data is a list
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data] if existing_data else []
                        
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"⚠️  Warning: Existing file {file_path} has invalid JSON format. Creating new file.")
                    print(f"   Error: {e}")
                    existing_data = []
            else:
                existing_data = []
            
            # Add new car data to the list
            existing_data.append(car_data)
            
            # Write the complete JSON array back to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved car data to {file_path} (Total cars: {len(existing_data)})")
            return file_path
            
        except Exception as e:
            print(f"❌ Error saving car data to {file_path}: {e}")
            return ""

def save_bulk_raw_data(car_data_list: List[Dict[str, Any]], name_prefix: str = "lacentrale") -> str:
    """
    Save multiple car data entries at once (more efficient for bulk operations)
    
    Args:
        car_data_list: List of car data dictionaries
        name_prefix: Prefix for the filename
    
    Returns:
        str: Path to the saved file
    """
    today = datetime.today().strftime("%Y-%m-%d")
    file_path = os.path.join(DATA_DIR, f"{name_prefix}_{today}.json")
    
    file_lock = get_file_lock(file_path)
    
    with file_lock:
        try:
            # Check if file exists and load existing data
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data] if existing_data else []
                        
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"⚠️  Warning: Existing file {file_path} has invalid JSON format. Creating new file.")
                    existing_data = []
            else:
                existing_data = []
            
            # Add all new car data to the list
            existing_data.extend(car_data_list)
            
            # Write the complete JSON array back to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(car_data_list)} cars to {file_path} (Total cars: {len(existing_data)})")
            return file_path
            
        except Exception as e:
            print(f"❌ Error saving bulk car data to {file_path}: {e}")
            return ""

def load_raw_data(file_path: str = None, name_prefix: str = "lacentrale") -> List[Dict[str, Any]]:
    """
    Load car data from JSON file
    
    Args:
        file_path: Specific file path to load (optional)
        name_prefix: Prefix to search for if file_path not provided
    
    Returns:
        List of car data dictionaries
    """
    if file_path is None:
        today = datetime.today().strftime("%Y-%m-%d")
        file_path = os.path.join(DATA_DIR, f"{name_prefix}_{today}.json")
    
    try:
        if not os.path.exists(file_path):
            print(f"⚠️  File {file_path} does not exist")
            return []
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Ensure data is a list
        if isinstance(data, list):
            print(f"✅ Loaded {len(data)} cars from {file_path}")
            return data
        else:
            print(f"✅ Loaded 1 car from {file_path} (converted to list)")
            return [data]
            
    except Exception as e:
        print(f"❌ Error loading data from {file_path}: {e}")
        return []

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

def convert_legacy_json_file(input_file: str, output_file: str = None) -> str:
    """
    Convert legacy JSON file (with concatenated objects) to proper JSON array format
    
    Args:
        input_file: Path to the legacy JSON file
        output_file: Path for the converted file (optional)
    
    Returns:
        str: Path to the converted file
    """
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_converted{ext}"
    
    try:
        car_data_list = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Handle the legacy format where JSON objects are concatenated
        if content.startswith('[') and content.endswith(']'):
            # Already in array format
            data = json.loads(content)
            car_data_list = data if isinstance(data, list) else [data]
        else:
            # Split concatenated JSON objects
            json_objects = content.split('}{')
            
            for i, json_str in enumerate(json_objects):
                # Fix the JSON format
                if i == 0 and len(json_objects) > 1:
                    json_str += '}'
                elif i == len(json_objects) - 1 and len(json_objects) > 1:
                    json_str = '{' + json_str
                elif len(json_objects) > 1:
                    json_str = '{' + json_str + '}'
                
                try:
                    car_data = json.loads(json_str)
                    if validate_car_data(car_data):
                        car_data_list.append(car_data)
                    else:
                        print(f"⚠️  Skipping invalid car data at position {i}")
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing JSON object {i}: {e}")
                    continue
        
        # Save as proper JSON array
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(car_data_list, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Converted {len(car_data_list)} cars from {input_file} to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error converting legacy JSON file: {e}")
        return ""







