from langchain_core.tools import tool


@tool
def llm_search(query: str):
    """
    Use the LLM model for general and basic information.
    """
    response = llm.invoke(query)
    return response
