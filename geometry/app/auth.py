from fastapi import Header, HTTPException, status
from .config import settings


async def require_api_key(x_api_key: str = Header(alias="X-API-Key")) -> None:
    """Validate the shared API key sent from the web app."""
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
