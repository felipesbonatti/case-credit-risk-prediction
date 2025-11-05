"""
Prediction endpoints
"""

from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import PredictRequest, PredictResponse, BatchPredictRequest, BatchPredictResponse
import structlog
import time

router = APIRouter()
logger = structlog.get_logger()


@router.post("", response_model=PredictResponse)
@router.post("/", response_model=PredictResponse)
async def predict(request: PredictRequest, req: Request):
    """
    Predict credit risk for a single customer

    Args:
        request: Customer data for prediction

    Returns:
        Prediction result with probability and recommendation
    """
    try:
        # Get model service from app state
        model_service = req.app.state.model_service

        # Make prediction
        result = await model_service.predict(request)

        logger.info(
            "Prediction made",
            cliente_id=request.cliente_id,
            prediction=result.prediction,
            probability=result.probability,
        )

        return result

    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchPredictResponse)
async def predict_batch(request: BatchPredictRequest, req: Request):
    """
    Predict credit risk for multiple customers (batch)

    Args:
        request: List of customer data for prediction

    Returns:
        List of prediction results
    """
    start_time = time.time()

    try:
        # Get model service from app state
        model_service = req.app.state.model_service

        # Make batch predictions
        predictions = []
        success = 0
        failed = 0

        for customer_request in request.requests:
            try:
                result = await model_service.predict(customer_request)
                # Convert PredictResponse to dict for Pydantic validation
                predictions.append(result.model_dump() if hasattr(result, "model_dump") else result)
                success += 1
            except Exception as e:
                logger.error(f"Batch prediction failed for customer: {e}")
                failed += 1

        processing_time = time.time() - start_time

        logger.info(
            "Batch prediction completed",
            total=len(request.requests),
            success=success,
            failed=failed,
            processing_time=processing_time,
        )

        return BatchPredictResponse(
            predictions=predictions,
            total=len(request.requests),
            success=success,
            failed=failed,
            processing_time=processing_time,
        )

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
