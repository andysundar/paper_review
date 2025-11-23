"""Reader Agent: Extracts and summarizes paper content."""
import asyncio
import json
from agents.base_agent import BaseAgent, Message
from agents.tools import extract_pdf_text, extract_sections, load_sample_paper


class ReaderAgent(BaseAgent):
    """
    Reader Agent Role:
    - Extracts text and structure from academic papers
    - Identifies key sections (abstract, methodology, results)
    - Summarizes main contributions
    - Uses: PDF extraction tool, section extraction tool
    """
    
    def __init__(self):
        super().__init__(
            name="Reader",
            role="Content Extractor & Summarizer"
        )
        
        # Register tools
        self.register_tool("extract_pdf", extract_pdf_text)
        self.register_tool("extract_sections", extract_sections)
        self.register_tool("load_sample_paper", load_sample_paper)
    
    async def process(self, paper_path: str) -> Message:
        """
        Process paper and extract key information.
        
        Args:
            paper_path: Path to PDF or paper identifier
        
        Returns:
            Message with extracted content and summary
        """
        tool_calls = []
        
        # First, try to load the paper (works with sample papers)
        load_result = await self.execute_tool("load_sample_paper", paper_id=paper_path)
        
        if load_result.get("success"):
            text = load_result["content"]
            tool_calls.append({
                "tool": "load_sample_paper",
                "input": {"paper_id": paper_path},
                "output": f"Loaded sample paper: {paper_path}"
            })
        else:
            # Try to extract from PDF
            extract_result = await self.execute_tool("extract_pdf", pdf_path=paper_path)
            
            if not extract_result.get("success"):
                error_msg = extract_result.get("error", "Unknown error")
                response = Message(
                    sender=self.name,
                    content=f"Failed to load paper: {error_msg}",
                    tool_calls=[]
                )
                self.add_to_history(response)
                return response
            
            text = extract_result["text"]
            tool_calls.append({
                "tool": "extract_pdf",
                "input": {"pdf_path": paper_path},
                "output": f"Extracted {extract_result['pages']} pages from PDF"
            })
        
        # Extract sections
        sections_result = await self.execute_tool("extract_sections", text=text)
        tool_calls.append({
            "tool": "extract_sections",
            "input": {"text_length": len(text)},
            "output": f"Identified {sections_result.get('section_count', 0)} sections"
        })
        
        # Generate summary
        summary = self._generate_summary(text, sections_result)
        
        response_content = {
            "status": "success",
            "paper_id": paper_path,
            "summary": summary,
            "sections": sections_result.get("sections", {}),
            "text_length": len(text),
            "key_insights": [
                "Paper structure identified and parsed",
                f"Extracted {sections_result.get('section_count', 0)} major sections",
                "Ready for detailed review by specialized agents"
            ]
        }
        
        response = Message(
            sender=self.name,
            content=json.dumps(response_content, indent=2),
            tool_calls=tool_calls
        )
        
        self.add_to_history(response)
        return response
    
    def _generate_summary(self, text: str, sections_result: dict) -> str:
        """Generate a high-level summary of the paper."""
        abstract = sections_result.get("sections", {}).get("abstract", "")
        
        if abstract:
            summary = abstract[:300] + "..." if len(abstract) > 300 else abstract
        else:
            # Fallback: use first 300 chars
            summary = text[:300] + "..."
        
        return summary
