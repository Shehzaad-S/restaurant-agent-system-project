"""
llm.py

Centralized LLM configuration and
agent creation utilities.
"""

from typing import Type

from pydantic import BaseModel
from pydantic_ai import Agent

from libs.logging_config import get_logger


logger = get_logger(__name__)

DEFAULT_MODEL = "google:gemini-3.5-flash"


def create_agent(
    system_prompt: str,
    result_type: Type[BaseModel],
    agent_name: str,
    model_name: str = DEFAULT_MODEL,
) -> Agent:
    """
    Create a configured PydanticAI agent.

    Args:
        system_prompt:
            Agent instructions.

        result_type:
            Structured Pydantic response model.

        model_name:
            Gemini model identifier.

    Returns:
        Configured PydanticAI agent.
    """

    logger.info(
        f"Creating {agent_name} with model: {model_name}"
    )

    return Agent(
        model=model_name,
        system_prompt=system_prompt,
        output_type=result_type,
    )


if __name__ == "__main__":

    class JokeResponse(BaseModel):

        joke: str

    agent = create_agent(
        system_prompt="Return a short joke.",
        result_type=JokeResponse,
    )

    result = agent.run_sync(
        "Tell me a joke about restaurants."
    )

    print(result.run_id)
    print(result.timestamp)
    print(result.usage)
