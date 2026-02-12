import json
import os
from typing import Dict, List
from fastapi import WebSocket

UUID_FILE = "valid_uuids.json"

class ConnectionManager:
    """
    Manages active WebSocket connections.
    Supports multiple connections per cart (ESP32 + Frontend).
    """
    def __init__(self):
        # Maps cart_id to a list of WebSocket connections
        # Example: "uuid-123": [WebSocket(ESP32), WebSocket(Frontend)]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.valid_uuids: List[str] = self.load_uuids()

    def load_uuids(self) -> List[str]:
        """Loads valid UUIDs from the JSON file."""
        # Use absolute path to ensure file is found regardless of execution context
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, UUID_FILE)
        
        if not os.path.exists(file_path):
            # Fallback to current directory
            file_path = UUID_FILE

        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found. No UUIDs will be valid.")
            return []
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Check structure: is it a list or a dict?
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "valid_cart_ids" in data:
                    return data["valid_cart_ids"]
                # Default fallback
                return data if isinstance(data, list) else [] 
        except Exception as e:
            print(f"Error loading UUIDs: {e}")
            return []

    async def connect_cart(self, websocket: WebSocket, cart_id: str) -> bool:
        """
        Accepts connection if UUID is valid.
        """
        # 1. Validate UUID before accepting
        if cart_id not in self.valid_uuids:
            # Reject connection
            return False

        # 2. Accept connection
        await websocket.accept()
        
        # 3. Store connection
        if cart_id not in self.active_connections:
            self.active_connections[cart_id] = []
        self.active_connections[cart_id].append(websocket)
        
        print(f"New connection for Cart {cart_id}. Total clients: {len(self.active_connections[cart_id])}")
        return True

    def disconnect_cart(self, websocket: WebSocket, cart_id: str):
        """Removes a specific socket connection."""
        if cart_id in self.active_connections:
            if websocket in self.active_connections[cart_id]:
                self.active_connections[cart_id].remove(websocket)
            
            # Clean up empty lists
            if not self.active_connections[cart_id]:
                del self.active_connections[cart_id]
                
            print(f"Client disconnected from Cart {cart_id}.")

    async def broadcast_to_cart(self, cart_id: str, message: dict):
        """
        Sends a JSON message to ALL clients connected to this cart_id.
        (e.g., updates both ESP32 and Frontend).
        """
        if cart_id in self.active_connections:
            # Iterate over a copy of the list to allow removal during iteration if needed
            for connection in self.active_connections[cart_id][:]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting: {e}")
                    # Could call disconnect logic here, but let the endpoint handle it
                    
    async def send_unlock_signal(self, cart_id: str):
        """
        Sends a specific unlock command.
        """
        await self.broadcast_to_cart(cart_id, {"command": "unlock", "status": "approved"})
        return True

# Global instance
manager = ConnectionManager()
