"""MCP Server for Paper Review Agents."""
import json
import asyncio
from typing import Any, Optional
from dataclasses import asdict
from agents.orchestrator import PaperReviewOrchestrator


class PaperReviewerMCPServer:
    """
    MCP Server exposing paper review agents as services.
    
    Implements MCP (Model Context Protocol) for standardized agent communication.
    """
    
    def __init__(self):
        self.orchestrator = PaperReviewOrchestrator()
        self.active_reviews = {}
        self.review_counter = 0
    
    async def submit_paper(self, paper_path: str) -> dict:
        """
        Submit a paper for review via MCP.
        
        Args:
            paper_path: Path to paper or paper identifier
        
        Returns:
            Task ID and initial acknowledgment
        """
        self.review_counter += 1
        task_id = f"review_{self.review_counter}"
        
        self.active_reviews[task_id] = {
            "status": "QUEUED",
            "paper_path": paper_path,
            "result": None
        }
        
        return {
            "task_id": task_id,
            "status": "QUEUED",
            "message": f"Paper submitted for review",
            "paper_path": paper_path
        }
    
    async def get_review_status(self, task_id: str) -> dict:
        """Get status of a review task."""
        
        if task_id not in self.active_reviews:
            return {"error": f"Task {task_id} not found"}
        
        task = self.active_reviews[task_id]
        return {
            "task_id": task_id,
            "status": task.get("status"),
            "paper_path": task.get("paper_path"),
            "result": task.get("result")
        }
    
    async def execute_review(self, task_id: str) -> dict:
        """Execute paper review for a submitted task."""
        
        if task_id not in self.active_reviews:
            return {"error": f"Task {task_id} not found"}
        
        task = self.active_reviews[task_id]
        paper_path = task.get("paper_path")
        
        try:
            task["status"] = "PROCESSING"
            
            # Execute review
            review_result = await self.orchestrator.review_paper(paper_path)
            
            task["status"] = "COMPLETED"
            task["result"] = review_result
            
            return {
                "task_id": task_id,
                "status": "COMPLETED",
                "review": review_result
            }
        
        except Exception as e:
            task["status"] = "FAILED"
            task["error"] = str(e)
            return {
                "task_id": task_id,
                "status": "FAILED",
                "error": str(e)
            }
    
    async def get_workflow_trace(self, task_id: str) -> dict:
        """Get detailed workflow trace for a completed review."""
        
        if task_id not in self.active_reviews:
            return {"error": f"Task {task_id} not found"}
        
        task = self.active_reviews[task_id]
        
        if task.get("status") != "COMPLETED":
            return {"error": f"Task {task_id} is not completed"}
        
        workflow = self.orchestrator.get_workflow_report()
        
        return {
            "task_id": task_id,
            "workflow": workflow,
            "agents_log": self._get_agents_log()
        }
    
    def _get_agents_log(self) -> dict:
        """Get logs from all agents."""
        
        return {
            "reader_agent": {
                "name": self.orchestrator.reader.name,
                "role": self.orchestrator.reader.role,
                "history_length": len(self.orchestrator.reader.conversation_history)
            },
            "meta_reviewer_agent": {
                "name": self.orchestrator.meta_reviewer.name,
                "role": self.orchestrator.meta_reviewer.role,
                "history_length": len(self.orchestrator.meta_reviewer.conversation_history)
            },
            "critic_agent": {
                "name": self.orchestrator.critic.name,
                "role": self.orchestrator.critic.role,
                "history_length": len(self.orchestrator.critic.conversation_history)
            }
        }
    
    async def handle_request(self, request: dict) -> dict:
        """
        Handle incoming MCP request.
        
        Supported operations:
        - submit_paper: Submit paper for review
        - get_status: Check review status
        - execute_review: Run the review
        - get_trace: Get workflow details
        """
        
        operation = request.get("operation")
        params = request.get("params", {})
        
        if operation == "submit_paper":
            return await self.submit_paper(params.get("paper_path"))
        
        elif operation == "get_status":
            return await self.get_review_status(params.get("task_id"))
        
        elif operation == "execute_review":
            return await self.execute_review(params.get("task_id"))
        
        elif operation == "get_trace":
            return await self.get_workflow_trace(params.get("task_id"))
        
        else:
            return {"error": f"Unknown operation: {operation}"}
