from typing import Optional
from fastapi import APIRouter
from app.evaluation import evaluator
from app.schemas import EvaluationSummary

router = APIRouter(prefix="/evaluation", tags=["Model Evaluation & Benchmarks"])

_cached_evaluation: Optional[EvaluationSummary] = None


@router.post("/run", response_model=EvaluationSummary)
async def run_evaluation_benchmark():
    """
    Executes benchmark evaluation on the 5 labelled scenarios.
    Calculates actual empirical metrics (Precision, Recall, F1, FPR, Diagnosis Accuracy).
    """
    global _cached_evaluation
    result = await evaluator.run_evaluation()
    _cached_evaluation = result
    return result


@router.get("/latest", response_model=EvaluationSummary)
async def get_latest_evaluation():
    """
    Returns latest benchmark evaluation results (or runs fresh benchmark if none cached).
    """
    global _cached_evaluation
    if _cached_evaluation is None:
        _cached_evaluation = await evaluator.run_evaluation()
    return _cached_evaluation
