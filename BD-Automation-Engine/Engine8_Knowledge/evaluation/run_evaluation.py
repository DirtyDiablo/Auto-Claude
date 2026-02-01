"""Run RAGAS evaluation on the BD Intelligence Hub."""

import json
import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict

# Add parent paths
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ragas_evaluator import get_evaluator

try:
    from scripts.query_router import QueryRouter
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False


async def run_evaluation(test_file: str = "test_cases.json") -> Dict:
    """
    Run RAGAS evaluation using test cases.

    Args:
        test_file: Path to test cases JSON file

    Returns:
        Dictionary with evaluation results
    """
    evaluator = get_evaluator()

    # Load test cases
    test_path = os.path.join(os.path.dirname(__file__), test_file)
    with open(test_path) as f:
        test_data = json.load(f)

    test_cases = test_data["test_cases"]

    if ROUTER_AVAILABLE:
        router = QueryRouter()
    else:
        print("Warning: QueryRouter not available, using mock responses")
        router = None

    results = []
    total_score = 0

    print(f"\n{'='*60}")
    print("BD Intelligence Hub - RAGAS Evaluation")
    print(f"{'='*60}")
    print(f"Running {len(test_cases)} test cases...\n")

    for i, tc in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {tc['question'][:50]}...")

        # Get system response
        if router:
            try:
                response = await router.smart_query(tc["question"])
                answer = response.answer
                contexts = [s.get("text", "") for s in response.sources[:3]]
            except Exception as e:
                print(f"  Error: {e}")
                answer = "Error retrieving answer"
                contexts = []
        else:
            # Mock response for testing without router
            answer = f"Mock answer for: {tc['question']}"
            contexts = ["Mock context 1", "Mock context 2"]

        # Evaluate
        eval_result = evaluator.evaluate_single(
            question=tc["question"],
            answer=answer,
            contexts=contexts,
            ground_truth=tc["ground_truth"]
        )

        score = eval_result.get("overall", 0)
        total_score += score

        results.append({
            "question": tc["question"],
            "system_answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "ground_truth": tc["ground_truth"],
            "metrics": eval_result
        })

        status = "PASS" if score >= 0.5 else "FAIL"
        print(f"  Score: {score:.2f} [{status}]")

    # Calculate averages
    avg_score = total_score / len(test_cases) if test_cases else 0

    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Test Cases: {len(test_cases)}")
    print(f"Average Score: {avg_score:.2f}")
    print(f"Pass Rate: {sum(1 for r in results if r['metrics'].get('overall', 0) >= 0.5)}/{len(test_cases)}")

    # Metric averages
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "answer_correctness"]
    print("\nMetric Averages:")
    for metric in metrics:
        avg = sum(r["metrics"].get(metric, 0) for r in results) / len(results) if results else 0
        print(f"  {metric}: {avg:.2f}")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(test_cases),
        "average_score": avg_score,
        "results": results
    }

    output_path = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    return output


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run RAGAS evaluation")
    parser.add_argument("--test-file", default="test_cases.json", help="Test cases file")
    args = parser.parse_args()

    asyncio.run(run_evaluation(args.test_file))


if __name__ == "__main__":
    main()
