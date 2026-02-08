"""
Skills System Services for slice_skills

Core business logic for skill management.
"""

import logging
import yaml
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..slice_base import AtomicSlice

logger = logging.getLogger(__name__)


class SkillServices:
    """Services for skill management."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.db = slice.database
        self.skills_path = Path("skills")
    
    async def load_skill(self, skill_file: str) -> Dict[str, Any]:
        """Load and parse a skill file."""
        try:
            skill_path = self.skills_path / skill_file
            
            # Validate path to prevent path traversal
            if ".." in str(skill_path) or skill_path.is_absolute():
                raise ValueError("Invalid skill file path")
            
            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse YAML with safe loader
            skill_data = yaml.safe_load(content)
            
            # Validate required fields
            if "name" not in skill_data:
                raise ValueError("Skill must have a name")
            if "version" not in skill_data:
                raise ValueError("Skill must have a version")
            
            return skill_data
            
        except Exception as e:
            logger.error(f"Error loading skill {skill_file}: {e}")
            raise
    
    async def register_skill(
        self,
        skill_data: Dict[str, Any],
        skill_file: str = None
    ) -> str:
        """Register a new skill."""
        skill_id = f"skill_{int(datetime.utcnow().timestamp() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO skills 
                   (id, name, version, description, parameters, handlers, 
                    category, file_path, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                skill_id,
                skill_data["name"],
                skill_data["version"],
                skill_data.get("description", ""),
                str(skill_data.get("parameters", {})),
                str(skill_data.get("handlers", {})),
                skill_data.get("category", "general"),
                skill_file or "",
                datetime.utcnow().isoformat()
            )
        
        logger.info(f"Skill registered: {skill_data['name']}")
        return skill_id
    
    async def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get skill by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM skills WHERE id = ?",
            (skill_id,)
        )
        return dict(row) if row else None
    
    async def list_skills(self, category: str = None) -> List[Dict[str, Any]]:
        """List all skills."""
        if category:
            rows = await self.db.fetchall(
                "SELECT * FROM skills WHERE category = ? ORDER BY name",
                (category,)
            )
        else:
            rows = await self.db.fetchall("SELECT * FROM skills ORDER BY name")
        
        return [dict(row) for row in rows]
    
    async def update_skill(
        self,
        skill_id: str,
        **updates
    ) -> bool:
        """Update skill."""
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [skill_id]
        
        await self.db.execute(
            f"UPDATE skills SET {set_clause} WHERE id = ?",
            values
        )
        return True
    
    async def delete_skill(self, skill_id: str) -> bool:
        """Delete skill."""
        await self.db.execute(
            "UPDATE skills SET is_active = 0 WHERE id = ?",
            (skill_id,)
        )
        return True
    
    async def execute_skill(
        self,
        skill_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a skill."""
        skill = await self.get_skill(skill_id)
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        handlers = eval(skill.get("handlers", "{}"))
        
        # Execute skill handler
        result = {"success": True, "output": {}}
        
        for handler_name, handler_path in handlers.items():
            try:
                # Import and execute handler
                handler = self._import_handler(handler_path)
                if handler:
                    output = handler.execute(parameters)
                    result["output"][handler_name] = output
            except Exception as e:
                result["success"] = False
                result["error"] = str(e)
                break
        
        return result
    
    def _import_handler(self, handler_path: str):
        """Import handler module."""
        try:
            parts = handler_path.rsplit(".", 1)
            if len(parts) == 2:
                module = __import__(parts[0], fromlist=[parts[1]])
                return getattr(module, parts[1])()
        except Exception as e:
            logger.error(f"Error importing handler {handler_path}: {e}")
        return None
    
    async def get_skill_stats(self) -> Dict[str, Any]:
        """Get skill statistics."""
        total = await self.db.fetchone("SELECT COUNT(*) as count FROM skills WHERE is_active = 1")
        by_category = await self.db.fetchall(
            """SELECT category, COUNT(*) as count FROM skills 
               WHERE is_active = 1 GROUP BY category"""
        )
        
        return {
            "total_skills": total["count"] if total else 0,
            "by_category": {row["category"]: row["count"] for row in by_category}
        }
