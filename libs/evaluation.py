""""Single Agent and Worflow Testing for Agentic System"""

from data.db_setup import (
    reset_database,
    seed_all,
)

from libs.agents import (
    SalesIntakeAgent,
    InventoryOperationsAgent,
    ReorderAgent,
    MenuStrategyAgent,
    CriticAgent,
    InventoryOrchestrator,
)

from libs.models import (
    SalesReport,
    SalesItem,
    InventoryAssessment,
    CriticReview,
    ReorderRecommendation,
    MenuRecommendation,
    ManagerDecision,
)

from libs.state import (
    WorkflowState,
    WorkflowMetrics
)

from libs.token_tracker import (
    TokenTracker,
)

# We want to reset the DBs before we run each workflow test


def reset_test_environment() -> None:
    """
    Reset the database to a known state before
    workflow evaluation.
    """

    reset_database()
    seed_all()

    print(
        "Test Environment reset and seeded successfully."
    )

# Sales Intake Agent Test ------------------------


async def test_sales_intake_agent():
    """
    Test the Sales Intake Agent.

    Verifies that the agent converts
    natural-language manager sales notes
    into a structured SalesReport.
    """

    print(
        "\n=== SALES INTAKE AGENT TEST ==="
    )

    sales_text = """
    Today we sold:
    - 4 Margherita Pizzas
    - 3 Alfredo Pastas
    - 6 Spaghetti Bolognese
    """

    token_tracker = TokenTracker()

    sales_agent = SalesIntakeAgent(
        token_tracker
    )

    print(
        "\nINPUT REPORT:"
    )
    print(sales_text)

    sales_report = await (
        sales_agent.execute(
            sales_text
        )
    )

    print(
        "\nSTRUCTURED OUTPUT:"
    )
    print(sales_report)

    #
    # Assertions
    #

    assert sales_report is not None, (
        "Sales report was not generated."
    )

    assert len(sales_report.sales) == 3, (
        "Expected exactly 3 sales items."
    )

    sales_lookup = {
        item.menu_item: item.quantity
        for item in sales_report.sales
    }

    assert (
        sales_lookup["Margherita Pizza"] == 4
    ), "Incorrect Margherita Pizza quantity."

    assert (
        sales_lookup["Alfredo Pasta"] == 3
    ), "Incorrect Alfredo Pasta quantity."

    assert (
        sales_lookup["Spaghetti Bolognese"] == 6
    ), "Incorrect Spaghetti Bolognese quantity."

    print(
        "\n TEST PASSED"
    )

    return sales_report


async def test_invalid_manager_input():
    """
    Test how the Sales Intake Agent handles
    poor quality manager input.

    This evaluation is intended to observe
    agent behavior under ambiguous or invalid
    input conditions.
    """

    print(
        "\n=== INVALID MANAGER INPUT TEST ==="
    )

    sales_text = """
    Yesterday was busy.

    Sold lots of food.

    Need more cheese soon.

    Everything went well.
    """

    token_tracker = TokenTracker()

    sales_agent = SalesIntakeAgent(
        token_tracker
    )

    print(
        "\nINPUT REPORT:"
    )

    print(sales_text)

    try:

        sales_report = await (
            sales_agent.execute(
                sales_text
            )
        )

        print(
            "\nSTRUCTURED OUTPUT:"
        )

        print(sales_report)

        #
        # Observation-style assertions
        #

        if not sales_report.sales:

            print(
                "\n OBSERVATION:"
            )

            print(
                "Agent was unable to identify any "
                "structured sales information from "
                "the manager input and returned an "
                "empty SalesReport."
            )

        else:

            print(
                "\n OBSERVATION:"
            )

            print(
                "Agent successfully extracted sales "
                "records from ambiguous input."
            )

        return sales_report

    except Exception as exc:

        print(
            "\n OBSERVATION:"
        )

        print(
            "Agent rejected invalid input."
        )

        print(
            f"\nException:\n{exc}"
        )

        return None


# Inventory Operations Agent Tests -------------------


