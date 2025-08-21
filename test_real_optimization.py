# TODO: Consider extracting this block into a separate method
def problematic_function():
    """Function with multiple issues for testing real optimization."""
    
    # Magic number issue
    timeout_value = 300
    
    # String formatting issue
    message = "User %s has %d points" % (user_name, points)
    
    # Exception handling issue
    try:
        result = risky_operation()
    except:
        pass
    
    # Complex conditional logic
    if (user.age > 18 and user.active == True and user.premium == True and (user.country == "BR" or user.country == "US")):
        print("Complex condition met")
    
    # God method simulation (long method)
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    
    return result

def another_function():
    """Another function with issues."""
    try:
        data = fetch_data()
        process_data(data)
    except Exception:
        return None