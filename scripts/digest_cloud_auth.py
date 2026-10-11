"""Resource-server identity checks; the identity provider issues the tokens."""

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .digest_cloud_editorial import EditorialError


@dataclass(frozen=True)
class VerifiedPrincipal:
    principal_id: str
    issuer: str
    subject: str
    client_id: str
    scopes: frozenset[str]
    expires_at: int


class JWTVerifier:
    """RS256 only; key resolution is configured by the server, never by jku/url."""

    def __init__(self, *, issuer, resource, owner_subject, owner_id, resolve_key,
                 allow_loopback=False):
        resource_url = urlsplit(resource)
        local = allow_loopback and resource_url.scheme == "http" and resource_url.hostname == "127.0.0.1"
        if (urlsplit(issuer).scheme != "https" or not urlsplit(issuer).netloc or
                not (resource_url.scheme == "https" or local) or not resource_url.netloc or
                resource_url.username or resource_url.password or resource_url.fragment or
                not isinstance(owner_subject, str) or not owner_subject or
                not isinstance(owner_id, str) or not owner_id or not callable(resolve_key)):
            raise ValueError("invalid_auth_configuration")
        self.issuer, self.resource = issuer, resource
        self.owner_subject, self.owner_id = owner_subject, owner_id
        self.resolve_key = resolve_key

    def verify(self, token):
        import jwt
        if not isinstance(token, str) or not token or len(token) > 16384:
            return None
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256":
                return None
            kid = header.get("kid")
            if not isinstance(kid, str) or not kid or len(kid) > 256:
                return None
            claims = jwt.decode(token, self.resolve_key(kid), algorithms=["RS256"],
                                issuer=self.issuer, audience=self.resource,
                                options={"require": ["iss", "sub", "aud", "exp", "iat"]})
            if (claims.get("sub") != self.owner_subject or
                    type(claims["exp"]) is not int or type(claims["iat"]) is not int or
                    ("nbf" in claims and type(claims["nbf"]) is not int)):
                return None
            client = claims.get("client_id", claims.get("azp"))
            scope = claims.get("scope")
            if not isinstance(client, str) or not client or not isinstance(scope, str):
                return None
            return VerifiedPrincipal(self.owner_id, self.issuer, self.owner_subject,
                                     client, frozenset(scope.split()), claims["exp"])
        except Exception:
            return None


class VerifiedOwnerPolicy:
    def __init__(self, issuer, subject):
        self.issuer, self.subject = issuer, subject

    def require(self, principal, owner_id, permission):
        if (not isinstance(principal, VerifiedPrincipal) or principal.principal_id != owner_id or
                principal.issuer != self.issuer or principal.subject != self.subject or
                principal.expires_at <= datetime.now(timezone.utc).timestamp() or
                permission not in principal.scopes):
            raise EditorialError("unauthorized")
        return principal.principal_id
