#!/usr/bin/env python3
"""
Simple Streamlit chat interface for the Local LLM Stack
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE = "http://192.168.1.30:8001"  # Use the specific IP address
MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct-AWQ"

def check_connection() -> bool:
    """Check if the orchestrator is running and healthy."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "healthy"
    except:
        pass
    return False

def send_message(message: str, conversation_history: list = None) -> str:
    """Send a message to the orchestrator and get response."""
    try:
        # Use conversation history if provided, otherwise start fresh
        messages = conversation_history if conversation_history else []
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{API_BASE}/chat/completions",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The model might be processing a complex request."
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to the orchestrator. Make sure the services are running."
    except Exception as e:
        return f"Error: {str(e)}"

def get_available_tools() -> list:
    """Get list of available tools."""
    try:
        response = requests.get(f"{API_BASE}/tools/schemas", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def main():
    st.set_page_config(
        page_title="Local LLM Chat",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
    }
    .error-message {
        background-color: #ffebee;
        border-left-color: #f44336;
        color: #c62828;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Local LLM Chat Interface</h1>
        <p>Powered by Qwen2.5-7B-Instruct-AWQ</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 System Status")
        
        # Connection status
        is_connected = check_connection()
        if is_connected:
            st.markdown('<p class="status-online">🟢 System Online</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-offline">🔴 System Offline</p>', unsafe_allow_html=True)
            st.error("Cannot connect to orchestrator. Make sure services are running with: `make up`")
        
        st.markdown("---")
        
        # Available tools
        st.header("🛠️ Available Tools")
        tools = get_available_tools()
        if tools:
            for tool in tools:
                tool_name = tool.get("function", {}).get("name", "Unknown")
                tool_desc = tool.get("function", {}).get("description", "No description")
                st.markdown(f"**{tool_name}**")
                st.caption(tool_desc)
        else:
            st.info("No tools available or connection failed")
        
        st.markdown("---")
        
        # Quick actions
        st.header("⚡ Quick Actions")
        if st.button("🔄 Refresh Status"):
            st.rerun()
        
        if st.button("🧹 Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    st.header("💬 Chat")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your local LLM assistant. I can help you with various tasks including tool execution, file operations, and general conversation. How can I assist you today?"
            }
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        elif message["role"] == "error":
            st.markdown(f"""
            <div class="chat-message error-message">
                <strong>❌ Error:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    if is_connected:
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                user_input = st.text_input(
                    "Type your message:",
                    placeholder="Ask me anything...",
                    label_visibility="collapsed"
                )
            with col2:
                submit_button = st.form_submit_button("Send", use_container_width=True)
        
        if submit_button and user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get assistant response
            with st.spinner("Thinking..."):
                # Convert Streamlit messages to API format
                api_messages = []
                for msg in st.session_state.messages:
                    if msg["role"] in ["user", "assistant"]:
                        api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                response = send_message(user_input, api_messages)
            
            # Add assistant response
            if response.startswith("Error:"):
                st.session_state.messages.append({"role": "error", "content": response})
            else:
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()
    else:
        st.warning("⚠️ System is offline. Please start the services first.")
        st.code("make up", language="bash")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>Local LLM Stack - Built with Streamlit</p>
        <p>API Endpoint: <code>http://localhost:8001</code></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
