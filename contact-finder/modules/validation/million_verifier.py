"""
MillionVerifier API Client
Verify email addresses in real-time using MillionVerifier's Single API
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class EmailResult(Enum):
    """MillionVerifier result codes"""
    OK = "ok"  # Email is valid and deliverable
    CATCH_ALL = "catch_all"  # Domain accepts all emails, can't verify individual
    UNKNOWN = "unknown"  # Unable to verify
    INVALID = "invalid"  # Email is invalid
    DISPOSABLE = "disposable"  # Temporary/disposable email


class EmailQuality(Enum):
    """MillionVerifier quality assessment"""
    GOOD = "good"
    RISKY = "risky"
    BAD = "bad"


@dataclass
class VerificationResult:
    """Result from MillionVerifier API"""
    email: str
    result: EmailResult
    quality: EmailQuality
    resultcode: int
    is_free: bool  # Free email provider (gmail, yahoo, etc.)
    is_role: bool  # Role account (info@, support@, etc.)
    did_you_mean: Optional[str]  # Suggested correction
    credits_remaining: int
    execution_time_seconds: float
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Email is definitively valid"""
        return self.result == EmailResult.OK

    @property
    def is_deliverable(self) -> bool:
        """Email is likely deliverable (ok or catch_all)"""
        return self.result in (EmailResult.OK, EmailResult.CATCH_ALL)

    @property
    def confidence_score(self) -> int:
        """Confidence score 0-100 based on result and quality"""
        if self.result == EmailResult.OK:
            if self.quality == EmailQuality.GOOD:
                return 100
            elif self.quality == EmailQuality.RISKY:
                return 70
            else:
                return 50
        elif self.result == EmailResult.CATCH_ALL:
            return 60  # Can't verify individual, but domain exists
        elif self.result == EmailResult.UNKNOWN:
            return 30
        else:  # INVALID or DISPOSABLE
            return 0


class MillionVerifierClient:
    """
    Client for MillionVerifier Single API

    API Docs: https://developer.millionverifier.com/
    Endpoint: https://api.millionverifier.com/api/v3/
    """

    BASE_URL = "https://api.millionverifier.com/api/v3/"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_seconds: int = 20,
        max_concurrent: int = 10
    ):
        """
        Initialize MillionVerifier client.

        Args:
            api_key: MillionVerifier API key (or use MILLIONVERIFIER_API_KEY env var)
            timeout_seconds: Timeout for each verification (2-60 seconds)
            max_concurrent: Maximum concurrent requests
        """
        self.api_key = api_key or os.environ.get("MILLIONVERIFIER_API_KEY")
        if not self.api_key:
            raise ValueError("MillionVerifier API key required")

        self.timeout_seconds = max(2, min(60, timeout_seconds))
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._session: Optional[aiohttp.ClientSession] = None
        self._verifications_count = 0
        self._credits_used = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout_seconds + 5)
            )
        return self._session

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def verify_email(self, email: str) -> VerificationResult:
        """
        Verify a single email address.

        Args:
            email: Email address to verify

        Returns:
            VerificationResult with verification details
        """
        async with self._semaphore:
            session = await self._get_session()

            params = {
                "api": self.api_key,
                "email": email.lower().strip(),
                "timeout": self.timeout_seconds
            }

            try:
                async with session.get(self.BASE_URL, params=params) as response:
                    data = await response.json()

                    # Check for errors
                    if data.get("error"):
                        return VerificationResult(
                            email=email,
                            result=EmailResult.UNKNOWN,
                            quality=EmailQuality.BAD,
                            resultcode=0,
                            is_free=False,
                            is_role=False,
                            did_you_mean=None,
                            credits_remaining=data.get("credits", 0),
                            execution_time_seconds=data.get("executiontime", 0),
                            error=data.get("error")
                        )

                    # Parse result
                    result_str = data.get("result", "unknown").lower()
                    try:
                        result = EmailResult(result_str)
                    except ValueError:
                        result = EmailResult.UNKNOWN

                    quality_str = data.get("quality", "bad").lower()
                    try:
                        quality = EmailQuality(quality_str)
                    except ValueError:
                        quality = EmailQuality.BAD

                    self._verifications_count += 1
                    self._credits_used += 1

                    return VerificationResult(
                        email=data.get("email", email),
                        result=result,
                        quality=quality,
                        resultcode=data.get("resultcode", 0),
                        is_free=data.get("free", False),
                        is_role=data.get("role", False),
                        did_you_mean=data.get("didyoumean") or None,
                        credits_remaining=data.get("credits", 0),
                        execution_time_seconds=data.get("executiontime", 0)
                    )

            except asyncio.TimeoutError:
                logger.warning(f"Timeout verifying email: {email}")
                return VerificationResult(
                    email=email,
                    result=EmailResult.UNKNOWN,
                    quality=EmailQuality.BAD,
                    resultcode=0,
                    is_free=False,
                    is_role=False,
                    did_you_mean=None,
                    credits_remaining=0,
                    execution_time_seconds=self.timeout_seconds,
                    error="timeout"
                )
            except Exception as e:
                logger.error(f"Error verifying email {email}: {e}")
                return VerificationResult(
                    email=email,
                    result=EmailResult.UNKNOWN,
                    quality=EmailQuality.BAD,
                    resultcode=0,
                    is_free=False,
                    is_role=False,
                    did_you_mean=None,
                    credits_remaining=0,
                    execution_time_seconds=0,
                    error=str(e)
                )

    async def verify_emails(self, emails: list[str]) -> list[VerificationResult]:
        """
        Verify multiple emails concurrently.

        Args:
            emails: List of email addresses to verify

        Returns:
            List of VerificationResult in same order as input
        """
        tasks = [self.verify_email(email) for email in emails]
        return await asyncio.gather(*tasks)

    async def get_credits(self) -> int:
        """Get available credits from API"""
        session = await self._get_session()

        try:
            async with session.get(
                "https://api.millionverifier.com/api/v3/credits",
                params={"api": self.api_key}
            ) as response:
                data = await response.json()
                return data.get("credits", 0)
        except Exception as e:
            logger.error(f"Error getting credits: {e}")
            return 0

    @property
    def verifications_count(self) -> int:
        """Number of verifications performed in this session"""
        return self._verifications_count

    @property
    def credits_used(self) -> int:
        """Credits used in this session"""
        return self._credits_used


async def verify_email_quick(email: str, api_key: Optional[str] = None) -> VerificationResult:
    """
    Quick helper to verify a single email.

    Args:
        email: Email to verify
        api_key: Optional API key (uses env var if not provided)

    Returns:
        VerificationResult
    """
    client = MillionVerifierClient(api_key=api_key)
    try:
        return await client.verify_email(email)
    finally:
        await client.close()
