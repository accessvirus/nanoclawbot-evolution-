"""
Agent Core Services - Service Layer for Agent Slice

This module provides real agent lifecycle, execution, and query services
with actual SQLite database persistence.
"""

import logging
import uuid
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentLifecycleServices:
    """Service for agent lifecycle management with SQLite persistence."""
    
    def __init__(self, slice: Any):
        self.slice = slice
        self.db_path = Path("data/agents.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._agents: Dict[str, Dict] = {}
    
    async def initialize(self) -> None:
        """Initialize database and load agents."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    instructions TEXT,
                    model TEXT DEFAULT 'gpt-4',
                    tools TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'created',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            await db.commit()
            
            # Load existing agents into memory
            cursor = await db.execute("SELECT * FROM agents")
            rows = await cursor.fetchall()
            for row in rows:
                self._agents[row[0]] = {
                    "id": row[0],
                    "name": row[1],
                    "instructions": row[2],
                    "model": row[3],
                    "tools": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "updated_at": row[7]
                }
    
    async def create_agent(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: list
    ) -> str:
        """Create a new agent with persistence."""
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        agent_data = {
            "id": agent_id,
            "name": name,
            "instructions": instructions,
            "model": model,
            "tools": str(tools),
            "status": "created",
            "created_at": now,
            "updated_at": now
        }
        
        # Save to SQLite
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO agents (id, name, instructions, model, tools, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_data["id"],
                agent_data["name"],
                agent_data["instructions"],
                agent_data["model"],
                agent_data["tools"],
                agent_data["status"],
                agent_data["created_at"],
                agent_data["updated_at"]
            ))
            await db.commit()
        
        # Cache in memory
        self._agents[agent_id] = agent_data
        
        logger.info(f"Created agent: {agent_id} ({name})")
        return agent_id
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent from persistence."""
        if agent_id not in self._agents:
            return False
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            await db.commit()
        
        del self._agents[agent_id]
        logger.info(f"Deleted agent: {agent_id}")
        return True
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent status from persistence."""
        if agent_id in self._agents:
            return self._agents[agent_id]
        
        # Try to load from database
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = await cursor.fetchone()
            if row:
                agent = {
                    "id": row[0],
                    "name": row[1],
                    "instructions": row[2],
                    "model": row[3],
                    "tools": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "updated_at": row[7]
                }
                self._agents[agent_id] = agent
                return agent
        return None
    
    async def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update agent status."""
        if agent_id not in self._agents:
            return False
        
        now = datetime.utcnow().isoformat()
        self._agents[agent_id]["status"] = status
        self._agents[agent_id]["updated_at"] = now
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "UPDATE agents SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, agent_id)
            )
            await db.commit()
        
        return True


class AgentExecutionServices:
    """Service for agent execution with SQLite persistence."""
    
    def __init__(self, slice: Any):
        self.slice = slice
        self.db_path = Path("data/agent_executions.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._executions: Dict[str, Dict] = {}
    
    async def initialize(self) -> None:
        """Initialize execution database."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    input_text TEXT,
                    result TEXT,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    duration_ms REAL,
                    executed_at TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                )
            """)
            await db.commit()
    
    async def run_agent(
        self,
        agent_id: str,
        input_text: str
    ) -> Dict[str, Any]:
        """Execute an agent with input and persistence."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        
        # Get agent from lifecycle services
        agent = await AgentLifecycleServices(self.slice).get_agent_status(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent {agent_id} not found"}
        
        try:
            # REAL LLM CALL - Using OpenRouter Gateway
            from providers.openrouter_gateway import OpenRouterGateway, OpenRouterConfig
            
            # Get API key from slice config or environment
            api_key = getattr(self.slice.config, 'openrouter_api_key', None) or \
                      getattr(self.slice, 'openrouter_api_key', None) or \
                      "sk-default-key"
            
            # Create gateway and make real LLM call
            config = OpenRouterConfig(api_key=api_key)
            gateway = OpenRouterGateway(config)
            
            # Build prompt from agent instructions
            system_prompt = agent.get('instructions', f"You are {agent['name']}")
            
            # Make real LLM call
            llm_response = await gateway.complete(
                prompt=input_text,
                model=agent.get('model', 'openai/gpt-4-turbo'),
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=4000
            )
            
            # Get real result from LLM
            result_text = llm_response.get("content", "")
            prompt_tokens = llm_response.get("prompt_tokens", 0)
            completion_tokens = llm_response.get("completion_tokens", 0)
            
            # Close gateway
            await gateway.close()
            
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            execution_data = {
                "id": execution_id,
                "agent_id": agent_id,
                "input_text": input_text,
                "result": result_text,
                "status": "completed",
                "error_message": None,
                "duration_ms": duration_ms,
                "executed_at": start_time.isoformat(),
                "model_used": agent.get('model', 'openai/gpt-4-turbo'),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
            
            # Persist execution with real LLM results
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("""
                    INSERT INTO executions 
                    (id, agent_id, input_text, result, status, duration_ms, executed_at, model_used, prompt_tokens, completion_tokens)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution_data["id"],
                    execution_data["agent_id"],
                    execution_data["input_text"],
                    execution_data["result"],
                    execution_data["status"],
                    execution_data["duration_ms"],
                    execution_data["executed_at"],
                    execution_data["model_used"],
                    execution_data["prompt_tokens"],
                    execution_data["completion_tokens"]
                ))
                await db.commit()
            
            self._executions[execution_id] = execution_data
            
            logger.info(f"Agent execution completed: {execution_id} (model: {execution_data['model_used']}, tokens: {prompt_tokens+completion_tokens})")
            return {
                "execution_id": execution_id,
                "agent_id": agent_id,
                "result": result_text,
                "duration_ms": duration_ms,
                "model_used": execution_data["model_used"],
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution by ID."""
        if execution_id in self._executions:
            return self._executions[execution_id]
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("SELECT * FROM executions WHERE id = ?", (execution_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "agent_id": row[1],
                    "input_text": row[2],
                    "result": row[3],
                    "status": row[4],
                    "error_message": row[5],
                    "duration_ms": row[6],
                    "executed_at": row[7]
                }
        return None


class AgentQueryServices:
    """Service for querying agents with SQLite."""
    
    def __init__(self, slice: Any):
        self.slice = slice
        self.db_path = Path("data/agents.db")
    
    async def list_agents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all agents, optionally filtered by status."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            if status:
                cursor = await db.execute(
                    "SELECT * FROM agents WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                cursor = await db.execute("SELECT * FROM agents ORDER BY created_at DESC")
            
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "instructions": row[2],
                    "model": row[3],
                    "tools": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "updated_at": row[7]
                }
                for row in rows
            ]
    
    async def search_agents(self, query: str) -> List[Dict[str, Any]]:
        """Search agents by name."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                "SELECT * FROM agents WHERE name LIKE ? ORDER BY created_at DESC",
                (f"%{query}%",)
            )
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "instructions": row[2],
                    "model": row[3],
                    "tools": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "updated_at": row[7]
                }
                for row in rows
            ]
    
    async def count_agents(self, status: Optional[str] = None) -> int:
        """Count agents."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            if status:
                cursor = await db.execute("SELECT COUNT(*) FROM agents WHERE status = ?", (status,))
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM agents")
            row = await cursor.fetchone()
            return row[0] if row else 0
