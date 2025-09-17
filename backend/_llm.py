import os
import json
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from prompts import EXTRACTOR_PROMPT

# =======================
# STATE
# =======================
class State(TypedDict):
    messages: Annotated[list, add_messages]
    pro: str
    con: str

# =======================
# LLM SETUP
# =======================
os.environ["LANGSMITH_TRACKING"] = os.getenv("LANGSMITH_TRACKING", "true")
BASE_MODEL = os.environ.get("GOOGLE_MODEL_CODENAME", "gemini-2.0-flash-lite")

# System prompts for each side
PRO_SYSTEM_PROMPT = """You are the PRO advocate in a debate. Your role is to argue for the positive position on any given question. 
Build the strongest case possible for your side. Consider this a formal debate that you need to win.
Your opponent will argue the opposite side, and it's his responsibility to attack you, not yours to find faults in your own argument.
Be concise and persuasive: answer with a short intro, then outline your arguments as self-contained points, then outro that summarizes your position.
Focus on benefits, advantages, and positive aspects of the topic."""

CON_SYSTEM_PROMPT = """You are the CON advocate in a debate. Your role is to argue for the negative position on any given question.
Build the strongest case possible for your side. Consider this a formal debate that you need to win.
Your opponent will argue the opposite side, and it's his responsibility to attack you, not yours to find faults in your own argument.
Be concise and persuasive: answer with a short intro, then outline your arguments as self-contained points, then outro that summarizes your position.
Focus on drawbacks, disadvantages, and negative aspects of the topic."""

# Extractor uses tool calling
@tool
def extract_pro_con(question: str) -> dict:
    """Extracts pro and con positions from a binary decision question."""
    return {"pro": "Positive side argument", "con": "Negative side argument"}

extractor_llm = ChatGoogleGenerativeAI(
    model=BASE_MODEL,
    temperature=0,
    max_output_tokens=200,
)

# Advocates are plain chat models
pro_llm = ChatGoogleGenerativeAI(model=BASE_MODEL, temperature=0, max_output_tokens=250)
con_llm = ChatGoogleGenerativeAI(model=BASE_MODEL, temperature=0, max_output_tokens=250)

# =======================
# NODES
# =======================
def extractor(state: State):
    """Extract pro and con. Halt if not applicable."""
    user_msg = state["messages"][-1].content
    prompt = EXTRACTOR_PROMPT.format(user_msg=user_msg)
    result = extractor_llm.invoke(prompt)
    try:
        result_dict = json.loads(result.content)
        pro = result_dict.get("pro", "").strip()
        con = result_dict.get("con", "").strip()
    except json.JSONDecodeError:
        pro, con = "", ""
    
    # Ensure valid dict is returned
    return {"pro": pro, "con": con}

def pro_node(state: State):
    """PRO advocate node with system message and only the original question"""
    # Get the original human question
    original_question = None
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            original_question = msg.content
            break
    
    if not original_question:
        original_question = state["messages"][-1].content
    
    # Create messages with system prompt and only the original question
    messages = [
        SystemMessage(content=PRO_SYSTEM_PROMPT),
        HumanMessage(content=original_question)
    ]
    
    res = pro_llm.invoke(messages)
    return {"messages": [res]}

def con_node(state: State):
    """CON advocate node with system message and only the original question"""
    # Get the original human question
    original_question = None
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            original_question = msg.content
            break
    
    if not original_question:
        original_question = state["messages"][-1].content
    
    # Create messages with system prompt and only the original question
    messages = [
        SystemMessage(content=CON_SYSTEM_PROMPT),
        HumanMessage(content=original_question)
    ]
    
    res = con_llm.invoke(messages)
    return {"messages": [res]}

# =======================
# GRAPH
# =======================
graph_builder = StateGraph(State)
# graph_builder.add_node("extractor", extractor)
graph_builder.add_node("pro", pro_node)
graph_builder.add_node("con", con_node)

# graph_builder.add_edge(START, "extractor")
# graph_builder.add_edge("extractor", "pro")
graph_builder.add_edge(START, "pro")
graph_builder.add_edge("pro", "con")
graph_builder.add_edge("con", END)

graph = graph_builder.compile()

# =======================
# RUN
# =======================
def stream_graph_updates(user_input: str):
    # Start with a HumanMessage containing the debate question
    initial_state = {
        "messages": [HumanMessage(content=user_input)]
    }
    
    events = graph.stream(initial_state)
    for event in events:
        for node_name, value in event.items():
            if "messages" in value:
                # Identify which side is speaking
                side = "PRO" if node_name == "pro" else "CON"
                print(f"{side} Argument:", value["messages"][-1].content)
                print("-" * 50)

if __name__ == "__main__":
    user_input = "Do you think Lay's chips are healthy?"
    print("Debate Question:", user_input)
    print("=" * 50)
    stream_graph_updates(user_input)