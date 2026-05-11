import sqlite3
import uuid
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph_agent_lab.graph import build_graph

def demonstrate_time_travel():
    print("--- DEMONSTRATING TIME TRAVEL & CRASH RECOVERY ---")
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    checkpointer = SqliteSaver(conn=conn)
    graph = build_graph(checkpointer=checkpointer)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("\n1. Running a tool scenario...")
    initial_state = {
        "query": "Check order status 12345",
        "scenario_id": "time-travel-demo",
        "attempt": 0,
        "max_attempts": 3,
        "messages": [],
        "tool_results": [],
        "errors": [],
        "events": [],
    }
    
    # Run the graph
    final_state = graph.invoke(initial_state, config=config)
    print("Final answer:", final_state.get("final_answer"))

    print("\n2. Simulating crash recovery...")
    # Create a new checkpointer and graph instance (like restarting the app)
    conn2 = sqlite3.connect("checkpoints.db", check_same_thread=False)
    conn2.execute("PRAGMA journal_mode=WAL")
    checkpointer2 = SqliteSaver(conn=conn2)
    graph2 = build_graph(checkpointer=checkpointer2)
    
    # We can retrieve the exact state after "crashing"
    recovered_state = graph2.get_state(config)
    print("Recovered answer after restart:", recovered_state.values.get("final_answer"))
    
    print("\n3. Demonstrating Time Travel...")
    # Fetch history
    history = list(graph2.get_state_history(config))
    print(f"Total historical states found: {len(history)}")
    
    # Let's say we want to fork the state from BEFORE the answer was finalized.
    # The history is returned in reverse chronological order (newest first).
    # The state right after "tool" execution (before "evaluate" or "answer") is somewhere in the middle.
    
    past_state_config = None
    for h in history:
        # Find the state where 'final_answer' was not yet generated
        if not h.values.get("final_answer"):
            past_state_config = h.config
            print(f"Found historical checkpoint: {past_state_config['configurable']['checkpoint_id']}")
            break
            
    if past_state_config:
        print("\n4. Replaying from historical checkpoint...")
        # We can update the state at that point or just invoke to replay
        replayed_state = graph2.invoke(None, config=past_state_config)
        print("Replayed final answer:", replayed_state.get("final_answer"))

if __name__ == "__main__":
    demonstrate_time_travel()
