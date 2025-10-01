from src.State.GraphState import GraphState
from langgraph.graph import StateGraph, START, END
from src.LLM.groqllm import GroqLLM
from src.Nodes.Nodes import agent
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from src.Nodes.Nodes import LLM_withTools, fetch_db_schema_tool, generate_sql_tool, execute_sql_query_tool, get_summary_tool




class Graph_builder:    
    def __init__(self): 
        self.graph = StateGraph(GraphState)

    def build_graph(self): 
        tools = [fetch_db_schema_tool, generate_sql_tool, execute_sql_query_tool, get_summary_tool]
        
        self.graph.add_node("agent", agent)
        self.graph.add_node("tools", ToolNode(tools))
        self.graph.add_edge(START, "agent")
        self.graph.add_conditional_edges(
            "agent",
            # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
            # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
            tools_condition,
        )
        self.graph.add_edge("tools", "agent")



        

        return self.graph.compile()


    def get_compiled_graph(self):
        """
        Get the complete, compiled graph ready for execution
        """
        return self.build_graph()



graph = Graph_builder().build_graph()
