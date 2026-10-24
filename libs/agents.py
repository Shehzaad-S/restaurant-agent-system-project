"""
Agents we will use for our agentic system

"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any, Literal

from libs.logging_config import get_logger
from libs.state import WorkflowState
from libs.token_tracker import TokenTracker
from libs.state_machine import (
    EntryPoint,
    StateMachine,
    Step,
    Termination
)

from libs.models import (
    InventoryAssessment,
    MenuRecommendation,
    ReorderRecommendation,
    InventoryItem,
    CriticReview,
    OrchestratorResponse,
    SalesReport,
)
from libs.llm import create_agent

from libs.state import WorkflowState
from libs.token_tracker import TokenTracker

from libs.tools import (
    update_inventory_from_sales,
    get_inventory_health,
    replenish_inventory,
    add_menu_special,
    get_low_stock_inventory,
    get_vendor_prices,
    calculate_reorder_quantity,
    get_expiry_risk_inventory,
)
from libs.manager_input import get_manager_approval

logger = get_logger(__name__)

T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    """
    Base class for workflow agents.

    Provides:
    - Logging
    - Timing
    - Token tracking
    """

    def __init__(
        self,
        agent_name: str,
        token_tracker: TokenTracker,
    ) -> None:

        self.agent_name = agent_name
        self.token_tracker = token_tracker

        self.logger = get_logger(agent_name)

    def before_run(
        self,
        state: WorkflowState,
    ) -> float:
        """
        Execute before agent logic.
        """

        self.logger.info(
            f"Starting agent: {self.agent_name}"
        )
        if self.agent_name not in state.metrics.agents_invoked:
            state.metrics.agents_invoked.append(
                self.agent_name
            )

        return time.perf_counter()

    def after_run(
        self,
        state: WorkflowState,
        start_time: float,
    ) -> None:
        """
        Execute after agent logic.
        """

        elapsed = (
            time.perf_counter() - start_time
        )

        state.metrics.execution_time_seconds += elapsed

        self.logger.info(
            f"Completed agent: {self.agent_name} "
            f"in {elapsed:.2f}s"
        )

    def update_token_usage(
        self,
        state: WorkflowState,
        usage: Any,
    ) -> None:
        """
        Update workflow token usage from a
        PydanticAI RunUsage object.
        """

        self.token_tracker.update_from_run_usage(usage)

        state.metrics.token_usage = (
            self.token_tracker.usage
        )

    def log_metrics(self) -> None:
        """
        Log current token metrics.
        """

        self.logger.info(
            self.token_tracker.summary()
        )

    @abstractmethod
    async def execute(
        self,
        state: WorkflowState,
    ) -> T:
        """
        Execute agent-specific business logic.

        Args:
            state: Current workflow state.

        Returns:
            Agent-specific result.
        """
        raise NotImplementedError

# For the Inventory Ops Agent we keep the LLM out of Inventory Management and Make it more deterministic


class InventoryOperationsAgent(
    BaseAgent[InventoryAssessment]
):
    """
    Handles inventory-related operations,
    inventory updates, and inventory health
    assessments.
    """

    def __init__(
        self,
        token_tracker: TokenTracker,
    ) -> None:

        super().__init__(
            agent_name="InventoryOperationsAgent",
            token_tracker=token_tracker,
        )

    async def execute(
        self,
        state: WorkflowState,
    ) -> InventoryAssessment:
        """
        Update inventory from sales and assess
        overall inventory health.

        Args:
            state:
                Current workflow state.

        Returns:
            InventoryAssessment containing
            low-stock and expiry-risk findings.

        Raises:
            ValueError:
                If a sales report is not available.
        """

        start_time = self.before_run(state)

        try:

            if state.sales_report is None:
                raise ValueError(
                    "A sales report is required before "
                    "inventory operations can execute."
                )

            inventory_updates = (
                update_inventory_from_sales(
                    state.sales_report
                )
            )

            assessment = get_inventory_health()

            self.logger.info(
                f"Applied {len(inventory_updates)} "
                "inventory updates."
            )

            return assessment

        finally:
            self.after_run(
                state=state,
                start_time=start_time,
            )

    async def replenish(
        self,
        ingredient_name: str,
        quantity: float,
    ) -> str:
        """
        Apply an approved inventory replenishment.
        """

        return replenish_inventory(
            ingredient_name=ingredient_name,
            quantity=quantity,
        )

    async def add_special(
        self,
        recommendation: MenuRecommendation,
    ) -> str:
        """
        Add an approved menu special.
        """

        return add_menu_special(
            recommendation=recommendation,
        )

# Reorder Agent


class ReorderAgent(
    BaseAgent[list[ReorderRecommendation]]
):
    """
    Uses inventory and vendor information to produce
    structured reorder recommendations.
    """

    SYSTEM_PROMPT = """
    You are a italian restaurant procurement specialist.

    Your responsibility is to recommend the most
    appropriate vendor for inventory replenishment.

    Consider:
    - Current stock levels
    - Reorder quantities
    - Vendor pricing
    - Vendor delivery times

    Prefer lower-cost vendors unless inventory levels
    indicate urgent replenishment is required.

    Always provide a concise business justification.
    Example decision:

    Ingredient: Mozzarella
    Current Quantity: 4kg
    Reorder Threshold: 10kg

    Vendor A:
    - $8.50/kg
    - 1 day delivery

    Vendor B:
    - $7.80/kg
    - 3 day delivery

    Preferred Outcome:
    Choose Vendor A because inventory is significantly below threshold and faster replenishment reduces stock-out risk. The business justification should explain the trade-off.

    Do not invent vendor names, prices, delivery times, or reorder quantities. Use only the data provided.

    """

    def __init__(
        self,
        token_tracker: TokenTracker,
    ) -> None:

        super().__init__(
            agent_name="ReorderAgent",
            token_tracker=token_tracker,
        )

        self.recommendation_agent = create_agent(
            system_prompt=self.SYSTEM_PROMPT,
            result_type=ReorderRecommendation,
            agent_name=self.agent_name,
        )

    async def execute(
        self,
        state: WorkflowState,
    ) -> list[ReorderRecommendation]:
        """
        Generate reorder recommendations for all
        low-stock inventory items.

        Args:
            state:
                Current workflow state.

        Returns:
            List of reorder recommendations.
        """

        start_time = self.before_run(state)

        try:

            assessment = state.inventory_assessment

            if assessment is None:
                raise ValueError(
                    "Inventory assessment not available."
                )

            if not assessment.low_stock_items:
                self.logger.info(
                    "No low-stock inventory items detected."
                )

                return []

            inventory_items = get_low_stock_inventory(
                assessment.low_stock_items
            )

            recommendations: list[
                ReorderRecommendation
            ] = []

            for item in inventory_items:

                reorder_quantity = (
                    calculate_reorder_quantity(
                        current_quantity=item.quantity,
                        reorder_threshold=item.reorder_threshold,
                    )
                )

                vendor_options = get_vendor_prices(
                    item.ingredient_name
                )

                prompt = f"""
                Ingredient: {item.ingredient_name}

                Current Quantity:
                {item.quantity}

                Reorder Threshold:
                {item.reorder_threshold}

                Recommended Reorder Quantity:
                {reorder_quantity}

                Vendor Options:
                {vendor_options}

                Select the best vendor and return a
                reorder recommendation.
                """

                result = (
                    await self.recommendation_agent.run(
                        prompt
                    )
                )

                self.update_token_usage(
                    state=state,
                    usage=result.usage,
                )

                recommendation = result.output

                recommendation.reorder_quantity = (
                    reorder_quantity
                )

                recommendations.append(
                    recommendation
                )

            self.log_metrics()

            return recommendations

        finally:

            self.after_run(
                state=state,
                start_time=start_time,
            )


# Menu Strategy Agent -----------------------------------------

class MenuStrategyAgent(
    BaseAgent[MenuRecommendation]
):
    """
    Generates strategic menu specials designed to
    reduce food waste and utilize inventory nearing
    expiry.
    """

    SYSTEM_PROMPT = """
    You are a italian restaurant menu strategist.

    Your role is to recommend a menu special that
    makes effective use of ingredients nearing expiry.

    Consider:
    - Ingredient quantities
    - Days until expiry
    - Logical ingredient combinations
    - Food waste reduction

    Create an appealing special name.

    Example decision:

    Ingredients:
    - Basil (2 days to expiry)
    - Mozzarella (3 days to expiry)

    Preferred outcome:
    Create a Caprese-style special that uses both
    ingredients and explain how the recommendation
    helps reduce waste.

    Do not invent ingredients.
    Use only the inventory provided.
    """

    def __init__(
        self,
        token_tracker: TokenTracker,
    ) -> None:

        super().__init__(
            agent_name="MenuStrategyAgent",
            token_tracker=token_tracker,
        )

        self.menu_agent = create_agent(
            system_prompt=self.SYSTEM_PROMPT,
            result_type=MenuRecommendation,
            agent_name=self.agent_name,
        )

    async def execute(
        self,
        state: WorkflowState,
    ) -> MenuRecommendation:
        """
        Generate a menu special based on inventory
        identified as being at risk of expiry.

        Args:
            state:
                Current workflow state.

        Returns:
            MenuRecommendation.
        """

        start_time = self.before_run(state)

        try:

            assessment = state.inventory_assessment

            if assessment is None:
                raise ValueError(
                    "Inventory assessment not available."
                )

            if not assessment.expiry_risk_items:
                raise ValueError(
                    "No expiry-risk inventory items found."
                )

            expiry_inventory = (
                get_expiry_risk_inventory(
                    assessment.expiry_risk_items
                )
            )

            prompt = f"""
            Generate a menu special using the
            following inventory:

            {expiry_inventory}
            """

            result = await self.menu_agent.run(
                prompt
            )

            self.update_token_usage(
                state=state,
                usage=result.usage,
            )

            recommendation = result.output

            self.log_metrics()

            return recommendation

        finally:

            self.after_run(
                state=state,
                start_time=start_time,
            )

# Critic Agent -------------------------------------------


class CriticAgent(
    BaseAgent[CriticReview]
):
    """
    Reviews workflow recommendations and provides
    an independent assessment before manager approval.
    """

    SYSTEM_PROMPT = """
    You are a senior operations specialist for a busy Italian restaurant.

    Your responsibility is to independently review inventory replenishment
    and menu strategy recommendations before they are submitted to restaurant
    management for approval.

    Restaurant Operational Objectives

    1. Prevent inventory stockouts.
    2. Minimize food waste.
    3. Utilize ingredients approaching expiry.
    4. Maintain operational efficiency.
    5. Select vendors that balance cost and delivery speed.
    6. Ensure menu recommendations are practical and align with
    an Italian restaurant menu.

    Review Criteria

    For reorder recommendations evaluate:

    - Whether the ingredient genuinely requires replenishment.
    - Whether the reorder quantity is reasonable.
    - Whether the selected vendor is justified.
    - Whether the explanation is logical and supported by the data.

    For menu recommendations evaluate:

    - Whether expiry-risk ingredients are being utilized.
    - Whether the proposed ingredients logically work together.
    - Whether the recommendation helps reduce food waste.
    - Whether the recommendation is practical for an Italian restaurant.

    Example: Strong Reorder Recommendation

    Inventory Situation:
    - Mozzarella: 4kg remaining
    - Reorder threshold: 10kg

    Recommendation:
    - Vendor: Fresh Foods Wholesale
    - Reorder quantity: 16kg

    Reasoning:
    - Inventory is significantly below threshold.
    - Vendor provides next-day delivery.
    - Recommendation reduces stockout risk.

    Assessment:
    - Approved: True
    - Confidence: High

    Example: Strong Menu Recommendation

    Expiry-Risk Ingredients:
    - Basil (2 days until expiry)
    - Mozzarella (3 days until expiry)

    Recommendation:
    - Caprese Pizza Special

    Reasoning:
    - Uses multiple ingredients nearing expiry.
    - Aligns with the existing Italian menu.
    - Helps reduce food waste.

    Assessment:
    - Approved: True
    - Confidence: High

    Example: Weak Menu Recommendation

    Expiry-Risk Ingredients:
    - Basil
    - Mozzarella

    Recommendation:
    - Chocolate Milkshake Special

    Assessment:
    - Approved: False

    Reason:
    - Does not utilize identified expiry-risk ingredients.
    - Does not address operational objectives.
    - Does not align with the restaurant menu.

    Confidence Score Guidelines

    0.90 - 1.00
    Very strong recommendation with no meaningful concerns.

    0.75 - 0.89
    Good recommendation with only minor concerns.

    0.50 - 0.74
    Recommendation is acceptable but contains notable weaknesses.

    Below 0.50
    Recommendation should generally be rejected.

    Output Rules

    - Be objective and critical.
    - Approve recommendations only when they support restaurant
    operational goals.
    - Reject recommendations that contain significant flaws or
    inconsistencies.
    - Explain your reasoning clearly in the feedback field.
    - Base your review only on the information provided.
    """

    def __init__(
        self,
        token_tracker: TokenTracker,
    ) -> None:

        super().__init__(
            agent_name="CriticAgent",
            token_tracker=token_tracker,
        )

        self.critic_agent = create_agent(
            system_prompt=self.SYSTEM_PROMPT,
            result_type=CriticReview,
            agent_name=self.agent_name,
        )

    async def execute(
        self,
        state: WorkflowState,
    ) -> CriticReview:
        """
        Review workflow recommendations and determine
        whether they should proceed to manager approval.

        Args:
            state:
                Current workflow state.

        Returns:
            CriticReview.
        """

        start_time = self.before_run(state)

        try:

            if state.inventory_assessment is None:
                raise ValueError(
                    "Inventory assessment is required."
                )

            prompt = f"""
            Inventory Assessment:

            {state.inventory_assessment}

            Reorder Recommendations:

            {state.reorder_recommendations}

            Menu Recommendations:

            {state.menu_recommendations}

            Review these recommendations and determine:

            1. Whether they should be approved.
            2. Your confidence level.
            3. Any concerns or feedback.
            """

            result = await self.critic_agent.run(
                prompt
            )

            self.update_token_usage(
                state=state,
                usage=result.usage,
            )

            review = result.output

            self.log_metrics()

            return review

        finally:

            self.after_run(
                state=state,
                start_time=start_time,
            )

# Sales Intake Agent (Not part of State Machine Workflow) ---------------------------

# Not a base agent but we still want to track token usage


class SalesIntakeAgent:
    """
    Converts unstructured restaurant sales notes
    into a structured SalesReport.
    """

    SYSTEM_PROMPT = """
    You are a restaurant sales intake specialist.

    Your responsibility is to convert unstructured
    manager sales notes into a structured SalesReport.

    Extract:

    - Menu item names
    - Quantities sold

    Rules:

    - Only use information explicitly provided.
    - Do not invent menu items.
    - Do not invent quantities.
    - Extract each sold menu item exactly once.

    Example:

    Input:

    Today we sold:
    - 4 Margherita Pizzas
    - 3 Alfredo Pastas
    - 6 Spaghetti Bolognese

    Output:

    SalesReport(
        sales=[
            SalesItem(
                menu_item="Margherita Pizza",
                quantity=4
            ),
            SalesItem(
                menu_item="Alfredo Pasta",
                quantity=3
            ),
            SalesItem(
                menu_item="Spaghetti Bolognese",
                quantity=6
            )
        ]
    )
    """

    def __init__(
        self,
        token_tracker: TokenTracker,
    ) -> None:

        self.agent_name = "SalesIntakAgent"
        self.sales_agent = create_agent(
            system_prompt=self.SYSTEM_PROMPT,
            result_type=SalesReport,
            agent_name=self.agent_name,
        )

        self.token_tracker = token_tracker
        self.logger = get_logger(
            "SalesIntakeAgent"
        )

    async def execute(
        self,
        report_text: str,
    ) -> SalesReport:
        """
        Convert manager sales notes into a
        structured SalesReport.

        Args:
            report_text:
                Natural-language sales report.

        Returns:
            Structured SalesReport.
        """

        self.logger.info(
            "Processing manager sales report."
        )

        result = await self.sales_agent.run(
            report_text
        )
        self.token_tracker.update_from_run_usage(
            result.usage
        )

        self.logger.info(
            self.token_tracker.summary()
        )

        return result.output


# <<<<<<<<<<<<<<<Orchestration Agent>>>>>>>>>>>>>> -------


class InventoryOrchestrator:

    MAX_RETRIES = 3

    def __init__(
            self,
            token_tracker: TokenTracker,
            approval_function=get_manager_approval):

        self.logger = get_logger(
            self.__class__.__name__
        )

        self.approval_function = approval_function

        self.token_tracker = token_tracker

        self.inventory_agent = (
            InventoryOperationsAgent(
                self.token_tracker
            )
        )

        self.reorder_agent = (
            ReorderAgent(
                self.token_tracker
            )
        )

        self.menu_agent = (
            MenuStrategyAgent(
                self.token_tracker
            )
        )

        self.critic_agent = (
            CriticAgent(
                self.token_tracker
            )
        )

        self.workflow = (
            self._build_workflow()
        )

    async def _inventory_analysis_step(
        self,
        state: WorkflowState,
    ) -> dict:
        """
        Execute inventory analysis.

        Args:
            state:
                Current workflow state.

        Returns:
            Workflow state updates.
        """

        assessment = (
            await self.inventory_agent.execute(
                state
            )
        )

        return {
            "inventory_assessment": assessment,
        }

    async def _reorder_step(
        self,
        state: WorkflowState,
    ) -> dict:
        """
        Generate reorder recommendations.
        """

        recommendations = (
            await self.reorder_agent.execute(
                state
            )
        )

        return {
            "reorder_recommendations":
                recommendations,
        }

    async def _menu_step(
        self,
        state: WorkflowState,
    ) -> dict:
        """
        Generate menu recommendations.
        """

        recommendation = (
            await self.menu_agent.execute(
                state
            )
        )

        return {
            "menu_recommendations": [
                recommendation
            ],
        }

    async def _critic_step(
        self,
        state: WorkflowState,
    ) -> dict:
        """
        Review workflow recommendations.
        """

        review = (
            await self.critic_agent.execute(
                state
            )
        )

        return {
            "critic_review": review,
        }

    def _manager_approval_step(
        self,
        state: WorkflowState,
    ) -> dict:
        """
        Request manager approval.
        """

        self.logger.info(
            "Awaiting manager approval."
        )

        self.logger.info(
            "\n=== REORDER RECOMMENDATIONS ==="
        )

        # Extra work to pretty print our recommendations
        for recommendation in state.reorder_recommendations:

            self.logger.info(
                f"""
                Ingredient    : {recommendation.ingredient_name}
                Quantity      : {recommendation.reorder_quantity} kg
                Vendor        : {recommendation.recommended_vendor}
                Total Cost    : ${recommendation.total_cost:.2f}

                Justification:
                {recommendation.justification}
                """
            )

        self.logger.info(
            "\n=== MENU RECOMMENDATIONS ==="
        )
        for recommendation in state.menu_recommendations:

            self.logger.info(
                f"""
                Special Name:
                {recommendation.special_name}

                Ingredients Used:
                {', '.join(recommendation.ingredients_used)}

                Reasoning:
                {recommendation.reasoning}
                """
            )

        if state.critic_review:

            self.logger.info(
                f"""
                === CRITIC REVIEW ===

                Approved:
                {state.critic_review.approved}

                Confidence Score:
                {state.critic_review.confidence_score:.2f}

                Feedback:
                {state.critic_review.feedback}
                """
            )
        # able to change in testing phase to avoid user input
        decision = (
            self.approval_function()
        )

        self.logger.info(
            f"Manager approval result: "
            f"{decision.approved}"
        )

        return {
            "manager_decision": decision,
        }

    async def _execute_updates_step(
        self,
        state: WorkflowState,
    ) -> dict:
        """
        Execute approved workflow actions.
        """

        actions: list[str] = []

        for recommendation in (
            state.reorder_recommendations
        ):

            result = (
                await self.inventory_agent.replenish(
                    ingredient_name=recommendation.ingredient_name,
                    quantity=recommendation.reorder_quantity,
                )
            )

            actions.append(result)

        for recommendation in (
            state.menu_recommendations
        ):

            result = (
                await self.inventory_agent.add_special(
                    recommendation
                )
            )

            actions.append(result)

        return {
            "final_actions": actions
        }

    def _is_inventory_healthy(
        self,
        state: WorkflowState,
    ) -> str:
        """
        Determine whether additional workflow
        processing is required.
        """

        assessment = state.inventory_assessment

        if (
            assessment
            and assessment.inventory_healthy
        ):
            return "FINALIZE"

        return "REORDER_RECOMMENDATION"

    def _is_critic_approved(
        self,
        state: WorkflowState,
    ) -> str:
        """
        Route workflow based on critic review.
        """

        review = state.critic_review

        if review is None:
            return "REJECT"

        if review.approved:
            return "MANAGER_APPROVAL"

        if (
            state.critic_retry_count
            < self.MAX_RETRIES
        ):
            return "CRITIC_RETRY"

        return "REJECT"

    def _is_manager_approved(
        self,
        state: WorkflowState,
    ) -> str:
        """
        Route workflow based on manager decision.
        """

        decision = state.manager_decision

        if decision is None:
            return "REJECT"

        if decision.approved:
            return "EXECUTE_UPDATES"

        if (
            state.manager_retry_count
            < self.MAX_RETRIES
        ):
            return "MANAGER_RETRY"

        return "REJECT"

    def _critic_retry_step(
        self,
        state: WorkflowState,
    ) -> dict:

        return {
            "critic_retry_count":
                state.critic_retry_count + 1
        }

    def _manager_retry_step(
        self,
        state: WorkflowState,
    ) -> dict:

        return {
            "manager_retry_count":
                state.manager_retry_count + 1
        }

    def _reject_workflow_step(
        self,
        state: WorkflowState,
    ) -> dict:
        """
        Record workflow rejection details and
        produce a final rejection summary.
        """

        if (
            state.critic_review is not None
            and not state.critic_review.approved
        ):
            return {
                "workflow_status": "rejected",
                "summary": (
                    "Workflow rejected after "
                    f"{state.critic_retry_count} critic retries. "
                    f"Final critic feedback: "
                    f"{state.critic_review.feedback}"
                ),
            }

        if (
            state.manager_decision is not None
            and not state.manager_decision.approved
        ):
            return {
                "workflow_status": "rejected",
                "summary": (
                    "Workflow rejected after "
                    f"{state.manager_retry_count} manager retries. "
                    f"Final manager feedback: "
                    f"{state.manager_decision.feedback}"
                ),
            }

        return {
            "workflow_status": "rejected",
            "summary": "Workflow rejected.",
        }

    def _finalize_step(
        self,
        state: WorkflowState,
    ) -> dict:
        """
        Produce the final workflow summary.
        """

        return {
            "workflow_status": "completed",
            "summary": (
                f"Workflow completed successfully. "
                f"Executed {len(state.final_actions)} actions. "
                f"Agents Invoked: "
                f"{', '.join(state.metrics.agents_invoked)}."
            ),
        }

    def _build_workflow(
        self,
    ) -> StateMachine[WorkflowState]:
        """
        Build and configure the inventory
        management workflow.
        """

        workflow = StateMachine(
            WorkflowState
        )

        # Entry / Exit

        entry = EntryPoint()

        termination = Termination()

        # Core Steps

        inventory_analysis = Step(
            "INVENTORY_ANALYSIS",
            self._inventory_analysis_step,
        )

        reorder_recommendation = Step(
            "REORDER_RECOMMENDATION",
            self._reorder_step,
        )

        menu_recommendation = Step(
            "MENU_RECOMMENDATION",
            self._menu_step,
        )

        critic_review = Step(
            "CRITIC_REVIEW",
            self._critic_step,
        )

        critic_retry = Step(
            "CRITIC_RETRY",
            self._critic_retry_step,
        )

        manager_approval = Step(
            "MANAGER_APPROVAL",
            self._manager_approval_step,
        )

        manager_retry = Step(
            "MANAGER_RETRY",
            self._manager_retry_step,
        )

        execute_updates = Step(
            "EXECUTE_UPDATES",
            self._execute_updates_step,
        )

        finalize = Step(
            "FINALIZE",
            self._finalize_step,
        )

        reject = Step(
            "REJECT",
            self._reject_workflow_step,
        )

        workflow.add_steps(
            [
                entry,
                inventory_analysis,
                reorder_recommendation,
                menu_recommendation,
                critic_review,
                critic_retry,
                manager_approval,
                manager_retry,
                execute_updates,
                finalize,
                reject,
                termination,
            ]
        )

        #
        # Entry
        #

        workflow.connect(
            entry,
            inventory_analysis,
        )

        #
        # Inventory Analysis
        #

        workflow.connect(
            inventory_analysis,
            [
                finalize,
                reorder_recommendation,
            ],
            self._is_inventory_healthy,
        )

        #
        # Recommendation Pipeline
        #

        workflow.connect(
            reorder_recommendation,
            menu_recommendation,
        )

        workflow.connect(
            menu_recommendation,
            critic_review,
        )

        #
        # Critic Review
        #

        workflow.connect(
            critic_review,
            [
                manager_approval,
                critic_retry,
                reject,
            ],
            self._is_critic_approved,
        )

        workflow.connect(
            critic_retry,
            reorder_recommendation,
        )

        #
        # Manager Approval
        #

        workflow.connect(
            manager_approval,
            [
                execute_updates,
                manager_retry,
                reject,
            ],
            self._is_manager_approved,
        )

        workflow.connect(
            manager_retry,
            reorder_recommendation,
        )

        #
        # Successful Completion
        #

        workflow.connect(
            execute_updates,
            finalize,
        )

        workflow.connect(
            finalize,
            termination,
        )

        #
        # Rejected Workflow
        #

        workflow.connect(
            reject,
            termination,
        )

        return workflow

    async def run(
        self,
        initial_state: WorkflowState,
    ) -> OrchestratorResponse:
        """
        Execute the inventory workflow.

        Args:
            initial_state:
                Starting workflow state.

        Returns:
            Final orchestrator response.
        """

        self.logger.info(
            "Starting inventory workflow."
        )
        # Keep token usage in sync from first LLM interaction (Sales Intake)
        initial_state.metrics.token_usage = (
            self.token_tracker.usage
        )

        run = await self.workflow.run(
            initial_state
        )

        final_state = run.get_final_state()

        if final_state is None:
            raise RuntimeError(
                "Workflow completed without a final state."
            )

        inventory_healthy = (
            final_state.inventory_assessment.inventory_healthy
            if final_state.inventory_assessment
            else False
        )

        self.logger.info(
            f"Workflow completed with status: "
            f"{final_state.workflow_status}"
        )

        return OrchestratorResponse(
            status=final_state.workflow_status,
            inventory_healthy=inventory_healthy,
            summary=final_state.summary or "",
            reorder_recommendations=(
                final_state.reorder_recommendations
            ),
            menu_recommendations=(
                final_state.menu_recommendations
            ),
            critic_review=(
                final_state.critic_review
            ),
            manager_decision=(
                final_state.manager_decision
            ),
            final_actions=(
                final_state.final_actions
            ),
            metrics=(
                final_state.metrics
            ),
        )
