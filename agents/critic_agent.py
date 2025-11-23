"""Critic Agent: Identifies weaknesses and provides detailed feedback."""
import asyncio
import json
from agents.base_agent import BaseAgent, Message
from agents.tools import analyze_text_quality, extract_citations


class CriticAgent(BaseAgent):
    """
    Critic Agent Role:
    - Identifies methodological weaknesses
    - Finds logical gaps and inconsistencies
    - Assesses clarity and presentation
    - Flags potential issues
    - Uses: Text quality analysis tool, citation extraction tool
    """
    
    def __init__(self):
        super().__init__(
            name="Critic",
            role="Weakness & Issue Identifier"
        )
        
        # Register tools
        self.register_tool("analyze_text_quality", analyze_text_quality)
        self.register_tool("extract_citations", extract_citations)
    
    async def process(self, reader_output: dict, meta_assessment: dict) -> Message:
        """
        Identify issues and weaknesses in the paper.
        
        Args:
            reader_output: Dictionary with extracted paper content from Reader
            meta_assessment: Assessment from MetaReviewer
        
        Returns:
            Message with identified issues and recommendations
        """
        tool_calls = []
        
        # Reconstruct text from sections
        sections = reader_output.get("sections", {})
        full_text = " ".join(str(v) for v in sections.values())
        
        # Analyze text quality
        quality_result = await self.execute_tool("analyze_text_quality", text=full_text)
        tool_calls.append({
            "tool": "analyze_text_quality",
            "input": {"text_length": len(full_text)},
            "output": f"Identified {len(quality_result.get('issues', []))} quality issues"
        })
        
        # Analyze citations
        citations_result = await self.execute_tool("extract_citations", text=full_text)
        tool_calls.append({
            "tool": "extract_citations",
            "input": {"text_length": len(full_text)},
            "output": f"Analyzed {citations_result.get('citation_count', 0)} citations"
        })
        
        # Generate detailed critique
        critique = self._generate_critique(
            sections=sections,
            quality_result=quality_result,
            citations_result=citations_result,
            meta_assessment=meta_assessment,
            reader_output=reader_output
        )
        
        response_content = {
            "status": "success",
            "paper_id": reader_output.get("paper_id"),
            "critique": critique,
            "severity_levels": {
                "critical": len([i for i in critique.get("issues", []) if i.get("severity") == "CRITICAL"]),
                "major": len([i for i in critique.get("issues", []) if i.get("severity") == "MAJOR"]),
                "minor": len([i for i in critique.get("issues", []) if i.get("severity") == "MINOR"])
            }
        }
        
        response = Message(
            sender=self.name,
            content=json.dumps(response_content, indent=2),
            tool_calls=tool_calls
        )
        
        self.add_to_history(response)
        return response
    
    def _generate_critique(self, sections: dict, quality_result: dict, 
                          citations_result: dict, meta_assessment: dict,
                          reader_output: dict) -> dict:
        """Generate detailed critique with identified issues."""
        
        issues = []
        
        # Quality issues
        for issue in quality_result.get("issues", []):
            issues.append({
                "category": "CLARITY",
                "issue": issue,
                "severity": "MAJOR"
            })
        
        # Structural issues
        if not sections.get("methodology"):
            issues.append({
                "category": "STRUCTURE",
                "issue": "Methodology section is missing or unclear",
                "severity": "CRITICAL",
                "recommendation": "Add detailed methodology description"
            })
        
        if not sections.get("conclusion"):
            issues.append({
                "category": "STRUCTURE",
                "issue": "Conclusion section is missing",
                "severity": "CRITICAL",
                "recommendation": "Add conclusion summarizing findings and future work"
            })
        
        # Citation issues
        citation_count = citations_result.get("citation_count", 0)
        if citation_count < 10:
            issues.append({
                "category": "REFERENCES",
                "issue": f"Insufficient citations ({citation_count} found)",
                "severity": "MAJOR",
                "recommendation": "Add more relevant references to support claims"
            })
        
        # Readability issues
        metrics = quality_result.get("metrics", {})
        if metrics.get("avg_sentence_length", 0) > 25:
            issues.append({
                "category": "READABILITY",
                "issue": "Sentences are too long on average",
                "severity": "MINOR",
                "recommendation": "Break longer sentences into shorter, clearer ones"
            })
        
        # Abstract check
        abstract = sections.get("abstract", "")
        if len(abstract) < 50:
            issues.append({
                "category": "CONTENT",
                "issue": "Abstract is too brief",
                "severity": "MAJOR",
                "recommendation": "Expand abstract to properly summarize the paper"
            })
        
        # Low quality score check
        if meta_assessment.get("overall_quality") == "POOR":
            issues.append({
                "category": "OVERALL",
                "issue": "Overall paper quality is poor",
                "severity": "CRITICAL",
                "recommendation": "Major revisions needed across all sections"
            })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues)
        
        return {
            "issue_count": len(issues),
            "issues": issues,
            "recommendations": recommendations,
            "summary": self._generate_summary(issues)
        }
    
    def _generate_recommendations(self, issues: list) -> list:
        """Generate actionable recommendations."""
        recommendations = []
        
        critical_count = len([i for i in issues if i.get("severity") == "CRITICAL"])
        major_count = len([i for i in issues if i.get("severity") == "MAJOR"])
        
        if critical_count > 0:
            recommendations.append({
                "priority": 1,
                "recommendation": f"Address {critical_count} critical issues before resubmission"
            })
        
        if major_count > 0:
            recommendations.append({
                "priority": 2,
                "recommendation": f"Resolve {major_count} major issues to improve paper quality"
            })
        
        recommendations.append({
            "priority": 3,
            "recommendation": "Consider reviewer feedback and minor improvements"
        })
        
        return recommendations
    
    def _generate_summary(self, issues: list) -> str:
        """Generate summary of critique."""
        if not issues:
            return "No significant issues identified."
        
        critical = len([i for i in issues if i.get("severity") == "CRITICAL"])
        major = len([i for i in issues if i.get("severity") == "MAJOR"])
        minor = len([i for i in issues if i.get("severity") == "MINOR"])
        
        summary = f"Identified {len(issues)} total issues: "
        parts = []
        if critical > 0:
            parts.append(f"{critical} critical")
        if major > 0:
            parts.append(f"{major} major")
        if minor > 0:
            parts.append(f"{minor} minor")
        
        summary += ", ".join(parts) + "."
        
        return summary
