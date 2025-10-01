from src.State.GraphState import GraphState
from langgraph.graph import StateGraph, START, END
from src.LLM.groqllm import GroqLLM
from src.Nodes.Nodes import AgentNodes



class Graph_builder:    
    def __init__(self): 
        self.graph = StateGraph(GraphState)
        self.llm = GroqLLM.get_llm()



    def build_graph(self): 
        agent_nodes = AgentNodes()
        fetch_db_schema = agent_nodes.fetch_db_schema
        generate_sql = agent_nodes.generate_sql
        execute_sql_query = agent_nodes.execute_sql_query
        summarize_results = agent_nodes.get_summary



        self.graph.add_node("fetch_db_schema", fetch_db_schema)
        self.graph.add_node("generate_sql", generate_sql)
        self.graph.add_node("execute_sql_query", execute_sql_query)
        self.graph.add_node("summarize_results", summarize_results)
        self.graph.add_edge(START, "fetch_db_schema")
        self.graph.add_edge("fetch_db_schema", "generate_sql")
        self.graph.add_edge("generate_sql", "execute_sql_query")
        self.graph.add_edge("execute_sql_query", "summarize_results")
        self.graph.add_edge("summarize_results", END)

        return self.graph.compile() 
    


    def get_compiled_graph(self):
        """
        Get the complete, compiled graph ready for execution
        """
        return self.build_graph()



graph = Graph_builder().build_graph()
