#!/usr/bin/env python3
"""
🧪 Test MetaAgent File Persistence

Test script to verify that the MetaAgent now actually applies
file modifications instead of just analyzing in memory.
"""

def god_method_example():
    """This is a god method that should trigger refactoring."""
    result = 0
    
    # Block 1: Database operations
    import sqlite3
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    # Block 2: Data processing
    for user in users:
        if user[1] == "admin":
            result += user[2] * 2
        elif user[1] == "user":
            result += user[2]
        else:
            result += user[2] / 2
    
    # Block 3: Validation logic
    if result > 1000:
        result = 1000
    elif result < 0:
        result = 0
    
    # Block 4: Logging and cleanup
    import logging
    logging.info(f"Calculated result: {result}")
    cursor.close()
    conn.close()
    
    # Block 5: More complex logic
    final_result = result
    if result > 500:
        final_result = result * 0.9
        if final_result > 800:
            final_result = 800
    elif result > 200:
        final_result = result * 1.1
        if final_result > 600:
            final_result = 600
    
    return final_result

class ExampleClass:
    """Example class with some methods."""
    
    def __init__(self):
        self.data = []
    
    def add_data(self, item):
        self.data.append(item)
    
    def process_data(self):
        return [x * 2 for x in self.data]

if __name__ == "__main__":
    example = ExampleClass()
    example.add_data(1)
    example.add_data(2)
    result = god_method_example()
    print(f"Result: {result}")