"""
Utilities for aggregating and tracking LLM token
usage across a workflow execution.
"""

from decimal import Decimal
from typing import Any

from libs.models import TokenUsage


class TokenTracker:
    """
    Aggregates token usage across multiple
    model invocations during a workflow run.
    """

    def __init__(self) -> None:
        self._usage = TokenUsage()

    @property
    def usage(self) -> TokenUsage:
        """
        Return the current aggregated token usage.

        Returns:
            TokenUsage: Aggregated workflow usage.
        """
        return self._usage

    def add_usage(
        self,
        request_tokens: int,
        response_tokens: int,
        requests: int = 1,
        reasoning_tokens: int = 0,
        estimated_cost: float = 0.0,
    ) -> None:
        """
        Manually update aggregated token usage.

        Args:
            request_tokens:
                Input/request token count.

            response_tokens:
                Output/response token count.

            requests:
                Number of model requests made.

            reasoning_tokens:
                Internal reasoning token count.

            estimated_cost:
                Estimated model cost.
        """

        self._usage.request_tokens += request_tokens
        self._usage.response_tokens += response_tokens
        self._usage.total_tokens += (
            request_tokens + response_tokens
        )

        self._usage.requests += requests
        self._usage.reasoning_tokens += reasoning_tokens
        self._usage.estimated_cost += estimated_cost

    def update_from_run_usage(
        self,
        usage: Any,
    ) -> None:
        """
        Update tracker using a PydanticAI RunUsage object.

        Args:
            usage:
                PydanticAI usage object returned from
                a model run.
        """

        reasoning_tokens = (
            usage.details.get("thoughts_tokens", 0)
            if getattr(usage, "details", None)
            else 0
        )

        self.add_usage(
            request_tokens=usage.input_tokens,
            response_tokens=usage.output_tokens,
            requests=usage.requests,
            reasoning_tokens=reasoning_tokens,
            estimated_cost=float(
                usage.cost
                if isinstance(usage.cost, Decimal)
                else usage.cost
            ),
        )

    def reset(self) -> None:
        """
        Reset all aggregated usage metrics.
        """

        self._usage = TokenUsage()

    def summary(self) -> dict[str, int | float]:
        """
        Return a summary suitable for logging
        and workflow reporting.

        Returns:
            Dictionary containing aggregated metrics.
        """

        return (
            "\n=== TOKEN USAGE SUMMARY ===\n"
            f"Requests          : {self.usage.requests}\n"
            f"Request Tokens    : {self.usage.request_tokens}\n"
            f"Response Tokens   : {self.usage.response_tokens}\n"
            f"Reasoning Tokens  : {self.usage.reasoning_tokens}\n"
            f"Total Tokens      : {self.usage.total_tokens}\n"
            f"Estimated Cost    : "
            f"${self.usage.estimated_cost:.5f}\n"
        )
