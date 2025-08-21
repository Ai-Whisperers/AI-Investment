from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..services.refresh import refresh_all

router = APIRouter()


@router.post("/refresh")
def manual_refresh(x_admin_token: str = Header(None), db: Session = Depends(get_db)):
    if not settings.ADMIN_TOKEN or x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    refresh_all(db)
    return {"status": "ok"}
