def very_long_function():
    # Esta função é muito longa e poderia ser dividida
    x = 1
    y = 2
    z = x + y
    result = z * 2
    if result > 5:
        print("Result is greater than 5")
    else:
        print("Result is not greater than 5")
    return result

def another_long_function():
    # Outra função longa
    data = [1, 2, 3, 4, 5]
    processed = []
    for item in data:
        if item % 2 == 0:
            processed.append(item * 2)
        else:
            processed.append(item + 1)
    return processed

if __name__ == "__main__":
    print("Testing backup functionality")
