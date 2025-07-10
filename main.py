from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langchain_core.memory import BaseMemory
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import Runnable
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain.memory import ConversationBufferMemory
from tools import expense_tools  # still used for summarization/reporting
import logging
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Expense schema
class Expense(BaseModel):
    date: str
    amount: float
    category: str
    description: str

# In-memory expense log (for demo purposes)
expense_log: List[dict] = []

# Expense Agent configuration
class ExpenseManager:
    def __init__(self,
                 name: str,
                 role: str,
                 description: str,
                 tone: str,
                 specialties: list[str],
                 features: list[str],
                 greeting_style: str,
                 response_style: str,
                 llm: BaseLanguageModel,
                 tools: Optional[List[BaseTool]] = None,
                 memory: Optional[BaseMemory] = None):
        self.name = name
        self.role = role
        self.description = description
        self.tone = tone
        self.specialties = specialties
        self.features = features
        self.greeting_style = greeting_style
        self.response_style = response_style
        self.llm = llm
        self.tools = tools
        self.memory = memory

def get_expense_manager(llm: BaseLanguageModel) -> ExpenseManager:
    return ExpenseManager(
        name="Penny",
        role="Personal Expense Assistant",
        description="An intelligent and friendly assistant that helps users track, log, and understand their spending patterns.",
        tone="Helpful and concise",
        specialties=["Expense Logging", "Spending Insights", "Monthly Reports"],
        features=["Log Expenses", "Summarize Spend", "Visual Reports"],
        greeting_style="Friendly and clear",
        response_style="Direct and practical",
        llm=llm
    )

def get_prompt_template():
    response_guidelines = """
    - Keep responses practical and to the point
    - Use simple language for easy financial understanding
    - Provide summaries, suggestions, and spending alerts when appropriate
    - Only use emojis when reinforcing positive behavior (e.g. 💰, 🚀) — 1 max
    - Don’t sound robotic or overly formal, but maintain clarity
    - Avoid lengthy explanations unless asked to elaborate
    """
    return ChatPromptTemplate.from_template(
        f"""
        You are an expense assistant named Penny.
        Your role is: Personal Expense Assistant.
        Your description is: An intelligent and friendly assistant that helps users track, log, and understand their spending patterns.
        Your tone is: Helpful and concise.
        Your specialties are: Expense Logging, Spending Insights, Monthly Reports.
        Your features include: Log Expenses, Summarize Spend, Visual Reports.
        Your greeting style is: Friendly and clear.
        Your response style is: Direct and practical.
        You will assist the user by responding to their queries or helping them manage their expenses.
        Always follow these response guidelines: {response_guidelines}.
        Conversation so far:
        {{chat_history}}
        The user says: {{input}}
        {{agent_scratchpad}}
        """
    )

class LoggingChatOpenAI(ChatOpenAI):
    def invoke(self, input, *args, **kwargs):
        logging.info(f"Payload to ChatOpenAI: {input}")
        return super().invoke(input, *args, **kwargs)

def extract_expense_from_llm(llm: BaseLanguageModel, user_input: str) -> Optional[Expense]:
    parser = PydanticOutputParser(pydantic_object=Expense)
    prompt = PromptTemplate(
        template="""
        You are a smart financial assistant. The user might type anything — a question, a report request, or a new expense.

        Your task is to detect whether the input is a new expense to be logged.

        If it is NOT an expense, respond with:
        "not an expense"

        If it IS an expense, return ONLY this valid JSON:

        {{
          "amount": float,
          "category": "one of: groceries, food, transport, bills, entertainment, misc",
          "date": "YYYY-MM-DD",
          "description": "full original user input"
        }}

        Input: {input}
        """,
        input_variables=["input"]
    )
    formatted = prompt.format(input=user_input)
    raw = llm.invoke([HumanMessage(content=formatted)]).content
    logging.info("LLM RAW OUTPUT:\n" + raw)

    if raw.strip().lower() == "not an expense":
        logging.info("LLM determined this is not an expense.")
        return None

    try:
        expense = parser.parse(raw)
        logging.info(f"Parsed Expense Object: {expense}")
        expense_log.append(expense.model_dump())
        return expense
    except Exception as e:
        logging.error(f"Failed to parse structured expense:\n{raw}\nError: {e}")
        return None

def run_expense_agent(user_message: str, memory=None):
    logging.info(f"Agent invoked with user_message: {user_message}")
    llm = LoggingChatOpenAI(model="gpt-4o", temperature=0.5)
    assistant = get_expense_manager(llm)
    prompt = get_prompt_template()

    if memory is None:
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # First, attempt to log the expense via LLM parser
    expense = extract_expense_from_llm(llm, user_message)
    if expense:
        return f"✅ Logged: R{expense.amount} for {expense.category} on {expense.date}", memory

    # If no structured data found, fall back to agent tools (e.g., summaries, reports)
    agent = create_tool_calling_agent(
        llm=assistant.llm,
        prompt=prompt,
        tools=expense_tools if assistant.tools is None else assistant.tools
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=expense_tools if assistant.tools is None else assistant.tools,
        memory=memory,
        verbose=True
    )

    agent_runnable: Runnable = agent_executor

    response = agent_runnable.invoke({"input": user_message})
    logging.info(f"Agent output: {response['output']}")
    return response["output"], memory

if __name__ == "__main__":
    logging.info("Starting expense manager workflow")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    while True:
        user_message = input("What would you like to do? (type 'exit' or 'quit' to end) ")
        if user_message.strip().lower() in ("exit", "quit"):
            logging.info("User exited the session.")
            break
        reply, memory = run_expense_agent(user_message, memory)
        print(reply)
    logging.info("Workflow complete")
