"""Tools for PDF extraction and text processing."""
import json
import os
import re
from typing import Optional
import PyPDF2


# Tool 1: PDF Extraction
def extract_pdf_text(pdf_path: str) -> dict:
    """
    Extract text from PDF file.
    Used by: Reader Agent
    """
    try:
        if not os.path.exists(pdf_path):
            return {"error": f"PDF not found: {pdf_path}"}
        
        text = ""
        metadata = {}
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = pdf_reader.metadata or {}
            
            for page_num, page in enumerate(pdf_reader.pages):
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text()
        
        return {
            "success": True,
            "text": text,
            "pages": len(pdf_reader.pages),
            "metadata": {
                "title": metadata.get("/Title", "Unknown"),
                "author": metadata.get("/Author", "Unknown"),
                "creation_date": metadata.get("/CreationDate", "Unknown")
            }
        }
    except Exception as e:
        return {"error": f"PDF extraction failed: {str(e)}"}


# Tool 2: Section Extraction
def extract_sections(text: str) -> dict:
    """
    Extract key sections from paper text.
    Used by: Reader Agent
    """
    try:
        sections = {
            "abstract": "",
            "introduction": "",
            "methodology": "",
            "results": "",
            "conclusion": "",
            "references": ""
        }
        
        # Simple heuristic-based extraction
        patterns = {
            "abstract": r"(?i)(abstract|summary)(.*?)(?=introduction|1\.|$)",
            "introduction": r"(?i)(introduction|1\.)(.*?)(?=method|2\.|$)",
            "methodology": r"(?i)(method|methodology|approach|2\.)(.*?)(?=result|experiment|3\.|$)",
            "results": r"(?i)(result|experiment|evaluation|finding|3\.)(.*?)(?=conclusion|4\.|discuss|$)",
            "conclusion": r"(?i)(conclusion|future work|4\.)(.*?)(?=reference|5\.|$)",
            "references": r"(?i)(reference|bibliography)(.*?)$"
        }
        
        for section, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(0)[:500]  # Limit to 500 chars per section
        
        return {
            "success": True,
            "sections": sections,
            "section_count": len([s for s in sections.values() if s])
        }
    except Exception as e:
        return {"error": f"Section extraction failed: {str(e)}"}


# Tool 3: Entity/Citation Extraction
def extract_citations(text: str) -> dict:
    """
    Extract citations from paper text.
    Used by: Reader & Critic Agents
    """
    try:
        # Simple regex patterns for common citation formats
        patterns = {
            "bracket_style": r"\[(\d+)\]",  # [1], [2]
            "parenthetical": r"\(([A-Z][a-z]+\set\sal\.,?\s?\d{4})\)",  # (Smith et al., 2020)
            "author_year": r"([A-Z][a-z]+\s+(?:and\s+)?(?:[A-Z][a-z]+)?\s+\(\d{4}\))"
        }
        
        citations = {}
        for style, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                citations[style] = matches[:10]  # Top 10 citations per style
        
        return {
            "success": True,
            "citation_count": sum(len(v) for v in citations.values()),
            "citations_by_style": citations
        }
    except Exception as e:
        return {"error": f"Citation extraction failed: {str(e)}"}


# Tool 4: Text Analysis
def analyze_text_quality(text: str) -> dict:
    """
    Analyze text quality metrics.
    Used by: Critic Agent
    """
    try:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = text.split()
        
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Check for clarity issues
        complex_words = [w for w in words if len(w) > 12]
        
        metrics = {
            "total_words": len(words),
            "total_sentences": len(sentences),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "complex_word_ratio": round(len(complex_words) / len(words), 3) if words else 0,
            "readability_score": round(20 - avg_sentence_length / 2, 1)  # Simple readability
        }
        
        issues = []
        if metrics["avg_sentence_length"] > 20:
            issues.append("Sentences are too long (potential clarity issue)")
        if metrics["complex_word_ratio"] > 0.15:
            issues.append("Too many complex words (potential readability issue)")
        
        return {
            "success": True,
            "metrics": metrics,
            "issues": issues
        }
    except Exception as e:
        return {"error": f"Text analysis failed: {str(e)}"}


# Tool 5: File I/O for saving results
def save_review_result(filename: str, content: dict) -> dict:
    """
    Save review results to file.
    Used by: MetaReviewer Agent
    """
    try:
        os.makedirs("paper_reviewer/data/results", exist_ok=True)
        filepath = f"paper_reviewer/data/results/{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(content, f, indent=2)
        
        return {
            "success": True,
            "filepath": filepath,
            "size_bytes": os.path.getsize(filepath)
        }
    except Exception as e:
        return {"error": f"File save failed: {str(e)}"}


# Tool 6: Load sample papers
def load_sample_paper(paper_id: str) -> dict:
    """
    Load sample paper from data directory.
    Used by: Reader Agent
    """
    try:
        sample_dir = "paper_reviewer/data/sample_papers"
        os.makedirs(sample_dir, exist_ok=True)
        
        # Return a sample paper if it exists
        filepath = f"{sample_dir}/{paper_id}.txt"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            return {"success": True, "content": content}
        else:
            return {"error": f"Paper not found: {paper_id}"}
    except Exception as e:
        return {"error": f"Load paper failed: {str(e)}"}
