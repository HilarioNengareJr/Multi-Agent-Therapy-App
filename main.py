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
from tools import therapy_tools
from langchain.memory import ConversationBufferMemory
import logging



load_dotenv()

logging.basicConfig(level=logging.INFO)

# Therapist schema
class Therapist(BaseModel):
    name: str
    role: str
    description: str
    tone: str
    specialties: list[str]
    techniques: list[str]
    greeting_style: str
    response_style: str
    llm: BaseLanguageModel
    tools: Optional[List[BaseTool]] = None
    memory: Optional[BaseMemory] = None

# Therapist configuration
def get_therapist(llm: BaseLanguageModel) -> Therapist:
    return Therapist(
        name="Dr. Jade Wyatt",
        role="Grief Counselor",
        description="A compassionate and experienced grief counselor specializing in helping individuals navigate the complexities of loss and bereavement.",
        tone="Gentle",
        specialties=["Grief Counseling", "Trauma Recovery", "Cognitive Behavioral Therapy"],
        techniques=["Mindfulness", "Acceptance Therapy", "Cognitive Restructuring"],
        greeting_style="Warm and welcoming",
        response_style="Reflective and Empathetic",
        llm=llm
    )

# Prompt template
def get_prompt_template():
    response_guidelines = """ 
    - Respond warmly and supportively
    - Use soft and appropriate emojis like 🌱, 💬, 💛, 🧘‍♀️, 🌼 when comforting the user
    - Avoid sounding robotic; write like a caring human would speak
    - Do not overuse emojis — 1–2 per response max, and only when it fits naturally
    - Never be cold or clinical, always validate the user’s feelings
    - Match your tone to their emotional state gently """
    return ChatPromptTemplate.from_template(
        f"""
        You are a therapist named Dr. Jade Wyatt.
        Your role is: Grief Counselor.
        Your description is: A compassionate and experienced grief counselor specializing in helping individuals navigate the complexities of loss and bereavement.
        Your tone is: Gentle.
        Your specialties are: Grief Counseling, Trauma Recovery, Cognitive Behavioral Therapy.
        Your techniques are: Mindfulness, Acceptance Therapy, Cognitive Restructuring.
        Your greeting style is: Warm and welcoming.
        Your response style is: Reflective and Empathetic.
        You will respond to the user's message using your expertise and techniques.
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

# Agent logic
def run_therapy_agent(user_message: str, memory=None):
    logging.info(f"Agent invoked with user_message: {user_message}")
    llm = LoggingChatOpenAI(model="gpt-4o", temperature=0.7)
    therapist = get_therapist(llm)
    prompt = get_prompt_template()

    if memory is None:
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    agent = create_tool_calling_agent(
        llm=therapist.llm,
        prompt=prompt,
        tools=therapy_tools if therapist.tools is None else therapist.tools
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=therapy_tools if therapist.tools is None else therapist.tools,
        memory=memory,
        verbose=True
    )

    agent_runnable: Runnable = agent_executor

    response = agent_runnable.invoke({"input": user_message})
    logging.info(f"Agent output: {response['output']}")
    return response["output"], memory

if __name__ == "__main__":
    logging.info("Starting therapy agent workflow")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    while True:
        user_message = input("How can I assist you today? (type 'exit' or 'quit' to end) ")
        if user_message.strip().lower() in ("exit", "quit"):
            logging.info("User exited the session.")
            break
        reply, memory = run_therapy_agent(user_message, memory)
        print(reply)
    logging.info("Workflow complete")