#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test Script for God Code Refactoring Agent

Tests the god code refactoring agent with various code samples
to ensure it properly detects and refactors god codes.
"""

import sys
import logging
from pathlib import Path

# Setup project path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from audit_system.agents.god_code_refactoring_agent import (
    GodCodeRefactoringAgent, 
    GodCodeType, 
    run_god_code_analysis
)

def test_god_method_detection():
    """Test detection of god methods."""
    
    print("\n🔍 Testing God Method Detection...")
    
    # Sample god method with multiple responsibilities
    sample_god_method = '''
def process_user_data(user_data, config):
    """A god method that does too many things."""
    
    # Validation responsibility
    if not user_data:
        raise ValueError("User data is required")
    if not isinstance(user_data, dict):
        raise TypeError("User data must be dictionary")
    assert 'email' in user_data, "Email is required"
        
    # Database access responsibility
    conn = database.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_data['email'],))
    existing_user = cursor.fetchone()
    
    # Business logic responsibility
    processed_data = {}
    for key, value in user_data.items():
        if key == 'email':
            processed_data[key] = value.lower().strip()
        elif key == 'age':
            processed_data[key] = int(value) if value else 18
        elif key == 'score':
            processed_data[key] = calculate_complex_score(value, config.multiplier)
        elif key == 'preferences':
            processed_data[key] = json.loads(value) if isinstance(value, str) else value
            
    # More database access
    if existing_user:
        cursor.execute("UPDATE users SET data = ? WHERE id = ?", 
                      (json.dumps(processed_data), existing_user[0]))
    else:
        cursor.execute("INSERT INTO users (email, data) VALUES (?, ?)", 
                      (processed_data['email'], json.dumps(processed_data)))
    conn.commit()
    conn.close()
    
    # Logging responsibility
    logger.info("Processed user data for: %s", processed_data.get('email'))
    logger.debug("Full processed data: %s", processed_data)
    
    # Formatting responsibility
    formatted_output = json.dumps(processed_data, indent=2, ensure_ascii=False)
    formatted_output = formatted_output.replace('\\n', '\\n  ')  # Pretty formatting
    
    # More business logic
    if processed_data.get('score', 0) > 100:
        send_notification(processed_data['email'], "High score achieved!")
        update_leaderboard(processed_data)
        
    # Caching responsibility  
    cache_key = f"user_data_{processed_data['email']}"
    redis_client.set(cache_key, formatted_output, ex=3600)
    
    # Error handling responsibility
    try:
        validate_data_integrity(processed_data)
    except ValidationError as e:
        logger.error("Data validation failed: %s", e)
        raise ValueError(f"Invalid data: {e}")
        
    return formatted_output

def calculate_complex_score(value, multiplier):
    """Helper function for score calculation."""
    return float(value) * multiplier * 1.5

def send_notification(email, message):
    """Send notification to user."""
    pass

def update_leaderboard(data):
    """Update leaderboard with user data."""
    pass

def validate_data_integrity(data):
    """Validate data integrity."""
    pass
'''
    
    agent = GodCodeRefactoringAgent(dry_run=True, aggressive_refactoring=False)
    detections = agent.analyze_god_codes("test_god_method.py", sample_god_method)
    
    if detections:
        detection = detections[0]
        print(f"✅ Detected {detection.type.value}: {detection.name}")
        print(f"   📏 Lines: {detection.total_lines}")
        print(f"   🎯 Complexity: {detection.complexity_score:.1f}")
        print(f"   📋 Responsibilities: {len(detection.responsibilities)}")
        print(f"   ⚠️  Priority: {detection.refactoring_priority}")
        print(f"   🔧 Suggested modules: {detection.suggested_separation}")
        
        # Test strategy generation
        strategy = agent.generate_refactoring_strategy(detection)
        print(f"   🚀 Strategy: {strategy.separation_approach}")
        print(f"   📦 New modules: {[m['name'] for m in strategy.new_modules]}")
        print(f"   📊 Expected improvement: {strategy.estimated_improvement}%")
        
        # Test refactoring application
        result = agent.apply_refactoring(sample_god_method, detection, strategy)
        print(f"   ✅ Refactoring success: {result.validation_passed}")
        print(f"   📁 Generated files: {list(result.refactored_modules.keys())}")
        
        return True
    else:
        print("❌ No god method detected")
        return False


def test_god_class_detection():
    """Test detection of god classes."""
    
    print("\n🔍 Testing God Class Detection...")
    
    # Sample god class with too many methods and responsibilities
    sample_god_class = '''
class UserManager:
    """A god class that handles too many responsibilities."""
    
    def __init__(self):
        self.db_connection = None
        self.cache = {}
        self.logger = logging.getLogger(__name__)
        
    # Database methods
    def connect_database(self):
        self.db_connection = database.connect()
        
    def execute_query(self, query, params):
        cursor = self.db_connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
        
    def save_user(self, user_data):
        query = "INSERT INTO users VALUES (?, ?, ?)"
        self.execute_query(query, user_data)
        
    def update_user(self, user_id, data):
        query = "UPDATE users SET data = ? WHERE id = ?"
        self.execute_query(query, (data, user_id))
        
    def delete_user(self, user_id):
        query = "DELETE FROM users WHERE id = ?"
        self.execute_query(query, (user_id,))
        
    # Business logic methods
    def validate_user_data(self, data):
        if not data.get('email'):
            raise ValueError("Email required")
        if '@' not in data['email']:
            raise ValueError("Invalid email")
            
    def calculate_user_score(self, user_data):
        score = 0
        score += len(user_data.get('name', '')) * 2
        score += user_data.get('age', 0) / 2
        return score
        
    def process_user_registration(self, data):
        self.validate_user_data(data)
        score = self.calculate_user_score(data)
        data['score'] = score
        self.save_user(data)
        
    # UI methods
    def display_user_info(self, user_id):
        user = self.get_user(user_id)
        print(f"User: {user['name']} ({user['email']})")
        
    def show_user_list(self):
        users = self.get_all_users()
        for user in users:
            print(f"{user['id']}: {user['name']}")
            
    def render_user_form(self):
        print("User Registration Form")
        print("Name: _______________")
        print("Email: _______________")
        
    # Caching methods
    def cache_user(self, user_id, data):
        self.cache[f"user_{user_id}"] = data
        
    def get_cached_user(self, user_id):
        return self.cache.get(f"user_{user_id}")
        
    def clear_user_cache(self, user_id):
        key = f"user_{user_id}"
        if key in self.cache:
            del self.cache[key]
            
    # Logging methods
    def log_user_action(self, action, user_id):
        self.logger.info(f"User {user_id}: {action}")
        
    def log_error(self, error, user_id=None):
        if user_id:
            self.logger.error(f"User {user_id} error: {error}")
        else:
            self.logger.error(f"Error: {error}")
            
    # Networking methods
    def send_welcome_email(self, user_email):
        import requests
        requests.post("http://api.email.com/send", {
            "to": user_email,
            "subject": "Welcome!"
        })
        
    def sync_with_external_api(self, user_data):
        import requests
        response = requests.post("http://api.external.com/users", 
                               json=user_data)
        return response.json()
        
    # Formatting methods
    def format_user_data(self, data):
        return json.dumps(data, indent=2)
        
    def export_users_csv(self):
        users = self.get_all_users()
        csv_lines = ["id,name,email"]
        for user in users:
            csv_lines.append(f"{user['id']},{user['name']},{user['email']}")
        return "\\n".join(csv_lines)
        
    # Helper methods
    def get_user(self, user_id):
        return self.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))[0]
        
    def get_all_users(self):
        return self.execute_query("SELECT * FROM users", ())
'''
    
    agent = GodCodeRefactoringAgent(dry_run=True, aggressive_refactoring=False)
    detections = agent.analyze_god_codes("test_god_class.py", sample_god_class)
    
    if detections:
        detection = detections[0]
        print(f"✅ Detected {detection.type.value}: {detection.name}")
        print(f"   📏 Lines: {detection.total_lines}")
        print(f"   🎯 Complexity: {detection.complexity_score:.1f}")
        print(f"   📋 Responsibilities: {len(detection.responsibilities)}")
        print(f"   ⚠️  Priority: {detection.refactoring_priority}")
        print(f"   🔧 Suggested classes: {detection.suggested_separation}")
        
        # Test strategy generation
        strategy = agent.generate_refactoring_strategy(detection)
        print(f"   🚀 Strategy: {strategy.separation_approach}")
        print(f"   📦 New classes: {[m['name'] for m in strategy.new_modules]}")
        print(f"   📊 Expected improvement: {strategy.estimated_improvement}%")
        
        return True
    else:
        print("❌ No god class detected")
        return False


def test_run_god_code_analysis_function():
    """Test the convenience function for running analysis."""
    
    print("\n🔍 Testing run_god_code_analysis function...")
    
    # Create a temporary test file
    test_file = Path("/tmp/test_god_code.py")
    
    sample_code = '''
def complex_data_processor(data, config):
    """This method does too many things - expanded version."""
    
    # Input validation - multiple checks
    if not data:
        raise ValueError("Data required")
    if not isinstance(data, list):
        raise TypeError("Data must be a list")
    if len(data) == 0:
        raise ValueError("Data cannot be empty")
    if not config:
        raise ValueError("Config required")
    assert hasattr(config, 'multiplier'), "Config must have multiplier"
    
    # Database operations - connection and setup
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS results (id INT, value FLOAT)")
    cursor.execute("DELETE FROM results WHERE created_at < ?", (datetime.now() - timedelta(days=30),))
    
    # Business logic - complex processing
    processed = {}
    failed_items = []
    total_value = 0
    
    for item in data:
        try:
            if 'id' not in item or 'value' not in item:
                failed_items.append(item)
                continue
            
            # Complex calculation with multiple conditions
            multiplier = config.multiplier
            if item.get('priority') == 'high':
                multiplier *= 2
            elif item.get('priority') == 'low':
                multiplier *= 0.5
                
            calculated_value = float(item['value']) * multiplier
            if calculated_value < 0:
                calculated_value = 0
                
            processed[item['id']] = calculated_value
            total_value += calculated_value
            
        except (ValueError, KeyError) as e:
            logger.error("Failed to process item %s: %s", item, e)
            failed_items.append(item)
    
    # Save to database - batch operations
    for key, value in processed.items():
        cursor.execute("INSERT INTO results VALUES (?, ?)", (key, value))
    
    # Update statistics
    cursor.execute("UPDATE stats SET total_processed = total_processed + ?", (len(processed),))
    cursor.execute("UPDATE stats SET total_value = total_value + ?", (total_value,))
    conn.commit()
    
    # Logging - detailed logging
    logger.info(f"Processed {len(processed)} items successfully")
    logger.info(f"Failed to process {len(failed_items)} items")
    logger.info(f"Total value calculated: {total_value}")
    
    if failed_items:
        logger.warning("Failed items: %s", failed_items)
    
    # Caching - store results
    cache_key = f"processed_data_{hash(str(data))}"
    cache.set(cache_key, processed, expire=3600)
    
    # Formatting - create formatted output
    formatted_result = {
        'processed_items': processed,
        'total_items': len(data),
        'successful_items': len(processed),
        'failed_items': len(failed_items),
        'total_value': total_value
    }
    
    formatted_output = json.dumps(formatted_result, indent=2, sort_keys=True)
    
    # Cleanup
    cursor.close()
    conn.close()
    
    return formatted_output
'''
    
    try:
        test_file.write_text(sample_code)
        
        # Run analysis with aggressive mode to catch smaller god methods
        results = run_god_code_analysis(str(test_file), aggressive=True, dry_run=True)
        
        if results.get('error'):
            print(f"❌ Analysis failed: {results['error']}")
            return False
        
        print(f"✅ Analysis completed:")
        print(f"   📁 File: {results['file_path']}")
        print(f"   🔍 Detections: {results['total_detections']}")
        print(f"   📋 Results: {len(results['detections'])}")
        
        for detection in results['detections']:
            print(f"     - {detection['type']}: {detection['name']} "
                  f"(lines: {detection['lines']}, priority: {detection['priority']})")
        
        return results['total_detections'] > 0
        
    finally:
        if test_file.exists():
            test_file.unlink()


def main():
    """Run all tests."""
    
    print("🧪 God Code Refactoring Agent - Test Suite")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_results = []
    
    # Run tests
    test_results.append(("God Method Detection", test_god_method_detection()))
    test_results.append(("God Class Detection", test_god_class_detection()))
    test_results.append(("Analysis Function", test_run_god_code_analysis_function()))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! God Code Refactoring Agent is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)