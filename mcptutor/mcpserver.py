from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
import random
import time
import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional


#load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))


# Get these from env variables
HOST = "localhost"
PORT = 8050


# Get the current directory to locate content files
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(CURRENT_DIR, "content")

# Create an MCP server
mcp = FastMCP(
    name="EducTools",
    host=HOST,
    port=PORT,
)

print(f"Starting MCP server with educ tools on {HOST}:{PORT}...")

# Simple in-memory database for student profiles (placeholder for real DB)
STUDENT_PROFILES = {
    "student1": {
        "id": "student1",
        "name": "Abebe Kebede",
        "grade_level": 12,       
        "subjects_of_interest": ["maths", "biology"],
        "learning_style": "visual",
        "difficulty_preference": "medium",
        "completed_topics": ["algebra", "photosynthesis"],
        "learning_goals": ["get ready for escle exam","improve understanding"],
        "performance_metrics": {
            "algebra": {"score": 7.5, "progress": "85%"},
            "science": {"score": 8.2, "progress": "90%"}
        },
        "last_session": "2025-05-03",
        "total_study_time": "23 hours"
    },
    "student2": {
        "id": "student2",
        "name": "Almaz Alemayehu",
        "grade_level": 12,        
        "subjects_of_interest": ["maths", "biology"],
        "learning_style": "reading",
        "difficulty_preference": "hard",
        "completed_topics": ["algebra", "photosynthesis"],
        "learning_goals": ["be a top performer in escle exam", "be a top performer in escle exam"],
        "performance_metrics": {
            "chemistry": {"score": 9.1, "progress": "92%"},
            "literature": {"score": 8.5, "progress": "88%"}
        },
        "last_session": "2025-05-04",
        "total_study_time": "31 hours"
    }
}

# -----  Tools -----
@mcp.tool()
def evaluate_answer(student_answer: str, correct_answer: str) -> dict:
    """
    Evaluates a student's answer against the correct answer.
    """
    # Simulate some processing time
    time.sleep(0.5)
    
    # Simple comparison logic
    words1 = set(student_answer.lower().split())
    words2 = set(correct_answer.lower().split())
    
    if not words1 or not words2:
        return {
            "score": 0.1,
            "feedback": "Your answer is too brief. Please provide more details."
        }
        
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    similarity = len(intersection) / len(union)
    
    if similarity > 0.7:
        return {
            "score": 0.9,
            "feedback": "Excellent answer! You've demonstrated a thorough understanding."
        }
    elif similarity > 0.4:
        return {
            "score": 0.6,
            "feedback": "Good attempt! You've understood the main concepts but missed some details."
        }
    else:
        return {
            "score": 0.3,
            "feedback": "You need to review this topic. Try focusing on the key concepts."
        }

@mcp.tool()
def generate_question(topic: str, difficulty: str) -> dict:
    """
    Generates a question based on topic and difficulty level.
    """
    # Simulate processing time
    time.sleep(0.5)
    
    questions = {
        "photosynthesis": {
            "easy": {
                "question": "What gas do plants absorb during photosynthesis?",
                "answer": "Carbon dioxide (CO2)"
            },
            "medium": {
                "question": "What are the two main products of photosynthesis?",
                "answer": "Glucose (sugar) and oxygen"
            },
            "hard": {
                "question": "Explain the role of chlorophyll in photosynthesis.",
                "answer": "Chlorophyll is the green pigment in plants that absorbs light energy, primarily from the blue and red parts of the spectrum. This absorbed energy is used to power the chemical reactions that convert CO2 and water into glucose and oxygen."
            }
        },
        "algebra": {
            "easy": {
                "question": "Solve for x: x + 5 = 12",
                "answer": "x = 7"
            },
            "medium": {
                "question": "Solve for x: 3x - 7 = 2x + 5",
                "answer": "x = 12"
            },
            "hard": {
                "question": "Solve the system of equations: 2x + y = 7 and 3x - 2y = 8",
                "answer": "x = 3, y = 1"
            }
        }
    }
    
    # Default response if topic/difficulty not found
    default_response = {
        "question": f"Please explain what you know about {topic}.",
        "answer": "This would be evaluated based on completeness and accuracy."
    }
    
    # Try to get the question, or return default
    return questions.get(topic, {}).get(difficulty, default_response)

