"""Phase 47A — Domain Embedding API (12 endpoints).

REST endpoints for synthetic data generation, fine-tuning, evaluation,
benchmarking, deployment, and A/B testing of domain-specific embeddings.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.embeddings.synthetic_data_generator import (
    SyntheticDataGenerator, get_synthetic_generator,
)
from src.embeddings.fine_tuner import (
    EmbeddingFineTuner, TrainingConfig, get_fine_tuner,
)
from src.embeddings.benchmark_suite import (
    EmbeddingBenchmarkSuite, GoldenQuery, get_benchmark_suite,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class SyntheticGenerateRequest(BaseModel):
    strategies: Optional[List[str]] = None
    max_per_strategy: int = 50


class FineTuneRequest(BaseModel):
    strategies: Optional[List[str]] = None
    max_triplets_per_strategy: int = 50
    base_model: str = "nomic-ai/modernbert-embed-base"
    matryoshka_dims: List[int] = Field(default_factory=lambda: [768, 512, 256, 128, 64])
    learning_rate: float = 2e-5
    batch_size: int = 32
    epochs: int = 3


class EvaluateRequest(BaseModel):
    model_id: str
    dimension: int = 768


class CompareRequest(BaseModel):
    model_a_id: str
    model_b_id: str


class DeployRequest(BaseModel):
    model_id: str


class BenchmarkRequest(BaseModel):
    model_id: str
    model_name: str = ""
    is_fine_tuned: bool = False


class ABTestStartRequest(BaseModel):
    model_a_id: str
    model_b_id: str
    traffic_split: float = 0.5


# =========================================
# ROUTE SETUP
# =========================================

def include_embeddings_router(app: FastAPI) -> None:
    """Register all embedding fine-tuning endpoints on the FastAPI app."""

    generator = get_synthetic_generator()
    tuner = get_fine_tuner()
    bench = get_benchmark_suite()

    # --------------------------------------------------
    # 1. POST /api/embeddings/synthetic/generate — Generate training triplets
    # --------------------------------------------------
    @app.post("/api/embeddings/synthetic/generate")
    async def embeddings_synthetic_generate(req: SyntheticGenerateRequest):
        """Generate synthetic training triplets."""
        job = generator.generate(
            strategies=req.strategies,
            max_per_strategy=req.max_per_strategy,
        )
        return {
            "job_id": job.id,
            "total_triplets": job.total_triplets,
            "by_strategy": job.triplets_by_strategy,
            "by_source": job.triplets_by_source,
            "by_difficulty": job.triplets_by_difficulty,
            "duration_sec": job.duration_sec,
        }

    # --------------------------------------------------
    # 2. GET /api/embeddings/synthetic/stats — Training data statistics
    # --------------------------------------------------
    @app.get("/api/embeddings/synthetic/stats")
    async def embeddings_synthetic_stats():
        """Get synthetic data generation statistics."""
        return generator.get_stats()

    # --------------------------------------------------
    # 3. POST /api/embeddings/fine-tune — Start fine-tuning job
    # --------------------------------------------------
    @app.post("/api/embeddings/fine-tune")
    async def embeddings_fine_tune(req: FineTuneRequest):
        """Start a fine-tuning job with auto-generated training data."""
        # Generate triplets first
        gen_job = generator.generate(
            strategies=req.strategies,
            max_per_strategy=req.max_triplets_per_strategy,
        )
        triplets = generator.get_triplets()

        if not triplets:
            raise HTTPException(400, "No training triplets generated")

        config = TrainingConfig(
            base_model=req.base_model,
            matryoshka_dims=req.matryoshka_dims,
            learning_rate=req.learning_rate,
            batch_size=req.batch_size,
            epochs=req.epochs,
        )

        job = tuner.start_fine_tuning(triplets, config)

        return {
            "job_id": job.id,
            "model_name": job.model_name,
            "status": job.status,
            "training_triplets": job.training_triplets,
            "eval_triplets": job.eval_triplets,
            "best_dimension": job.best_dimension,
            "metrics": {
                str(dim): metrics.to_dict()
                for dim, metrics in job.metrics.items()
            },
            "training_loss_final": job.training_loss[-1] if job.training_loss else None,
            "duration_sec": job.duration_sec,
        }

    # --------------------------------------------------
    # 4. GET /api/embeddings/fine-tune/{job_id} — Fine-tuning job status
    # --------------------------------------------------
    @app.get("/api/embeddings/fine-tune/{job_id}")
    async def embeddings_fine_tune_status(job_id: str):
        """Get fine-tuning job status and metrics."""
        job = tuner.get_job(job_id)
        if not job:
            raise HTTPException(404, "Fine-tuning job not found")

        return {
            "job_id": job.id,
            "model_name": job.model_name,
            "status": job.status,
            "training_triplets": job.training_triplets,
            "eval_triplets": job.eval_triplets,
            "best_dimension": job.best_dimension,
            "metrics": {
                str(dim): metrics.to_dict()
                for dim, metrics in job.metrics.items()
            },
            "training_loss": job.training_loss,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "duration_sec": job.duration_sec,
        }

    # --------------------------------------------------
    # 5. POST /api/embeddings/evaluate — Evaluate model on test set
    # --------------------------------------------------
    @app.post("/api/embeddings/evaluate")
    async def embeddings_evaluate(req: EvaluateRequest):
        """Evaluate a model on current test triplets."""
        triplets = generator.get_triplets()
        if not triplets:
            raise HTTPException(400, "No test triplets available. Generate data first.")

        metrics = tuner.evaluate_model(req.model_id, triplets, req.dimension)
        return metrics.to_dict()

    # --------------------------------------------------
    # 6. POST /api/embeddings/benchmark — Run golden benchmark suite
    # --------------------------------------------------
    @app.post("/api/embeddings/benchmark")
    async def embeddings_benchmark(req: BenchmarkRequest):
        """Run golden benchmark suite against a model."""
        run = bench.run_benchmark(
            model_id=req.model_id,
            model_name=req.model_name,
            is_fine_tuned=req.is_fine_tuned,
        )
        return {
            "run_id": run.id,
            "model_id": run.model_id,
            "model_name": run.model_name,
            "total_queries": run.total_queries,
            "overall_metrics": run.overall_metrics,
            "metrics_by_category": run.metrics_by_category,
            "passed_regression": run.passed_regression,
            "regression_details": run.regression_details,
        }

    # --------------------------------------------------
    # 7. POST /api/embeddings/compare — Compare two models
    # --------------------------------------------------
    @app.post("/api/embeddings/compare")
    async def embeddings_compare(req: CompareRequest):
        """Compare two embedding models head-to-head."""
        triplets = generator.get_triplets()
        return tuner.compare_models(req.model_a_id, req.model_b_id, triplets)

    # --------------------------------------------------
    # 8. POST /api/embeddings/deploy — Deploy fine-tuned model
    # --------------------------------------------------
    @app.post("/api/embeddings/deploy")
    async def embeddings_deploy(req: DeployRequest):
        """Deploy a fine-tuned model with zero-downtime rollover."""
        result = tuner.deploy_model(req.model_id)
        if result.get("error"):
            raise HTTPException(404, result["error"])
        return result

    # --------------------------------------------------
    # 9. GET /api/embeddings/models — List all available models
    # --------------------------------------------------
    @app.get("/api/embeddings/models")
    async def embeddings_models():
        """List all available embedding models."""
        models = tuner.list_models()
        return {"models": models, "total": len(models)}

    # --------------------------------------------------
    # 10. GET /api/embeddings/quality/history — Quality scores over time
    # --------------------------------------------------
    @app.get("/api/embeddings/quality/history")
    async def embeddings_quality_history():
        """Quality scores over time for all fine-tuned models."""
        history = tuner.get_quality_history()
        return {"history": history, "total": len(history)}

    # --------------------------------------------------
    # 11. POST /api/embeddings/ab-test/start — Start A/B test
    # --------------------------------------------------
    @app.post("/api/embeddings/ab-test/start")
    async def embeddings_ab_test_start(req: ABTestStartRequest):
        """Start an A/B test between two models."""
        test = tuner.start_ab_test(
            model_a_id=req.model_a_id,
            model_b_id=req.model_b_id,
            traffic_split=req.traffic_split,
        )
        winner = test.model_a_id if test.model_a_wins > test.model_b_wins else test.model_b_id
        return {
            "test_id": test.id,
            "model_a_id": test.model_a_id,
            "model_b_id": test.model_b_id,
            "queries_served": test.queries_served,
            "model_a_wins": test.model_a_wins,
            "model_b_wins": test.model_b_wins,
            "current_leader": winner,
            "status": test.status,
        }

    # --------------------------------------------------
    # 12. GET /api/embeddings/ab-test/results — A/B test results
    # --------------------------------------------------
    @app.get("/api/embeddings/ab-test/results")
    async def embeddings_ab_test_results():
        """Get all A/B test results."""
        results = tuner.get_ab_results()
        return {"tests": results, "total": len(results)}

    logger.info("Embeddings API: 12 endpoints registered under /api/embeddings/*")
