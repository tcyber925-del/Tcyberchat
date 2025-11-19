from fastapi import APIRouter, Response

from ..services import metrics

router = APIRouter()


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    payload = metrics.render_metrics()
    return Response(content=payload, media_type="text/plain; version=0.0.4")
