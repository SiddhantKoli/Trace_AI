import pytest

from app.evaluation import BenchmarkEvaluator


@pytest.mark.asyncio
async def test_benchmark_uses_reviewed_point_anomaly_annotations():
    result = await BenchmarkEvaluator().run_evaluation()

    assert len(result.scenario_results) == 5
    assert all("ground truth lines:" in scenario.details for scenario in result.scenario_results)
    assert result.diagnosis_accuracy == 1.0

    baseline = next(
        scenario
        for scenario in result.scenario_results
        if scenario.scenario_name == "Normal Baseline Operational Activity"
    )
    assert baseline.expected_category == "unknown"
    assert baseline.true_anomalies == 0
