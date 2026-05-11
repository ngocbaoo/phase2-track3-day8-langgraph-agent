import os
import sqlite3
import uuid
import streamlit as st
from langgraph.types import Command
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph_agent_lab.graph import build_graph

# Enable real HITL
os.environ["LANGGRAPH_INTERRUPT"] = "true"

st.set_page_config(page_title="Support Agent UI", layout="centered")
st.title("🤖 Support Agent (Streamlit HITL)")

@st.cache_resource
def get_graph():
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    checkpointer = SqliteSaver(conn=conn)
    return build_graph(checkpointer=checkpointer)

graph = get_graph()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

config = {"configurable": {"thread_id": st.session_state.thread_id}}

current_state = graph.get_state(config)

query = st.chat_input("Enter your support request...")

if query:
    st.chat_message("user").write(query)
    
    # Initialize state
    initial_state = {
        "query": query,
        "scenario_id": "custom",
        "attempt": 0,
        "max_attempts": 3,
        "messages": [],
        "tool_results": [],
        "errors": [],
        "events": [],
    }
    
    with st.spinner("Processing..."):
        # Run until interrupt or end
        graph.invoke(initial_state, config=config)
        st.rerun()

current_state = graph.get_state(config)
if current_state and current_state.next:
    if "approval" in current_state.next:
        st.warning("⚠️ Action requires your approval!")
        
        # Read the interrupt value from the tasks
        pending_action = current_state.values.get("proposed_action", "Unknown action")
        
        st.info(f"**Proposed Action:** {pending_action}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", use_container_width=True):
                with st.spinner("Resuming with approval..."):
                    graph.invoke(Command(resume=True), config=config)
                st.rerun()
        with col2:
            if st.button("❌ Reject", use_container_width=True):
                with st.spinner("Resuming with rejection..."):
                    graph.invoke(Command(resume=False), config=config)
                st.rerun()
elif current_state and not current_state.next and current_state.values.get("final_answer"):
    st.chat_message("assistant").write(current_state.values.get("final_answer"))
    
    with st.expander("Show Graph Events"):
        st.json(current_state.values.get("events", []))
