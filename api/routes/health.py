from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "online", "service": "api-nutricion"}
