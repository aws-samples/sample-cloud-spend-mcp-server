#!/usr/bin/env python3
"""
LangGraph MCP Client 

This script demonstrates using LangGraph with the MultiServerMCPClient adapter to connect to an
MCP-compatible server and query information using a Bedrock-hosted Claude model.

The script accepts command line arguments for:
- Server host and port
- Model ID to use
- User message to process

Usage:
    python langgraph_mcp_client.py --host hostname --port port --model model_id --message "your question"

Example:
    python langgraph_mcp_sse_client.py --host ec2-44-192-72-20.compute-1.amazonaws.com --port 8000 \
        --model anthropic.claude-3-haiku-20240307-v1:0 --message "my bedrock usage in last 7 days?"
"""

import asyncio
import argparse
from typing import Dict, List, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_aws import ChatBedrock

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the LangGraph MCP client.
    
    Returns:
        argparse.Namespace: The parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='LangGraph MCP Client')
    
    # Server connection arguments
    parser.add_argument('--host', type=str, default='ec2-44-192-72-20.compute-1.amazonaws.com',
                        help='Hostname of the MCP server')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port of the MCP server')
    parser.add_argument('--server-name', type=str, default='weather',
                         help='Server name identifier in the configuration')
    
    # Model arguments
    parser.add_argument('--model', type=str, default='anthropic.claude-3-haiku-20240307-v1:0',
                        help='Model ID to use with Bedrock')
    
    # Message arguments
    parser.add_argument('--message', type=str, default='my bedrock usage in last 7 days?',
                        help='Message to send to the agent')
    parser.add_argument('--system-message', type=str,
                        default='You are a helpful AI assistant. Answer the user\'s questions accurately and concisely.',
                        help='System message to set context for the agent')
                        
    return parser.parse_args()

async def main():
    """
    Main function that:
    1. Parses command line arguments
    2. Sets up the LangChain MCP client and Bedrock model
    3. Creates a LangGraph agent with available tools
    4. Invokes the agent with the provided message
    5. Displays the response
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Display configuration
    secure = 's' if args.port == 443 else ''
    server_url = f"http{secure}://{args.host}:{args.port}/sse"
    print(f"Connecting to MCP server: {server_url}")
    print(f"Using model: {args.model}")
    print(f"Message: {args.message}")
    
    # Initialize the model
    model = ChatBedrock(model_id=args.model)
    
    try:
        # Initialize MCP client with the server configuration
        async with MultiServerMCPClient(
            {
                args.server_name: {
                    "url": server_url,
                    "transport": "sse",
                }
            }
        ) as client:
            print("Connected to MCP server successfully")
            
            # Get available tools and display them
            tools = client.get_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Create the agent with the model and tools
            agent = create_react_agent(
                model, 
                tools
            )
            
            # Format the message with system message first
            formatted_messages = [
                {"role": "system", "content": args.system_message},
                {"role": "user", "content": args.message}
            ]
            
            print("\nInvoking agent...\n" + "-"*40)
            
            # Invoke the agent with the formatted messages
            response = await agent.ainvoke({"messages": formatted_messages})
            
            print("\nResponse:" + "\n" + "-"*40)
            
            # Process and display the response
            if response and "messages" in response and response["messages"]:
                # Get the last message from the response
                last_message = response["messages"][-1]
                
                if isinstance(last_message, dict) and "content" in last_message:
                    # Display the content of the response
                    print(last_message["content"])
                else:
                    print(str(last_message.content))
            else:
                print("No valid response received")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())