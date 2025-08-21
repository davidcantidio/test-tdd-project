#!/usr/bin/env python3
"""
Test file with intentional code smells and issues for MetaAgent optimization testing.

This file contains various problems that should be detected and fixed by the specialized agents:
- God method with mixed responsibilities
- Code duplication 
- Complex conditional logic
- Performance issues
- Missing error handling
"""

import os
import sys
import json
import time
from typing import List, Dict, Any


class TestProcessor:
    """Test class with intentional code quality issues."""
    
    def __init__(self):
        self.data = []
        self.cache = {}
        self.stats = {"processed": 0, "errors": 0}
    
    def process_data_with_everything(self, input_data: List[Dict], options: Dict = None):
        """God method that does everything - should be refactored by GodCodeRefactoringAgent."""
        
        # Input validation (responsibility 1)
        if not input_data:
            print("No input data provided")
            return None
        if not isinstance(input_data, list):
            print("Input must be a list")
            return None
        
        # Configuration setup (responsibility 2)
        if options is None:
            options = {}
        enable_cache = options.get("enable_cache", True)
        max_items = options.get("max_items", 1000)
        debug_mode = options.get("debug", False)
        
        # Data processing (responsibility 3)
        processed_items = []
        for i, item in enumerate(input_data):
            if i >= max_items:
                break
                
            # Validation for each item
            if not isinstance(item, dict):
                print(f"Item {i} is not a dictionary")
                self.stats["errors"] += 1
                continue
                
            if "id" not in item:
                print(f"Item {i} missing required 'id' field")
                self.stats["errors"] += 1
                continue
                
            # Cache checking
            item_id = item["id"]
            if enable_cache and item_id in self.cache:
                if debug_mode:
                    print(f"Using cached result for item {item_id}")
                processed_items.append(self.cache[item_id])
                continue
            
            # Complex processing logic
            processed_item = {"id": item_id}
            
            # Data transformation
            if "name" in item:
                processed_item["name"] = item["name"].strip().title()
            if "value" in item:
                try:
                    processed_item["value"] = float(item["value"])
                except (ValueError, TypeError):
                    processed_item["value"] = 0.0
                    self.stats["errors"] += 1
            
            # Business logic calculations
            if "category" in item:
                category = item["category"].lower()
                if category == "premium":
                    processed_item["priority"] = 1
                    processed_item["discount"] = 0.15
                elif category == "standard":
                    processed_item["priority"] = 2
                    processed_item["discount"] = 0.05
                elif category == "basic":
                    processed_item["priority"] = 3
                    processed_item["discount"] = 0.0
                else:
                    processed_item["priority"] = 4
                    processed_item["discount"] = 0.0
            
            # Performance calculation (inefficient N+1 pattern)
            related_items = []
            for other_item in input_data:
                if other_item.get("parent_id") == item_id:
                    related_items.append(other_item)
            processed_item["related_count"] = len(related_items)
            
            # Cache storage
            if enable_cache:
                self.cache[item_id] = processed_item
            
            processed_items.append(processed_item)
            self.stats["processed"] += 1
            
            if debug_mode:
                print(f"Processed item {item_id}: {processed_item}")
        
        # Output formatting (responsibility 4)
        result = {
            "items": processed_items,
            "total_processed": len(processed_items),
            "total_errors": self.stats["errors"],
            "cache_size": len(self.cache),
            "processing_time": time.time()
        }
        
        # Logging and cleanup (responsibility 5)
        if debug_mode:
            print(f"Processing completed: {result['total_processed']} items")
            print(f"Errors encountered: {result['total_errors']}")
        
        # Save to file for audit trail
        try:
            with open("processing_log.json", "a") as f:
                json.dump(result, f)
                f.write("\n")
        except Exception as e:
            print(f"Failed to write log: {e}")
        
        return result
    
    def duplicate_validation_logic(self, item: Dict) -> bool:
        """Duplicated validation logic - should be extracted."""
        if not isinstance(item, dict):
            return False
        if "id" not in item:
            return False
        if not item["id"]:
            return False
        return True
    
    def another_validation_method(self, data: Dict) -> bool:
        """More duplicated validation - should be consolidated."""
        if not isinstance(data, dict):
            return False
        if "id" not in data:
            return False
        if not data["id"]:
            return False
        return True
    
    def complex_conditional_method(self, user_type: str, subscription: str, usage: int):
        """Complex nested conditionals - should be simplified."""
        
        if user_type == "premium":
            if subscription == "monthly":
                if usage < 100:
                    return {"rate": 0.10, "limit": 1000}
                elif usage < 500:
                    return {"rate": 0.08, "limit": 2000}
                else:
                    return {"rate": 0.05, "limit": 5000}
            elif subscription == "yearly":
                if usage < 100:
                    return {"rate": 0.08, "limit": 1500}
                elif usage < 500:
                    return {"rate": 0.06, "limit": 3000}
                else:
                    return {"rate": 0.03, "limit": 10000}
        elif user_type == "standard":
            if subscription == "monthly":
                if usage < 100:
                    return {"rate": 0.15, "limit": 500}
                elif usage < 500:
                    return {"rate": 0.12, "limit": 1000}
                else:
                    return {"rate": 0.10, "limit": 2000}
            elif subscription == "yearly":
                if usage < 100:
                    return {"rate": 0.12, "limit": 750}
                elif usage < 500:
                    return {"rate": 0.10, "limit": 1500}
                else:
                    return {"rate": 0.08, "limit": 3000}
        else:  # basic user
            if subscription == "monthly":
                return {"rate": 0.20, "limit": 200}
            else:
                return {"rate": 0.18, "limit": 300}
    
    def method_with_no_error_handling(self, file_path: str):
        """Method without proper error handling - should be improved."""
        with open(file_path, "r") as f:
            data = json.load(f)
        
        result = data["important_field"]
        processed = result * 2 + data["another_field"]
        
        with open("output.json", "w") as f:
            json.dump({"result": processed}, f)
        
        return processed


def standalone_function_with_issues():
    """Standalone function with performance issues."""
    
    # Inefficient list operations
    items = []
    for i in range(1000):
        items.append(f"item_{i}")
    
    # Inefficient string concatenation
    result = ""
    for item in items:
        result += item + ", "
    
    # Inefficient searching
    found_items = []
    for target in ["item_100", "item_200", "item_300"]:
        for item in items:
            if item == target:
                found_items.append(item)
                break
    
    return result, found_items


if __name__ == "__main__":
    # Test code that could also be optimized
    processor = TestProcessor()
    
    test_data = [
        {"id": "1", "name": "  test item  ", "value": "123.45", "category": "premium"},
        {"id": "2", "name": "another item", "value": "invalid", "category": "standard"},
        {"id": "3", "name": "third item", "value": "67.89", "category": "basic"},
    ]
    
    result = processor.process_data_with_everything(test_data, {"debug": True})
    print(f"Processing result: {result}")
    
    # Test standalone function
    string_result, found = standalone_function_with_issues()
    print(f"Found items: {found}")