async def test_inventory_operations_agent():
    """
    Test the Inventory Operations Agent.

    Verifies that inventory is updated from sales
    data and that an inventory assessment is
    successfully produced.
    """

    print(
        "\n=== INVENTORY OPERATIONS AGENT TEST ==="
    )

    reset_test_environment()

    sales_report = SalesReport(
        sales=[
            SalesItem(
                menu_item="Margherita Pizza",
                quantity=4,
            ),
            SalesItem(
                menu_item="Alfredo Pasta",
                quantity=3,
            ),
            SalesItem(
                menu_item="Spaghetti Bolognese",
                quantity=6,
            ),
        ]
    )

    state = WorkflowState(
        sales_report=sales_report,
    )

    token_tracker = TokenTracker()

    inventory_agent = (
        InventoryOperationsAgent(
            token_tracker
        )
    )

    print(
        "\nINPUT SALES REPORT:"
    )

    print(sales_report)

    assessment = await (
        inventory_agent.execute(
            state
        )
    )

    print(
        "\nINVENTORY ASSESSMENT:"
    )

    print(assessment)

    #
    # Assertions
    #

    assert assessment is not None, (
        "Inventory assessment was not generated."
    )

    assert (
        hasattr(
            assessment,
            "inventory_healthy"
        )
    ), (
        "Inventory health flag missing."
    )

    assert (
        hasattr(
            assessment,
            "low_stock_items"
        )
    ), (
        "Low stock items missing."
    )

    assert (
        hasattr(
            assessment,
            "expiry_risk_items"
        )
    ), (
        "Expiry risk items missing."
    )

    #
    # We expect our seeded dataset and sales
    # activity to create inventory issues.
    #
    assert (
        len(
            assessment.low_stock_items
        ) > 0
    ), (
        "Expected at least one low-stock item."
    )

    assert (
        len(
            assessment.expiry_risk_items
        ) > 0
    ), (
        "Expected at least one expiry-risk item."
    )

    print(
        "\n TEST PASSED"
    )

    return assessment

# Reorder Agent Test ---------------


async def test_reorder_agent():
    """
    Test the Reorder Agent.

    Verifies that the agent generates
    replenishment recommendations for
    low-stock inventory items.
    """

    print(
        "\n=== REORDER AGENT TEST ==="
    )

    assessment = InventoryAssessment(
        inventory_healthy=False,
        low_stock_items=[
            "Basil",
            "Mozzarella",
            "Pesto Sauce",
        ],
        expiry_risk_items=[],
        summary=(
            "Several ingredients are below "
            "their reorder thresholds."
        ),
    )

    state = WorkflowState(
        inventory_assessment=assessment,
    )

    token_tracker = TokenTracker()

    reorder_agent = ReorderAgent(
        token_tracker
    )

    print(
        "\nINPUT INVENTORY ASSESSMENT:"
    )

    print(assessment)

    recommendations = await (
        reorder_agent.execute(
            state
        )
    )

    print(
        "\nREORDER RECOMMENDATIONS:"
    )

    for recommendation in recommendations:

        print(
            f"""
            Ingredient    : {recommendation.ingredient_name}
            Quantity      : {recommendation.reorder_quantity} kg
            Vendor        : {recommendation.recommended_vendor}
            Total Cost    : ${recommendation.total_cost:.2f}

            Justification:
            {recommendation.justification}
            """
        )

    #
    # Assertions
    #

    assert recommendations, (
        "Expected reorder recommendations."
    )

    assert (
        len(recommendations) == 3
    ), (
        "Expected three reorder recommendations."
    )

    for recommendation in recommendations:

        assert (
            recommendation.ingredient_name
        ), (
            "Ingredient name is missing."
        )

        assert (
            recommendation.recommended_vendor
        ), (
            "Recommended vendor is missing."
        )

        assert (
            recommendation.reorder_quantity > 0
        ), (
            "Reorder quantity must be greater than zero."
        )

        assert (
            recommendation.total_cost > 0
        ), (
            "Total cost must be greater than zero."
        )

        assert (
            recommendation.justification
        ), (
            "Justification is missing."
        )

    print(
        "\n TEST PASSED"
    )

    return recommendations


async def test_menu_strategy_agent():
    """
    Test the Menu Strategy Agent.

    Verifies that the agent generates a
    menu special using ingredients that
    are approaching expiry.
    """

    print(
        "\n=== MENU STRATEGY AGENT TEST ==="
    )

    assessment = InventoryAssessment(
        inventory_healthy=False,
        low_stock_items=[],
        expiry_risk_items=[
            "Basil",
            "Mushrooms",
            "Pesto Sauce",
        ],
        summary=(
            "Several ingredients are approaching "
            "their expiry dates."
        ),
    )

    state = WorkflowState(
        inventory_assessment=assessment,
    )

    token_tracker = TokenTracker()

    menu_agent = MenuStrategyAgent(
        token_tracker
    )

    print(
        "\nINPUT INVENTORY ASSESSMENT:"
    )

    print(assessment)

    recommendation = await (
        menu_agent.execute(
            state
        )
    )

    print(
        "\nMENU RECOMMENDATION:"
    )

    print(
        f"""
        Special Name:
        {recommendation.special_name}

        Ingredients Used:
        {", ".join(recommendation.ingredients_used)}

        Reasoning:
        {recommendation.reasoning}
        """
    )

    #
    # Assertions
    #

    assert recommendation is not None, (
        "Expected a menu recommendation."
    )

    assert (
        recommendation.special_name
    ), (
        "Special name is missing."
    )

    assert (
        recommendation.ingredients_used
    ), (
        "Expected ingredients to be used."
    )

    assert (
        len(
            recommendation.ingredients_used
        ) > 0
    ), (
        "Ingredients list is empty."
    )

    assert (
        recommendation.reasoning
    ), (
        "Reasoning is missing."
    )

    print(
        "\n TEST PASSED"
    )

    return recommendation

