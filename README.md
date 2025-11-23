# Multi-Agent Research Paper Reviewer

A sophisticated multi-agent system that reviews academic papers using specialized AI agents with distinct roles. Each agent has access to dedicated tools and collaborates in a structured workflow to provide comprehensive paper feedback.

## Overview

This system implements a 3-agent review pipeline:
1. **Reader** - Extracts and summarizes paper content
2. **MetaReviewer** - Assesses quality and research contribution
3. **Critic** - Identifies weaknesses and provides actionable feedback

## Quick Start

### Installation

```bash
cd paper_reviewer

# Install dependencies
pip install PyPDF2 streamlit --break-system-packages

# Verify installation
python -c "import PyPDF2; import streamlit; print('✓ Dependencies installed')"
```

### Run the Interactive UI

```bash
cd paper_reviewer
streamlit run ui/streamlit_app.py
```

Then open: `http://localhost:8501`

### Run Evaluation Harness

```bash
cd paper_reviewer
python -m pytest eval/evaluation_harness.py -v

# Or run directly:
python eval/evaluation_harness.py
```

### Review a Single Paper (Python API)

```python
import asyncio
from agents.orchestrator import PaperReviewOrchestrator

async def main():
    orchestrator = PaperReviewOrchestrator()
    review = await orchestrator.review_paper("sample_paper_1")
    print(review)

asyncio.run(main())
```

## Project Structure

```
paper_reviewer/
├── agents/
│   ├── base_agent.py           # Base agent class with tools
│   ├── tools.py                # Tool implementations (6 tools)
│   ├── reader_agent.py         # Reader agent implementation
│   ├── meta_reviewer_agent.py  # MetaReviewer agent implementation
│   ├── critic_agent.py         # Critic agent implementation
│   └── orchestrator.py         # Orchestration & workflow
├── mcp-server/
│   └── mcp_server.py           # MCP server for agent access
├── data/
│   ├── sample_papers/          # Sample paper texts
│   └── results/                # Review results (auto-created)
├── eval/
│   ├── test_cases.json         # 6+ test cases
│   ├── evaluation_harness.py   # Test runner & metrics
│   └── evaluation_report.json  # Results (auto-generated)
├── ui/
│   └── streamlit_app.py        # Web UI
├── ARCH.md                     # Architecture (1 page)
└── README.md                   # This file
```

## Agent Details

### Reader Agent
**Role:** Content Extraction & Summarization

Tools:
- `extract_pdf(pdf_path)` - Extract text and metadata from PDF
- `extract_sections(text)` - Parse major paper sections
- `load_sample_paper(paper_id)` - Load sample papers

Output:
```json
{
  "status": "success",
  "paper_id": "...",
  "summary": "...",
  "sections": {"abstract": "...", "methodology": "...", ...},
  "text_length": 5000,
  "key_insights": ["..."]
}
```

### MetaReviewer Agent
**Role:** Quality & Contribution Assessment

Tools:
- `extract_citations(text)` - Parse citations
- `save_review_result(filename, content)` - Persist results

Output:
```json
{
  "status": "success",
  "assessment": {
    "novelty_score": 8,
    "methodology_score": 7,
    "overall_quality": "EXCELLENT",
    "assessment_details": {...}
  }
}
```

### Critic Agent
**Role:** Issue Identification & Feedback

Tools:
- `analyze_text_quality(text)` - Readability & clarity metrics
- `extract_citations(text)` - Citation analysis

Output:
```json
{
  "status": "success",
  "critique": {
    "issues": [
      {
        "category": "CLARITY",
        "issue": "...",
        "severity": "MAJOR",
        "recommendation": "..."
      }
    ],
    "recommendations": [...]
  }
}
```

## Tool Implementations

The system includes 6 tools with full error handling:

1. **extract_pdf_text()** - PyPDF2-based PDF extraction
2. **extract_sections()** - Regex-based section parsing
3. **extract_citations()** - Citation format detection
4. **analyze_text_quality()** - Readability metrics (avg sentence length, complexity)
5. **save_review_result()** - JSON persistence
6. **load_sample_paper()** - File-based paper loading

## Evaluation Harness

### Running Tests

```bash
# Run all 6 test cases
python eval/evaluation_harness.py

# Run specific test
python -c "from eval.evaluation_harness import EvaluationHarness; 
h = EvaluationHarness('eval/test_cases.json'); 
import asyncio; 
asyncio.run(h.run_all_tests())"
```

### Test Cases (6 programmatic tests)

1. **TEST_001** - Basic paper loading and extraction
   - Validates Reader agent can extract text and identify sections
   - Expected: 3+ sections found, text > 100 chars

