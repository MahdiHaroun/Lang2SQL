import json
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from src.LLM.llm_with_tools import llm_with_tools
from src.Agent.agent import SQLAgent
from src.redis_client import redis_client

# -----------------------------
# Graph builder
# -----------------------------
class Graph_builder: 
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.graph = StateGraph(MessagesState)
        self.llm_with_tools_instance = llm_with_tools(session_id)
        self.llm_tools = self.llm_with_tools_instance.llm_with_tools()
        self.assistant = SQLAgent().get_agent(self.llm_tools)
        self.memory_saver = MemorySaver()

    def build_graph(self):
        tools = self.llm_with_tools_instance.get_tools()

        self.graph.add_node("assistant", self.assistant)
        self.graph.add_node("tools", ToolNode(tools))
        self.graph.add_edge(START, "assistant")
        self.graph.add_conditional_edges("assistant", tools_condition)
        self.graph.add_edge("tools", "assistant")

        return self.graph.compile(checkpointer=self.memory_saver)

    def get_compiled_graph(self):
        """Get the complete, compiled graph ready for execution"""
        return self.build_graph()

# -----------------------------
# Simple session graph management (no Redis serialization)
# -----------------------------
def get_session_graph(session_id: str):
    """Create a fresh graph for a specific session"""
    print(f"Creating fresh graph for session {session_id}.")
    
    # Simply create a fresh graph with session-specific tools
    # No Redis storage of graph objects to avoid pickling issues
    graph_builder = Graph_builder(session_id)
    return graph_builder.get_compiled_graph()

def save_session_graph(session_id: str, graph_instance):
    """No-op function - we don't store graphs in Redis to avoid pickling issues"""
    # Graph state is handled by the built-in MemorySaver
    # Session data (database connections) are handled by Tools.py
    pass

# -----------------------------
# Default graph for backward compatibility
# -----------------------------
graph = Graph_builder().get_compiled_graph()
