import httpx
from typing import List
from ..models.base import GitHubIssue

class GitHubService:
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str = None):
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    async def fetch_open_issues(self, repo: str) -> List[GitHubIssue]:
        """
        Fetch all open issues from a GitHub repository.
        Handles pagination automatically.
        """
        issues = []
        page = 1
        per_page = 100  # Max allowed by GitHub API
        
        async with httpx.AsyncClient() as client:
            while True:
                url = f"{self.BASE_URL}/repos/{repo}/issues"
                params = {
                    "state": "open",
                    "page": page,
                    "per_page": per_page
                }
                
                response = await client.get(
                    url, 
                    headers=self.headers, 
                    params=params
                )
                
                if response.status_code != 200:
                    raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
                
                data = response.json()
                
                if not data:
                    break
                
                # Filter out pull requests (GitHub API returns PRs as issues too)
                for item in data:
                    if "pull_request" not in item:
                        issue = GitHubIssue(
                            id=item["id"],
                            title=item["title"],
                            body=item.get("body"),
                            html_url=item["html_url"],
                            created_at=item["created_at"]
                        )
                        issues.append(issue)
                
                # Check if there are more pages
                if len(data) < per_page:
                    break
                    
                page += 1
        
        return issues