from typing import List, TypedDict, Dict, Any, NotRequired, Union
from langchain_core.messages import BaseMessage



class GraphState(TypedDict):


    question: NotRequired[str]
    generated_sql: NotRequired[str]
    db_schema: NotRequired[Dict[str, Any]]
    summary: NotRequired[str]
    query_result: NotRequired[Union[List[Dict[str, Any]], Dict[str, Any]]]
    messages: NotRequired[List[BaseMessage]]
