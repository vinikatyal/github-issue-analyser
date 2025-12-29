import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from ..models.base import GitHubIssue


class CacheService:
    def __init__(self, db_path: str = "issues_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY,
                repo TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT,
                html_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                cached_at TEXT NOT NULL
            )
        """)

        # Index for faster repo lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_repo ON issues(repo)
        """)

        conn.commit()
        conn.close()

    def cache_issues_smart(self, repo: str, issues: List[GitHubIssue]) -> dict:
        """
        Smart caching - only update issues that have changed.
        Returns stats about what was cached.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cached_at = datetime.utcnow().isoformat()
            stats = {"inserted": 0, "updated": 0, "unchanged": 0}

            for issue in issues:
                # Check if issue exists and get its cached version
                print("Issue", issue)
                cursor.execute("""
                    SELECT updated_at FROM issues WHERE id = ? AND repo = ?
                """, (issue.id, repo))
                existing = cursor.fetchone()

                if existing is None:
                    # New issue - insert
                    cursor.execute("""
                        INSERT INTO issues 
                        (id, repo, title, body, html_url, created_at, updated_at, cached_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        issue.id, repo, issue.title, issue.body,
                        issue.html_url, issue.created_at.isoformat(),
                        issue.updated_at.isoformat(), cached_at
                    ))
                    stats["inserted"] += 1

                elif existing[0] != issue.updated_at.isoformat():
                    # Issue was updated - update cache
                    cursor.execute("""
                        UPDATE issues 
                        SET title=?, body=?, updated_at=?, cached_at=?
                        WHERE id=? AND repo=?
                    """, (
                        issue.title, issue.body,
                        issue.updated_at.isoformat(), cached_at,
                        issue.id, repo
                    ))
                    stats["updated"] += 1
                else:
                    stats["unchanged"] += 1

            conn.commit()
            conn.close()
            print(stats)
            return True

        except Exception as e:
            print(f"Cache error: {e}")
            return None

    def cache_issues(self, repo: str, issues: List[GitHubIssue]) -> bool:
        """
        Cache issues for a repository.
        Clears existing issues for the repo before inserting new ones.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clear existing issues for this repo
            cursor.execute("DELETE FROM issues WHERE repo = ?", (repo,))

            # Insert new issues
            cached_at = datetime.utcnow().isoformat()
            for issue in issues:
                cursor.execute("""
                    INSERT INTO issues (id, repo, title, body, html_url, created_at, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    issue.id,
                    repo,
                    issue.title,
                    issue.body,
                    issue.html_url,
                    issue.created_at.isoformat(),
                    cached_at
                ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Cache error: {e}")
            return False

    def get_issues(self, repo: str) -> List[GitHubIssue]:
        """Retrieve cached issues for a repository."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, body, html_url, created_at 
            FROM issues 
            WHERE repo = ?
            ORDER BY created_at DESC
        """, (repo,))

        rows = cursor.fetchall()
        conn.close()

        issues = []
        for row in rows:
            ## return in GithubIssue format
            issue = GitHubIssue(
                id=row[0],
                title=row[1],
                body=row[2],
                html_url=row[3],
                created_at=datetime.fromisoformat(row[4])
            )
            issues.append(issue)

        return issues

    def has_cached_issues(self, repo: str) -> bool:
        """Check if issues are cached for a repository."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM issues WHERE repo = ?", (repo,))
        count = cursor.fetchone()[0]

        conn.close()
        return count > 0
