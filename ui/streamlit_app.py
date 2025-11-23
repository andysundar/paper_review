"""Streamlit UI for Multi-Agent Paper Reviewer."""
import streamlit as st
import asyncio
import json
from io import StringIO
import sys
import os

# Get the absolute path to paper_reviewer directory
script_dir = os.path.dirname(os.path.abspath(__file__))  # ui/ directory
parent_dir = os.path.dirname(script_dir)  # paper_reviewer/ directory
grandparent_dir = os.path.dirname(parent_dir)  # parent of paper_reviewer

# Add both paths to ensure imports work
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)

from agents.orchestrator import PaperReviewOrchestrator


def initialize_session_state():
    """Initialize session state variables."""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = PaperReviewOrchestrator()
    if 'current_review' not in st.session_state:
        st.session_state.current_review = None
    if 'review_history' not in st.session_state:
        st.session_state.review_history = []


def render_header():
    """Render page header."""
    st.set_page_config(page_title="Multi-Agent Paper Reviewer", layout="wide")
    st.title("📚 Multi-Agent Research Paper Reviewer")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Reader Agent", "Active", "Extraction")
    with col2:
        st.metric("MetaReviewer", "Active", "Assessment")
    with col3:
        st.metric("Critic Agent", "Active", "Feedback")


def render_input_section():
    """Render paper input section."""
    st.subheader("📄 Submit Paper for Review")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        paper_input = st.text_input(
            "Enter paper ID or path:",
            value="sample_paper_1",
            placeholder="e.g., sample_paper_1 or /path/to/paper.pdf"
        )
    
    with col2:
        submit_button = st.button("🔍 Review Paper", use_container_width=True)
    
    return paper_input, submit_button


async def execute_review(paper_path: str):
    """Execute paper review."""
    with st.spinner("🔄 Reviewing paper... This may take a moment."):
        try:
            review = await st.session_state.orchestrator.review_paper(paper_path)
            st.session_state.current_review = review
            st.session_state.review_history.append({
                "paper": paper_path,
                "review": review
            })
            return review
        except Exception as e:
            st.error(f"Error during review: {str(e)}")
            return None


