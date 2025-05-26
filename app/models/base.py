"""Base models used across the application."""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ApiResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = datetime.now().isoformat() 