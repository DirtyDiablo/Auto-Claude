"""
RAGAS Evaluation Framework
Repository: https://github.com/explodinggradients/ragas (8,000+ stars)
"""

from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness
    )
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    logger.warning("RAGAS not available - install with: pip install ragas")


class RAGASEvaluator:
    """Evaluate RAG pipeline quality using RAGAS metrics."""

    def __init__(self):
        if RAGAS_AVAILABLE:
            self.metrics = [
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
                answer_correctness
            ]
        else:
            self.metrics = []

    def evaluate_responses(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[str]
    ) -> Dict:
        """
        Evaluate RAG responses using RAGAS metrics.

        Args:
            questions: List of questions asked
            answers: List of generated answers
            contexts: List of context lists used for each answer
            ground_truths: List of expected correct answers

        Returns:
            Dictionary with evaluation metrics
        """
        if not RAGAS_AVAILABLE:
            return {"error": "RAGAS not available - install with: pip install ragas"}

        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
        }
        dataset = Dataset.from_dict(data)

        try:
            results = evaluate(dataset, metrics=self.metrics)

            return {
                "faithfulness": results.get("faithfulness", 0),
                "answer_relevancy": results.get("answer_relevancy", 0),
                "context_precision": results.get("context_precision", 0),
                "context_recall": results.get("context_recall", 0),
                "answer_correctness": results.get("answer_correctness", 0),
                "overall": sum(results.values()) / len(results) if results else 0
            }
        except Exception as e:
            logger.error(f"RAGAS evaluation error: {e}")
            return {"error": str(e)}

    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str
    ) -> Dict:
        """Evaluate a single response."""
        return self.evaluate_responses(
            [question], [answer], [contexts], [ground_truth]
        )

    def evaluate_batch(self, test_cases: List[Dict]) -> List[Dict]:
        """
        Evaluate a batch of test cases.

        Args:
            test_cases: List of dicts with keys: question, answer, contexts, ground_truth

        Returns:
            List of evaluation results for each test case
        """
        results = []
        for tc in test_cases:
            result = self.evaluate_single(
                question=tc["question"],
                answer=tc["answer"],
                contexts=tc.get("contexts", []),
                ground_truth=tc["ground_truth"]
            )
            result["question"] = tc["question"]
            results.append(result)
        return results


def get_evaluator() -> RAGASEvaluator:
    """Get a RAGAS evaluator instance."""
    return RAGASEvaluator()
