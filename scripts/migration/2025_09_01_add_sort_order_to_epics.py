#!/usr/bin/env python3
"""
Migration: add sort_order to framework_epics
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("framework.db")

def run():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("ALTER TABLE framework_epics ADD COLUMN sort_order INTEGER DEFAULT 0")
        conn.commit()
        print("✅ sort_order column added to framework_epics")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ sort_order already exists, skipping")
        else:
            raise
    finally:
        conn.close()

if __name__ == "__main__":
    run()
