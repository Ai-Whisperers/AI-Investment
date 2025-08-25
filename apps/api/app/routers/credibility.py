"""
Credibility scoring router for evaluating financial information sources.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.credibility_scorer import credibility_scorer, SourceStatus
from ..utils.token_dep import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/credibility")


# Request/Response models
class EvaluateContentRequest(BaseModel):
    content: str = Field(..., description="Content to evaluate")
    source_id: str = Field(..., description="Unique source identifier")
    source_name: str = Field(..., description="Name of content creator")
    platform: str = Field(..., description="Platform (youtube, reddit, etc)")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")


class EvaluationResponse(BaseModel):
    credibility_score: float
    scam_flags: List[str]
    source_status: str
    recommendation: str


class TrackPredictionRequest(BaseModel):
    source_id: str = Field(..., description="Source who made prediction")
    prediction: str = Field(..., description="The prediction text")
    target_date: str = Field(..., description="When to evaluate (ISO format)")
    metadata: Optional[Dict] = Field(None, description="Additional context")


class EvaluatePredictionRequest(BaseModel):
    prediction_id: str = Field(..., description="ID of tracked prediction")
    outcome: bool = Field(..., description="Was prediction correct?")
    details: Optional[str] = Field("", description="Outcome details")


class SourceReport(BaseModel):
    profile: dict
    recent_evaluations: int
    average_quality: float
    total_scam_flags: int
    predictions: dict
    recommendation: str


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_content(
    request: EvaluateContentRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Evaluate content from a financial information source.
    
    Analyzes for:
    - Scam indicators and red flags
    - Content quality and professionalism
    - Source credibility and track record
    """
    credibility, scam_flags, status = credibility_scorer.evaluate_content(
        content=request.content,
        source_id=request.source_id,
        source_name=request.source_name,
        platform=request.platform,
        metadata=request.metadata
    )
    
    # Get source report for recommendation
    report = credibility_scorer.get_source_report(request.source_id)
    recommendation = report["recommendation"] if report else "New source - evaluating"
    
    return EvaluationResponse(
        credibility_score=credibility,
        scam_flags=scam_flags,
        source_status=status.value,
        recommendation=recommendation
    )


@router.post("/track-prediction")
async def track_prediction(
    request: TrackPredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Track a prediction made by a source for later evaluation.
    
    Helps build accuracy history for sources.
    """
    try:
        target_date = datetime.fromisoformat(request.target_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format."
        )
    
    prediction_id = credibility_scorer.track_prediction(
        source_id=request.source_id,
        prediction=request.prediction,
        target_date=target_date,
        metadata=request.metadata
    )
    
    return {
        "prediction_id": prediction_id,
        "status": "tracked",
        "message": "Prediction tracked for future evaluation"
    }


@router.post("/evaluate-prediction")
async def evaluate_prediction(
    request: EvaluatePredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate a previously tracked prediction.
    
    Updates source accuracy and credibility scores.
    """
    credibility_scorer.evaluate_prediction(
        prediction_id=request.prediction_id,
        outcome=request.outcome,
        details=request.details
    )
    
    return {
        "status": "evaluated",
        "outcome": "correct" if request.outcome else "incorrect",
        "message": "Prediction evaluated and source profile updated"
    }


@router.get("/source/{source_id}", response_model=SourceReport)
async def get_source_report(
    source_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get detailed credibility report for a source.
    
    Includes:
    - Credibility score and status
    - Prediction accuracy history
    - Scam indicators detected
    - Recommendation
    """
    report = credibility_scorer.get_source_report(source_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    return SourceReport(**report)


@router.get("/top-sources")
async def get_top_sources(
    platform: Optional[str] = None,
    limit: int = 10,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get top credible sources.
    
    Returns whitelisted and high-credibility sources.
    """
    sources = credibility_scorer.get_top_sources(platform, limit)
    
    return {
        "sources": sources,
        "count": len(sources),
        "platform": platform or "all"
    }


@router.get("/blacklist")
async def get_blacklisted_sources(
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get list of blacklisted sources to avoid.
    
    These sources have been identified as:
    - Scammers
    - Pump and dump promoters
    - Consistently inaccurate
    """
    blacklisted = credibility_scorer.get_blacklisted_sources()
    
    return {
        "blacklisted_sources": blacklisted,
        "count": len(blacklisted),
        "warning": "These sources should be avoided due to low credibility"
    }


@router.get("/statistics")
async def get_credibility_statistics(
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get overall statistics about source credibility.
    """
    total_sources = len(credibility_scorer.sources)
    
    status_counts = {
        "whitelisted": 0,
        "testlisted": 0,
        "blacklisted": 0,
        "unknown": 0
    }
    
    platform_counts = {}
    
    for source in credibility_scorer.sources.values():
        status_counts[source.status.value] += 1
        
        if source.platform not in platform_counts:
            platform_counts[source.platform] = 0
        platform_counts[source.platform] += 1
    
    # Calculate average metrics
    avg_credibility = sum(
        s.credibility_score for s in credibility_scorer.sources.values()
    ) / max(total_sources, 1)
    
    avg_accuracy = sum(
        s.accuracy_rate for s in credibility_scorer.sources.values()
    ) / max(total_sources, 1)
    
    total_evaluations = len(credibility_scorer.evaluations)
    
    # Count predictions
    total_predictions = sum(
        len(preds) for preds in credibility_scorer.prediction_tracker.values()
    )
    
    evaluated_predictions = sum(
        sum(1 for p in preds if p["evaluated"])
        for preds in credibility_scorer.prediction_tracker.values()
    )
    
    return {
        "total_sources": total_sources,
        "status_distribution": status_counts,
        "platform_distribution": platform_counts,
        "average_credibility": avg_credibility,
        "average_accuracy": avg_accuracy,
        "total_evaluations": total_evaluations,
        "predictions": {
            "total": total_predictions,
            "evaluated": evaluated_predictions,
            "pending": total_predictions - evaluated_predictions
        }
    }


@router.post("/bulk-evaluate")
async def bulk_evaluate_sources(
    sources: List[EvaluateContentRequest],
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate multiple sources in batch.
    
    Useful for processing multiple posts/videos at once.
    """
    results = []
    
    for source in sources:
        credibility, scam_flags, status = credibility_scorer.evaluate_content(
            content=source.content,
            source_id=source.source_id,
            source_name=source.source_name,
            platform=source.platform,
            metadata=source.metadata
        )
        
        results.append({
            "source_id": source.source_id,
            "credibility_score": credibility,
            "status": status.value,
            "scam_detected": len(scam_flags) > 0
        })
    
    return {
        "evaluated": len(results),
        "results": results,
        "summary": {
            "high_credibility": sum(1 for r in results if r["credibility_score"] > 0.7),
            "low_credibility": sum(1 for r in results if r["credibility_score"] < 0.3),
            "scams_detected": sum(1 for r in results if r["scam_detected"])
        }
    }


@router.get("/scam-patterns")
async def get_scam_patterns():
    """
    Get list of scam patterns the system looks for.
    
    Educational endpoint to help users identify scams.
    """
    return {
        "patterns": credibility_scorer.SCAM_PATTERNS,
        "description": "These patterns indicate potential scams or untrustworthy sources",
        "advice": "Be cautious of content containing these phrases"
    }


@router.get("/quality-indicators")
async def get_quality_indicators():
    """
    Get list of quality indicators the system looks for.
    
    Shows what makes content credible.
    """
    return {
        "indicators": credibility_scorer.QUALITY_PATTERNS,
        "description": "These patterns indicate professional, analytical content",
        "advice": "Look for content that includes these terms and concepts"
    }