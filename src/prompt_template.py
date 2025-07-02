from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from models import ErgData

system_prompt = """
You are an expert at reading rowing ergometer screen images and extracting workout data.
"""

# Use LangChain's PydanticOutputParser to generate format instructions
parser = PydanticOutputParser(pydantic_object=ErgData)
format_instructions = parser.get_format_instructions()
escaped_format_instructions = format_instructions.replace("{", "{{").replace("}", "}}")

user_prompt = f"""
Given the attached erg screen image, extract the following as JSON:

- summary: total distance, total time, average split, average rate, average HR (if available)
- splits: for each split, extract split number, split distance, split time, split pace, rate, HR (if available)

Output only valid JSON in the following format:
{escaped_format_instructions}

Image path: {{image_path}}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt)
])

# Basic prompt for the new responses.parse method
BASIC_PROMPT = """
You are an expert at reading rowing ergometer screen images and extracting workout data.

Given the attached erg screen image, extract the following structured data:

1. Summary information:
   - total_distance: The total distance rowed (in meters)
   - total_time: The total time taken (in MM:SS.S format)
   - average_split: The average split time (in MM:SS.S format)
   - average_rate: The average stroke rate (strokes per minute)
   - average_hr: The average heart rate (if available)

2. Split breakdown:
   - For each split, extract:
     - split_number: The split number (1, 2, 3, etc.)
     - split_distance: The distance for this split (in meters)
     - split_time: The time for this split (in MM:SS.S or :SS.S format)
     - split_pace: The pace for this split (in MM:SS.S format)
     - rate: The stroke rate for this split (strokes per minute)
     - hr: The heart rate for this split (if available)

Please extract all visible data from the ergometer screen image accurately.
""" 