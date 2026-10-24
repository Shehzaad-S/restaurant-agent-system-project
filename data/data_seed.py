""" Python Script to setup sql tables for Pizza Restaurant """

INVENTORY_DATA = [
    {
        "ingredient_name": "Mozzarella",
        "quantity": 4.0,
        "unit": "kg",
        "reorder_threshold": 10.0,
        "days_to_expiry": 5
    },
    {
        "ingredient_name": "Tomato Sauce",
        "quantity": 8.0,
        "unit": "kg",
        "reorder_threshold": 5.0,
        "days_to_expiry": 14
    },
    {
        "ingredient_name": "Basil",
        "quantity": 1.0,
        "unit": "kg",
        "reorder_threshold": 3.0,
        "days_to_expiry": 2
    },
    {
        "ingredient_name": "Pepperoni",
        "quantity": 6.0,
        "unit": "kg",
        "reorder_threshold": 4.0,
        "days_to_expiry": 18
    },
    {
        "ingredient_name": "Mushrooms",
        "quantity": 5.0,
        "unit": "kg",
        "reorder_threshold": 3.0,
        "days_to_expiry": 3
    },
    {
        "ingredient_name": "Bell Peppers",
        "quantity": 4.0,
        "unit": "kg",
        "reorder_threshold": 3.0,
        "days_to_expiry": 5
    },
    {
        "ingredient_name": "Onions",
        "quantity": 7.0,
        "unit": "kg",
        "reorder_threshold": 3.0,
        "days_to_expiry": 21
    },
    {
        "ingredient_name": "Pizza Dough",
        "quantity": 25.0,
        "unit": "kg",
        "reorder_threshold": 10.0,
        "days_to_expiry": 7
    },
    {
        "ingredient_name": "Spaghetti",
        "quantity": 12.0,
        "unit": "kg",
        "reorder_threshold": 5.0,
        "days_to_expiry": 90
    },
    {
        "ingredient_name": "Penne",
        "quantity": 10.0,
        "unit": "kg",
        "reorder_threshold": 5.0,
        "days_to_expiry": 90
    },
    {
        "ingredient_name": "Ground Beef",
        "quantity": 6.0,
        "unit": "kg",
        "reorder_threshold": 4.0,
        "days_to_expiry": 4
    },
    {
        "ingredient_name": "Alfredo Sauce",
        "quantity": 5.0,
        "unit": "kg",
        "reorder_threshold": 3.0,
        "days_to_expiry": 6
    },
    {
        "ingredient_name": "Pesto Sauce",
        "quantity": 3.0,
        "unit": "kg",
        "reorder_threshold": 2.0,
        "days_to_expiry": 3
    },
    {
        "ingredient_name": "Parmesan",
        "quantity": 3.0,
        "unit": "kg",
        "reorder_threshold": 2.0,
        "days_to_expiry": 25
    }
]

# ========================================================================================

RECIPES_DATA = [

    # PIZZAS

    {
        "menu_item": "Margherita Pizza",
        "ingredient_name": "Pizza Dough",
        "quantity_required": 0.30
    },
    {
        "menu_item": "Margherita Pizza",
        "ingredient_name": "Tomato Sauce",
        "quantity_required": 0.12
    },
    {
        "menu_item": "Margherita Pizza",
        "ingredient_name": "Mozzarella",
        "quantity_required": 0.15
    },
    {
        "menu_item": "Margherita Pizza",
        "ingredient_name": "Basil",
        "quantity_required": 0.01
    },

    {
        "menu_item": "Pepperoni Pizza",
        "ingredient_name": "Pizza Dough",
        "quantity_required": 0.30
    },
    {
        "menu_item": "Pepperoni Pizza",
        "ingredient_name": "Tomato Sauce",
        "quantity_required": 0.12
    },
    {
        "menu_item": "Pepperoni Pizza",
        "ingredient_name": "Mozzarella",
        "quantity_required": 0.15
    },
    {
        "menu_item": "Pepperoni Pizza",
        "ingredient_name": "Pepperoni",
        "quantity_required": 0.08
    },

    {
        "menu_item": "Vegetarian Pizza",
        "ingredient_name": "Pizza Dough",
        "quantity_required": 0.30
    },
    {
        "menu_item": "Vegetarian Pizza",
        "ingredient_name": "Tomato Sauce",
        "quantity_required": 0.12
    },
    {
        "menu_item": "Vegetarian Pizza",
        "ingredient_name": "Mozzarella",
        "quantity_required": 0.15
    },
    {
        "menu_item": "Vegetarian Pizza",
        "ingredient_name": "Mushrooms",
        "quantity_required": 0.06
    },
    {
        "menu_item": "Vegetarian Pizza",
        "ingredient_name": "Bell Peppers",
        "quantity_required": 0.05
    },
    {
        "menu_item": "Vegetarian Pizza",
        "ingredient_name": "Onions",
        "quantity_required": 0.03
    },


    # PASTAS

    {
        "menu_item": "Alfredo Pasta",
        "ingredient_name": "Penne",
        "quantity_required": 0.15
    },
    {
        "menu_item": "Alfredo Pasta",
        "ingredient_name": "Alfredo Sauce",
        "quantity_required": 0.12
    },
    {
        "menu_item": "Alfredo Pasta",
        "ingredient_name": "Parmesan",
        "quantity_required": 0.03
    },

    {
        "menu_item": "Spaghetti Bolognese",
        "ingredient_name": "Spaghetti",
        "quantity_required": 0.15
    },
    {
        "menu_item": "Spaghetti Bolognese",
        "ingredient_name": "Ground Beef",
        "quantity_required": 0.12
    },
    {
        "menu_item": "Spaghetti Bolognese",
        "ingredient_name": "Tomato Sauce",
        "quantity_required": 0.10
    },
    {
        "menu_item": "Spaghetti Bolognese",
        "ingredient_name": "Parmesan",
        "quantity_required": 0.03
    },

    {
        "menu_item": "Pesto Penne",
        "ingredient_name": "Penne",
        "quantity_required": 0.15
    },
    {
        "menu_item": "Pesto Penne",
        "ingredient_name": "Pesto Sauce",
        "quantity_required": 0.10
    },
    {
        "menu_item": "Pesto Penne",
        "ingredient_name": "Parmesan",
        "quantity_required": 0.03
    }
]

