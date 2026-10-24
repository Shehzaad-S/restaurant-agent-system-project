"""Script to Populate SQLite database"""
import sqlite3
from pathlib import Path

# Import seeded data
# Very important to use parmaterized queries.

from data.data_seed import (INVENTORY_DATA, RECIPES_DATA,
                            VENDOR_PRICES_DATA, MENU_ITEMS_DATA)

BASE_DIR = Path(__file__).resolve().parent

DB_NAME = "restaurant.db"
DB_PATH = BASE_DIR / DB_NAME


def get_connection():
    """Create and return a SQLite connection."""
    return sqlite3.connect(DB_PATH)


CREATE_TABLES = {

    "inventory": """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_name TEXT UNIQUE NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            reorder_threshold REAL NOT NULL,
            days_to_expiry INTEGER NOT NULL
        );
    """,

    "recipes": """
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_item TEXT NOT NULL,
            ingredient_name TEXT NOT NULL,
            quantity_required REAL NOT NULL
        );
    """,

    "vendor_prices": """
        CREATE TABLE IF NOT EXISTS vendor_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT NOT NULL,
            ingredient_name TEXT NOT NULL,
            price_per_kg REAL NOT NULL,
            delivery_days INTEGER NOT NULL
        );
    """,

    "menu_items": """
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_item TEXT NOT NULL,
            active INTEGER NOT NULL,
            special INTEGER NOT NULL
        );
    """,

    "workflow_runs": """
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT,
            final_status TEXT
        ); 
    """
}

TABLES = ["inventory", "recipes", "vendor_prices",
          "menu_items", "workflow_runs"]


def create_tables():
    """Create all database tables safely using context managers."""

    with get_connection() as conn:
        cursor = conn.cursor()

        for table_name, create_sql in CREATE_TABLES.items():
            cursor.execute(create_sql)
            print(f">>> Created table: {table_name}")

    print(">>>> All tables created successfully.")


def drop_tables():
    """Drop all existing tables safely using context managers."""

    # The 'with' block ensures the connection is closed even if an execution fails
    with get_connection() as conn:
        cursor = conn.cursor()

        for table in TABLES:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f">>> Dropped table: {table}")

    print(">>>> Database cleaned.")


def reset_database():
    """Reset and recreate all database tables."""

    drop_tables()
    create_tables()

    print(">>>> Database reset complete.")


# Seeding the Tables

def seed_inventory():
    """Populate inventory table."""

    query = """
        INSERT INTO inventory (
            ingredient_name,
            quantity,
            unit,
            reorder_threshold,
            days_to_expiry
        )
        VALUES (?, ?, ?, ?, ?)
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        for item in INVENTORY_DATA:
            cursor.execute(
                query,
                (
                    item["ingredient_name"],
                    item["quantity"],
                    item["unit"],
                    item["reorder_threshold"],
                    item["days_to_expiry"]
                )
            )

    print(f"<<<< Seeded {len(INVENTORY_DATA)} inventory records.")


def seed_recipes():
    """Populate recipes table."""

    query = """
        INSERT INTO recipes (
            menu_item,
            ingredient_name,
            quantity_required
        )
        VALUES (?, ?, ?)
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        for recipe in RECIPES_DATA:
            cursor.execute(
                query,
                (
                    recipe["menu_item"],
                    recipe["ingredient_name"],
                    recipe["quantity_required"]
                )
            )

    print(f"<<<< Seeded {len(RECIPES_DATA)} recipe records.")


def seed_vendor_prices():
    """Populate vendor pricing table."""

    query = """
        INSERT INTO vendor_prices (
            vendor_name,
            ingredient_name,
            price_per_kg,
            delivery_days
        )
        VALUES (?, ?, ?, ?)
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        for record in VENDOR_PRICES_DATA:
            cursor.execute(
                query,
                (
                    record["vendor_name"],
                    record["ingredient_name"],
                    record["price_per_kg"],
                    record["delivery_days"]
                )
            )

    print(f"<<<< Seeded {len(VENDOR_PRICES_DATA)} vendor pricing records.")


def seed_menu_items():
    """Populate menu items table."""

    query = """
        INSERT INTO menu_items (
            menu_item,
            active,
            special
        )
        VALUES (?, ?, ?)
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        for item in MENU_ITEMS_DATA:
            cursor.execute(
                query,
                (
                    item["menu_item"],
                    int(item["active"]),
                    int(item["special"])
                )
            )

    print(f"<<<< Seeded {len(MENU_ITEMS_DATA)} menu items.")


def seed_all():
    """Populate all tables with seed data."""

    seed_inventory()
    seed_recipes()
    seed_vendor_prices()
    seed_menu_items()

    print(">>>>> <<<<<< Database successfully seeded.")


def verify_seeding():
    """Print row counts for all tables."""

    print("\n <<< Verifying Database Seed Counts >>>")

    with get_connection() as conn:
        cursor = conn.cursor()

        for table in TABLES:
            query = f"SELECT COUNT(*) FROM {table}"
            cursor.execute(query)

            count = cursor.fetchone()[0]

            print(f"Table '{table:<15}': {count} rows")

    print("--------------------------------------\n")


def inspect_table(table_name: str, limit: int = 5):
    """Preview sample data from a table."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT * FROM {table_name} LIMIT {limit}"
        )

        rows = cursor.fetchall()

    print(f"\n--- {table_name.upper()} ---")
    for row in rows:
        print(row)


if __name__ == "__main__":
    # always reset to avoid duplication (otherwise we can use the UNIQUE keword here)
    reset_database()
    seed_all()
    verify_seeding()
    # inspect_table("inventory")
