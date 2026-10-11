"""Synchronous storage and identity boundaries shared by editorial adapters."""

from typing import Protocol

from .digest_cloud_editorial_rules import IssueDecision


class OriginalReadError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class IssueControlPort(Protocol):
    def get_issue(self, issue_date: str) -> dict: ...

    def transact_issue(self, issue_date: str, decide) -> IssueDecision:
        """Return only after committing the decision; exceptions roll back."""
        ...


class OriginalReadPort(Protocol):
    def read_base(self, issue_date: str, base_identity: str) -> dict: ...


class OwnerPolicy(Protocol):
    def require(self, principal, owner_id: str, permission: str) -> str:
        """Authorize trusted request context and return its stable actor ID."""
        ...
