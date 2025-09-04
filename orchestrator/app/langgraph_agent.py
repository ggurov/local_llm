"""LangGraph agent implementation."""

import json
import time
from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from .llm_client import LLMClient
from .vector_store import VectorStore
from .tools import ToolRegistry
from .models import ChatMessage


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    current_step: str
    max_iterations: int
    iteration_count: int


class LangGraphAgent:
    """LangGraph-based agent for orchestrating tool calls."""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.vector_store = VectorStore()
        self.tool_registry = ToolRegistry()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze", self._analyze_input)
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("finalize", self._finalize_response)
        
        # Add edges
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "retrieve")
        workflow.add_edge("retrieve", "generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            self._should_use_tools,
            {
                "tools": "execute_tools",
                "finalize": "finalize"
            }
        )
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def _analyze_input(self, state: AgentState) -> AgentState:
        """Analyze the input to determine what tools might be needed."""
        messages = state["messages"]
        last_message = messages[-1]["content"] if messages else ""
        
        # Simple analysis - in a real implementation, you might use the LLM
        # to analyze the input and determine required tools
        state["current_step"] = "analyzed"
        state["iteration_count"] = 0
        
        return state
    
    async def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant context from vector store."""
        messages = state["messages"]
        if messages:
            last_message = messages[-1]["content"]
            try:
                # Search for relevant documents
                results = await self.vector_store.search(last_message, limit=3)
                if results:
                    context = "\n".join([r["text"] for r in results])
                    # Add context to the last message
                    messages[-1]["content"] = f"Context: {context}\n\nQuery: {last_message}"
                    state["messages"] = messages
            except Exception as e:
                print(f"Warning: Context retrieval failed: {e}")
        
        state["current_step"] = "context_retrieved"
        return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate response using the LLM."""
        messages = state["messages"]
        tool_schemas = self.tool_registry.get_tool_schemas()
        
        try:
            response = await self.llm_client.chat_completion(
                messages=messages,
                # tools=tool_schemas,  # Temporarily disabled until vLLM tool calling is configured
                temperature=0.7
            )
            
            # Extract the response
            choice = response["choices"][0]
            message = choice["message"]
            
            # Add the AI response to messages
            ai_message = {
                "role": "assistant",
                "content": message.get("content", ""),
                "tool_calls": message.get("tool_calls", [])
            }
            messages.append(ai_message)
            state["messages"] = messages
            
            # Store tool calls if any
            if message.get("tool_calls"):
                state["tool_calls"] = message["tool_calls"]
            
            state["current_step"] = "response_generated"
            
        except Exception as e:
            error_message = {
                "role": "assistant",
                "content": f"Error generating response: {str(e)}"
            }
            messages.append(error_message)
            state["messages"] = messages
            state["current_step"] = "error"
        
        return state
    
    def _should_use_tools(self, state: AgentState) -> str:
        """Determine if tools should be used."""
        if state.get("tool_calls") and state["iteration_count"] < state.get("max_iterations", 3):
            return "tools"
        return "finalize"
    
    async def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute tool calls."""
        tool_calls = state.get("tool_calls", [])
        messages = state["messages"]
        
        for tool_call in tool_calls:
            try:
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                tool_call_id = tool_call["id"]
                
                # Execute the tool
                result = await self.tool_registry.execute_tool(
                    tool_name, tool_call_id, arguments
                )
                
                # Add tool result to messages
                tool_message = {
                    "role": "tool",
                    "content": json.dumps(result.result) if result.result else result.error,
                    "tool_call_id": tool_call_id
                }
                messages.append(tool_message)
                
            except Exception as e:
                error_message = {
                    "role": "tool",
                    "content": f"Tool execution error: {str(e)}",
                    "tool_call_id": tool_call.get("id", "unknown")
                }
                messages.append(error_message)
        
        state["messages"] = messages
        state["tool_calls"] = []  # Clear tool calls
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        state["current_step"] = "tools_executed"
        
        return state
    
    async def _finalize_response(self, state: AgentState) -> AgentState:
        """Finalize the response."""
        state["current_step"] = "completed"
        return state
    
    async def process_request(
        self,
        messages: List[ChatMessage],
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """Process a chat request through the agent."""
        # Convert ChatMessage objects to dict format
        message_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        initial_state = AgentState(
            messages=message_dicts,
            tool_calls=[],
            current_step="start",
            max_iterations=max_iterations,
            iteration_count=0
        )
        
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extract the final response
            final_messages = final_state["messages"]
            ai_messages = [msg for msg in final_messages if msg["role"] == "assistant"]
            
            if ai_messages:
                last_ai_message = ai_messages[-1]
                return {
                    "response": last_ai_message["content"],
                    "tool_calls": last_ai_message.get("tool_calls", []),
                    "messages": final_messages,
                    "status": "success"
                }
            else:
                return {
                    "response": "No response generated",
                    "messages": final_messages,
                    "status": "error"
                }
                
        except Exception as e:
            return {
                "response": f"Agent processing failed: {str(e)}",
                "messages": message_dicts,
                "status": "error"
            }
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all components."""
        return {
            "llm": await self.llm_client.health_check(),
            "vector_store": await self.vector_store.health_check()
        }

