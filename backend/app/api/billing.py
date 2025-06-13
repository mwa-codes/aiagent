import os
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
import stripe

router = APIRouter(prefix="/billing", tags=["billing"])

# Set Stripe API key from environment variable
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class CheckoutSessionRequest(BaseModel):
    price_id: str  # Stripe Price ID for the subscription plan
    customer_email: str | None = None  # Optionally prefill email


@router.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest):
    success_url = os.getenv("STRIPE_SUCCESS_URL",
                            "http://localhost:3000/success")
    cancel_url = os.getenv("STRIPE_CANCEL_URL", "http://localhost:3000/cancel")

    if not stripe.api_key:
        raise HTTPException(
            status_code=500, detail="Stripe API key not configured.")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": request.price_id,
                "quantity": 1,
            }],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            customer_email=request.customer_email,
        )
        return {"sessionId": session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
