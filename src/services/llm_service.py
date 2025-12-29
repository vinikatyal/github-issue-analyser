# llm_service.py
import openai
from typing import List, Dict
import os


class LLMService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        print("API Key", api_key)
        self.client = openai.OpenAI(api_key=self.api_key)

    def analyze_issues(self, issues: List[Dict], prompt: str) -> str:
        """
        Analyze GitHub issues using OpenAI LLM.

        Args:
            issues: List of issue dictionaries with id, title, body, html_url, created_at
            prompt: User's natural language prompt for analysis

        Returns:
            LLM's analysis as a string
        """
        # Format issues for the LLM
        issues_text = self._format_issues(issues)

        # Create the system and user messages
        system_message = """You are a helpful assistant that analyzes GitHub issues. 
        You will be given a list of issues and a prompt asking you to analyze them.
        Provide clear, actionable insights based on the issues provided."""

        user_message = f"""Here are the GitHub issues to analyze:

        {issues_text}

        ---

        User's request: {prompt}"""

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        return response.choices[0].message.content

    def _format_issues(self, issues: List[Dict]) -> str:
        """Format issues into a readable string for the LLM."""
        if not issues:
            return "No issues found."

        formatted = []

        
        for i, issue in enumerate(issues, 1):
            issue_text = f"""Issue #{i}:
        - Title: {issue.title}
        - Created: {issue.created_at}
        - Description: {issue.body}
        """
            formatted.append(issue_text)

        return "\n".join(formatted)
