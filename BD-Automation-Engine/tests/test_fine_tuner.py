"""Tests for Phase 47A — Embedding Fine-Tuner."""

import pytest

from src.embeddings.synthetic_data_generator import SyntheticDataGenerator, Triplet
from src.embeddings.fine_tuner import (
    EmbeddingFineTuner,
    TrainingConfig,
    FineTuneJob,
    EmbeddingModel,
    EvalMetrics,
    ABTest,
    ModelStatus,
    get_fine_tuner,
)


@pytest.fixture
def tuner():
    return EmbeddingFineTuner()


@pytest.fixture
def triplets():
    gen = SyntheticDataGenerator()
    gen.generate()
    return gen.get_triplets()


# =========================================
# BASELINE MODEL
# =========================================

def test_baseline_model_registered(tuner):
    models = tuner.list_models()
    assert len(models) >= 1
    baseline = [m for m in models if m["is_baseline"]]
    assert len(baseline) == 1
    assert baseline[0]["name"] == "all-MiniLM-L6-v2"


def test_baseline_model_deployed(tuner):
    deployed = tuner.get_deployed_model()
    assert deployed is not None
    assert deployed.is_baseline
    assert deployed.status == "deployed"


def test_baseline_has_metrics(tuner):
    deployed = tuner.get_deployed_model()
    assert 384 in deployed.metrics
    assert deployed.metrics[384].recall_at_10 > 0


# =========================================
# FINE-TUNING
# =========================================

