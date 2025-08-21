#!/usr/bin/env python3
"""
Example code with multiple issues for demonstrating Intelligent Code Agent.
This file intentionally contains various code smells and anti-patterns.
"""

import os
import sys

class UserManager:
    def __init__(self):
        self.users = []
        self.db_connection = None
    
    def create_user_and_send_email_and_log_and_validate(self, name, email, age, preferences, permissions, metadata):
        """God method that does way too many things - needs refactoring!"""
        # Validation logic (should be extracted)
        if not name or len(name) < 2:
            return False
        if "@" not in email:
            return False
        if age < 18 or age > 120:
            return False
        
        # Database operations (should be extracted)
        try:
            connection = self.get_db_connection()
            query = f"INSERT INTO users (name, email, age) VALUES ('{name}', '{email}', {age})"  # SQL injection vulnerability!
            connection.execute(query)
            user_id = connection.lastrowid
        except:  # Bare except - bad practice!
            return None
        
        # Email sending logic (should be extracted)
        try:
            email_body = "Welcome " + name + "! Your email is " + email  # String concatenation - inefficient!
            self.send_email(email, email_body)
        except Exception:
            pass  # Exception swallowing - terrible practice!
        
        # Logging logic (should be extracted)
        log_message = "User created: " + name + " with email " + email + " and age " + str(age)
        print(log_message)  # Should use proper logging!
        
        # Permission setup (should be extracted)
        for permission in permissions:
            try:
                self.assign_permission(user_id, permission)
            except:
                continue  # More exception swallowing!
        
        # Metadata processing (should be extracted)
        for key in metadata:
            value = metadata[key]
            try:
                query = f"INSERT INTO user_metadata (user_id, key, value) VALUES ({user_id}, '{key}', '{value}')"  # More SQL injection!
                connection.execute(query)
            except Exception:
                return False  # Even more exception swallowing!
        
        # Magic numbers everywhere!
        if len(preferences) > 10:  # Magic number!
            preferences = preferences[:10]
        
        # Complex conditional logic
        if age > 65 and "senior" in preferences and len(metadata) > 5 and "premium" in permissions and user_id > 1000:
            self.apply_senior_discount(user_id)
        
        return user_id
    
    def get_db_connection(self):
        """Another method with problems."""
        try:
            if not self.db_connection:
                password = "hardcoded_password_123"  # Hardcoded secret!
                self.db_connection = create_connection("localhost", "admin", password)
            return self.db_connection
        except:
            return None  # More exception swallowing!
    
    def send_email(self, to, body):
        """Placeholder for email sending."""
        print("Email sent to: " + to)  # String concatenation again!
    
    def assign_permission(self, user_id, permission):
        """Placeholder for permission assignment."""
        pass
    
    def apply_senior_discount(self, user_id):
        """Placeholder for senior discount."""
        pass


def create_connection(host, username, password):
    """Placeholder for database connection."""
    return None


# More problematic code
def process_users_in_loop():
    """Function that demonstrates N+1 query problem."""
    manager = UserManager()
    user_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    user_details = []
    for user_id in user_ids:
        # This creates N+1 query problem!
        try:
            connection = manager.get_db_connection()
            query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection + N+1 problem!
            result = connection.execute(query)
            user_details.append(result)
        except Exception:
            continue  # Exception swallowing in loop!
    
    return user_details


# Function with magic numbers and string concatenation
def generate_report(users, start_date, end_date):
    """Generate user report with multiple issues."""
    report = "User Report\n"
    report = report + "=" * 50 + "\n"  # String concatenation
    report = report + "Generated on: " + str(start_date) + "\n"  # More concatenation
    
    total_users = len(users)
    if total_users > 100:  # Magic number!
        report = report + "Large user base detected!\n"
    elif total_users > 50:  # Another magic number!
        report = report + "Medium user base.\n"
    elif total_users > 10:  # Yet another magic number!
        report = report + "Small user base.\n"
    
    return report


if __name__ == "__main__":
    # Main execution with problems
    manager = UserManager()
    
    # Creating users with hardcoded data
    users_data = [
        ("John", "john@email.com", 25, ["sports", "music"], ["read", "write"], {"country": "US"}),
        ("Jane", "jane@email.com", 30, ["art", "travel"], ["read"], {"country": "UK"}),
        ("Bob", "bob@email.com", 70, ["senior", "books"], ["premium", "read"], {"country": "CA", "plan": "gold"}),
    ]
    
    for name, email, age, prefs, perms, meta in users_data:
        try:
            user_id = manager.create_user_and_send_email_and_log_and_validate(name, email, age, prefs, perms, meta)
            print("Created user with ID: " + str(user_id))  # String concatenation
        except Exception:
            print("Failed to create user")  # Exception swallowing
    
    # Process users with N+1 problem
    all_users = process_users_in_loop()
    
    # Generate report
    import datetime
    report = generate_report(all_users, datetime.date.today(), datetime.date.today())
    print(report)