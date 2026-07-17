"""
Minimal Web UI for the Diagrama agent using Streamlit.

Renders Mermaid diagrams directly in the browser with a
chat-like interface. Run with: streamlit run web_app.py
"""

import re
import streamlit as st

from agent import Agent
from llm_client import LLMClient
from conversation_context import ConversationContext
from tools.tools import tools


st.set_page_config(
    page_title="Diagrama",
    page_icon="📐",
    layout="wide"
)


def render_mermaid(mermaid_code):
    """
    Renders a Mermaid diagram in Streamlit using mermaid.js.
    st.code() only syntax-highlights the code but doesn't render
    the actual diagram - this function embeds mermaid.js via
    st.html() to produce the visual output.
    """
    html = f"""
    <div style="background: white; border-radius: 10px; padding: 20px;
                display: flex; justify-content: center;">
        <pre class="mermaid">
{mermaid_code}
        </pre>
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """
    st.html(html)


def parse_response(response):
    """
    Splits the agent's response into the Mermaid code block and
    the explanation text that follows it.
    """
    match = re.search(r"```mermaid\n([\s\S]*?)```", response)
    if match:
        mermaid_code = match.group(1).strip()
        explanation = response[match.end():].strip()
        return mermaid_code, explanation
    return None, response


# --- Session state initialization ---
if "context" not in st.session_state:
    st.session_state.context = ConversationContext()
    st.session_state.llm_client = LLMClient()
    st.session_state.agent = Agent(
        st.session_state.llm_client,
        st.session_state.context,
        tools=tools
    )
    st.session_state.chat_history = []


# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📐 Diagrama")
    st.caption("AI diagram generator for software architects")

    st.divider()

    st.markdown("**Supported diagrams:**")
    st.markdown(
        "- 🔀 Flowchart\n"
        "- 🔄 Sequence Diagram\n"
        "- 🏗️ Class Diagram\n"
        "- 🗄️ ER Diagram\n"
        "- 📊 State Diagram"
    )

    st.divider()

    usage = st.session_state.context.get_token_usage()
    cost = st.session_state.context.get_estimated_cost()

    col1, col2 = st.columns(2)
    col1.metric("Input", f"{usage['input_tokens']}")
    col2.metric("Output", f"{usage['output_tokens']}")
    st.metric("Estimated Cost", f"${cost:.6f}")

    st.divider()

    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.context = ConversationContext()
        st.session_state.agent = Agent(
            st.session_state.llm_client,
            st.session_state.context,
            tools=tools
        )
        st.session_state.chat_history = []
        st.rerun()


# --- Main area title ---
if not st.session_state.chat_history:
    st.markdown(
        """
        <div style="text-align: center; padding: 60px 20px 30px 20px;">
            <h1 style="font-size: 2.5em;">📐 Diagrama</h1>
            <p style="color: gray; font-size: 1.1em;">
                Describe a system, process, or workflow and I'll generate
                a Mermaid diagram for it.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# --- Chat history display ---
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        if msg.get("mermaid_code"):
            render_mermaid(msg["mermaid_code"])
            if msg.get("explanation"):
                st.caption(msg["explanation"])
        else:
            st.markdown(msg["content"])


# --- User input ---
user_input = st.chat_input("Describe a system, process, or workflow...")

if user_input:
    # Show user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Generating diagram..."):
            try:
                response = st.session_state.agent.process_message(user_input)
            except RuntimeError as e:
                st.error(f"Error: {e}")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"Error: {e}"
                })
                st.stop()

        mermaid_code, explanation = parse_response(response)

        if mermaid_code:
            render_mermaid(mermaid_code)
            if explanation:
                st.caption(explanation)

            st.session_state.chat_history.append({
                "role": "assistant",
                "mermaid_code": mermaid_code,
                "explanation": explanation
            })
        else:
            st.markdown(response)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })

    st.rerun()