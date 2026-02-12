import datetime
from fastapi import APIRouter, HTTPException
from services.payment import PaymentService
from core.manager import manager
from models.schemas import PayRequest, PaymentNotification

router = APIRouter()

# --- Endpoints ---

@router.post("/pay")
async def pay(req: PayRequest):
    """
    Endpoint for Frontend to initiate payment.
    Records time and amount.
    """
    try:
        # result = PaymentService.initiate_payment(req.cart_id, req.amount)
        # return result
        raise NotImplementedError("Payment service not hooked up.")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

@router.post("/webhook/payment")
async def payment_webhook(notification: PaymentNotification):
    """
    Receives payment confirmation.
    If valid, triggers unlock on ESP32.
    """
    try:
        # valid = PaymentService.process_payment_notification(notification.dict())
        # if valid:
        #     # Find cart_id associated with this payment (logic needed in service)
        #     # For now, we don't have the cart_id here without the service state.
        #     # cart_id = ... 
        #     # await manager.send_unlock_signal(cart_id)
        #     pass
        raise NotImplementedError("Webhook logic not implemented.")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

@router.post("/unlock-debug")
async def force_unlock(cart_id: str):
    """
    Debug endpoint to manually trigger unlock for a cart.
    """
    success = await manager.send_unlock_signal(cart_id)
    if success:
        return {"status": "signal_sent"}
    return {"status": "failed", "reason": "Cart not connected"}
