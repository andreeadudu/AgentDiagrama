"""
Core agent orchestration.

The agent coordinates communication between the conversation context,
the Knowledge Base retrieval layer (semantic search), the available
tools, and the language model.
"""

import json
import logging
import re

from embeddings_client import EmbeddingsClient

logger = logging.getLogger(__name__)


def _clean_response(text):
    """
    Removes internal implementation details that sometimes leak into
    the model's final answer (raw JSON tool arguments/results, or
    meta-commentary like "I'll validate this now"), keeping only the
    Mermaid code block and the explanation that follows it.

    This is a code-level safeguard: instructing the model via the
    procedure prompt to stay silent about internal steps is not always
    enough, since some models narrate their process anyway. Enforcing
    the final response shape in code guarantees a clean result
    regardless of what the model included on the way there.
    """
    if not text:
        return text

    match = re.search(r"```mermaid", text)
    if not match:
        return text.strip()

    closing = text.find("```", match.end())
    if closing == -1:
        return text[match.start():].strip()

    closing_end = closing + 3
    diagram_block = text[match.start():closing_end]
    explanation = text[closing_end:].strip()

    return f"{diagram_block}\n\n{explanation}".strip()


class Agent:
    def __init__(self, llm_client, context, tools=None):
        self.llm_client = llm_client
        self.context = context
        self.tools = {tool.name: tool for tool in tools} if tools else {}
        self.embeddings_client = EmbeddingsClient()

    def _handle_tool_calls(self, tool_calls):
        results = []
        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            raw_arguments = tc["function"]["arguments"]
            tool_id = tc["id"]

            try:
                arguments = json.loads(raw_arguments)
            except (json.JSONDecodeError, TypeError):
                arguments = {}

            tool = self.tools.get(tool_name)
            if tool:
                try:
                    result = tool.callback(**arguments)
                except Exception as e:
                    logger.error("Tool '%s' raised an error: %s", tool_name, e)
                    result = f"Tool '{tool_name}' failed with error: {e}"
            else:
                result = f"Tool '{tool_name}' not found"

            logger.info("Tool call: %s(%s) -> %s", tool_name, arguments, result)

            results.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": str(result)
            })
        return results

    def _remove_last_retrieval_message(self):
        """
        Removes the most recently injected retrieval/notice message
        from history, if any.

        Cost optimization: retrieved context is only relevant to the
        turn it was fetched for. Without removing it, every past
        retrieval would stay in history forever, and each new message
        sent to the model would carry the full accumulated cost of
        every previous retrieval - growing token usage (and price)
        linearly with conversation length for no benefit.

        Messages are marked with an internal "_retrieval" flag rather
        than matched by content/text, so this stays correct even if
        the retrieval message wording changes later.
        """
        messages = self.context.get_history()
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("_retrieval"):
                self.context.remove_message_at(i)
                return

    def _inject_relevant_context(self, user_message):
        """
        Retrieval-based Context Injection, with a fallback strategy
        and cost optimization.

        Searches the embedded Knowledge Base chunks (e.g. the full
        Mermaid syntax reference, which is too large to always load)
        for content relevant to the user's message, and adds it to the
        conversation as an extra system message, only when relevant
        chunks are found.

        Fallback behavior:
        - If the search itself fails (e.g. the embeddings server is
          unreachable), the error is caught and treated as "no results",
          so a retrieval problem never crashes the whole conversation.
        - If no relevant chunks are found, the model is explicitly told
          that no verified reference was found, so it can be transparent
          in its answer about relying on general knowledge instead of
          silently presenting an unverified answer as if it were backed
          by the Knowledge Base.

        Cost optimization:
        - The retrieval injected on the previous turn is removed
          before injecting a fresh one, so only the latest retrieval
          is ever sent to the model (see _remove_last_retrieval_message).
        """
        self._remove_last_retrieval_message()

        try:
            results = self.embeddings_client.semantic_search(user_message)
        except Exception as e:
            logger.warning("Retrieval search failed (%s), falling back to no context.", e)
            results = []

        if not results:
            logger.info("No relevant chunks found.")
            self.context.add_message({
                "role": "system",
                "content": (
                    "# Retrieval Notice\n"
                    "No specific reference material was found in the Knowledge "
                    "Base for this request. Answer using your general knowledge "
                    "of Mermaid syntax, and mention in your explanation that "
                    "this wasn't verified against the internal syntax reference."
                ),
                "_retrieval": True
            })
            return

        logger.info(
            "Found %d relevant chunk(s): %s",
            len(results),
            [(r['document_id'], r['chunk_index'], round(r['similarity'], 2)) for r in results]
        )

        context_text = "\n\n".join(
            f"[{r['document_id']} #{r['chunk_index']} - similarity {r['similarity']:.2f}]\n{r['content']}"
            for r in results
        )

        self.context.add_message({
            "role": "system",
            "content": f"# Relevant Context\n{context_text}",
            "_retrieval": True
        })

    @timed
    def process_message(self, user_message):
        """
        Runs one full turn: retrieval, model call, tool execution
        (if any), follow-up model call, and response cleanup.

        Fallback behavior: if the model endpoint itself is unreachable
        or errors out (RuntimeError from LLMClient), that's re-raised
        as-is - main.py is responsible for catching it and keeping the
        CLI loop alive, since the agent has no sensible answer to give
        without the model.
        """
        logger.info("User question: %s", user_message)

        self._inject_relevant_context(user_message)

        self.context.add_message({
            "role": "user",
            "content": user_message
        })

        response = self.llm_client.generate_response(
            self.context.get_history(),
            tools=list(self.tools.values())
        )

        message = response["message"]
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            self.context.add_message(message)

            tool_results = self._handle_tool_calls(tool_calls)
            for result in tool_results:
                self.context.add_message(result)

            response = self.llm_client.generate_response(
                self.context.get_history()
            )
            message = response["message"]

        self.context.add_message(message)

        final_response = _clean_response(message.get("content", ""))
        logger.info("Generated response: %s", final_response[:200])

        return final_response