def render_summary_section(review: dict):
    """Render summary section."""
    st.subheader("📊 Review Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        quality = review.get("quality_assessment", {}).get("overall_quality", "UNKNOWN")
        st.metric("Overall Quality", quality)
    
    with col2:
        novelty = review.get("quality_assessment", {}).get("novelty_score", 0)
        st.metric("Novelty Score", f"{novelty}/10")
    
    with col3:
        methodology = review.get("quality_assessment", {}).get("methodology_score", 0)
        st.metric("Methodology Score", f"{methodology}/10")
    
    with col4:
        recommendation = review.get("overall_recommendation", "UNKNOWN")
        color = "🟢" if recommendation == "ACCEPT" else "🟡" if "REVISIONS" in recommendation else "🔴"
        st.metric("Recommendation", f"{color} {recommendation}")


def render_assessment_section(review: dict):
    """Render detailed assessment."""
    st.subheader("📋 Quality Assessment")
    
    assessment = review.get("quality_assessment", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Assessment Scores:**")
        scores_data = {
            "Novelty": assessment.get("novelty_score", 0),
            "Methodology": assessment.get("methodology_score", 0),
            "Citations": assessment.get("citation_score", 0),
            "Completeness": assessment.get("completeness_score", 0),
            "Overall": assessment.get("average_score", 0)
        }
        
        for metric, score in scores_data.items():
            st.progress(min(score / 10, 1.0), text=f"{metric}: {score}/10")
    
    with col2:
        st.write("**Assessment Details:**")
        details = assessment.get("assessment_details", {})
        for key, value in details.items():
            st.write(f"• **{key}**: {value}")


def render_critique_section(review: dict):
    """Render critique section."""
    st.subheader("🔍 Detailed Critique")
    
    critique = review.get("critique", {})
    issues = critique.get("issues", [])
    
    # Issue summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        critical_count = len([i for i in issues if i.get("severity") == "CRITICAL"])
        st.metric("Critical Issues", critical_count, delta=None)
    
    with col2:
        major_count = len([i for i in issues if i.get("severity") == "MAJOR"])
        st.metric("Major Issues", major_count, delta=None)
    
    with col3:
        minor_count = len([i for i in issues if i.get("severity") == "MINOR"])
        st.metric("Minor Issues", minor_count, delta=None)
    
    # Issues list
    if issues:
        st.write("**Issues Found:**")
        
        for issue in issues:
            severity = issue.get("severity", "UNKNOWN")
            category = issue.get("category", "UNKNOWN")
            issue_text = issue.get("issue", "")
            recommendation = issue.get("recommendation", "")
            
            severity_color = "🔴" if severity == "CRITICAL" else "🟠" if severity == "MAJOR" else "🟡"
            
            with st.expander(f"{severity_color} [{category}] {issue_text[:60]}..."):
                st.write(f"**Severity:** {severity}")
                st.write(f"**Category:** {category}")
                st.write(f"**Issue:** {issue_text}")
                if recommendation:
                    st.write(f"**Recommendation:** {recommendation}")
    else:
        st.success("✓ No significant issues found!")


def render_recommendations_section(review: dict):
    """Render recommendations section."""
    st.subheader("💡 Recommendations & Next Steps")
    
    next_steps = review.get("next_steps", [])
    
    if next_steps:
        for step in next_steps:
            priority = step.get("priority", "UNKNOWN")
            action = step.get("action", "")
            details = step.get("details", [])
            
            priority_color = "🔴" if priority == "HIGH" else "🟠" if priority == "MEDIUM" else "🟢"
            
            with st.expander(f"{priority_color} [{priority}] {action}"):
                if details:
                    for detail in details:
                        st.write(f"• {detail}")
    
    # Overall recommendation
    recommendation = review.get("overall_recommendation", "UNKNOWN")
    
    st.markdown("---")
    
    if recommendation == "ACCEPT":
        st.success(f"✅ **Recommendation: ACCEPT**\n\nThis paper is ready for publication.")
    elif "MINOR_REVISIONS" in recommendation:
        st.info(f"ℹ️ **Recommendation: {recommendation}**\n\nAddress minor issues to strengthen the paper.")
    elif recommendation == "MAJOR_REVISIONS_REQUIRED":
        st.warning(f"⚠️ **Recommendation: {recommendation}**\n\nSignificant improvements needed before resubmission.")
    else:
        st.error(f"❌ **Recommendation: {recommendation}**")


def render_extraction_section(review: dict):
    """Render extraction section."""
    st.subheader("📖 Paper Extraction")
    
    extraction = review.get("reader_extraction", {})
    
    st.write(f"**Summary:**\n{extraction.get('summary', 'N/A')}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Text Length", f"{extraction.get('text_length', 0):,} chars")
    with col2:
        st.metric("Sections Found", extraction.get("sections_identified", 0))
    with col3:
        insights = extraction.get("key_insights", [])
        st.metric("Key Insights", len(insights))


def render_workflow_section(review: dict):
    """Render workflow trace."""
    st.subheader("🔄 Workflow Trace")
    
    workflow_steps = [
        {"agent": "Reader", "role": "Content Extraction"},
        {"agent": "MetaReviewer", "role": "Quality Assessment"},
        {"agent": "Critic", "role": "Issue Identification"}
    ]
    
    for i, step in enumerate(workflow_steps, 1):
        st.write(f"**Step {i}: {step['agent']}**")
        st.caption(f"Role: {step['role']}")
        st.progress((i / len(workflow_steps)), text=f"{i}/{len(workflow_steps)} complete")


def render_download_section(review: dict):
    """Render download section."""
    st.subheader("📥 Export Review")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export as JSON
        json_str = json.dumps(review, indent=2)
        st.download_button(
            label="📄 Download as JSON",
            data=json_str,
            file_name=f"review_{review.get('paper_id', 'paper')}.json",
            mime="application/json"
        )
    
    with col2:
        # Export as formatted text
        text_str = format_review_as_text(review)
        st.download_button(
            label="📝 Download as Text",
            data=text_str,
            file_name=f"review_{review.get('paper_id', 'paper')}.txt",
            mime="text/plain"
        )


def format_review_as_text(review: dict) -> str:
    """Format review as readable text."""
    
    lines = [
        "=" * 70,
        "MULTI-AGENT PAPER REVIEW",
        "=" * 70,
        f"\nPaper ID: {review.get('paper_id')}",
        f"Status: {review.get('review_status')}",
        "\n" + "=" * 70,
        "SUMMARY",
        "=" * 70,
    ]
    
    extraction = review.get("reader_extraction", {})
    lines.append(f"\nSummary:\n{extraction.get('summary', 'N/A')}")
    
    assessment = review.get("quality_assessment", {})
    lines.append("\n" + "=" * 70)
    lines.append("QUALITY ASSESSMENT")
    lines.append("=" * 70)
    lines.append(f"Overall Quality: {assessment.get('overall_quality', 'UNKNOWN')}")
    lines.append(f"Novelty Score: {assessment.get('novelty_score', 0)}/10")
    lines.append(f"Methodology Score: {assessment.get('methodology_score', 0)}/10")
    lines.append(f"Average Score: {assessment.get('average_score', 0)}/10")
    
    critique = review.get("critique", {})
    lines.append("\n" + "=" * 70)
    lines.append("CRITIQUE")
    lines.append("=" * 70)
    
    issues = critique.get("issues", [])
    for issue in issues:
        lines.append(f"\n- [{issue.get('severity')}] {issue.get('issue')}")
        if issue.get("recommendation"):
            lines.append(f"  Recommendation: {issue.get('recommendation')}")
    
    lines.append("\n" + "=" * 70)
    lines.append("RECOMMENDATION")
    lines.append("=" * 70)
    lines.append(f"\n{review.get('overall_recommendation', 'UNKNOWN')}")
    
    return "\n".join(lines)


def main():
    """Main app function."""
    initialize_session_state()
    render_header()
    
    # Input section
    paper_input, submit_button = render_input_section()
    
    # Execute review if button pressed
    if submit_button and paper_input:
        review = asyncio.run(execute_review(paper_input))
        if review:
            st.session_state.current_review = review
    
    # Display results if review exists
    if st.session_state.current_review:
        review = st.session_state.current_review
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Summary",
            "📋 Assessment",
            "🔍 Critique",
            "📖 Extraction",
            "🔄 Workflow"
        ])
        
        with tab1:
            render_summary_section(review)
            render_recommendations_section(review)
        
        with tab2:
            render_assessment_section(review)
        
        with tab3:
            render_critique_section(review)
        
        with tab4:
            render_extraction_section(review)
        
        with tab5:
            render_workflow_section(review)
        
        st.markdown("---")
        render_download_section(review)
    
    else:
        st.info("👈 Enter a paper ID and click 'Review Paper' to get started!")


if __name__ == "__main__":
    main()
