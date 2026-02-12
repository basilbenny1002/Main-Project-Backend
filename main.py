from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import cart, website

app = FastAPI()

# --- CORS Configuration ---
# Allows requests from any origin (e.g., Netlify, Localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(cart.router)
app.include_router(website.router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
