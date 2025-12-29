from fastapi import FastAPI, HTTPException
from .models.base import ScanRequest, ScanResponse, AnalyzeRequest, AnalyzeResponse

# -------------------------------
# App
# -------------------------------
from .services.github_service import GitHubService
from .services.cache_service import CacheService
from .services.llm_service import LLMService
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="GitHub Issue Analyzer",
    description="Fetch, cache, and analyze GitHub issues using LLM",
    version="1.0.0"
)

# Initialize services
github_service = GitHubService(token=os.getenv("GITHUB_TOKEN"))
cache_service = CacheService()
llm_service = LLMService(api_key=os.getenv("OPENAI_API_KEY"))


@app.get("/")
def root():
    return {"message": "GitHub Issue Analyzer API", "status": "running"}


@app.post("/scan", response_model=ScanResponse)
async def scan(scan_input: ScanRequest):
    """
    Fetch all open issues from a GitHub repository and cache them locally.
    """
    
    # Validate repo format
    if "/" not in scan_input.repo or scan_input.repo.count("/") != 1:
        raise HTTPException(
            status_code=400, 
            detail="Invalid repo format. Use 'owner/repository-name'"
        )
    
    try:
        # Fetch issues from GitHub
        issues = await github_service.fetch_open_issues(scan_input.repo)
        print(f"Fetched {len(issues)} issues from {scan_input.repo}")
        
        # Cache issues locally
        cached_successfully = cache_service.cache_issues_smart(scan_input.repo, issues)
        
        return ScanResponse(
            repo=scan_input.repo,
            issues_fetched=len(issues),
            cached_successfully=cached_successfully
        )
        
    except Exception as e:
        print(f"Error scanning repo: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(analyze_request: AnalyzeRequest): 
    """ Analyze the open issues based on a prompt """

    try:
        # Fetch issues from GitHub
        issues = cache_service.get_issues(analyze_request.repo)
        print(f"Fetched {len(issues)} issues from {analyze_request.repo}")
        
        analysed_response = llm_service.analyze_issues(issues, analyze_request.prompt)

        return AnalyzeResponse(
            repo=analyze_request.repo,
            prompt=analyze_request.prompt,
            analysis=analysed_response
        )
        
    except Exception as e:
        print(f"Error analysing repo: {e}")
        raise HTTPException(status_code=500, detail=str(e))




