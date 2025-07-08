from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Optional 
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langchain_core.memory import BaseMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import tool_calling_agent


load_dotenv()

# setting a prompt template
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

llm = ChatOpenAI(model="gpt-4o", temperature=0.7) 

parser = PydanticOutputParser(pydantic_object=Therapist)

response_guidelines = """ 
    - Respond warmly and supportively
    - Use soft and appropriate emojis like 🌱, 💬, 💛, 🧘‍♀️, 🌼 when comforting the user
    - Avoid sounding robotic; write like a caring human would speak
    - Do not overuse emojis — 1–2 per response max, and only when it fits naturally
    - Never be cold or clinical, always validate the user’s feelings
    - Match your tone to their emotional state gently """

prompt = ChatPromptTemplate.from_template(
        """
        You are a therapist named {name}.
        Your role is: {role}.
        Your description is: {description}.
        Your tone is: {tone}.
        Your specialties are: {specialties}.
        Your techniques are: {techniques}.
        Your greeting style is: {greeting_style}.
        Your response style is: {response_style}.
        You will respond to the user's message using your expertise and techniques.
        Always follow these response guidelines: {response_guidelines}.
        The user says: {user_message}
        """
)

therapist = Therapist(
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

user_message = "why do I miss her so much? It's been months and I still feel this emptiness inside. I thought time would help, but it just seems to get harder. I don't know how to cope with this pain anymore."

formatted_prompt = prompt.format_messages(
    name=therapist.name,
    role=therapist.role,
    description=therapist.description,
    tone=therapist.tone,
    specialties=", ".join(therapist.specialties),
    techniques=", ".join(therapist.techniques), 
    greeting_style=therapist.greeting_style,
    response_style=therapist.response_style,
    response_guidelines=response_guidelines,
    user_message=user_message
)

response = therapist.llm.invoke(formatted_prompt)
print(response.content)