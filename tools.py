import logging
from langchain_community.tools import  WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper  # Fixed import
from langchain.tools import Tool
search = DuckDuckGoSearchRun()

logging.basicConfig(level=logging.INFO)

def mindfulness_breathing_exercise(input: str) -> str:
    logging.info(f"MindfulnessBreathing tool called with input: {input}")
    return (
        "Let's do a short breathing exercise together:\n"
        "1. Breathe in slowly for 4 seconds.\n"
        "2. Hold your breath for 4 seconds.\n"
        "3. Breathe out slowly for 4 seconds.\n"
        "4. Pause for 4 seconds.\n"
        "Repeat this cycle a few times. 🌱"
    )

mindfulness_tool = Tool(
    name="MindfulnessBreathing",
    func=mindfulness_breathing_exercise,
    description="Guides the user through a simple mindfulness breathing exercise."
)

# Example: Wikipedia and DuckDuckGo search tools (already imported)
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())  # Fixed usage
def wikipedia_tool_func(query: str) -> str:
    logging.info(f"WikipediaSearch tool called with query: {query}")
    return wikipedia.run(query)

wikipedia_tool = Tool(
    name="WikipediaSearch",
    func=wikipedia_tool_func,
    description="Searches Wikipedia for psychoeducation or mental health topics."
)

def duckduckgo_tool_func(query: str) -> str:
    logging.info(f"DuckDuckGoSearch tool called with query: {query}")
    return search.run(query)

duckduckgo_tool = Tool(
    name="DuckDuckGoSearch",
    func=duckduckgo_tool_func,
    description="Searches the web for mental health resources or definitions."
)

def therapy_research_tool_func(query: str) -> str:
    logging.info(f"TherapyResearch tool called with query: {query}")
    # Use DuckDuckGo to search for therapy research and best practices
    results = search.run(f"{query} therapy research best practices site:.gov OR site:.edu OR site:.org")
    return (
        "Here are some research-based insights and best practices I found:\n"
        f"{results}\n"
        "These results are from reputable sources. Please consult a licensed professional for personalized advice."
    )

therapy_research_tool = Tool(
    name="TherapyResearch",
    func=therapy_research_tool_func,
    description=(
        "Searches for recent research, guidelines, or best practices in therapy from reputable sources "
        "(such as .gov, .edu, or .org domains) and summarizes the findings for the user."
    )
)

# List of tools to use in your agent
therapy_tools = [mindfulness_tool, wikipedia_tool, duckduckgo_tool, therapy_research_tool]
