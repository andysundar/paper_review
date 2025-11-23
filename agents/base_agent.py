"""Base agent class with tool support."""
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Message:
    """Message structure for inter-agent communication."""
    sender: str
    content: str
    tool_calls: Optional[list] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class BaseAgent(ABC):
    """Base agent with tool capability."""
    
    def __init__(self, name: str, role: str, tools: Optional[dict] = None):
        self.name = name
        self.role = role
        self.tools = tools or {}
        self.conversation_history = []
    
    def register_tool(self, tool_name: str, tool_func):
        """Register a tool that this agent can use."""
        self.tools[tool_name] = tool_func
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a registered tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        try:
            tool_func = self.tools[tool_name]
            if asyncio.iscoroutinefunction(tool_func):
                return await tool_func(**kwargs)
            else:
                return tool_func(**kwargs)
        except Exception as e:
            return {"error": str(e)}
    
    def add_to_history(self, message: Message):
        """Add message to conversation history."""
        self.conversation_history.append(asdict(message))
    
    @abstractmethod
    async def process(self, input_data: str) -> Message:
        """Process input and return message. To be implemented by subclasses."""
        pass
    
    def get_history(self) -> list:
        """Get conversation history."""
        return self.conversation_history