@mcp.tool()
def get_hint(topic: str, question: str) -> str:
    """
    Provides a hint for a given question to help students.
    """
    # Simulate processing time
    time.sleep(0.5)
    
    hints = {
        "photosynthesis": [
            "Think about the gases involved in the process.",
            "Remember that plants use sunlight as an energy source.",
            "Consider what raw materials plants need to grow."
        ],
        "algebra": [
            "Try isolating the variable on one side of the equation.",
            "Remember to perform the same operation on both sides.",
            "For systems of equations, try substitution or elimination."
        ]
    }
    
    # Get hints for the topic or use general hints
    topic_hints = hints.get(topic, [
        "Try breaking down the problem into smaller parts.",
        "Review the key definitions related to this topic.",
        "Think about similar problems you've solved before."
    ])
    
    # Return a random hint
    return random.choice(topic_hints)

@mcp.tool()
def get_student_profile(student_id: str) -> Dict[str, Any]:
    """
    Retrieves the full profile of a student including their learning preferences, 
    progress, and performance metrics.
    
    Args:
        student_id: Unique identifier for the student
        
    Returns:
        Dictionary containing the student's profile information or error message
    """
    # Simulate some processing time
    time.sleep(0.3)
    
    profile = STUDENT_PROFILES.get(student_id)
    if profile:
        return {
            "status": "success",
            "profile": profile,
            "message": f"Successfully retrieved profile for {profile['name']}"
        }
    else:
        return {
            "status": "error",
            "message": f"No profile found for student_id: {student_id}",
            "available_students": list(STUDENT_PROFILES.keys())
        }



# ----- Educational Resources -----

# e.g.  topic://algebra
@mcp.resource("topic://{topic}")
def get_topic_resource(topic: str) -> str:
    """
    Provides educational content for a subject.
    
    Args:
        subject: The topic to get content for (e.g., 'algebra', 'photosynthesis')
        
    Returns:
        The content of the subject as markdown text
    """
    try:
        file_path = os.path.join(CONTENT_DIR, f"{topic.lower()}.md")
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"No content available for {topic}."

# resource://students
@mcp.resource("resource://students")
def get_all_student_profiles() -> str:
    """
    Provides access to all student profiles in the system.
    This resource returns a JSON string of all available student profiles.
    """
    
    return json.dumps(STUDENT_PROFILES, indent=2)
    
 
# e.g  student://student2
@mcp.resource("student://{student_id}")
def get_student_resource(student_id: str) -> str:
    """
    Provides access to a specific student's profile as a resource.
    
    Args:
        student_id: The ID of the student to retrieve
        
    Returns:
        JSON string representation of the student profile
    """
    profile = STUDENT_PROFILES.get(student_id)
    if profile:
        return json.dumps(profile, indent=2)
    else:
        return json.dumps({
            "error": f"Student profile not found for ID: {student_id}",
            "available_students": list(STUDENT_PROFILES.keys())
        }, indent=2)



# ----- MCP PROMPTS -----
@mcp.prompt()
def evaluate_student_work(answer: str) -> str:
    """
    Prompt template for evaluating student work.
    
    Args:
        answer: The student's answer to evaluate
        
    Returns:
        A structured prompt for evaluation
    """
    return f"""Please evaluate this student's answer carefully:

Answer: {answer}

Provide feedback on:
1. Correctness - Is the answer factually accurate?
2. Completeness - Did they address all parts of the question?
3. Clarity - Is the explanation clear and well-structured?
4. Areas for improvement
"""

@mcp.prompt()
def explain_concept(concept: str, level: str) -> list[base.Message]:
    """
    Prompt for detailed explanation of a concept.
    
    Args:
        concept: The concept to explain
        level: The student level (needs work, medium, advanced)
        
    Returns:
        A conversation template for explaining concepts
    """
    return [
        base.UserMessage(f"Please explain '{concept}' at a {level} level."),
        base.UserMessage("Include relevant examples and analogies where helpful."),
        base.AssistantMessage(f"I'll explain {concept} in a way that's appropriate for {level} students.")
    ]




# Run the server with SSE 
if __name__ == "__main__":
    print(f"MCP Server is running on {HOST}:{PORT}") 
    print("\nPress Ctrl+C to stop the server")    
    mcp.run(transport="sse")