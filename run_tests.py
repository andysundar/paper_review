#!/usr/bin/env python3
"""Test runner for Multi-Agent Paper Reviewer."""
import sys
import asyncio

sys.path.insert(0, 'paper_reviewer')

from eval.evaluation_harness import EvaluationHarness


async def main():
    """Run evaluation harness."""
    test_cases_file = "eval/test_cases.json"
    output_file = "eval/evaluation_report.json"
    
    print("\n" + "="*70)
    print("MULTI-AGENT PAPER REVIEWER - TEST SUITE")
    print("="*70)
    
    harness = EvaluationHarness(test_cases_file)
    metrics = await harness.run_all_tests()
    
    harness.print_report(metrics)
    harness.save_report(metrics, output_file)
    
    return metrics


if __name__ == "__main__":
    metrics = asyncio.run(main())
    sys.exit(0 if metrics["summary"]["passed"] == metrics["summary"]["total_tests"] else 1)
