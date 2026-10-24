"""Agent Tools for Multi Agent System"""

import sys
from pathlib import Path
import math

from sqlite3 import Cursor

from data.db_setup import get_connection
from libs.logging_config import get_logger
from libs.models import (
    SalesReport,
    InventoryAssessment,
    MenuRecommendation,
    InventoryItem,
)

# Calculate the path to the parent directory (../)
parent_dir = str(Path(__file__).resolve().parent.parent)

# Add it to the Python search path if it's not already there
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


# Inventory Operations Tools -----------


def get_recipe(
    menu_item: str,
    cursor: Cursor | None = None,
) -> list[dict[str, str | float]]:
    """
    Retrieve the ingredient requirements for a menu item.

    An existing database cursor may be supplied to allow
    the function to participate in an active transaction.

    Args:
        menu_item:
            Name of the menu item.

        cursor:
            Optional active SQLite cursor.

    Returns:
        List of ingredient records containing ingredient
        names and quantities required.
    """

    query = """
        SELECT
            ingredient_name,
            quantity_required
        FROM recipes
        WHERE menu_item = ?
    """

    if cursor is not None:
        cursor.execute(query, (menu_item,))
        rows = cursor.fetchall()

        return [
            {
                "ingredient_name": row[0],
                "quantity_required": row[1],
            }
            for row in rows
        ]

    with get_connection() as conn:
        local_cursor = conn.cursor()

        local_cursor.execute(
            query,
            (menu_item,),
        )

        rows = local_cursor.fetchall()

    return [
        {
            "ingredient_name": row[0],
            "quantity_required": row[1],
        }
        for row in rows
    ]


def update_inventory_from_sales(
    sales_report: SalesReport,
) -> list[str]:
    """
    Reduce inventory quantities based on a structured sales report.

    The function calculates ingredient consumption using recipe
    information and updates inventory levels within a single
    database transaction.

    Args:
        sales_report:
            Structured sales report.

    Returns:
        Human-readable summary of inventory updates.

    Raises:
        ValueError:
            If inventory would fall below zero.
    """

    updates: list[str] = []

    with get_connection() as conn:
        cursor = conn.cursor()

        for sale in sales_report.sales:

            recipe = get_recipe(
                sale.menu_item,
                cursor=cursor,
            )

            for ingredient in recipe:

                ingredient_name = str(
                    ingredient["ingredient_name"]
                )

                depletion_amount = (
                    float(
                        ingredient["quantity_required"]
                    )
                    * sale.quantity
                )

                cursor.execute(
                    """
                    SELECT quantity
                    FROM inventory
                    WHERE ingredient_name = ?
                    """,
                    (ingredient_name,),
                )

                result = cursor.fetchone()

                if result is None:
                    raise ValueError(
                        f"Ingredient '{ingredient_name}' "
                        f"not found in inventory."
                    )

                current_quantity = float(result[0])

                new_quantity = (
                    current_quantity
                    - depletion_amount
                )

                if new_quantity < 0:
                    raise ValueError(
                        f"Insufficient inventory for "
                        f"'{ingredient_name}'. "
                        f"Current stock: "
                        f"{current_quantity:.2f}, "
                        f"required: "
                        f"{depletion_amount:.2f}"
                    )

                cursor.execute(
                    """
                    UPDATE inventory
                    SET quantity = ?
                    WHERE ingredient_name = ?
                    """,
                    (
                        new_quantity,
                        ingredient_name,
                    ),
                )

                updates.append(
                    f"{ingredient_name} "
                    f"reduced by "
                    f"{depletion_amount:.2f}"
                )

        conn.commit()

    return updates


