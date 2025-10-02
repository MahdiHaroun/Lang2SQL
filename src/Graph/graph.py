from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from src.LLM.llm_with_tools import llm_with_tools
from src.Agent.agent import SQLAgent 


class Graph_builder: 
    def __init__(self):
        self.graph = StateGraph(MessagesState)
        self.llm_with_tools_instance = llm_with_tools()
        self.llm_tools = self.llm_with_tools_instance.llm_with_tools()
        self.assistant = SQLAgent().get_agent(self.llm_tools)
        self.memory_saver = MemorySaver()


    def build_graph(self):
        tools = self.llm_with_tools_instance.get_tools()


        self.graph.add_node("assistant", self.assistant)
        self.graph.add_node("tools", ToolNode(tools))
        self.graph.add_edge(START, "assistant")
        self.graph.add_conditional_edges(
            "assistant",
            # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
            # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
            tools_condition,
        )
        self.graph.add_edge("tools", "assistant")

        return self.graph.compile(checkpointer=self.memory_saver)
    

    
    def get_compiled_graph(self):
        """
        Get the complete, compiled graph ready for execution
        """
        return self.build_graph()



graph = Graph_builder().get_compiled_graph()