def test_start_fine_tuning(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    assert isinstance(job, FineTuneJob)
    assert job.id.startswith("ft_")
    assert job.status == "completed"


def test_fine_tune_model_name(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    assert job.model_name.startswith("bd-embed-v")


def test_fine_tune_train_eval_split(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    assert job.training_triplets > 0
    assert job.eval_triplets > 0
    assert job.training_triplets + job.eval_triplets == len(triplets)


def test_fine_tune_loss_curve(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    assert len(job.training_loss) > 0
    # Loss should generally decrease
    assert job.training_loss[-1] < job.training_loss[0]


def test_fine_tune_matryoshka_metrics(tuner, triplets):
    config = TrainingConfig(matryoshka_dims=[768, 256, 64])
    job = tuner.start_fine_tuning(triplets, config)
    assert 768 in job.metrics
    assert 256 in job.metrics
    assert 64 in job.metrics


def test_fine_tune_best_dimension(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    assert job.best_dimension in job.config.matryoshka_dims


def test_fine_tune_improves_over_baseline(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    baseline = tuner.get_deployed_model()
    baseline_r10 = baseline.metrics[384].recall_at_10
    best_r10 = job.metrics[job.best_dimension].recall_at_10
    # Fine-tuned should outperform baseline
    assert best_r10 > baseline_r10


def test_fine_tune_registers_model(tuner, triplets):
    before = len(tuner.list_models())
    tuner.start_fine_tuning(triplets)
    after = len(tuner.list_models())
    assert after == before + 1


def test_fine_tune_custom_config(tuner, triplets):
    config = TrainingConfig(
        learning_rate=1e-4,
        epochs=5,
        batch_size=16,
    )
    job = tuner.start_fine_tuning(triplets, config)
    assert job.status == "completed"


def test_fine_tune_records_duration(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    assert job.duration_sec > 0


def test_get_job(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    retrieved = tuner.get_job(job.id)
    assert retrieved is not None
    assert retrieved.id == job.id


def test_get_job_not_found(tuner):
    assert tuner.get_job("nonexistent") is None


# =========================================
# EVALUATION
# =========================================

def test_evaluate_baseline(tuner, triplets):
    baseline = tuner.get_deployed_model()
    metrics = tuner.evaluate_model(baseline.id, triplets)
    assert isinstance(metrics, EvalMetrics)
    assert metrics.recall_at_10 > 0


def test_evaluate_fine_tuned(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    models = tuner.list_models()
    ft_model = [m for m in models if not m["is_baseline"]][0]
    metrics = tuner.evaluate_model(ft_model["id"], triplets, 768)
    assert metrics.recall_at_10 > 0


def test_eval_metrics_to_dict(tuner, triplets):
    baseline = tuner.get_deployed_model()
    metrics = tuner.evaluate_model(baseline.id, triplets)
    d = metrics.to_dict()
    assert "recall@1" in d
    assert "recall@10" in d
    assert "mrr" in d
    assert "ndcg@10" in d


# =========================================
# COMPARISON
# =========================================

def test_compare_models(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    baseline = tuner.get_deployed_model()
    models = tuner.list_models()
    ft_model = [m for m in models if not m["is_baseline"]][0]

    result = tuner.compare_models(baseline.id, ft_model["id"], triplets)
    assert "winner" in result
    assert "recall_at_10_improvement" in result
    assert "recommendation" in result


def test_compare_returns_both_metrics(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    models = tuner.list_models()
    ids = [m["id"] for m in models]
    result = tuner.compare_models(ids[0], ids[1], triplets)
    assert "model_a" in result
    assert "model_b" in result
    assert "metrics" in result["model_a"]


def test_compare_not_found(tuner, triplets):
    result = tuner.compare_models("bad_id", "other_bad_id", triplets)
    assert "error" in result


# =========================================
# DEPLOYMENT
# =========================================

def test_deploy_model(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    models = tuner.list_models()
    ft_model = [m for m in models if not m["is_baseline"]][0]

    result = tuner.deploy_model(ft_model["id"])
    assert result["deployed"] is True
    assert tuner.get_deployed_model().id == ft_model["id"]


def test_deploy_not_found(tuner):
    result = tuner.deploy_model("nonexistent")
    assert result["deployed"] is False


def test_deploy_changes_status(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    models = tuner.list_models()
    ft_model = [m for m in models if not m["is_baseline"]][0]

    tuner.deploy_model(ft_model["id"])
    model = tuner.get_model(ft_model["id"])
    assert model.status == "deployed"


# =========================================
# A/B TESTING
# =========================================

def test_start_ab_test(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    models = tuner.list_models()
    ids = [m["id"] for m in models]

    test = tuner.start_ab_test(ids[0], ids[1])
    assert isinstance(test, ABTest)
    assert test.id.startswith("ab_")
    assert test.queries_served > 0


def test_ab_test_has_results(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    models = tuner.list_models()
    ids = [m["id"] for m in models]

    test = tuner.start_ab_test(ids[0], ids[1])
    assert test.model_a_wins + test.model_b_wins == test.queries_served


def test_ab_test_complete(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    models = tuner.list_models()
    ids = [m["id"] for m in models]

    test = tuner.start_ab_test(ids[0], ids[1])
    completed = tuner.complete_ab_test(test.id)
    assert completed.status == "completed"


def test_ab_results(tuner, triplets):
    job = tuner.start_fine_tuning(triplets)
    models = tuner.list_models()
    ids = [m["id"] for m in models]

    tuner.start_ab_test(ids[0], ids[1])
    results = tuner.get_ab_results()
    assert len(results) == 1
    assert "winner" in results[0]


# =========================================
# QUALITY HISTORY
# =========================================

def test_quality_history(tuner, triplets):
    tuner.start_fine_tuning(triplets)
    history = tuner.get_quality_history()
    assert len(history) == 1
    assert "recall_at_10" in history[0]
    assert "model_name" in history[0]


def test_quality_history_accumulates(tuner, triplets):
    tuner.start_fine_tuning(triplets)
    tuner.start_fine_tuning(triplets)
    history = tuner.get_quality_history()
    assert len(history) == 2


# =========================================
# STATS
# =========================================

def test_stats(tuner, triplets):
    tuner.start_fine_tuning(triplets)
    stats = tuner.get_stats()
    assert stats["total_jobs"] == 1
    assert stats["total_models"] == 2  # baseline + 1 fine-tuned


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    t1 = get_fine_tuner()
    t2 = get_fine_tuner()
    assert t1 is t2