# Critic Agent Test ---------------------------------


async def test_critic_agent():
    """
    Test the Critic Agent.

    Verifies that the agent can evaluate
    reorder and menu recommendations and
    provide an approval decision with
    supporting feedback.
    """

    print(
        "\n=== CRITIC AGENT TEST ==="
    )

    state = WorkflowState(
        inventory_assessment=InventoryAssessment(
            inventory_healthy=False,
            low_stock_items=[
                "Basil",
                "Mozzarella",
                "Pesto Sauce",
            ],
            expiry_risk_items=[
                "Basil",
                "Mushrooms",
                "Pesto Sauce",
            ],
            summary=(
                "Several inventory items require "
                "replenishment and expiry mitigation."
            ),
        ),
        reorder_recommendations=[
            ReorderRecommendation(
                ingredient_name="Basil",
                reorder_quantity=6.0,
                recommended_vendor="Fresh Foods Wholesale",
                total_cost=32.83,
                justification=(
                    "Current stock is critically below "
                    "reorder threshold."
                ),
            ),
            ReorderRecommendation(
                ingredient_name="Mozzarella",
                reorder_quantity=19.0,
                recommended_vendor="Fresh Foods Wholesale",
                total_cost=155.13,
                justification=(
                    "Current stock is critically low and "
                    "requires rapid replenishment."
                ),
            ),
        ],
        menu_recommendations=[
            MenuRecommendation(
                special_name=(
                    "Rustic Pesto Mushroom "
                    "& Fresh Basil Special"
                ),
                ingredients_used=[
                    "Basil",
                    "Mushrooms",
                    "Pesto Sauce",
                ],
                reasoning=(
                    "Uses multiple ingredients nearing "
                    "expiry and reduces waste."
                ),
            )
        ],
    )

    token_tracker = TokenTracker()

    critic_agent = CriticAgent(
        token_tracker
    )

    print(
        "\nINPUT RECOMMENDATIONS:"
    )

    print(state.reorder_recommendations)
    print(state.menu_recommendations)

    review = await (
        critic_agent.execute(
            state
        )
    )

    print(
        "\nCRITIC REVIEW:"
    )

    print(review)

    #
    # Assertions
    #

    assert review is not None, (
        "Expected a critic review."
    )

    assert isinstance(
        review.approved,
        bool,
    ), (
        "Approval decision must be boolean."
    )

    assert (
        review.feedback
    ), (
        "Feedback is missing."
    )

    assert (
        review.confidence_score >= 0
    ), (
        "Confidence score must be valid."
    )

    assert (
        review.confidence_score <= 1
    ), (
        "Confidence score must not exceed 1."
    )

    print(
        "\n TEST PASSED"
    )

    return review

# Full Workflow Test-------------------------------------
# Avoid user input here


def auto_approve() -> ManagerDecision:
    """
    Automatically approve recommendations.
    """

    return ManagerDecision(
        approved=True,
        feedback="Auto-approved for testing.",
    )


class RejectThenApprove:
    """
    Reject the first approval request and
    approve the second to validate workflow
    retry behavior.
    """

    def __init__(self):
        self.calls = 0

    def __call__(
        self,
    ) -> ManagerDecision:

        self.calls += 1

        if self.calls == 1:

            return ManagerDecision(
                approved=False,
                feedback=(
                    "Automatically rejected "
                    "for testing."
                ),
            )

        return ManagerDecision(
            approved=True,
            feedback=(
                "Automatically approved "
                "for testing."
            ),
        )


