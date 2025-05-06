# Building with Model Control Protocol (MCP): LLM powered Tutor app

A practical demonstration of the Model Control Protocol (MCP) for building an AI powered  educational system 




### The Problem MCP Solves

Modern AI applications face a fundamental challenge: connecting language models to external tools and data sources. Without a standardized protocol, developers must:

- Create custom integrations for each tool
- Manage complex state between models and tools
- Handle different APIs for each model type
- Maintain duplicated code across projects

The Model Control Protocol provides a unified interface for:
- **Tools**: Actions that perform operations
- **Resources**: Data access through URI schemes
- **Prompts**: Structured conversation templates

### Why This Matters

MCP enables:
- **Separation of Concerns**: Models focus on reasoning, servers handle tools
- **Flexible Architecture**: Multiple transport protocols (SSE, Stdio, HTTP)
- **Ecosystem Growth**: Reusable tools across applications
- **Independent Scaling**: Deploy MCP servers separately from main application

### Practical Approach

This project demonstrates a practical approach to MCP on a real world project:

- We will be working on an AI powered Tutor app using llms and the  MCP protocol.The project is trimmed down  to a level just enough to show case the benefits and capabilities of the this protocol. My primary objective is go beyond a POC and have a realworld implementation.






## System Architecture

### Overview

```
User Interface (CLI)
        ↓
Assistant Module (OpenAI Integration)
        ↓
MCP Client (Protocol Implementation)
        ↓ [HTTP/SSE]
MCP Server (Tools, Resources, Prompts)
        ↓
Data Layer (Profiles, Content, Config)
```



### Step 1.  Setting up the MCP Server

The server exposes capabilities that LLMs can discover and use.

**Tools**: Action-oriented functions
```python
@mcp.tool()
def evaluate_answer(student_answer: str, correct_answer: str) -> dict:
    """Evaluates student responses with detailed feedback"""
    # Implementation...
```

**Resources**: Data access via URIs
```python
@mcp.resource("student://{student_id}")
def get_student_resource(student_id: str) -> str:
    """Access student profiles via URI scheme"""
    # Implementation...
```

**Prompts**: Conversation templates
```python
@mcp.prompt()
def explain_concept(concept: str, level: str) -> list[Message]:
    """Structured prompts for concept explanations"""
    # Implementation...
```

**mcpserver.py**: 
```python
# mcpserver.py (minimal)
from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP(
    name="MyMCPServer",
    host="localhost",
    port=8050,
)

# Define tools
@mcp.tool()
def evaluate_answer(student_answer: str, correct_answer: str) -> dict:
    """
    Evaluates a student's answer against the correct answer.
    """
    #Implementation...    
    return {
        "score": 0.1,
        "feedback": "Your answer is too brief. Please provide more details."
    }        

# Define  resources
# resource Uri:   student://student2
@mcp.resource("student://{student_id}")
def get_student_resource(student_id: str) -> str:
    """
    Provides access to a specific student's profile as a resource.    
    Args:
        student_id: The ID of the student to retrieve        
    Returns:
        JSON string representation of the student profile
    """
    # Implementation...
    return json.dumps(profile, indent =2)

# Define a prompt template
@mcp.prompt()
def explain_concept(concept: str) -> str:
    """Template for explaining concepts."""
    return f"Please explain '{concept}' in simple terms."

# Run the server
if __name__ == "__main__":
    print("MCP Server running on localhost:8050")
    mcp.run(transport="sse")
```

#### Running the server

You can run the server directly
```bash
# Using UV
uv run mcptutor/mcpserver.py

# Or As a python script
python mcptutor/mcpserver.py
```

-The server at this point initializes the capabilities defined  and starts listening at the specified port.
-You should see: MCP Server is running on localhost:8050

I
#### Why SSE Transport?
MCP supports various transports, but Server-Sent Events (SSE) offers several advantages:

1. **Independent Deployment**: MCP server can run as a separate service
2. **Horizontal Scaling:**: Multiple server instances behind load balancers
3. **Stream Processing:**: Real-time data streaming for results
3. **Maintained Connections:**: Persistent connections reduce overhead

