"""Multi-Agent Orchestrator using LangGraph."""
import asyncio
import json
from typing import Optional, Dict, Any
from agents.reader_agent import ReaderAgent
from agents.meta_reviewer_agent import MetaReviewerAgent
from agents.critic_agent import CriticAgent


class PaperReviewOrchestrator:
    """Orchestrates the multi-agent paper review workflow."""
    
    def __init__(self):
        self.reader = ReaderAgent()
        self.meta_reviewer = MetaReviewerAgent()
        self.critic = CriticAgent()
        self.workflow_history = []
    
    async def review_paper(self, paper_path: str) -> Dict[str, Any]:
        """
        Execute complete paper review workflow.
        
        Workflow:
        1. Reader extracts and summarizes paper content
        2. MetaReviewer assesses quality and contribution
        3. Critic identifies issues and provides feedback
        
        Args:
            paper_path: Path to paper PDF or paper identifier
        
        Returns:
            Complete review with feedback from all agents
        """
        print(f"\n{'='*70}")
        print(f"Starting Multi-Agent Paper Review for: {paper_path}")
        print(f"{'='*70}\n")
        
        # Step 1: Reader Agent
        print("[1/3] Reader Agent: Extracting paper content...")
        reader_message = await self.reader.process(paper_path)
        
        try:
            reader_output = json.loads(reader_message.content)
        except json.JSONDecodeError:
            reader_output = {"sections": {}, "paper_id": paper_path}
        
        print(f"✓ Reader completed. Found {reader_output.get('text_length', 0)} characters.")
        print(f"  Summary: {reader_output.get('summary', '')[:100]}...")
        
        self.workflow_history.append({
            "step": 1,
            "agent": "Reader",
            "message": reader_message
        })
        
        # Step 2: MetaReviewer Agent
        print("\n[2/3] MetaReviewer Agent: Assessing quality and contribution...")
        meta_message = await self.meta_reviewer.process(reader_output)
        
        try:
            meta_output = json.loads(meta_message.content)
            assessment = meta_output.get("assessment", {})
        except json.JSONDecodeError:
            assessment = {}
        
        print(f"✓ MetaReviewer completed.")
        print(f"  Overall Quality: {assessment.get('overall_quality', 'UNKNOWN')}")
        print(f"  Novelty Score: {assessment.get('novelty_score', 0)}/10")
        print(f"  Methodology Score: {assessment.get('methodology_score', 0)}/10")
        
        self.workflow_history.append({
            "step": 2,
            "agent": "MetaReviewer",
            "message": meta_message
        })
        
        # Step 3: Critic Agent
        print("\n[3/3] Critic Agent: Identifying weaknesses and providing feedback...")
        critic_message = await self.critic.process(reader_output, assessment)
        
        try:
            critic_output = json.loads(critic_message.content)
            critique = critic_output.get("critique", {})
        except json.JSONDecodeError:
            critique = {}
        
        print(f"✓ Critic completed.")
        print(f"  Critical Issues: {critic_output.get('severity_levels', {}).get('critical', 0)}")
        print(f"  Major Issues: {critic_output.get('severity_levels', {}).get('major', 0)}")
        print(f"  Minor Issues: {critic_output.get('severity_levels', {}).get('minor', 0)}")
        
        self.workflow_history.append({
            "step": 3,
            "agent": "Critic",
            "message": critic_message
        })
        
        # Compile final review
        final_review = self._compile_review(
            reader_output,
            assessment,
            critique
        )
        
        print(f"\n{'='*70}")
        print("Review Complete!")
        print(f"{'='*70}\n")
        
        return final_review
    
    def _compile_review(self, reader_output: dict, assessment: dict, critique: dict) -> dict:
        """Compile all agent outputs into a single review."""
        
        return {
            "paper_id": reader_output.get("paper_id"),
            "review_status": "COMPLETE",
            "reader_extraction": {
                "summary": reader_output.get("summary", ""),
                "text_length": reader_output.get("text_length", 0),
                "sections_identified": len(reader_output.get("sections", {})),
                "key_insights": reader_output.get("key_insights", [])
            },
            "quality_assessment": assessment,
            "critique": critique,
            "overall_recommendation": self._generate_final_recommendation(assessment, critique),
            "next_steps": self._generate_next_steps(assessment, critique)
        }
    
    def _generate_final_recommendation(self, assessment: dict, critique: dict) -> str:
        """Generate final recommendation based on assessment and critique."""
        
        overall_quality = assessment.get("overall_quality", "UNKNOWN")
        critical_issues = critique.get("issues", [])
        critical_count = len([i for i in critical_issues if i.get("severity") == "CRITICAL"])
        
        if overall_quality == "EXCELLENT" and critical_count == 0:
            return "ACCEPT"
        elif overall_quality == "GOOD" and critical_count == 0:
            return "ACCEPT_WITH_MINOR_REVISIONS"
        elif critical_count > 0:
            return "MAJOR_REVISIONS_REQUIRED"
        else:
            return "REJECT"
    
    def _generate_next_steps(self, assessment: dict, critique: dict) -> list:
        """Generate actionable next steps."""
        
        steps = []
        
        critical_issues = [i for i in critique.get("issues", []) if i.get("severity") == "CRITICAL"]
        if critical_issues:
            steps.append({
                "priority": "HIGH",
                "action": f"Address {len(critical_issues)} critical issues",
                "details": [i.get("recommendation", "") for i in critical_issues[:3]]
            })
        
        major_issues = [i for i in critique.get("issues", []) if i.get("severity") == "MAJOR"]
        if major_issues:
            steps.append({
                "priority": "MEDIUM",
                "action": f"Resolve {len(major_issues)} major issues",
                "details": [i.get("recommendation", "") for i in major_issues[:3]]
            })
        
        if assessment.get("overall_quality") in ["EXCELLENT", "GOOD"]:
            steps.append({
                "priority": "LOW",
                "action": "Consider formatting and presentation improvements",
                "details": ["Polish figures and tables", "Proofread for typos"]
            })
        
        return steps if steps else [{"priority": "LOW", "action": "Paper is ready for submission"}]
    
    def get_workflow_report(self) -> dict:
        """Get detailed report of the review workflow."""
        
        return {
            "total_steps": len(self.workflow_history),
            "agents_involved": [step.get("agent") for step in self.workflow_history],
            "workflow": [
                {
                    "step": step.get("step"),
                    "agent": step.get("agent"),
                    "tool_calls": step.get("message").tool_calls or [],
                    "timestamp": step.get("message").timestamp
                }
                for step in self.workflow_history
            ]
        }
