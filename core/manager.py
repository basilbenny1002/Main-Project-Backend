import json
import os
from typing import Dict, List, Optional
from fastapi import WebSocket

UUID_FILE = "valid_uuids.json"

class ConnectionManager:
    """
    Manages active WebSocket connections for Carts (ESP32) and potentially Frontends.
    """
    def __init__(self):
        # Active connections for ESP32 carts: {cart_id: WebSocket}
        self.active_cart_connections: Dict[str, WebSocket] = {}
        self.valid_uuids: List[str] = self.load_uuids()

    def load_uuids(self) -> List[str]:
        """Loads valid UUIDs from the JSON file."""
        if not os.path.exists(UUID_FILE):
            print(f"Warning: {UUID_FILE} not found. No UUIDs will be valid.")
            return []
        try:
            with open(UUID_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading UUIDs: {e}")
            return []

    async def connect_cart(self, websocket: WebSocket, cart_id: str) -> bool:
        """
        Accepts connection from ESP32 if UUID is valid.
        """
        await websocket.accept()
        
        if cart_id not in self.valid_uuids:
            # Code 4000: Invalid ID
            await websocket.close(code=4000, reason="Invalid UUID")
            return False
            
        self.active_cart_connections[cart_id] = websocket
        print(f"Cart {cart_id} connected.")
        return True

    def disconnect_cart(self, cart_id: str):
        """Removes a cart connection."""
        if cart_id in self.active_cart_connections:
            del self.active_cart_connections[cart_id]
            print(f"Cart {cart_id} disconnected.")

    async def send_unlock_signal(self, cart_id: str):
        """
        Sends an unlock signal to the ESP32.
        
        Args:
            cart_id (str): The ID of the cart to unlock.
        """
        if cart_id in self.active_cart_connections:
            websocket = self.active_cart_connections[cart_id]
            try:
                # Protocol to be defined. Sending generic JSON for now.
                await websocket.send_json({"command": "unlock"})
                return True
            except Exception as e:
                print(f"Error sending unlock signal: {e}")
                return False
        return False

# Global instance
manager = ConnectionManager()
