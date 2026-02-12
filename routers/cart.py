from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from core.manager import manager
from services.database import DatabaseService

router = APIRouter()

@router.websocket("/cart/{cart_id}")
async def cart_websocket_endpoint(websocket: WebSocket, cart_id: str):
    """
    WebSocket endpoint for ESP32 connections.
    URL: ws://<base_url>/cart/<cart_id>
    
    Logic:
    1. Verify UUID (handled by manager.connect_cart).
    2. Accept connection.
    3. Listen for product IDs sent by ESP32.
    4. On receive:
       - Query DatabaseService.
       - Send data to Frontend (Placeholder).
    """
    is_connected = await manager.connect_cart(websocket, cart_id)
    
    if is_connected:
        try:
            while True:
                # Expecting a product ID (number) from ESP32
                data = await websocket.receive_text()
                print(f"Received from cart {cart_id}: {data}")
                
                try:
                    product_id = int(data)
                    
                    # TODO: Implement the actual flow
                    # try:
                    #     product_data = DatabaseService.get_product_by_id(product_id)
                    #     # TODO: Send 'product_data' to the Frontend associated with 'cart_id'
                    #     print(f"Scanned product: {product_data}")
                    # except NotImplementedError:
                    #     print("Database service not ready.")
                        
                except ValueError:
                    print(f"Invalid data received from cart {cart_id}: {data}")
                    
        except WebSocketDisconnect:
            manager.disconnect_cart(cart_id)
            print(f"Cart {cart_id} disconnected unexpectedly.")
