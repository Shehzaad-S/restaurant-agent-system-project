"""Human in the Loop manager utility function with"""


from dataclasses import dataclass
import random

SAMPLE_MANAGER_REPORTS = [
    """
    Today we sold:
    - 4 Margherita Pizzas
    - 3 Alfredo Pastas
    - 6 Spaghetti Bolognese
    """,

    """
    Busy lunch service.

    Sold:
    - 5 Margherita Pizzas
    - 10 Pesto Penne
    - 10 Vegetarian Pizzas
    """,

    """
    Slow rainy day.

    Sold:
    - 4 Vegetarian Pizzas
    - 2 Alfredo Pastas
    - 1 Spaghetti Bolognese
    """
]


@dataclass
class ManagerDecision:
    """
    Human approval decision captured during the
    manager review stage.
    """

    approved: bool
    feedback: str


def get_sample_manager_report() -> str:
    """Picks our a simluted Manger Input at random"""

    return random.choice(
        SAMPLE_MANAGER_REPORTS
    )


def get_manager_approval() -> ManagerDecision:
    """
    Request manager approval for generated
    recommendations.

    Returns:
        ManagerDecision containing the approval
        status and optional feedback.
    """

    while True:

        response = input(
            "\nApprove recommendations? (y/n): "
        ).strip().lower()

        if response in {"y", "yes"}:

            return ManagerDecision(
                approved=True,
                feedback="Approved by manager."
            )

        if response in {"n", "no"}:

            feedback = input(
                "\nPlease provide feedback for "
                "the recommendation team:\n"
            ).strip()

            if not feedback:
                feedback = (
                    "Manager rejected recommendations."
                )

            return ManagerDecision(
                approved=False,
                feedback=feedback,
            )

        print(
            "Invalid input. Please enter "
            "'y' or 'n'."
        )
