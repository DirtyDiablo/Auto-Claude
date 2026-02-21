"""
Auth Management API — API key CRUD and JWT token issuance.

Admin-only endpoints for managing API keys and issuing JWT tokens.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from Engine8_Knowledge.auth import (
    AuthUser,
    Role,
    create_api_key,
    create_jwt,
    require_role,
    revoke_api_key,
    _load_keys,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CreateKeyRequest(BaseModel):
    name: str = Field(..., description="Descriptive name for this API key")
    role: str = Field("bd_team", description="Role: admin, bd_manager, bd_team")


class CreateKeyResponse(BaseModel):
    key: str = Field(..., description="The API key (shown only once)")
    name: str
    role: str


class RevokeKeyRequest(BaseModel):
    key_hash: str = Field(..., description="SHA-256 hash of the key to revoke")


class IssueTokenRequest(BaseModel):
    user_id: str = Field(..., description="User identifier for the JWT")
    role: str = Field("bd_team", description="Role: admin, bd_manager, bd_team")


class TokenResponse(BaseModel):
    token: str
    user_id: str
    role: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/keys", response_model=CreateKeyResponse)
async def create_key(
    req: CreateKeyRequest,
    user: AuthUser = Depends(require_role(Role.ADMIN)),
):
    """Create a new API key. Admin only."""
    if req.role not in ("admin", "bd_manager", "bd_team"):
        raise HTTPException(status_code=400, detail="Invalid role")
    result = create_api_key(req.name, req.role)
    return CreateKeyResponse(**result)


@router.delete("/keys")
async def delete_key(
    req: RevokeKeyRequest,
    user: AuthUser = Depends(require_role(Role.ADMIN)),
):
    """Revoke an API key. Admin only."""
    if revoke_api_key(req.key_hash):
        return {"status": "revoked", "key_hash": req.key_hash}
    raise HTTPException(status_code=404, detail="Key not found")


@router.get("/keys")
async def list_keys(
    user: AuthUser = Depends(require_role(Role.ADMIN)),
):
    """List all API keys (hashes and metadata, not the keys themselves). Admin only."""
    store = _load_keys()
    keys = []
    for key_hash, meta in store.get("keys", {}).items():
        keys.append({
            "key_hash": key_hash[:12] + "...",
            "name": meta["name"],
            "role": meta["role"],
            "active": meta.get("active", True),
            "created_at": meta.get("created_at"),
            "last_used": meta.get("last_used"),
        })
    return {"keys": keys}


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    req: IssueTokenRequest,
    user: AuthUser = Depends(require_role(Role.ADMIN)),
):
    """Issue a JWT token for a user. Admin only. Requires BD_JWT_SECRET."""
    if req.role not in ("admin", "bd_manager", "bd_team"):
        raise HTTPException(status_code=400, detail="Invalid role")
    try:
        token = create_jwt(req.user_id, req.role)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return TokenResponse(token=token, user_id=req.user_id, role=req.role)


@router.get("/me")
async def get_current_user_info(
    user: AuthUser = Depends(require_role(Role.BD_TEAM)),
):
    """Get info about the currently authenticated user."""
    return {
        "user_id": user.user_id,
        "role": user.role.value,
        "auth_method": user.auth_method,
        "permissions": sorted(user.permissions),
    }
