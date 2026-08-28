"""Payment endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentListResponse,
    PaymentRead,
    VerifyRequest,
)
from app.services.payment_service import (
    BadReferenceError,
    MembershipNotFoundError,
    NotOwnerError,
    NotPayableError,
    PaymentNotFoundError,
    PaymentService,
)

router = APIRouter()


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a payment checkout for a membership",
)
def checkout(
    body: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckoutResponse:
    from app.services.payments.registry import get_provider

    provider = get_provider(body.provider)
    try:
        payment = PaymentService().start_payment(
            db,
            user=user,
            membership_id=body.membership_id,
            provider=provider,
            method=body.method,
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Membership not found") from exc
    except NotOwnerError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except NotPayableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CheckoutResponse(payment=PaymentRead.model_validate(payment))


@router.post(
    "/{payment_id}/verify",
    response_model=PaymentRead,
    summary="Verify a payment with the provider and activate membership on success",
)
def verify(
    payment_id: int,
    body: VerifyRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaymentRead:
    from app.models.payment import Payment as PaymentModel
    from app.services.payments.registry import get_provider

    payment = db.get(PaymentModel, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    provider = get_provider(payment.provider)
    force = body.force_outcome if body is not None else None
    try:
        verified = PaymentService().verify_payment(
            db,
            user=user,
            payment_id=payment_id,
            provider=provider,
            force_outcome=force,
        )
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Payment not found") from exc
    except NotOwnerError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BadReferenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PaymentRead.model_validate(verified)


@router.get(
    "/me",
    response_model=PaymentListResponse,
    summary="List the current user's payments",
)
def my_payments(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaymentListResponse:
    items = PaymentService().list_for_user(db, user)
    return PaymentListResponse(
        items=[PaymentRead.model_validate(p) for p in items],
        total=len(items),
    )


admin_router = APIRouter()


@admin_router.get(
    "",
    response_model=PaymentListResponse,
    summary="[admin] List all payments",
)
def list_all(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> PaymentListResponse:
    items = PaymentService().list_all(db)
    return PaymentListResponse(
        items=[PaymentRead.model_validate(p) for p in items],
        total=len(items),
    )