
import os
import json
import asyncio
import nest_asyncio
import openai
from dotenv import load_dotenv
import mcpclient


nest_asyncio.apply()

# Load environment variables from root .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# MCP Server URL - without the /sse part, our mcpclient will add it
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8050")

async def chat_with_assistant():
    """Run a chat session with the assistant"""
    # Step 1: Initialize - Discover what the server offers
    print("\n--- Step 1: Discovery Phase ---")
    print(f"Discovering capabilities from MCP server at {MCP_SERVER_URL}...")
    
    # Discover tools
    openai_tools = await mcpclient.discover_tools(MCP_SERVER_URL)
    if not openai_tools:
        print("No tools discovered. Please start the MCP server first.")
        return
    
    # List resources
    resources = await mcpclient.list_resources(MCP_SERVER_URL)
    print(f"Discovered {len(resources)} resources")
    
    # List prompts
    prompts = await mcpclient.list_prompts(MCP_SERVER_URL)
    print(f"Discovered {len(prompts)} prompts")
    
    # Step 2: Initialize chat 
    print("\n--- Step 2: Starting Chat Session ---")
    print("Type 'exit' to quit the chat")
    print("Special commands:")
    print("  - '/resource <uri>' to use a resource")
    print("  - '/prompt <name> <arg1:value1> <arg2:value2>' to use a prompt")   
    print("  - '/help' to show this help message")
    
    # Create an ongoing conversation
    messages = [
        {"role": "system", "content": """You are an educational assistant that helps students learn. 
You have access to:
1. Educational tools for generating questions, providing hints, and evaluating answers
2. Rich educational content provided through resources
3. Structured prompts for common educational tasks

Always use the most appropriate tool, resource, or prompt to provide the best educational experience."""}
    ]
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
        
        # Check for special commands
        if user_input.startswith('/'):
            command_parts = user_input.split()
            command = command_parts[0].lower()
            
            if command == '/help':
                print("Special commands:")
                print("  - '/resource <uri>' to use a resource")
                print("  - '/prompt <name> <arg1:value1> <arg2:value2>' to use a prompt")               
                print("  - '/help' to show this help message")
                continue               

                
            elif command == '/resource' and len(command_parts) >= 2:
                resource_uri = command_parts[1]
                try:
                    print(MCP_SERVER_URL, " resource_uri:", resource_uri)
                    resource_content = await mcpclient.read_resource(MCP_SERVER_URL, resource_uri)
                    print(f"\nResource content:\n{resource_content}")
                    
                    # Also add to the conversation if user wants
                    add_to_chat = input("\nAdd this resource to the chat? (y/n): ")
                    if add_to_chat.lower() == 'y':
                        messages.append({"role": "user", "content": f"\n\n{resource_content}"})
                        print("Resource added to chat.")
                except Exception as e:
                    print(f"Error reading resource: {e}")
                continue
                
            elif command == '/prompt' and len(command_parts) >= 2:
                prompt_name = command_parts[1]
                prompt_args = {}
                
                # Parse arguments in format arg:value
                for arg_value in command_parts[2:]:
                    if ':' in arg_value:
                        arg, value = arg_value.split(':', 1)
                        prompt_args[arg] = value
                
                try:
                    prompt_content = await mcpclient.get_prompt(MCP_SERVER_URL, prompt_name, prompt_args)
                    print(f"\nPrompt content:\n{prompt_content}")
                    
                    # Also add to the conversation if user wants
                    add_to_chat = input("\nAdd this prompt to the chat? (y/n): ")
                    if add_to_chat.lower() == 'y':
                        messages.append({"role": "user", "content": prompt_content})
                        print("Prompt added to chat.")
                except Exception as e:
                    print(f"Error getting prompt: {e}")
                continue
        
        # Regular input - add to conversation
        messages.append({"role": "user", "content": user_input})
        
        # Step 3: LLM decides what to do
        print("\n--- Step 3: LLM Processing ---")
        response = openai.chat.completions.create(
            model="gpt-4", 
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        messages.append(assistant_message)
        
        # Step# Step 4: Check if LLM wants to use a tool
        if assistant_message.tool_calls:
            print("LLM decided to use tools:")
            
            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"  - Calling: {function_name} with args: {function_args}")
                
                # Step 5: MCP Client invokes  the tool on the MCP Server
                print("\n--- Step 4: MCP Tool Execution ---")
                tool_result = await mcpclient.execute_tool(MCP_SERVER_URL, function_name, function_args)
                print(f"Tool result: {tool_result}")
                
                # Step 6: Send tool result back to LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_result
                })
            
            # Step 7: Get final response from LLM with tool results
            print("\n--- Step 5: Final LLM Response ---")
            final_response = openai.chat.completions.create(
                model="gpt-4", 
                messages=messages
            )
            
            final_message = final_response.choices[0].message
            messages.append(final_message)
            
            # Print the assistant's response
            print(f"\nAssistant: {final_message.content}")
        else:
            # LLM didn't use any tools, just print the response
            print(f"\nAssistant: {assistant_message.content}")

if __name__ == "__main__":
    asyncio.run(chat_with_assistant())