from typing import Optional

from models import db, User


# =====================================================
# Internal helpers
# =====================================================

def _get_user(*, company_id: int, user_id: int) -> Optional[User]:
    """
    Fetch a user scoped to a company.
    """
    return User.query.filter_by(
        id=user_id,
        company_id=company_id,
    ).first()


# =====================================================
# User creation
# =====================================================

def create_user(
    *,
    company_id: int,
    creator_role: str,
    email: str,
    role: str,
) -> User:
    """
    Create a new user inside a company.

    Rules:
    - COMPANY_ADMIN cannot create SUPER_ADMIN
    - Email must be unique per company
    """

    if creator_role == "COMPANY_ADMIN" and role == "SUPER_ADMIN":
        raise PermissionError("FORBIDDEN_ROLE")

    existing = User.query.filter_by(
        company_id=company_id,
        email=email,
    ).first()

    if existing:
        raise ValueError("USER_ALREADY_EXISTS")

    user = User(
        email=email,
        role=role,
        company_id=company_id,
        status="ACTIVE",
    )

    db.session.add(user)
    db.session.commit()
    return user


# =====================================================
# Role change
# =====================================================

def change_user_role(
    *,
    company_id: int,
    actor_user_id: int,
    actor_role: str,
    target_user_id: int,
    new_role: str,
) -> User:
    """
    Change role of a user.

    Rules:
    - Cannot modify self
    - COMPANY_ADMIN cannot promote to SUPER_ADMIN
    - Target user must belong to same company
    """

    if actor_user_id == target_user_id:
        raise PermissionError("CANNOT_MODIFY_SELF")

    user = _get_user(company_id=company_id, user_id=target_user_id)
    if not user:
        raise ValueError("USER_NOT_FOUND")

    if actor_role == "COMPANY_ADMIN" and new_role == "SUPER_ADMIN":
        raise PermissionError("FORBIDDEN_ROLE")

    user.role = new_role
    db.session.commit()
    return user


# =====================================================
# User deactivation
# =====================================================

def deactivate_user(
    *,
    company_id: int,
    actor_user_id: int,
    target_user_id: int,
) -> User:
    """
    Soft deactivate a user.

    Rules:
    - Cannot deactivate self
    - User must belong to same company
    """

    if actor_user_id == target_user_id:
        raise PermissionError("CANNOT_MODIFY_SELF")

    user = _get_user(company_id=company_id, user_id=target_user_id)
    if not user:
        raise ValueError("USER_NOT_FOUND")

    user.status = "INACTIVE"
    db.session.commit()
    return user
