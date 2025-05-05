import asyncio
import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client


nest_asyncio.apply()

def format_server_url(url):
    """
    Formats the server URL to ensure it ends with /sse
    """
    # If it already has /sse, we're good
    if url.endswith('/sse'):
        return url
    
    # If it has a trailing slash, add sse
    if url.endswith('/'):
        return f"{url}sse"
    
    # Otherwise add /sse
    return f"{url}/sse"

async def discover_tools(server_url):
    """
    Discover the tools available on the MCP server.
    
    Args:
        server_url: URL of the MCP server (with or without /sse)
    
    Returns:
        List of tools formatted for OpenAI
    """
    # Format the URL to ensure it has /sse
    formatted_url = format_server_url(server_url)
    print(f"Connecting to MCP server at {formatted_url}")
    
    try:
        async with sse_client(formatted_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                
                # List available tools
                tools_result = await session.list_tools()
                
                # Convert to OpenAI format
                openai_tools = []
                print(f"Discovered {len(tools_result.tools)} tools:")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description or 'No description'}")
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema
                        }
                    })
                
                return openai_tools

    except Exception as e:
        print(f"Regular exception: {type(e).__name__}: {e}")
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"Caused by: {e.__cause__}")
        
        import traceback
        print(f"Traceback: {traceback.format_tb(e.__traceback__)}")
        return []

async def execute_tool(server_url, tool_name, arguments):
    """
    Execute a tool on the MCP server.
    
    Args:
        server_url: URL of the MCP server (with or without /sse)
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool
        
    Returns:
        Result of the tool execution
    """
    # Format the URL to ensure it has /sse
    formatted_url = format_server_url(server_url)
    
    try:
        async with sse_client(formatted_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                
                # Call the tool
                result = await session.call_tool(tool_name, arguments)
                
                # Extract the result
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return None
    except Exception as e:
        print(f"Error executing tool {tool_name}: {e}")
        return f"Error: {str(e)}"


#Resources
async def list_resources(server_url):
    """
    List available resources from the MCP server.
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        Dictionary with resource information
    """
    formatted_url = format_server_url(server_url)
    
    try:
        async with sse_client(formatted_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                
                # List available resources
                resources_result = await session.list_resources()                
                
                for resource in resources_result.resources:
                    print(f"  - {resource.name}: {resource.description or 'No description'}")
                
                return resources_result.resources
    except Exception as e:
        print(f"Error listing resources: {e}")
        return []

async def read_resource(server_url, resource_uri):
    """
    Read a resource from the MCP server.
    
    Args:
        server_url: URL of the MCP server
        resource_uri: URI of the resource to read
        
    Returns:
        Content of the resource
    """
    formatted_url = format_server_url(server_url)
    print("Inside read_resource client")
    
    try:
        async with sse_client(formatted_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                
                # Read the resource
                result = await session.read_resource(resource_uri)               
                #print(f"Read resource {resource_uri}, mime type: {result.mimeType}")

                if hasattr(result,'contents') and result.contents:
                    
                    content = result.contents[0]

                    if hasattr(content, 'text'):
                        return content.text
                    else:
                        return str(content)
                elif hasattr(result,'text'):
                    return result.text
                else:
                    return f"Unexpected result structure for : {resource_uri}"
    except Exception as e:
        print(f"Error reading resource {resource_uri}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"


#Prompts
async def list_prompts(server_url):
    """
    List available prompts from the MCP server.
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        List of available prompts
    """
    formatted_url = format_server_url(server_url)
    
    try:
        async with sse_client(formatted_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                
                # List available prompts
                prompts_result = await session.list_prompts()
                
                print(f"Discovered {len(prompts_result.prompts)} prompts:")
                for prompt in prompts_result.prompts:
                    print(f"  - {prompt.name}: {prompt.description or 'No description'}")
                    if prompt.arguments:
                        print(f"    Arguments: {', '.join(arg.name for arg in prompt.arguments)}")
                
                return prompts_result.prompts
    except Exception as e:
        print(f"Error listing prompts: {e}")
        return []

async def get_prompt(server_url, prompt_name, arguments):
    """
    Get a prompt from the MCP server.
    
    Args:
        server_url: URL of the MCP server
        prompt_name: Name of the prompt to get
        arguments: Arguments to pass to the prompt
        
    Returns:
        Content of the prompt
    """
    formatted_url = format_server_url(server_url)
    
    try:
        async with sse_client(formatted_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                
                # Get the prompt
                result = await session.get_prompt(prompt_name, arguments)
                
                if hasattr(result, 'messages'):
                    # Convert messages to a single string for simplicity
                    prompt_text = "\n\n".join([
                        f"{msg.role}: {msg.content[0].text}" for msg in result.messages
                    ])
                    return prompt_text
                else:
                    return result.text
    except Exception as e:
        print(f"Error getting prompt {prompt_name}: {e}")
        return f"Error: {str(e)}"



# Simple test function to verify the client works
async def test_client(server_url):
    """
    Test the MCP client by discovering tools and calling a simple tool.
    
    Args:
        server_url: URL of the MCP server (with or without /sse)
    """
    print("Testing MCP client...", server_url)
    tools = await discover_tools(server_url)
    
    if not tools:
        print("No tools discovered. Is the server running?")
        return
    
    print("\nTest successful! MCP client is working.")
    
