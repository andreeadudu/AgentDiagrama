"""
LLM integration layer.

This module is responsible for all communication
with the language model.
"""

from openai import APIConnectionError, APIStatusError, OpenAI

from config import (
    MODEL_NAME,
    AZURE_ENDPOINT,
    API_KEY
)

from tools.tool import Tool

# Internal-only keys used for bookkeeping in ConversationContext (e.g.
# "_retrieval" marks a message as a retrieval injection, so the agent
# can find and remove it next turn). These must never be sent to the
# model - the OpenAI SDK's message schema doesn't expect them, and
# some backends reject unknown fields outright.
INTERNAL_MESSAGE_KEYS = {"_retrieval"}


def _sanitize_message(message):
    """Strips internal bookkeeping keys before a message is sent to the model."""
    return {k: v for k, v in message.items() if k not in INTERNAL_MESSAGE_KEYS}


class LLMClient:

    def __init__(self):
        self.client = OpenAI(
            base_url=AZURE_ENDPOINT,
            api_key=API_KEY
        )

    def _tool_to_dict(self, tool: Tool):
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        }

    def generate_response(self, messages, tools=None):
        """
        Sends the conversation history to the model and returns its
        response in a normalized dict format.

        Raises RuntimeError with a clear message on connection
        failures or API errors (bad key, rate limit, invalid model),
        instead of letting the raw OpenAI SDK exception propagate.
        """
        kwargs = {
            "model": MODEL_NAME,
            "messages": [_sanitize_message(m) for m in messages]
        }

        if tools:
            kwargs["tools"] = [
                self._tool_to_dict(tool)
                for tool in tools
            ]

        try:
            response = self.client.chat.completions.create(**kwargs)
        except APIConnectionError as e:
            raise RuntimeError(
                f"Could not reach the model endpoint at "
                f"{AZURE_ENDPOINT}. Check your connection. ({e})"
            ) from e
        except APIStatusError as e:
            raise RuntimeError(
                f"Model endpoint returned an error: "
                f"{e.status_code} {e.message}"
            ) from e

        message = response.choices[0].message

        result = {
            "message": {
                "role": "assistant",
                "content": message.content
            }
        }

        if getattr(message, "tool_calls", None):
            result["message"]["tool_calls"] = []

            for tc in message.tool_calls:
                result["message"]["tool_calls"].append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

        return result