async def test_full_workflow_approved():
    """
    Test complete workflow execution using
    automatic manager approval.
    """

    print(
        "\n=== FULL WORKFLOW TEST (APPROVED) ==="
    )

    reset_test_environment()

    token_tracker = TokenTracker()

    sales_text = """
    Today we sold:
    - 4 Margherita Pizzas
    - 3 Alfredo Pastas
    - 6 Spaghetti Bolognese
    """

    sales_agent = SalesIntakeAgent(
        token_tracker
    )

    orchestrator = (
        InventoryOrchestrator(
            token_tracker,
            approval_function=auto_approve,
        )
    )

    sales_report = await (
        sales_agent.execute(
            sales_text
        )
    )

    state = WorkflowState(
        sales_report=sales_report,
    )

    response = await (
        orchestrator.run(
            state
        )
    )

    print(
        "\nWORKFLOW RESPONSE:"
    )

    print(response)

    #
    # Assertions
    #

    assert (
        response.status
        == "completed"
    ), (
        "Workflow did not complete."
    )

    assert (
        response.manager_decision
        is not None
    ), (
        "Manager decision missing."
    )

    assert (
        response.manager_decision.approved
        is True
    ), (
        "Expected approval."
    )

    assert (
        len(response.final_actions) > 0
    ), (
        "Expected executed actions."
    )

    assert (
        len(
            response.reorder_recommendations
        ) > 0
    ), (
        "Expected reorder recommendations."
    )

    print(
        "\n TEST PASSED"
    )

    return response


async def test_workflow_retry_path():
    """
    Test workflow retry behavior.

    Verifies that manager rejection
    triggers a workflow retry and
    eventually completes successfully.
    """

    print(
        "\n=== WORKFLOW RETRY TEST ==="
    )

    reset_test_environment()

    token_tracker = TokenTracker()

    sales_text = """
    Today we sold:
    - 4 Margherita Pizzas
    - 3 Alfredo Pastas
    - 6 Spaghetti Bolognese
    """

    sales_agent = SalesIntakeAgent(
        token_tracker
    )

    approval_strategy = (
        RejectThenApprove()
    )

    orchestrator = (
        InventoryOrchestrator(
            token_tracker,
            approval_function=approval_strategy,
        )
    )

    sales_report = await (
        sales_agent.execute(
            sales_text
        )
    )

    state = WorkflowState(
        sales_report=sales_report,
    )

    response = await (
        orchestrator.run(
            state
        )
    )

    print(
        "\nWORKFLOW RESPONSE:"
    )

    print(response)

    #
    # Assertions
    #

    assert (
        approval_strategy.calls == 2
    ), (
        "Expected one rejection and one approval."
    )

    assert (
        response.status
        == "completed"
    ), (
        "Workflow should complete after retry."
    )

    assert (
        response.manager_decision
        is not None
    ), (
        "Manager decision missing."
    )

    assert (
        response.manager_decision.approved
        is True
    ), (
        "Expected final approval."
    )

    assert (
        len(response.final_actions)
        > 0
    ), (
        "Expected executed actions."
    )

    print(
        "\n TEST PASSED"
    )

    return response

# Observational test, if sales input is empty


async def test_workflow_with_empty_sales_report():
    """
    Observe workflow behavior when the
    Sales Intake Agent produces an empty
    SalesReport due to ambiguous manager input.

    This is an evaluation/observation test,
    not a pass/fail test.
    """

    print(
        "\n=== EMPTY SALES REPORT WORKFLOW TEST ==="
    )

    reset_test_environment()

    token_tracker = TokenTracker()

    sales_report = SalesReport(
        sales=[]
    )

    state = WorkflowState(
        sales_report=sales_report,
    )

    orchestrator = (
        InventoryOrchestrator(
            token_tracker,
            approval_function=auto_approve,
        )
    )

    print(
        "\nINPUT SALES REPORT:"
    )

    print(sales_report)

    try:

        response = await (
            orchestrator.run(
                state
            )
        )

        print(
            "\nWORKFLOW RESPONSE:"
        )

        print(response)

        print(
            "\n OBSERVATION:"
        )

        if response.inventory_healthy:

            print(
                "Workflow completed with a healthy "
                "inventory assessment despite no "
                "sales information being provided."
            )

        elif response.reorder_recommendations:

            print(
                "Workflow continued and generated "
                "recommendations even though no "
                "sales activity was recorded."
            )

        else:

            print(
                "Workflow completed without making "
                "significant recommendations."
            )

        return response

    except Exception as exc:

        print(
            "\n OBSERVATION:"
        )

        print(
            "Workflow failed when provided an "
            "empty SalesReport."
        )

        print(
            f"\nException:\n{exc}"
        )

        return None
