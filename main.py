"""
Application entry point.

This module provides a simple command-line
interface for interacting with the agent.
"""

import json
import os

from logging_config import setup_logging
setup_logging()

from agent import Agent
from llm_client import LLMClient
from conversation_context import ConversationContext
from tools.tools import tools

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    class _NoColor:
        def __getattr__(self, _):
            return ""
    Fore = _NoColor()
    Style = _NoColor()

HISTORY_DIR = "conversation_history"


def read_user_input():
    """
    Reads a (possibly multi-line) message from the user.

    The user can paste text containing multiple lines (e.g. a long
    process description). Input is collected line by line until an
    empty line is entered, then joined into a single message. This
    prevents a pasted multi-line message from being split into
    several separate messages sent one after another to the model.
    """
    print(f"\n{Fore.CYAN}You (press Enter on an empty line to send):{Style.RESET_ALL}")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return " ".join(lines)


def export_conversation(context):
    """
    Saves the current conversation history to a JSON file in
    conversation_history/. The filename includes a timestamp
    so multiple sessions can coexist without overwriting.
    """
    os.makedirs(HISTORY_DIR, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{timestamp}.json"
    filepath = os.path.join(HISTORY_DIR, filename)

    data = {
        "messages": context.get_history(),
        "token_usage": context.get_token_usage(),
        "estimated_cost": context.get_estimated_cost()
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"{Fore.GREEN}Conversation exported to {filepath}{Style.RESET_ALL}")


def import_conversation(context):
    """
    Lists available saved sessions and lets the user pick one
    to restore. Replaces the current conversation history with
    the imported one.
    """
    if not os.path.isdir(HISTORY_DIR):
        print(f"{Fore.YELLOW}No saved conversations found.{Style.RESET_ALL}")
        return

    files = sorted([
        f for f in os.listdir(HISTORY_DIR)
        if f.endswith(".json")
    ])

    if not files:
        print(f"{Fore.YELLOW}No saved conversations found.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Available sessions:{Style.RESET_ALL}")
    for i, f in enumerate(files, start=1):
        print(f"  {i}. {f}")

    choice = input(f"\n{Fore.CYAN}Enter number to import (or 'cancel'): {Style.RESET_ALL}").strip()

    if choice.lower() == "cancel":
        return

    try:
        index = int(choice) - 1
        if index < 0 or index >= len(files):
            raise ValueError
    except ValueError:
        print(f"{Fore.RED}Invalid choice.{Style.RESET_ALL}")
        return

    filepath = os.path.join(HISTORY_DIR, files[index])

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"{Fore.RED}Failed to load session: {e}{Style.RESET_ALL}")
        return

    context.messages = data["messages"]
    context.input_tokens = data["token_usage"]["input_tokens"]
    context.output_tokens = data["token_usage"]["output_tokens"]

    print(f"{Fore.GREEN}Conversation restored from {filepath} "
          f"({len(context.messages)} messages){Style.RESET_ALL}")


def main():
    context = ConversationContext()

    llm_client = LLMClient()

    agent = Agent(llm_client, context, tools=tools)

    print(f"{Fore.GREEN}Diagrama started.{Style.RESET_ALL} "
          f"Describe a process, system, or workflow "
          f"and I'll turn it into a Mermaid diagram.\n"
          f"Commands: 'exit' to quit | 'export' to save session | 'import' to load session")

    while True:
        user_input = read_user_input()

        if user_input.lower() == "exit":
            print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
            break

        if user_input.lower() == "export":
            export_conversation(context)
            continue

        if user_input.lower() == "import":
            import_conversation(context)
            continue

        if not user_input:
            continue

        try:
            response = agent.process_message(user_input)
        except RuntimeError as e:
            print(f"\n{Fore.RED}[error] {e}{Style.RESET_ALL}")
            print("The conversation was preserved - try again, or type 'exit' to quit.")
            continue

        print(f"\n{Fore.GREEN}AI:{Style.RESET_ALL} {response}")

        usage = context.get_token_usage()
        cost = context.get_estimated_cost()
        print(f"{Fore.LIGHTBLACK_EX}[stats] input={usage['input_tokens']} tokens | "
              f"output={usage['output_tokens']} tokens | "
              f"estimated cost=${cost:.6f}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()