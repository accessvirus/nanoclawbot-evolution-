"""
Master Swarm Chat - AI Swarm Orchestration Interface

This module provides:
- Master AI LLM that coordinates all slices
- Natural language interface to control the swarm
- Self-aware implementation knowledge
- Cross-slice orchestration via chat
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from refactorbot.providers.openrouter_gateway import OpenRouterGateway, OpenRouterConfig

logger = logging.getLogger(__name__)


class SliceInfo:
    """Information about a slice for the AI to understand."""
    
    def __init__(
        self,
        slice_id: str,
        name: str,
        description: str,
        operations: List[str],
        capabilities: List[str]
    ):
        self.slice_id = slice_id
        self.name = name
        self.description = description
        self.operations = operations
        self.capabilities = capabilities
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.slice_id,
            "name": self.name,
            "description": self.description,
            "operations": self.operations,
            "capabilities": self.capabilities
        }


# Slice knowledge base for the AI
SLICE_KNOWLEDGE = [
    SliceInfo(
        slice_id="slice_agent",
        name="Agent Core",
        description="Manages AI agent lifecycle and orchestration",
        operations=["create_agent", "run_agent", "get_agent_status", "list_agents", "delete_agent"],
        capabilities=["agent_creation", "agent_execution", "agent_management"]
    ),
    SliceInfo(
        slice_id="slice_tools",
        name="Tools Slice",
        description="Tool registration, validation, and execution",
        operations=["register_tool", "execute_tool", "list_tools", "validate_tool", "delete_tool"],
        capabilities=["tool_registry", "tool_execution", "tool_validation"]
    ),
    SliceInfo(
        slice_id="slice_memory",
        name="Memory Slice",
        description="Persistent memory storage and retrieval",
        operations=["store_memory", "retrieve_memory", "search_memories", "delete_memory", "list_memories"],
        capabilities=["memory_storage", "memory_search", "memory_management"]
    ),
    SliceInfo(
        slice_id="slice_communication",
        name="Communication Slice",
        description="Message handling and channel management",
        operations=["send_message", "create_channel", "get_messages", "subscribe", "publish"],
        capabilities=["messaging", "channel_management", "event_publishing"]
    ),
    SliceInfo(
        slice_id="slice_session",
        name="Session Slice",
        description="User session management and state",
        operations=["create_session", "get_session", "update_session", "delete_session", "list_sessions"],
        capabilities=["session_management", "state_persistence", "user_context"]
    ),
    SliceInfo(
        slice_id="slice_providers",
        name="Providers Slice",
        description="LLM provider management and routing",
        operations=["list_providers", "select_provider", "get_model", "track_cost"],
        capabilities=["provider_routing", "model_selection", "cost_tracking"]
    ),
    SliceInfo(
        slice_id="slice_skills",
        name="Skills Slice",
        description="Skill registration and execution",
        operations=["register_skill", "execute_skill", "list_skills", "update_skill", "delete_skill"],
        capabilities=["skill_registry", "skill_execution", "skill_management"]
    ),
    SliceInfo(
        slice_id="slice_eventbus",
        name="Event Bus Slice",
        description="Event-driven communication between slices",
        operations=["publish_event", "subscribe", "unsubscribe", "get_events"],
        capabilities=["event_publishing", "event_subscription", "event_routing"]
    ),
]


class MasterSwarmChat:
    """
    Master AI Swarm Controller.
    
    This AI is aware of the entire implementation and can:
    - Coordinate all slices as a swarm
    - Dispatch tasks to appropriate slices
    - Synthesize responses from multiple slices
    - Learn and improve from interactions
    """
    
    SYSTEM_PROMPT = """You are RefactorBot, a Master AI Swarm Orchestrator.

## Your Architecture

You control 8 specialized AI slices that work together as a swarm:

1. **Agent Core** - Creates and manages AI agents
2. **Tools Slice** - Registers and executes tools
3. **Memory Slice** - Persistent memory storage
4. **Communication Slice** - Messaging and channels
5. **Session Slice** - User session management
6. **Providers Slice** - LLM provider routing
7. **Skills Slice** - Skill registry and execution
8. **Event Bus** - Event-driven communication

## How You Work

