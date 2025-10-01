from typing import List, TypedDict, Dict, Any, NotRequired, Union



class GraphState(TypedDict):


    question: str
    generated_sql: NotRequired[str]
    db_schema: NotRequired[Dict[str, Any]]
    #db_cardinalities: List[Any]
    #validation_status: bool
    summary: NotRequired[str]
    query_result: NotRequired[Union[List[Dict[str, Any]], Dict[str, Any]]]