def get_inventory_health() -> InventoryAssessment:
    """
    Assess current inventory health.

    Evaluates inventory levels against reorder thresholds
    and identifies ingredients approaching expiry.

    Returns:
        InventoryAssessment containing low-stock items,
        expiry-risk items, and overall inventory health.
    """

    low_stock_items: list[str] = []
    expiry_risk_items: list[str] = []

    query = """
        SELECT
            ingredient_name,
            quantity,
            reorder_threshold,
            days_to_expiry
        FROM inventory
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(query)

        rows = cursor.fetchall()

    for row in rows:

        ingredient_name = row[0]
        quantity = float(row[1])
        reorder_threshold = float(row[2])
        days_to_expiry = int(row[3])

        if quantity <= reorder_threshold:
            low_stock_items.append(ingredient_name)

        if days_to_expiry <= 3:
            expiry_risk_items.append(ingredient_name)

    inventory_healthy = not (
        low_stock_items or expiry_risk_items
    )

    summary = (
        "Inventory levels are healthy."
        if inventory_healthy
        else (
            f"Detected {len(low_stock_items)} low-stock "
            f"items and {len(expiry_risk_items)} "
            f"expiry-risk items."
        )
    )

    return InventoryAssessment(
        inventory_healthy=inventory_healthy,
        low_stock_items=low_stock_items,
        expiry_risk_items=expiry_risk_items,
        summary=summary,
    )


def replenish_inventory(
    ingredient_name: str,
    quantity: float,
) -> str:
    """
    Increase inventory levels following an approved
    replenishment recommendation.

    Args:
        ingredient_name:
            Inventory item to replenish.

        quantity:
            Amount of stock to add.

    Returns:
        Human-readable update summary.

    Raises:
        ValueError:
            If the ingredient does not exist or
            quantity is invalid.
    """

    if quantity <= 0:
        raise ValueError(
            "Replenishment quantity must be greater than zero."
        )

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT quantity
            FROM inventory
            WHERE ingredient_name = ?
            """,
            (ingredient_name,),
        )

        result = cursor.fetchone()

        if result is None:
            raise ValueError(
                f"Ingredient '{ingredient_name}' "
                "not found in inventory."
            )

        current_quantity = float(result[0])

        new_quantity = current_quantity + quantity

        cursor.execute(
            """
            UPDATE inventory
            SET quantity = ?
            WHERE ingredient_name = ?
            """,
            (
                new_quantity,
                ingredient_name,
            ),
        )

        conn.commit()

    return (
        f"{ingredient_name} replenished by "
        f"{quantity:.2f}. "
        f"New quantity: {new_quantity:.2f}"
    )


def add_menu_special(
    recommendation: MenuRecommendation,
) -> str:
    """
    Add an approved menu special to the menu_items table.

    The special is assumed to have already passed:
    - Menu Strategy Agent generation
    - Operations Critic review
    - Manager approval

    Args:
        recommendation:
            Approved menu recommendation produced by the
            Menu Strategy Agent.

    Returns:
        Human-readable confirmation message.

    Raises:
        ValueError:
            If the special name is invalid or already exists.
    """

    special_name = recommendation.special_name.strip()

    if not special_name:
        raise ValueError(
            "Special name cannot be empty."
        )

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM menu_items
            WHERE menu_item = ?
            """,
            (special_name,),
        )

        existing_record = cursor.fetchone()

        if existing_record:
            raise ValueError(
                f"Menu item '{special_name}' already exists."
            )

        cursor.execute(
            """
            INSERT INTO menu_items (
                menu_item,
                active,
                special
            )
            VALUES (?, ?, ?)
            """,
            (
                special_name,
                1,  # active
                1,  # special
            ),
        )

        conn.commit()

    return (
        f"Approved special '{special_name}' "
        f"added to menu using ingredients: "
        f"{', '.join(recommendation.ingredients_used)}."
    )


# Reorder Agent Tools -----------------------------------------
def get_vendor_prices(
    ingredient_name: str,
) -> list[dict[str, str | float | int]]:
    """
    Retrieve vendor pricing information for an ingredient.

    Args:
        ingredient_name:
            Ingredient to source.

    Returns:
        Vendor pricing records.

    Raises:
        ValueError:
            If no vendor pricing is found.
    """

    query = """
        SELECT
            vendor_name,
            ingredient_name,
            price_per_kg,
            delivery_days
        FROM vendor_prices
        WHERE ingredient_name = ?
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            query,
            (ingredient_name,),
        )

        rows = cursor.fetchall()

    if not rows:
        raise ValueError(
            f"No vendor pricing found for "
            f"'{ingredient_name}'."
        )

    return [
        {
            "vendor_name": row[0],
            "ingredient_name": row[1],
            "price_per_kg": row[2],
            "delivery_days": row[3],
        }
        for row in rows
    ]


