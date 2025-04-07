"""
This file provides a simple MCP client using just the mcp Python package.
It shows how to access the different MCP server capabilities (prompts, tools etc.) via the message types
supported by the protocol. See: https://modelcontextprotocol.io/docs/concepts/architecture.

Usage: 
  python mcp_sse_client.py [--host HOSTNAME] [--port PORT]

Example:
  python mcp_sse_client.py --host ec2-44-192-72-20.compute-1.amazonaws.com --port 8000
"""
import argparse
from mcp import types
from mcp import ClientSession
from mcp.client.sse import sse_client

# Optional: create a sampling callback
async def handle_sampling_message(message: types.CreateMessageRequestParams) -> types.CreateMessageResult:
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text="Hello, world! from model",
        ),
        model="gpt-3.5-turbo",
        stopReason="endTurn",
    )

async def run(server_url):
    print(f"Connecting to MCP server at: {server_url}")    
    
    async with sse_client(server_url) as (read, write):
        async with ClientSession(read, write, sampling_callback=handle_sampling_message) as session:
            # Initialize the connection
            await session.initialize()

            # List available prompts
            prompts = await session.list_prompts()
            print("\nAvailable prompts:")
            print(prompts)

            # List available resources
            resources = await session.list_resources()
            print("\nAvailable resources:")
            print(resources)

            # List available tools
            tools = await session.list_tools()
            print("\nAvailable tools:")
            print(tools)

            # Call the Bedrock usage stats tool with command-line arguments
            days = 7
            region = 'us-east-1'
            print(f"\nCalling get_bedrock_daily_usage_stats tool with days={days}, region={region}:")
            result = await session.call_tool(
                "get_bedrock_daily_usage_stats", 
                arguments={"params": {"days": days, "region": region}}
            )
            
            # Display the results
            print("\nBedrock Usage Results:")
            for r in result.content:
                print(r.text)

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='MCP Client for Bedrock Usage Statistics')
    parser.add_argument('--host', type=str, default='ec2-44-192-72-20.compute-1.amazonaws.com', 
                        help='Hostname of the MCP server')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port of the MCP server')
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Build the server 
    secure = ''
    
    # Automatically turn to https if port is 443
    if args.port == 443:
        secure = 's'
    server_url = f"http{secure}://{args.host}:{args.port}/sse"
    
    # Run the async main function
    import asyncio
    asyncio.run(run(server_url))