Alternatively you can use **stdio transport** if you would like you would like to use the same host for both the client and server.

#### Debugging with MCP Inspector

The MCP Inspector is a valuable tool for testing your server implementation.
```bash
mcp dev mcpserver.py
```

---
With the inspector, you can:

-View available tools, resources, and prompts
-Execute tools with test parameters
-Access resources via URI
-Monitor response formats



### Step 2: Building the MCP Client

The client library connects to the MCP server and makes its capabilities available to your application.

```python
# mcpclient.py (minimal example)
from mcp import ClientSession
from mcp.client.sse import sse_client

async def discover_tools(server_url):
    """Discover available tools on the MCP server."""
    async with sse_client(f"{server_url}/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_result = await session.list_tools()            
            # Convert to format usable by LLMs
            return [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                for tool in tools_result.tools
            ]

async def execute_tool(server_url, tool_name, arguments):
    """Execute a tool on the MCP server."""
    async with sse_client(f"{server_url}/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else None
```

### Step 3  :Building the Assistant
The assistant integrates with OpenAI's API to provide a chat interface that uses MCP tools.
```python
# assistant.py (minimal example)
import asyncio
import json
import openai
import mcpclient

# Config
MCP_SERVER_URL = "http://localhost:8050"
openai.api_key = "your-api-key"

async def main():
    # 1. Discover available tools
    tools = await mcpclient.discover_tools(MCP_SERVER_URL)
    
    # 2. Initialize conversation
    messages = [
        {"role": "system", "content": "You're an assistant with access to external tools."}
    ]
    
    # 3. User input
    user_input = input("You: ")
    messages.append({"role": "user", "content": user_input})
    
    # 4. LLM with tool access
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    assistant_message = response.choices[0].message
    messages.append(assistant_message)
    
    # 5. Handle tool calls
    if assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            # Extract tool details
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Execute the tool via MCP
            tool_result = await mcpclient.execute_tool(
                MCP_SERVER_URL, 
                function_name, 
                function_args
            )
            
            # Add result to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": tool_result
            })
        
        # 6. Get final response
        final_response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        print(f"Assistant: {final_response.choices[0].message.content}")
    else:
        print(f"Assistant: {assistant_message.content}")

if __name__ == "__main__":
    asyncio.run(main())
```
#### Running the Assistant

```bash
# Using UV
uv run mcptutor/assistant.py

# Or As a python script
python mcptutor/assistant.py
```


#### Development Tips

1. **Start with MCP Inspectort**: Start with MCP Inspector: Verify your server works before building the client
2. **Use Minimal Tools First**: Begin with 1-2 simple tools, then expand
3. **Error Handling**: MCP tools should return structured errors, not exceptions
4. **Resource Design**: Use consistent URI patterns for resources
5. **Test Thoroughly**: Each tool should handle edge cases gracefully


### Testing the System
With the server running in one terminal and the assistant in another, you can test:

#### Using Tools Automatically
```python

You: give me an algebra question

- LLM Processing -
LLM decided to use tools:
  - Calling: generate_question with args: {'topic': 'algebra', 'difficulty': 'medium'}

- MCP Tool Execution -
Tool result: {"question": "Solve for x: 3x - 7 = 2x + 5", "answer": "x = 12"}

- Final LLM Response -

Assistant: Here is a question for you: 

Solve for x in the equation: 3x - 7 = 2x + 5

```

#### Accessing a Resource

```python
You: /resource student://student1

Resource content:
{
  "id": "student1",
  "name": "Abebe Kebede",
  "grade_level": 12,
  "subjects_of_interest": [
    "maths",
    "biology"
  ],
  "learning_style": "visual",  
  ... 
}

```

#### MCP Inspector 
![mcpinspector](https://github.com/user-attachments/assets/521a2697-7344-42ca-aa34-3e851813dbc3)


#### Assistant Terminal
![assistantterminal](https://github.com/user-attachments/assets/0507bae7-0d97-481f-b65b-a9f8e3511518)

#### Connect

• [LinkedIn: Yoseph Lemma](https://www.linkedin.com/in/yberhanu/)  

