#!/usr/bin/env python3
"""
Simple standalone demo - Run this to test the system
Just: python simple_demo.py
"""
import sys
import os
import asyncio
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import
from agents.orchestrator import PaperReviewOrchestrator


async def main():
    print("\n" + "="*70)
    print("PAPER REVIEWER DEMO")
    print("="*70 + "\n")
    
    orchestrator = PaperReviewOrchestrator()
    
    # Review a sample paper
    print("Reviewing sample_paper_1...\n")
    review = await orchestrator.review_paper("sample_paper_1")
    
    # Display results
    print("\n" + "="*70)
    print("REVIEW RESULTS")
    print("="*70 + "\n")
    
    print(f"Paper: {review.get('paper_id')}")
    print(f"Status: {review.get('review_status')}")
    
    assessment = review.get("quality_assessment", {})
    print(f"\nQuality Assessment:")
    print(f"  Overall Quality: {assessment.get('overall_quality')}")
    print(f"  Novelty Score: {assessment.get('novelty_score')}/10")
    print(f"  Methodology Score: {assessment.get('methodology_score')}/10")
    print(f"  Average Score: {assessment.get('average_score')}/10")
    
    critique = review.get("critique", {})
    issues = critique.get("issues", [])
    print(f"\nIssues Found: {len(issues)}")
    for issue in issues[:3]:
        print(f"  - [{issue.get('severity')}] {issue.get('issue')}")
    
    print(f"\nRecommendation: {review.get('overall_recommendation')}")
    print("\n" + "="*70 + "\n")
    
    # Save results
    with open("review_output.json", "w") as f:
        json.dump(review, f, indent=2)
    print("✅ Review saved to review_output.json")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
