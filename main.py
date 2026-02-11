import json
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

app = FastAPI()

# Configuration
UUID_FILE = "valid_uuids.json"

# --- Data Models ---

class ProductUpdate(BaseModel):
    """Model for updating or adding a product."""
    id: Optional[str] = None  # Optional, will be auto-assigned if missing
    name: str
    price: float
    quantity: int
    description: Optional[str] = None

class CartUpdateReq(BaseModel):
    """Incoming request to update a cart."""
    cart_id: str
    product: ProductUpdate

class CartRemoveReq(BaseModel):
    """Incoming request to remove an item from a cart."""
    cart_id: str
    product_id: str

# --- Manager Class ---

class ConnectionManager:
    """
    Manages active WebSocket connections.
    Maps Cart UUIDs to specific WebSocket instances and tracks cart contents.
    """
    def __init__(self):
        # Dictionary to hold active connections: {cart_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Stores the current state of products for each cart: {cart_id: {product_id: product_data}}
        self.cart_contents: Dict[str, Dict[str, dict]] = {}
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

    async def connect(self, websocket: WebSocket, cart_id: str):
        """Accepts connection if UUID is valid."""
        await websocket.accept()
        
        if cart_id not in self.valid_uuids:
            # Code 4000: User defined custom error for invalid ID
            await websocket.close(code=4000, reason="Invalid UUID")
            return False
            
        self.active_connections[cart_id] = websocket
        
        # Initialize empty state for this cart if not present
        if cart_id not in self.cart_contents:
            self.cart_contents[cart_id] = {}
            
        return True

    def disconnect(self, cart_id: str):
        """Removes a connection from the pool."""
        if cart_id in self.active_connections:
            del self.active_connections[cart_id]

    async def send_update_to_cart(self, cart_id: str, data: dict):
        """Sends a JSON message to a specific cart's frontend."""
        if cart_id in self.active_connections:
            connection = self.active_connections[cart_id]
            try:
                await connection.send_json(data)
                return True
            except Exception:
                self.disconnect(cart_id)
                return False
        return False

    def get_next_id(self, cart_id: str) -> str:
        """Calculates the next incremental ID for a cart."""
        items = self.cart_contents.get(cart_id, {})
        max_id = 0
        for pid in items:
            try:
                pid_int = int(pid)
                if pid_int > max_id:
                    max_id = pid_int
            except ValueError:
                continue # Ignore non-integer IDs if any exist
        return str(max_id + 1)

    def process_product_update(self, cart_id: str, product: ProductUpdate) -> dict:
        """
        Updates the internal state:
        - Auto-assigns ID if missing.
        - Increments quantity if ID exists.
        - Returns the final product dictionary.
        """
        if cart_id not in self.cart_contents:
            self.cart_contents[cart_id] = {}

        current_items = self.cart_contents[cart_id]
        
        # Determine ID
        target_id = product.id
        if not target_id:
            target_id = self.get_next_id(cart_id)
        
        final_product = product.dict()
        final_product['id'] = target_id

        # Check for existence and update quantity
        if target_id in current_items:
            existing_item = current_items[target_id]
            # Assumes product.quantity is the ADDED amount, not the total.
            # User said "Added to quantity if the same product is added twice"
            # This implies the API sends the increment.
            new_quantity = existing_item['quantity'] + product.quantity
            final_product['quantity'] = new_quantity
            # Keep name/desc from new update (allows updating those fields)
        
        # Save to state
        self.cart_contents[cart_id][target_id] = final_product
        return final_product

    def remove_product_state(self, cart_id: str, product_id: str):
        """Removes a product from internal state tracking."""
        if cart_id in self.cart_contents and product_id in self.cart_contents[cart_id]:
            del self.cart_contents[cart_id][product_id]


# Initialize manager
manager = ConnectionManager()


# --- Routes ---

@app.get("/")
async def get_index():
    return FileResponse("index.html")

@app.get("/admin")
async def get_admin():
    return FileResponse("admin.html")

@app.get("/api/monitor/carts")
async def get_active_carts():
    return {"carts": list(manager.active_connections.keys())}

@app.get("/api/monitor/cart/{cart_id}")
async def get_cart_contents(cart_id: str):
    if cart_id in manager.cart_contents:
        return {"items": list(manager.cart_contents[cart_id].values())}
    return {"items": []}

@app.websocket("/ws/{cart_id}")
async def websocket_endpoint(websocket: WebSocket, cart_id: str):
    is_connected = await manager.connect(websocket, cart_id)
    
    if is_connected:
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(cart_id)

@app.post("/api/update_cart_product")
async def update_cart_item(req: CartUpdateReq):
    """
    Updates a product. checks for existing ID to increment quantity.
    """
    if req.cart_id not in manager.active_connections:
        return {"status": "ignored", "reason": "Cart not currently connected"}

    # Process logic (Increment qty, assign ID)
    final_product = manager.process_product_update(req.cart_id, req.product)

    payload = {
        "action": "update",
        "product": final_product
    }
    
    success = await manager.send_update_to_cart(req.cart_id, payload)
    if success:
        return {"status": "sent", "product": final_product}
    else:
        raise HTTPException(status_code=500, detail="Failed to send to socket")

@app.post("/api/remove_cart_product")
async def remove_cart_item(req: CartRemoveReq):
    if req.cart_id not in manager.active_connections:
        return {"status": "ignored", "reason": "Cart not currently connected"}

    # Update state
    manager.remove_product_state(req.cart_id, req.product_id)

    payload = {
        "action": "remove",
        "product_id": req.product_id
    }
    
    success = await manager.send_update_to_cart(req.cart_id, payload)
    if success:
        return {"status": "removed", "id": req.product_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to send to socket")
