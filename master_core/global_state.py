"""
Global State Manager - Manages global state across all slices.

Uses SQLite for persistence.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel


class GlobalStateModel(BaseModel):
    """Model for global state"""
    key: str
    value: Dict[str, Any]
    updated_at: datetime = datetime.utcnow()


class SliceStateModel(BaseModel):
    """Model for slice state"""
    slice_id: str
    status: str
    health_status: str
    last_heartbeat: datetime
    resource_usage: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}


class GlobalStateManager:
    """
    Manages global state across all slices.
    Thread-safe with SQLite persistence.
    """
    
    def __init__(self, db_path: str = "data/master.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the global state database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create global state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create slice states table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS slice_states (
                slice_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'stopped',
                health_status TEXT NOT NULL DEFAULT 'unhealthy',
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resource_usage TEXT DEFAULT '{}',
                metrics TEXT DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    # -------------------------------------------------------------------------
    # Global State Operations
    # -------------------------------------------------------------------------
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set a global state value"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO global_state (key, value, updated_at)
                VALUES (?, ?, ?)
                """,
                (key, json.dumps(value), datetime.utcnow())
            )
            
            conn.commit()
            conn.close()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a global state value"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT value, updated_at FROM global_state WHERE key = ?",
                (key,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a global state value"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM global_state WHERE key = ?", (key,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return deleted
    
    def get_all(self) -> Dict[str, GlobalStateModel]:
        """Get all global state values"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT key, value, updated_at FROM global_state")
            
            rows = cursor.fetchall()
            conn.close()
            
            return {
                row[0]: GlobalStateModel(
                    key=row[0],
                    value=json.loads(row[1]),
                    updated_at=datetime.fromisoformat(row[2])
                )
                for row in rows
            }
    
    # -------------------------------------------------------------------------
    # Slice State Operations
    # -------------------------------------------------------------------------
    
    def update_slice_state(
        self,
        slice_id: str,
        status: str,
        health_status: str,
        resource_usage: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update a slice's state"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO slice_states 
                (slice_id, status, health_status, last_heartbeat, resource_usage, metrics, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slice_id,
                    status,
                    health_status,
                    datetime.utcnow(),
                    json.dumps(resource_usage or {}),
                    json.dumps(metrics or {}),
                    datetime.utcnow()
                )
            )
            
            conn.commit()
            conn.close()
    
    def get_slice_state(self, slice_id: str) -> Optional[SliceStateModel]:
        """Get a slice's state"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT slice_id, status, health_status, last_heartbeat, 
                       resource_usage, metrics, updated_at
                FROM slice_states WHERE slice_id = ?
                """,
                (slice_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return SliceStateModel(
                    slice_id=row[0],
                    status=row[1],
                    health_status=row[2],
                    last_heartbeat=datetime.fromisoformat(row[3]),
                    resource_usage=json.loads(row[4]),
                    metrics=json.loads(row[5])
                )
            return None
    
    def get_all_slice_states(self) -> Dict[str, SliceStateModel]:
        """Get all slice states"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT slice_id, status, health_status, last_heartbeat,
                       resource_usage, metrics, updated_at
                FROM slice_states
                """
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            return {
                row[0]: SliceStateModel(
                    slice_id=row[0],
                    status=row[1],
                    health_status=row[2],
                    last_heartbeat=datetime.fromisoformat(row[3]),
                    resource_usage=json.loads(row[4]),
                    metrics=json.loads(row[5])
                )
                for row in rows
            }
    
    def heartbeat(self, slice_id: str) -> None:
        """Update slice heartbeat"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE slice_states 
                SET last_heartbeat = ?
                WHERE slice_id = ?
                """,
                (datetime.utcnow(), slice_id)
            )
            
            conn.commit()
            conn.close()
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def clear_all(self) -> None:
        """Clear all global state (use with caution)"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM global_state")
            cursor.execute("DELETE FROM slice_states")
            
            conn.commit()
            conn.close()
    
    def export_state(self) -> Dict[str, Any]:
        """Export entire state as JSON"""
        return {
            "global_state": {k: v.dict() for k, v in self.get_all().items()},
            "slice_states": {k: v.dict() for k, v in self.get_all_slice_states().items()},
            "exported_at": datetime.utcnow().isoformat()
        }
