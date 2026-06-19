from google import genai

from google.genai import types

from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

from pydantic import BaseModel

class ResumeAnalysis(BaseModel):
    summary: str
    skills: list[str]
    feedback: str


def gemini_content_generator(file_path: str, mime_type: str):
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    print(file_bytes)
    prompt = """
            Role: 
            You are a Senior Recruiter and Talent Acquisition Strategist. Your role is about analyzing the resume and find out crucial information regarding the candidate.
            
            Task:
            Analyze the resume_text objectively to provide high-signal, actionable feedback for the hiring manager and interview panel, find missing gaps, discrepancies, omissions, or hidden weaknesses if there are.

            Rules: 
            Provide your analysis structured exactly against the required schema:
            1. SUMMARY: A dense, 3-4 sentence professional profile. Quantify impact where possible. Absolutely zero generic corporate buzzwords.
            2. SKILLS: Categorized extraction of technical and soft skills. Only include skills backed by concrete evidence.
            3. FEEDBACK: Focus on high-leverage achievements, short tenures, sudden role shifts, stagnant progression, or lack of ownership metrics.
            """
            
    # Prepare the payload so it's identical for both calls
    # Wrapping the file bytes in types.Part.from_bytes()
    file_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    contents_payload = [file_part, prompt]

    # 1. Count Tokens
    token_count = client.models.count_tokens(
        model="gemini-2.5-flash",
        contents=contents_payload
    )
    print(f"Total tokens: {token_count.total_tokens}")
    
    # 2. Generate Content (Fixed: contents_payload now includes the file)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents_payload,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResumeAnalysis,
        )
    )

    return response.parsed


# import re


# def add_numbers(a: int, b: int):
#     print('add_number called whee',a,b)
#     """
#     Tool function that performs addition.
#     """
#     return a + b


# # Tool registry
# TOOLS = {
#     "add_numbers": add_numbers
# }



# # -----------------------------
# # ReAct Prompt
# # -----------------------------
# REACT_PROMPT = """
# You are a ReAct reasoning agent.

# You have access to this tool:

# add_numbers(a, b)

# Description:
# Adds two numbers and returns the result.

# Your job is to decide when a tool is needed.

# IMPORTANT:
# - You do not execute tools yourself.
# - You do not create Observation.
# - You do not create the final Answer until an Observation is provided.
# - After providing an Action, stop and wait for the tool result.

# Follow this process:

# Step 1:
# Think about what needs to be done.

# Step 2:
# If a tool is required, output only the Action.

# Format:

# Thought:
# <what you need to figure out>

# Action:
# <tool_name(arguments)>


# After the system executes the tool, it will provide:

# Observation:
# <tool result>


# Only after receiving an Observation, continue:

# Thought:
# <interpret the observation>

# Answer:
# <final answer>


# Rules:
# - Use tools only when a calculation or external operation is required.
# - Do not perform calculations yourself when a tool is available.
# - Do not create Observation yourself. Observation will be provided by the system after tool execution.
# - After receiving an Observation, check whether the original question has been solved.
# - If the answer can be determined from the Observation, immediately provide the Answer.
# - Do not call the same tool with the same arguments more than once.
# - Do not repeat a previous Action.
# - Use previous Observations as memory and do not recalculate already solved steps.
# - Do not request another tool call after the final result is known.
# - Do not invent tool results.
# - Stop when the final answer is available.
# """


# # -----------------------------
# # Parse Action
# # -----------------------------

# def parse_action(text):
#     """
#     Extract tool call from Gemini response.

#     Supports:
#     add_numbers(10, 12)
#     add_numbers(a=10, b=12)
#     """

#     pattern = r"add_numbers\((?:a=)?(\d+),\s*(?:b=)?(\d+)\)"

#     match = re.search(pattern, text)

#     if match:

#         return "add_numbers", {
#             "a": int(match.group(1)),
#             "b": int(match.group(2))
#         }

#     return None, None


# # -----------------------------
# # Execute Tool
# # -----------------------------

# def execute_tool(tool_name, args):
#     """
#     Executes the requested tool.
#     """

#     if tool_name not in TOOLS:
#         return "Tool not found"


#     tool = TOOLS[tool_name]

#     return tool(**args)



# # -----------------------------
# # ReAct Loop
# # -----------------------------

# def run_react_agent( question):
#     """
#     Runs the Thought -> Action -> Observation loop.
#     """

#     conversation = f"""
# {REACT_PROMPT}

# Question:
# {question}
# """


#     for _ in range(5):

#         # Ask Gemini what to do next
#         response = client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=conversation
#         )


#         output = response.text


#         # If Gemini has final answer, stop
#         if "Answer:" in output:
#             return output



#         # Extract tool request
#         tool_name, args = parse_action(output)


#         # No valid action found
#         if not tool_name:
#             return output



#         # Run tool
#         observation = execute_tool(
#             tool_name,
#             args
#         )


#         # Add result back into context
#         conversation += f"""

# {output}

# Observation:
# {observation}

# """


#     return "Maximum iterations reached"