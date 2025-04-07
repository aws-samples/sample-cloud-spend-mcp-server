#!/usr/bin/env python3
"""
AWS Cost Explorer Assistant

This Chainlit application provides a conversational interface to help users
explore and analyze their AWS costs. It uses Claude via Bedrock and integrates
with an MCP server that provides tools for AWS cost analysis.

The application maintains a conversation history to provide context-aware
responses across multiple interactions.

To configure the MCP server, set environment variables before running:
    export MCP_SERVER_URL=your-server-hostname
    export MCP_SERVER_PORT=your-server-port

Example:
    export MCP_SERVER_URL=localhost
    export MCP_SERVER_PORT=8000
    chainlit run app.py --port 8080
"""

import os
import chainlit as cl
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# Get configuration from environment variables with defaults
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "ec2-44-192-72-20.compute-1.amazonaws.com")
MCP_SERVER_PORT = os.getenv("MCP_SERVER_PORT", "8000")
SECURE = 's' if MCP_SERVER_PORT == "443" else ''
FULL_MCP_URL = f"http{SECURE}://{MCP_SERVER_URL}:{MCP_SERVER_PORT}/sse"

# Print configuration at module load time
print(f"MCP Server configured at: {FULL_MCP_URL}")
print("To change this configuration, set the MCP_SERVER_URL and MCP_SERVER_PORT environment variables")

# Initialize the model
model = ChatBedrock(model="us.anthropic.claude-3-5-haiku-20241022-v1:0")

@cl.on_chat_start
async def start():
    welcome_message = f"""
# 👋 Welcome to your AWS cost explorer assistant.
    
I'm ready to help you with your questions related to your AWS spend. How can I help you save today?

_Connected to MCP server at: {MCP_SERVER_URL}:{MCP_SERVER_PORT}_
    """
    await cl.Message(content=welcome_message).send()
    
    # Initialize conversation history with a system message at the beginning
    cl.user_session.set(
        "message_history",
        []  # Start with an empty history - we'll add the system message when formatting for the agent
    )

@cl.on_message
async def main(message: cl.Message):
    # Get the conversation history
    message_history = cl.user_session.get("message_history")
    
    # Add the current user message to history
    message_history.append({"role": "user", "content": message.content})
    
    # Show a thinking message
    thinking_msg = cl.Message(content="Thinking...")
    await thinking_msg.send()
    
    try:
        async with MultiServerMCPClient(
            {
                "weather": {
                    "url": FULL_MCP_URL,
                    "transport": "sse",
                }
            }
        ) as client:
            # Create the agent
            agent = create_react_agent(
                model, 
                client.get_tools(), 
                #prompt="You are an AI assistant, use your knowledge and tools provided to you to answer user questions"
            )
            
            # Format messages for the agent - ensure system message is first
            formatted_messages = [
                {"role": "system", "content": "You are a helpful AI assistant specializing in AWS cost analysis. Answer the user's questions accurately and concisely."}
            ]
            # Add the rest of the conversation history
            formatted_messages.extend(message_history)
        
            # Invoke the agent with properly formatted message history
            print(f"Sending request to MCP server at: {FULL_MCP_URL}")
            print(f"formatted_messages={formatted_messages}")
            response = await agent.ainvoke({"messages": formatted_messages})
            
            # Remove the thinking message
            await thinking_msg.remove()
            
            # Extract the content from the response
            if response and "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                
                if isinstance(last_message, dict) and "content" in last_message:
                    content = last_message["content"]
                else:
                    content = str(last_message.content)
                
                # Add the assistant's response to the conversation history
                message_history.append({"role": "assistant", "content": content})
                
                # Save the updated history (without system message)
                cl.user_session.set("message_history", message_history)
                
                # Send the message
                await cl.Message(content=content).send()
            else:
                await cl.Message(content="No valid response received").send()
                
    except Exception as e:
        # Remove the thinking message
        await thinking_msg.remove()
        
        # Send error message
        error_message = f"""
## ❌ Error Occurred

```
{str(e)}
```

Please try again or check your query.
        """
        await cl.Message(content=error_message, author="System").send()
        
        # Print error to console for debugging
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    cl.run(
        title="AWS Cost Explorer",
        description="An intelligent assistant for analyzing your AWS costs"
    )