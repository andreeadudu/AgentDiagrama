"""
Streamlit Web UI for the Diagrama agent.
 
Renders Mermaid diagrams directly in the browser using mermaid.js
embedded via st.html(). Supports file upload (.txt) for reading
requirements from design docs, and conversation export to JSON.
 
Run with: streamlit run streamlit_app.py
"""
 
import json
import os
import re
import tempfile
from datetime import datetime
 
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
    Renders a Mermaid diagram using mermaid.js via st.html().
    Streamlit's st.code(language='mermaid') only syntax-highlights
    the code but does not produce the actual visual diagram.
    """
    escaped = mermaid_code.replace("<", "&lt;").replace(">", "&gt;")
    html = f"""
    <div id="mermaid-container" style="
        background: #ffffff;
        border-radius: 10px;
        padding: 24px;
        display: flex;
        justify-content: center;
        min-height: 100px;
    ">
        <pre class="mermaid">{escaped}</pre>
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        await mermaid.run();
    </script>
    """
    st.components.v1.html(html, height=500, scrolling=True)
 
 
def parse_response(response):
    """
    Splits the agent's response into the Mermaid code block
    and the explanation text that follows it.
    """
    match = re.search(r"```mermaid\n([\s\S]*?)```", response)
    if match:
        mermaid_code = match.group(1).strip()
        explanation = response[match.end():].strip()
        return mermaid_code, explanation
    return None, response
 
 
def export_conversation():
    """
    Builds a JSON export of the current conversation history
    including token usage and cost.
    """
    data = {
        "exported_at": datetime.now().isoformat(),
        "messages": st.session_state.chat_history,
        "token_usage": st.session_state.context.get_token_usage(),
        "estimated_cost": st.session_state.context.get_estimated_cost()
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
 
 
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
    st.session_state.uploaded_file_processed = False
 
 
# --- Sidebar ---
with st.sidebar:
    st.markdown("## Diagrama")
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
 
    # --- File upload ---
    st.markdown("**Upload a requirement file:**")
    uploaded_file = st.file_uploader(
        "Drop a .txt file with a system description",
        type=["txt"],
        label_visibility="collapsed"
    )
 
    if uploaded_file and not st.session_state.uploaded_file_processed:
        file_content = uploaded_file.read().decode("utf-8").strip()
        if file_content:
            # Save to a temp file so the tool can also find it
            temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(file_content)
 
            prompt = (
                f"Generate a diagram from the following requirement document "
                f"({uploaded_file.name}):\n\n{file_content}"
            )
            st.session_state.pending_file_prompt = prompt
            st.session_state.uploaded_file_processed = True
            st.rerun()
 
    st.divider()
 
    # --- Session stats ---
    usage = st.session_state.context.get_token_usage()
    cost = st.session_state.context.get_estimated_cost()
 
    col1, col2 = st.columns(2)
    col1.metric("Input", f"{usage['input_tokens']}")
    col2.metric("Output", f"{usage['output_tokens']}")
    st.metric("Estimated Cost", f"${cost:.6f}")
 
    st.divider()
 
    # --- Export conversation ---
    if st.session_state.chat_history:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 Export Conversation",
            data=export_conversation(),
            file_name=f"diagrama_session_{timestamp}.json",
            mime="application/json",
            use_container_width=True
        )
 
    # --- New session ---
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.context = ConversationContext()
        st.session_state.agent = Agent(
            st.session_state.llm_client,
            st.session_state.context,
            tools=tools
        )
        st.session_state.chat_history = []
        st.session_state.uploaded_file_processed = False
        if "pending_file_prompt" in st.session_state:
            del st.session_state.pending_file_prompt
        st.rerun()
 
 
# --- Welcome screen ---
if not st.session_state.chat_history:
    st.markdown(
        """
        <div style="text-align: center; padding: 60px 20px 30px 20px;">
            <h1 style="font-size: 2.5em;">📐 Diagrama</h1>
            <p style="color: gray; font-size: 1.1em;">
                Describe a system, process, or workflow<br>
                and I'll generate a Mermaid diagram for it.<br><br>
                You can also upload a .txt file from the sidebar.
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
 
 
# --- Handle file upload prompt ---
def process_user_message(user_input):
    """Sends a message to the agent and displays the response."""
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    with st.chat_message("user"):
        st.markdown(user_input)
 
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
 
 
# Process pending file upload
if "pending_file_prompt" in st.session_state:
    prompt = st.session_state.pending_file_prompt
    del st.session_state.pending_file_prompt
    process_user_message(prompt)
 
# --- User text input ---
user_input = st.chat_input("Describe a system, process, or workflow...")
 
if user_input:
    process_user_message(user_input)
 