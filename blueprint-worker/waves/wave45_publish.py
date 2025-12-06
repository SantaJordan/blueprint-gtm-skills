"""
Wave 4.5: GitHub Pages Publishing

Publishes the HTML playbook to GitHub Pages and returns the shareable URL.
"""
import httpx
import base64
import asyncio
from datetime import datetime
from typing import Optional


class Wave45Publish:
    """Wave 4.5: Publish playbook to GitHub Pages."""

    def __init__(self, github_token: str, repo: str, owner: str):
        self.token = github_token
        self.repo = repo
        self.owner = owner
        self.base_url = "https://api.github.com"

    async def publish(self, html_content: str, company_slug: str) -> str:
        """
        Publish HTML playbook to GitHub Pages.

        Args:
            html_content: Complete HTML string
            company_slug: URL-safe company name (e.g., "owner-com")

        Returns:
            GitHub Pages URL (e.g., "https://santajordan.github.io/blueprint-gtm-playbooks/...")
        """
        filename = f"blueprint-gtm-playbook-{company_slug}.html"

        async with httpx.AsyncClient(timeout=60) as client:
            # Check if file already exists (to get SHA for update)
            sha = await self._get_file_sha(client, filename)

            # Create/update file
            success, error_msg = await self._create_or_update_file(
                client, filename, html_content, sha
            )

            if not success:
                raise Exception(f"Failed to publish to GitHub: {error_msg}")

        # Generate Pages URL
        pages_url = f"https://{self.owner}.github.io/{self.repo}/{filename}"

        # Verify deployment (with retries)
        verified = await self._verify_deployment(pages_url)

        if not verified:
            # Still return URL even if not verified yet
            print(f"[Wave 4.5] Deployment may still be in progress: {pages_url}")

        return pages_url

    async def _get_file_sha(self, client: httpx.AsyncClient, filename: str) -> Optional[str]:
        """Get SHA of existing file (needed for updates)."""
        try:
            response = await client.get(
                f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{filename}",
                headers=self._auth_headers()
            )

            if response.status_code == 200:
                return response.json().get("sha")
        except Exception:
            pass

        return None

    async def _create_or_update_file(
        self,
        client: httpx.AsyncClient,
        filename: str,
        content: str,
        sha: Optional[str]
    ) -> tuple:
        """Create or update file in GitHub repo. Returns (success, error_msg)."""
        path = f"/repos/{self.owner}/{self.repo}/contents/{filename}"

        payload = {
            "message": f"Publish playbook: {filename.replace('.html', '')} ({datetime.now().strftime('%Y-%m-%d')})",
            "content": base64.b64encode(content.encode()).decode(),
            "branch": "main"
        }

        if sha:
            payload["sha"] = sha

        response = await client.put(
            f"{self.base_url}{path}",
            headers=self._auth_headers(),
            json=payload
        )

        if response.status_code not in [200, 201]:
            error_msg = f"{response.status_code} - {response.text[:500]}"
            print(f"[Wave 4.5] GitHub API error: {error_msg}")
            return (False, error_msg)

        return (True, None)

    async def _verify_deployment(self, url: str, max_attempts: int = 4) -> bool:
        """Verify that the page is accessible."""
        async with httpx.AsyncClient(timeout=10) as client:
            for attempt in range(max_attempts):
                wait_time = 5 + (attempt * 5)  # 5, 10, 15, 20 seconds
                await asyncio.sleep(wait_time)

                try:
                    response = await client.head(url)
                    if response.status_code == 200:
                        return True
                except Exception:
                    pass

        return False

    def _auth_headers(self) -> dict:
        """Get authorization headers for GitHub API."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
