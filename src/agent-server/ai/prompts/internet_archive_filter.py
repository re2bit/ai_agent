from langchain_core.prompts import PromptTemplate
filter_prompt = PromptTemplate.from_template(
    """You are a helpful assistant that filters Internet Archive search results.

    The user is looking for: {query}

    Here are the search results (item identifiers):
    {results}

    Please filter these results to only include relevant items. But dont be too aggressive.
    We will load Metadata later and verify the results.
    Return your answer as a JSON list of item identifiers. return only json, no other text.
    Example format: ["item1", "item2", "item3"]
    """
)

# Format the prompt with the query and results
formatted_prompt = filter_prompt.format(
    query=state["query"],
    results=json.dumps(state["results"])
)