# ================================================================================

VENDOR_PRICES_DATA = [

    # Mozzarella
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Mozzarella",
        "price_per_kg": 8.50,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Mozzarella",
        "price_per_kg": 7.80,
        "delivery_days": 3
    },

    # Tomato Sauce
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Tomato Sauce",
        "price_per_kg": 3.20,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Tomato Sauce",
        "price_per_kg": 2.90,
        "delivery_days": 2
    },

    # Basil
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Basil",
        "price_per_kg": 6.50,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Basil",
        "price_per_kg": 5.90,
        "delivery_days": 4
    },

    # Pepperoni
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Pepperoni",
        "price_per_kg": 9.50,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Pepperoni",
        "price_per_kg": 8.80,
        "delivery_days": 2
    },

    # Mushrooms
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Mushrooms",
        "price_per_kg": 4.50,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Mushrooms",
        "price_per_kg": 4.20,
        "delivery_days": 3
    },

    # Bell Peppers
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Bell Peppers",
        "price_per_kg": 4.80,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Bell Peppers",
        "price_per_kg": 4.40,
        "delivery_days": 2
    },

    # Onions
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Onions",
        "price_per_kg": 2.20,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Onions",
        "price_per_kg": 2.00,
        "delivery_days": 2
    },

    # Pizza Dough
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Pizza Dough",
        "price_per_kg": 3.50,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Pizza Dough",
        "price_per_kg": 3.10,
        "delivery_days": 2
    },

    # Pastas
    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Spaghetti",
        "price_per_kg": 2.60,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Spaghetti",
        "price_per_kg": 2.30,
        "delivery_days": 2
    },

    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Penne",
        "price_per_kg": 2.70,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Penne",
        "price_per_kg": 2.40,
        "delivery_days": 2
    },

    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Ground Beef",
        "price_per_kg": 10.50,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Ground Beef",
        "price_per_kg": 9.90,
        "delivery_days": 2
    },

    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Alfredo Sauce",
        "price_per_kg": 5.20,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Alfredo Sauce",
        "price_per_kg": 4.80,
        "delivery_days": 2
    },

    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Pesto Sauce",
        "price_per_kg": 6.20,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Pesto Sauce",
        "price_per_kg": 5.70,
        "delivery_days": 3
    },

    {
        "vendor_name": "Fresh Foods Wholesale",
        "ingredient_name": "Parmesan",
        "price_per_kg": 11.00,
        "delivery_days": 1
    },
    {
        "vendor_name": "Metro Restaurant Supply",
        "ingredient_name": "Parmesan",
        "price_per_kg": 10.20,
        "delivery_days": 3
    }

]

# ================================================================================

MENU_ITEMS_DATA = [
    {
        "menu_item": "Margherita Pizza",
        "active": True,
        "special": False
    },
    {
        "menu_item": "Pepperoni Pizza",
        "active": True,
        "special": False
    },
    {
        "menu_item": "Vegetarian Pizza",
        "active": True,
        "special": False
    },
    {
        "menu_item": "Alfredo Pasta",
        "active": True,
        "special": False
    },
    {
        "menu_item": "Spaghetti Bolognese",
        "active": True,
        "special": False
    },
    {
        "menu_item": "Pesto Penne",
        "active": True,
        "special": False
    }
]
