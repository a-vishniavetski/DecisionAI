import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

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

# Shared system prompt
BASE_SYSTEM_PROMPT = """You are participating in a formal debate. The goal is to choose a decision from a binary choice, based on the input information provided.
Build the strongest case possible for your assigned side. 
Don't try to find flaws in your own position - Your opponent will argue the opposite side, and it's his responsibility to do so.
Consider this a debate that you need to win. 
Be concise and persuasive: answer with a short intro, then outline your arguments as self-contained points, then outro that summarizes your position.

This is how the debate works: The PRO side presents their position first, arguing for the positive/affirmative position. 
The CON side then responds, arguing for the negative position and can directly counter the PRO arguments.

Do not make addresses, greetings, or apologies. Focus solely on the arguments."""

# Judge system prompt
JUDGE_SYSTEM_PROMPT = """You are an impartial judge in a formal debate. 
Your task is to evaluate the strength of the arguments presented by both sides and determine 
the winner based on the quality of their reasoning and evidence, and those alone.

Be consice, objective and present the user with the final decision."""

# Advocates are plain chat models
pro_llm = ChatGoogleGenerativeAI(model=BASE_MODEL, temperature=0, max_output_tokens=250)
con_llm = ChatGoogleGenerativeAI(model=BASE_MODEL, temperature=0, max_output_tokens=250)
judge_llm = ChatGoogleGenerativeAI(model=BASE_MODEL, temperature=0, max_output_tokens=300)

# =======================
# NODES
# =======================
def pro_node(state: State):
    """PRO advocate node - presents the opening position"""
    # Get the original human question
    original_question = None
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            original_question = msg.content
            break
    
    if not original_question:
        original_question = state["messages"][-1].content
    
    # Create messages with system prompt, side assignment, and original question
    messages = [
        SystemMessage(content=BASE_SYSTEM_PROMPT),
        HumanMessage(content=f"Your side: PRO\n\nDebate question: {original_question}")
    ]
    
    res = pro_llm.invoke(messages)
    return {"messages": [res]}

def con_node(state: State):
    """CON advocate node - responds to PRO and argues against"""
    # Get the original human question
    original_question = None
    pro_argument = None
    
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            original_question = msg.content
        elif isinstance(msg, AIMessage) and pro_argument is None:
            # First AI message should be from PRO
            pro_argument = msg.content
    
    if not original_question:
        original_question = state["messages"][-1].content
    
    # Create messages with system prompt, side assignment, original question, and PRO argument to counter
    prompt_content = f"Your side: CON\n\nDebate question: {original_question}"
    if pro_argument:
        prompt_content += f"\n\nThe PRO side has argued:\n{pro_argument}\n\nNow present your counter-argument."
    
    messages = [
        SystemMessage(content=BASE_SYSTEM_PROMPT),
        HumanMessage(content=prompt_content)
    ]
    
    res = con_llm.invoke(messages)
    return {"messages": [res]}


def judge_node(state: State):
    """Judge node - evaluates both sides and declares a winner"""
    # Get the original human question, PRO argument, and CON argument
    original_question = None
    pro_argument = None
    con_argument = None
    
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            original_question = msg.content
        elif isinstance(msg, AIMessage):
            if pro_argument is None:
                pro_argument = msg.content
            elif con_argument is None:
                con_argument = msg.content
    
    if not original_question:
        original_question = state["messages"][-1].content
    
    # Create messages with system prompt, original question, PRO argument, and CON argument
    prompt_content = f"Debate question: {original_question}\n\n"
    if pro_argument:
        prompt_content += f"PRO side argued:\n{pro_argument}\n\n"
    if con_argument:
        prompt_content += f"CON side argued:\n{con_argument}\n\n"
    
    prompt_content += "Based on the arguments presented, evaluate the strength of each side and declare the winner (PRO or CON). Provide a brief explanation for your decision. End your message with a 'You should ...' and then spell out the decision."
    
    messages = [
        SystemMessage(content=JUDGE_SYSTEM_PROMPT),
        HumanMessage(content=prompt_content)
    ]
    
    res = judge_llm.invoke(messages)
    return {"messages": [res]}

# =======================
# GRAPH
# =======================
graph_builder = StateGraph(State)
graph_builder.add_node("pro", pro_node)
graph_builder.add_node("con", con_node)
graph_builder.add_node("judge", judge_node)

graph_builder.add_edge(START, "pro")
graph_builder.add_edge("pro", "con")
graph_builder.add_edge("con", "judge")
graph_builder.add_edge("judge", END)

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
                if node_name == "pro":
                    side = "PRO" 
                elif node_name == "con":
                    side = "CON"
                elif node_name == "judge":
                    side = "JUDGE"
                print(f"{side} Argument:", value["messages"][-1].content)
                print("-" * 50)

if __name__ == "__main__":
    # user_input = "Do you think Lay's chips are healthy?"
    user_input = input("Enter a debate question: ")
    print("=" * 50)
    stream_graph_updates(user_input)