2. **TEST_002** - Citation extraction and analysis
   - Validates MetaReviewer can count and analyze citations
   - Expected: ≥5 citations found, assessment complete

3. **TEST_003** - Quality issue detection
   - Validates Critic agent identifies quality problems
   - Expected: Issues detected with severity levels

4. **TEST_004** - Full workflow orchestration
   - End-to-end review with all 3 agents
   - Expected: All steps complete, final recommendation provided

5. **TEST_005** - Error handling
   - Validates graceful handling of missing papers
   - Expected: Error returned, no crash

6. **TEST_006** - Assessment scoring
   - Validates scores are in valid ranges [0-10]
   - Expected: All scores within bounds

### Metrics Computed

- **Success Rate:** % of tests that passed
- **Latency:** Avg/Min/Max execution time per test (ms)
- **Tool Calls:** Total tool invocations per test
- **Constraint Violations:** Assessment scores out of range

### View Results

```bash
cat eval/evaluation_report.json | python -m json.tool
```

## MCP Server Usage

```python
from mcp_server.mcp_server import PaperReviewerMCPServer

server = PaperReviewerMCPServer()

# Submit paper
submit_resp = await server.submit_paper("paper.pdf")
task_id = submit_resp["task_id"]

# Execute review
result = await server.execute_review(task_id)

# Get trace
trace = await server.get_workflow_trace(task_id)
```

## Sample Output

```
======================================================================
Starting Multi-Agent Paper Review for: sample_paper_1
======================================================================

[1/3] Reader Agent: Extracting paper content...
✓ Reader completed. Found 5000 characters.
  Summary: This paper presents a comprehensive study of deep learning...

[2/3] MetaReviewer Agent: Assessing quality and contribution...
✓ MetaReviewer completed.
  Overall Quality: EXCELLENT
  Novelty Score: 8/10
  Methodology Score: 8/10

[3/3] Critic Agent: Identifying weaknesses and providing feedback...
✓ Critic completed.
  Critical Issues: 0
  Major Issues: 1
  Minor Issues: 2

======================================================================
Review Complete!
======================================================================
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│         User Input (Paper Path)                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
       ┌───────────────────────────┐
       │   Reader Agent            │
       │ - extract_pdf()           │
       │ - extract_sections()      │
       │ Output: sections, summary │
       └───────────────┬───────────┘
                       │
                       ▼
       ┌───────────────────────────┐
       │   MetaReviewer Agent      │
       │ - extract_citations()     │
       │ - save_review_result()    │
       │ Output: assessment scores │
       └───────────────┬───────────┘
                       │
                       ▼
       ┌───────────────────────────┐
       │   Critic Agent            │
       │ - analyze_text_quality()  │
       │ - extract_citations()     │
       │ Output: issues, recs      │
       └───────────────┬───────────┘
                       │
                       ▼
       ┌───────────────────────────┐
       │   Orchestrator            │
       │ - Compile final review    │
       │ - Generate recommendation │
       └───────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │  Final Review Report     │
        │  - Summary               │
        │  - Assessment            │
        │  - Critique              │
        │  - Recommendation        │
        └──────────────────────────┘
```

## Key Features

-  **3 Specialized Agents** - Each with distinct roles and tools
-  **6+ Tool Implementations** - PDF extraction, citation analysis, quality metrics
-  **Structured Workflow** - Sequential processing with shared outputs
-  **Comprehensive Evaluation** - 6+ programmatic test cases with metrics
-  **Interactive UI** - Streamlit-based web interface
-  **MCP Server** - Standardized agent access
-  **Error Handling** - Graceful degradation and informative errors
-  **Result Persistence** - Save and export reviews as JSON
-  **Tool Visibility** - All tool calls tracked in message history

## Performance Notes

- **Single Paper:** 5-10 seconds (3 agents, sequential execution)
- **Throughput:** ~6-12 papers/minute on single thread
- **Memory:** ~50MB per concurrent review
- **Scalability:** Can be parallelized at orchestrator level

## Limitations & Future Work

- Currently processes text-based papers (PDF parsing is basic)
- Assessment scores use heuristics (could use ML models)
- No multi-hop reasoning across documents
- Single-language support (English)
- No parallel agent execution (could speed up 3x with async)

## Citation

If you use this system, please cite:

```bibtex
@software{paper_reviewer_2025,
  title = {Multi-Agent Research Paper Reviewer},
  author = {Anindya Bandopadhyay},
  year = {2025},
  url = {https://github.com/andysundar/paper_review}
}
```

## License

Apache 2.0

## Contact

For questions or issues, please reach out to the me.
