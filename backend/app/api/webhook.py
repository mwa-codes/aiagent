
import os
import stripe
import logging
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Plan

router = APIRouter(prefix="/webhook", tags=["webhook"])


STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Example mapping: Replace with your actual Stripe price IDs and plan names
STRIPE_PRICE_TO_PLAN = {
    "price_123": "pro",    # Example: Pro plan
    "price_456": "premium",  # Example: Premium plan
    # Add more mappings as needed
}

logger = logging.getLogger("stripe_webhook")
logging.basicConfig(level=logging.INFO)


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500, detail="Stripe webhook secret not configured.")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    event_type = event["type"]
    logger.info(f"Received Stripe event: {event_type}")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")
        stripe_customer_id = session.get("customer")
        price_id = None
        # Get the price ID from the subscription if available
        if session.get("subscription"):
            subscription = stripe.Subscription.retrieve(
                session["subscription"])
            if subscription and subscription["items"]["data"]:
                price_id = subscription["items"]["data"][0]["price"]["id"]

        # Map Stripe price_id to plan name
        plan_name = STRIPE_PRICE_TO_PLAN.get(price_id)
        plan = db.query(Plan).filter(
            Plan.name == plan_name).first() if plan_name else None

        # Find user by Stripe customer ID first, then by email
        user = None
        if stripe_customer_id:
            user = db.query(User).filter(
                User.stripe_customer_id == stripe_customer_id).first()
        if not user and customer_email:
            user = db.query(User).filter(User.email == customer_email).first()

        if user:
            # Store Stripe customer ID if not already set
            if stripe_customer_id and not user.stripe_customer_id:
                user.stripe_customer_id = stripe_customer_id
            # Update plan if mapping found
            if plan:
                user.plan_id = plan.id
                logger.info(f"Upgraded user {user.email} to plan {plan.name}")
            else:
                logger.warning(
                    f"No plan mapping found for price_id {price_id}")
            db.commit()
        else:
            logger.error(
                f"User not found for Stripe event: email={customer_email}, customer_id={stripe_customer_id}")

    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        stripe_customer_id = subscription.get("customer")
        # Find user by Stripe customer ID
        user = None
        if stripe_customer_id:
            user = db.query(User).filter(
                User.stripe_customer_id == stripe_customer_id).first()
        # Fallback: try to get email from subscription (if available)
        customer_email = subscription.get("customer_email")
        if not user and customer_email:
            user = db.query(User).filter(User.email == customer_email).first()
        # Downgrade to free plan
        free_plan = db.query(Plan).filter(Plan.name.ilike("%free%"))
        if user and free_plan:
            user.plan_id = free_plan.first().id
            logger.info(f"Downgraded user {user.email} to free plan")
            db.commit()
        else:
            logger.error(
                f"User not found for subscription.deleted: customer_id={stripe_customer_id}, email={customer_email}")

    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")

    return {"status": "success"}