When user asks for something:
1. Understand the intent
2. Determine which slice(s) needed
3. Dispatch commands to slices
4. Collect results
5. Synthesize final response

## Example Interactions

User: "Create an agent that can search the web"
→ Use Agent Core to create agent
→ Use Tools Slice to register search tool
→ Return agent with capabilities

User: "Remember this: my favorite color is blue"
→ Use Memory Slice to store the fact
→ Confirm storage

User: "What do I have stored?"
→ Use Memory Slice to retrieve memories
→ List found items

## Constraints

- Be helpful and proactive
- Explain what slices you're using
- Handle errors gracefully
- Self-improve from interactions
"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "z-ai/glm-4.5-air:free"
    ):
        self.api_key = api_key
        self.model = model
        self.gateway: Optional[OpenRouterGateway] = None
        self.conversation_history: List[Dict[str, str]] = []
        
        # Initialize slice knowledge
        self.slice_info = {s.slice_id: s for s in SLICE_KNOWLEDGE}
    
    def initialize(self) -> None:
        """Initialize the OpenRouter gateway."""
        if self.api_key:
            import asyncio
            self.gateway = asyncio.run(OpenRouterGateway.create(self.api_key))
            logger.info("Master Swarm Chat initialized with OpenRouter")
    
    def get_slice_descriptions(self) -> str:
        """Get formatted slice descriptions for the AI."""
        descriptions = []
        for slice_info in SLICE_KNOWLEDGE:
            descriptions.append(
                f"- **{slice_info.name}** ({slice_info.slice_id}):\n"
                f"  {slice_info.description}\n"
                f"  Operations: {', '.join(slice_info.operations)}"
            )
        return "\n".join(descriptions)
    
    def get_implementation_summary(self) -> str:
        """Get a summary of the implementation."""
        return f"""
## RefactorBot Implementation Summary

**Architecture:** Vertical Slice Architecture with 8 atomic slices
**Orchestration:** Master Core AI Orchestrator
**Communication:** Event-driven via Event Bus
**Storage:** SQLite with per-slice databases
**LLM Gateway:** OpenRouter with multiple providers

**Available Slices:**
{self.get_slice_descriptions()}

**Current Capabilities:**
- Multi-slice orchestration
- Persistent memory
- Agent lifecycle management
- Tool registration and execution
- Event-driven communication
- Session management
- Cost tracking
"""
    
    def chat(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and return AI response with slice actions.
        
        Args:
            user_message: The user's message
            context: Optional context from previous interactions
            
        Returns:
            Dict with 'response' (AI text) and 'actions' (slice commands)
        """
        import asyncio
        
        # Build the full prompt
        system_prompt = self.SYSTEM_PROMPT + "\n" + self.get_implementation_summary()
        
        # Add context if available
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add user message
        user_msg = user_message
        if context:
            user_msg += f"\n\nContext: {json.dumps(context, indent=2)}"
        messages.append({"role": "user", "content": user_msg})
        
        # Call the LLM
        if self.gateway:
            response = asyncio.run(self.gateway.complete(
                prompt=user_message,
                model=self.model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=4000
            ))
            ai_response = response.get("content", "I understand.")
        else:
            # Fallback for when no API key
            ai_response = self._fallback_chat(user_message)
        
        # Store in history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Limit history
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Parse actions from response (simple extraction)
        actions = self._extract_actions(ai_response)
        
        return {
            "response": ai_response,
            "actions": actions,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _fallback_chat(self, message: str) -> str:
        """Fallback chat when no API key is available."""
        message_lower = message.lower()
        
        # Simple keyword-based responses
        if "create" in message_lower and "agent" in message_lower:
            return """I'll create an agent for you.

**Dispatching to Agent Core:**
```json
{
  "operation": "create_agent",
  "payload": {
    "name": "New Agent",
    "instructions": "Based on your request",
    "model": "gpt-4",
    "tools": []
  }
}
```

Note: Configure OPENROUTER_API_KEY in .env for full AI capabilities."""
        
        if "remember" in message_lower or "store" in message_lower:
            return """I'll store that in memory.

**Dispatching to Memory Slice:**
```json
{
  "operation": "store_memory",
  "payload": {
    "key": "user_fact",
    "value": "...",  
    "category": "user_preferences"
  }
}
```"""
        
        if "what" in message_lower and ("stored" in message_lower or "remember" in message_lower):
            return """Let me check your stored memories.

**Dispatching to Memory Slice:**
```json
{
  "operation": "list_memories",
  "payload": {}
}
```"""
        
        if "help" in message_lower:
            return f"""I'm RefactorBot, a Master AI Swarm. Here's what I can do:

**Available Slices:**
1. Agent Core - Create and manage AI agents
2. Tools - Register and execute tools
3. Memory - Store and retrieve information
4. Communication - Send messages and manage channels
5. Session - Manage user sessions
6. Providers - Route to different LLMs
7. Skills - Register and execute skills
8. Event Bus - Event-driven communication

**Example Commands:**
- "Create an agent that can..."
- "Remember that..."
- "What do I have stored?"
- "Execute tool X with parameters Y"

Configure OPENROUTER_API_KEY for full AI intelligence!"""
        
        return """I understand your message, but I'm running in limited mode.

Configure OPENROUTER_API_KEY in your .env file for full AI capabilities.

**I can still help with basic operations:**
- Creating agents
- Storing memories
- Listing stored data
- Managing tools

What would you like to do?"""
    
    def _extract_actions(self, response: str) -> List[Dict[str, Any]]:
        """Extract slice actions from the AI response."""
        actions = []
        
        # Look for JSON code blocks
        import re
        json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        
        for block in json_blocks:
            try:
                action = json.loads(block)
                if "operation" in action or "slice" in action:
                    actions.append(action)
            except:
                pass
        
        return actions
    
    def parse_command(self, message: str) -> Dict[str, Any]:
        """
        Parse a natural language command into slice operations.
        
        Returns:
            Dict with 'slices' and 'operations' to execute
        """
        message_lower = message.lower()
        
        result = {
            "slices": [],
            "operations": [],
            "payload": {},
            "confidence": 0.0
        }
        
        # Detect slice and operation from message
        if "agent" in message_lower:
            result["slices"].append("slice_agent")
            if "create" in message_lower or "make" in message_lower:
                result["operations"].append("create_agent")
                result["payload"]["name"] = "New Agent"
                result["confidence"] = 0.9
            elif "run" in message_lower or "execute" in message_lower:
                result["operations"].append("run_agent")
                result["confidence"] = 0.9
            elif "list" in message_lower or "show" in message_lower:
                result["operations"].append("list_agents")
                result["confidence"] = 0.9
        
        elif "memory" in message_lower or "remember" in message_lower or "store" in message_lower:
            result["slices"].append("slice_memory")
            if "store" in message_lower or "remember" in message_lower:
                result["operations"].append("store_memory")
                result["confidence"] = 0.9
            elif "get" in message_lower or "retrieve" in message_lower:
                result["operations"].append("retrieve_memory")
                result["confidence"] = 0.9
            elif "list" in message_lower or "what" in message_lower:
                result["operations"].append("list_memories")
                result["confidence"] = 0.9
        
        elif "tool" in message_lower:
            result["slices"].append("slice_tools")
            if "register" in message_lower or "add" in message_lower:
                result["operations"].append("register_tool")
                result["confidence"] = 0.9
            elif "run" in message_lower or "execute" in message_lower:
                result["operations"].append("execute_tool")
                result["confidence"] = 0.9
        
        elif "skill" in message_lower:
            result["slices"].append("slice_skills")
            if "register" in message_lower:
                result["operations"].append("register_skill")
                result["confidence"] = 0.9
            elif "execute" in message_lower or "run" in message_lower:
                result["operations"].append("execute_skill")
                result["confidence"] = 0.9
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the Master Swarm Chat."""
        return {
            "initialized": self.gateway is not None,
            "model": self.model,
            "history_length": len(self.conversation_history),
            "slices_known": list(self.slice_info.keys())
        }


async def create_master_chat(api_key: Optional[str] = None) -> MasterSwarmChat:
    """Factory function to create and initialize MasterSwarmChat."""
    chat = MasterSwarmChat(api_key=api_key)
    await chat.initialize()
    return chat
