# DatabaseManager API Reference

## Overview
The DatabaseManager class provides enterprise-grade database operations.

## Class Methods

### get_connection()
Get a database connection from the pool.

**Parameters:**
- `database_name` (str): Database name (default: "framework")

**Returns:**
- `Connection`: SQLAlchemy connection

**Raises:**
- `ConnectionError`: Connection failed
- `CircuitBreakerOpenError`: Circuit breaker open

### create_client()
Create a new client record.

**Parameters:**
- `client_data` (dict): Client information
- `validate` (bool): Enable validation (default: True)

**Returns:**
- `int`: Created client ID

**Examples:**
```python
from tempfile import NamedTemporaryFile
from streamlit_extension.utils.database import DatabaseManager

tmp = NamedTemporaryFile(delete=False)
db = DatabaseManager(tmp.name)
with db.get_connection():
    pass
```
