from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.manager import manager
from services.database import DatabaseService

router = APIRouter()

@router.websocket("/cart/{cart_id}")
async def cart_websocket_endpoint(websocket: WebSocket, cart_id: str):
    """
    WebSocket endpoint.
    Used by BOTH ESP32 (to send scans) and Frontend (to receive updates).
    """
    # Attempt connection
    is_connected = await manager.connect_cart(websocket, cart_id)
    
    if not is_connected:
        # Close with policy violation code if invalid UUID
        await websocket.close(code=1008, reason="Invalid UUID")
        return
    
    try:
        while True:
            # Wait for data (from ESP32 or Frontend)
            # ESP32 sends: "12345" (Product ID)
            data = await websocket.receive_text()
            print(f"Received from {cart_id}: {data}")
            
            # Process logic:
            try:
                # Assume data is a numeric product ID from ESP32
                product_id = int(data)
                
                # 1. Lookup Product (Service Placeholder)
                try:
                    # product_data = DatabaseService.get_product_by_id(product_id)
                    product_data = {"id": product_id, "name": "Placeholder Item", "price": 10.0, "quantity": 1}
                except NotImplementedError:
                    product_data = {"error": "Database Service not available"}

                # 2. Logic: Add or Remove?
                # For now, we just broadcast "item_scanned". 
                # Real implementation: Check if item is in 'cart state' and toggle it.
                
                # 3. Broadcast to all (Frontend gets update)
                response = {
                    "event": "cart_update",
                    "action": "add", # or 'remove'
                    "product": product_data
                }
                await manager.broadcast_to_cart(cart_id, response)
                
            except ValueError:
                # Keep alive or other non-integer messages
                pass
                
    except WebSocketDisconnect:
        manager.disconnect_cart(websocket, cart_id)