def calculate_reorder_quantity(
    current_quantity: float,
    reorder_threshold: float,
) -> float:
    """
    Calculate a recommended replenishment amount.

    Business Rule:
    Replenish inventory to twice the reorder threshold.

    Args:
        current_quantity:
            Current inventory level.

        reorder_threshold:
            Minimum stock threshold.

    Returns:
        Recommended reorder quantity.

    Raises:
        ValueError:
            If inputs are invalid.
    """

    if current_quantity < 0:
        raise ValueError(
            "Current quantity cannot be negative."
        )

    if reorder_threshold < 0:
        raise ValueError(
            "Reorder threshold cannot be negative."
        )

    target_quantity = (
        reorder_threshold * 2
    )
    # Reorder quantities must be whole kilograms.
    # Round up to ensure inventory reaches the target level.
    return max(
        math.ceil(target_quantity - current_quantity),
        0.0,
    )


def get_low_stock_inventory(
    low_stock_items: list[str],
) -> list[InventoryItem]:
    """
    Retrieve detailed inventory records for ingredients
    identified as low stock by the Inventory Operations Agent.

    Args:
        low_stock_items:
            Ingredient names extracted from an
            InventoryAssessment.

    Returns:
        List of InventoryItem records.

    Raises:
        ValueError:
            If no ingredient names are provided.
    """

    if not low_stock_items:
        raise ValueError(
            "At least one low-stock ingredient "
            "must be provided."
        )

    placeholders = ",".join(
        "?"
        for _ in low_stock_items
    )

    query = f"""
        SELECT
            ingredient_name,
            quantity,
            unit,
            reorder_threshold,
            days_to_expiry
        FROM inventory
        WHERE ingredient_name IN ({placeholders})
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            query,
            tuple(low_stock_items),
        )

        rows = cursor.fetchall()

    return [
        InventoryItem(
            ingredient_name=row[0],
            quantity=row[1],
            unit=row[2],
            reorder_threshold=row[3],
            days_to_expiry=row[4],
        )
        for row in rows
    ]

# Menu Strategy Agent Tools --------------------------


def get_expiry_risk_inventory(
    expiry_risk_items: list[str],
) -> list[InventoryItem]:
    """
    Retrieve detailed inventory records for ingredients
    identified as being at risk of expiry.

    Args:
        expiry_risk_items:
            Ingredient names extracted from an
            InventoryAssessment.

    Returns:
        List of InventoryItem records.

    Raises:
        ValueError:
            If no expiry-risk ingredient names
            are provided.
    """

    if not expiry_risk_items:
        raise ValueError(
            "At least one expiry-risk ingredient "
            "must be provided."
        )

    placeholders = ",".join(
        "?"
        for _ in expiry_risk_items
    )

    query = f"""
        SELECT
            ingredient_name,
            quantity,
            unit,
            reorder_threshold,
            days_to_expiry
        FROM inventory
        WHERE ingredient_name IN ({placeholders})
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            query,
            tuple(expiry_risk_items),
        )

        rows = cursor.fetchall()

    return [
        InventoryItem(
            ingredient_name=row[0],
            quantity=row[1],
            unit=row[2],
            reorder_threshold=row[3],
            days_to_expiry=row[4],
        )
        for row in rows
    ]
