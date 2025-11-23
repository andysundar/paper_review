"""MetaReviewer Agent: Assesses research contribution and methodological quality."""
import asyncio
import json
from agents.base_agent import BaseAgent, Message
from agents.tools import extract_citations, save_review_result


class MetaReviewerAgent(BaseAgent):
    """
    MetaReviewer Agent Role:
    - Evaluates research novelty and contribution
    - Assesses methodological soundness
    - Checks citation patterns and references
    - Generates structured review assessment
    - Uses: Citation extraction tool, file I/O tool
    """
    
    def __init__(self):
        super().__init__(
            name="MetaReviewer",
            role="Quality & Contribution Assessor"
        )
        
        # Register tools
        self.register_tool("extract_citations", extract_citations)
        self.register_tool("save_review", save_review_result)
    
    async def process(self, reader_output: dict) -> Message:
        """
        Assess paper quality based on Reader output.
        
        Args:
            reader_output: Dictionary with extracted paper content from Reader
        
        Returns:
            Message with quality assessment
        """
        tool_calls = []
        
        # Extract full text for citation analysis
        sections = reader_output.get("sections", {})
        full_text = " ".join(str(v) for v in sections.values())
        
        # Analyze citations
        citations_result = await self.execute_tool("extract_citations", text=full_text)
        tool_calls.append({
            "tool": "extract_citations",
            "input": {"text_length": len(full_text)},
            "output": f"Found {citations_result.get('citation_count', 0)} citations"
        })
        
        # Generate assessment
        assessment = self._assess_quality(
            sections=sections,
            citations=citations_result,
            reader_output=reader_output
        )
        
        # Save review
        save_result = await self.execute_tool(
            "save_review",
            filename=f"{reader_output.get('paper_id', 'paper')}_assessment.json",
            content=assessment
        )
        tool_calls.append({
            "tool": "save_review",
            "input": {"filename": f"{reader_output.get('paper_id')}_assessment.json"},
            "output": f"Saved to {save_result.get('filepath', 'unknown')}"
        })
        
        response_content = {
            "status": "success",
            "paper_id": reader_output.get("paper_id"),
            "assessment": assessment,
            "citations_found": citations_result.get("citation_count", 0),
            "novelty_score": assessment.get("novelty_score", 0),
            "methodology_score": assessment.get("methodology_score", 0),
            "overall_quality": assessment.get("overall_quality", "UNKNOWN")
        }
        
        response = Message(
            sender=self.name,
            content=json.dumps(response_content, indent=2),
            tool_calls=tool_calls
        )
        
        self.add_to_history(response)
        return response
    
    def _assess_quality(self, sections: dict, citations: dict, reader_output: dict) -> dict:
        """Generate quality assessment based on multiple factors."""
        
        # Novelty assessment
        abstract = sections.get("abstract", "")
        has_novel_language = any(word in abstract.lower() for word in 
                                 ["novel", "new", "first", "propose", "introduce"])
        novelty_score = 7 if has_novel_language else 5
        
        # Methodology assessment
        methodology = sections.get("methodology", "")
        has_methodology = len(methodology) > 100
        methodology_score = 8 if has_methodology else 4
        
        # Citation assessment
        citation_count = citations.get("citation_count", 0)
        citation_score = min(10, 3 + (citation_count // 5))  # More citations = better
        
        # Completeness assessment
        sections_present = len([s for s in sections.values() if s])
        completeness_score = min(10, 2 + (sections_present * 1.5))
        
        # Overall quality
        avg_score = (novelty_score + methodology_score + citation_score + completeness_score) / 4
        
        if avg_score >= 8:
            overall_quality = "EXCELLENT"
        elif avg_score >= 6:
            overall_quality = "GOOD"
        elif avg_score >= 4:
            overall_quality = "FAIR"
        else:
            overall_quality = "POOR"
        
        return {
            "novelty_score": novelty_score,
            "methodology_score": methodology_score,
            "citation_score": citation_score,
            "completeness_score": completeness_score,
            "overall_quality": overall_quality,
            "average_score": round(avg_score, 2),
            "assessment_details": {
                "has_clear_methodology": has_methodology,
                "demonstrates_novelty": has_novel_language,
                "adequate_citations": citation_count >= 10,
                "sections_completeness": f"{sections_present}/6 major sections"
            }
        }
