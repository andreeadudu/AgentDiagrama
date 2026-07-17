"""
Conversation memory management.

This module is responsible for storing and retrieving
messages exchanged between the user and the AI assistant.
It also dynamically builds the system prompt from the
Knowledge Base, tracks token usage and estimated cost, and
trims older history once the conversation grows too large
(Context Recycling).
"""
import logging

from config import (
    INPUT_TOKEN_PRICE_PER_MILLION,
    OUTPUT_TOKEN_PRICE_PER_MILLION,
    MAX_CONTEXT_TOKENS,
    CONTEXT_TRIM_KEEP_LAST,
)
from utils import count_tokens
import knowledge_base_loader as kb

logger = logging.getLogger(__name__)


class ConversationContext:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0

        self.messages = []
        self.add_message(self.assemble_system_prompt())

    def assemble_system_prompt(self):
        """
        Builds the system prompt dynamically by concatenating:
        - every document in knowledge/prompts/
        - documents in knowledge/facts/ marked always_load: true
        - documents in knowledge/procedures/ marked always_load: true
        """
        sections = []

        for doc in kb.load_prompts():
            sections.append(f"# {doc['name']}\n{doc['content']}")

        for doc in kb.load_facts(only_always_load=True):
            sections.append(f"# {doc['name']}\n{doc['content']}")

        for doc in kb.load_procedures(only_always_load=True):
            sections.append(f"# {doc['name']}\n{doc['content']}")

        return {
            "role": "system",
            "content": "\n\n".join(sections)
        }

    def add_message(self, message):
        content = message.get("content") or ""
        tokens = count_tokens(content)

        if message.get("role") == "assistant":
            self.output_tokens += tokens
        else:
            self.input_tokens += tokens

        self.messages.append(message)
        self._maybe_trim_history()

    def remove_message_tokens(self, message):
        """
        Reverses the token accounting for a message being removed from
        history. Used whenever a message is dropped (stale retrieval
        replaced each turn, or old history trimmed for Context
        Recycling), so input_tokens/output_tokens stay accurate
        instead of overstating what's actually sent to the model.
        """
        content = message.get("content") or ""
        tokens = count_tokens(content)

        if message.get("role") == "assistant":
            self.output_tokens -= tokens
        else:
            self.input_tokens -= tokens

    def remove_message_at(self, index):
        """
        Removes the message at the given index from history and
        reverses its token accounting in one step.
        """
        message = self.messages[index]
        self.remove_message_tokens(message)
        del self.messages[index]

    def _maybe_trim_history(self):
        """
        Context Recycling: when accumulated input tokens exceed
        MAX_CONTEXT_TOKENS, older messages are dropped to keep the
        conversation within a safe budget.

        The system prompt (always messages[0]) is never dropped - the
        agent can't function without it. The most recent
        CONTEXT_TRIM_KEEP_LAST messages are also protected, so an
        in-progress diagram refinement never loses the diagram it
        refers to.

        This is a simple sliding-window strategy rather than
        summarization: for a diagram-generation agent, each diagram is
        usually self-contained, so dropping old exchanges outright is
        an acceptable trade-off against the extra cost and complexity
        a summarization call would add.
        """
        if self.input_tokens <= MAX_CONTEXT_TOKENS:
            return

        protected_start = max(1, len(self.messages) - CONTEXT_TRIM_KEEP_LAST)

        trimmed_count = 0
        while self.input_tokens > MAX_CONTEXT_TOKENS and len(self.messages) > protected_start:
            self.remove_message_at(1)
            protected_start -= 1
            trimmed_count += 1

        if trimmed_count:
            logger.info(
                "Trimmed %d older message(s) to stay under the %d-token budget.",
                trimmed_count, MAX_CONTEXT_TOKENS
            )

    def get_history(self):
        return self.messages

    def get_token_usage(self):
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens
        }

    def get_estimated_cost(self):
        input_cost = (self.input_tokens / 1_000_000) * INPUT_TOKEN_PRICE_PER_MILLION
        output_cost = (self.output_tokens / 1_000_000) * OUTPUT_TOKEN_PRICE_PER_MILLION
        return input_cost + output_cost