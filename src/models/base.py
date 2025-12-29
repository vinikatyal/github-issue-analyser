from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ============== GitHub Issue Models ==============

class GitHubIssue(BaseModel):
    """Model representing a GitHub issue from the API"""
    id: int
    title: str
    body: Optional[str] = None
    html_url: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # For ORM compatibility (SQLite)


# ============== /scan Endpoint Models ==============

class ScanRequest(BaseModel):
    """Request body for POST /scan"""
    repo: str = Field(
        ...,
        description="Repository in 'owner/repo-name' format",
        pattern=r"^[\w\-\.]+/[\w\-\.]+$",
        examples=["facebook/react", "microsoft/vscode"]
    )


class ScanResponse(BaseModel):
    """Response body for POST /scan"""
    repo: str
    issues_fetched: int
    cached_successfully: bool
    message: Optional[str] = None


# ============== /analyze Endpoint Models ==============

class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze"""
    repo: str = Field(
        ...,
        description="Repository in 'owner/repo-name' format",
        pattern=r"^[\w\-\.]+/[\w\-\.]+$",
        examples=["facebook/react"]
    )
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language prompt for LLM analysis",
        examples=["Find themes across recent issues and recommend what to fix first"]
    )


class AnalyzeResponse(BaseModel):
    """Response body for POST /analyze"""
    repo: str
    prompt: str
    analysis: str  # LLM's response


# ============== Error Models ==============

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============== Database/Cache Models ==============

class CachedRepo(BaseModel):
    """Metadata about a cached repository"""
    repo: str
    last_scanned: datetime
    issue_count: int


class CacheStatus(BaseModel):
    """Response for cache status check (optional endpoint)"""
    repos_cached: List[CachedRepo]
    total_issues: int