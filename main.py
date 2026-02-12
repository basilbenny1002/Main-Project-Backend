from fastapi import FastAPI
from fastapi.responses import FileResponse
from routers import cart, website

app = FastAPI()

# Include Routers
app.include_router(cart.router)
app.include_router(website.router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# --- Static/HTML Routes ---

@app.get("/")
async def get_index():
    # Adjusted path to frontend folder
    return FileResponse("frontend/index.html")

@app.get("/admin")
async def get_admin():
    # Adjusted path to frontend folder
    return FileResponse("frontend/admin.html")
