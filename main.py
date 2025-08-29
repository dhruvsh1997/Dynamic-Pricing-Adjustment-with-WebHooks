# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random
import datetime
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated database
pricing_db = {
    "product1": {"price": 100.0, "last_updated": datetime.datetime.now()},
    "product2": {"price": 50.0, "last_updated": datetime.datetime.now()}
}

# Simulated market data
def get_market_data():
    return {
        "demand": random.uniform(0.5, 2.0),  # Demand multiplier
        "competitor_price": random.uniform(80, 120),
        "trend": random.choice(["rising", "falling", "stable"])
    }

# AI pricing adjustment (simulated)
def adjust_price(current_price, market_data):
    # Simple AI logic (real implementation would use ML models)
    new_price = current_price * market_data["demand"]
    
    if market_data["trend"] == "rising":
        new_price *= 1.1
    elif market_data["trend"] == "falling":
        new_price *= 0.9
    
    # Keep within competitor range
    new_price = max(market_data["competitor_price"] * 0.9, 
                   min(new_price, market_data["competitor_price"] * 1.1))
    
    return round(new_price, 2)

# Webhook endpoint with better error handling
@app.post("/webhook/market-update")
async def market_update_webhook(request: Request):
    try:
        # Check if content type is JSON
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(status_code=400, detail="Content-Type must be application/json")
        
        # Try to parse JSON body
        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        # Validate required fields
        if not data or "product_id" not in data:
            raise HTTPException(status_code=400, detail="Missing required field: product_id")
        
        product_id = data.get("product_id")
        
        if product_id not in pricing_db:
            raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")
        
        market_data = get_market_data()
        current_price = pricing_db[product_id]["price"]
        new_price = adjust_price(current_price, market_data)
        
        # Update pricing
        pricing_db[product_id]["price"] = new_price
        pricing_db[product_id]["last_updated"] = datetime.datetime.now()
        
        logger.info(f"Price updated for {product_id}: {current_price} -> {new_price}")
        
        return {
            "product_id": product_id,
            "old_price": current_price,
            "new_price": new_price,
            "market_data": market_data,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# API to get current pricing
@app.get("/pricing/{product_id}")
async def get_pricing(product_id: str):
    if product_id not in pricing_db:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")
    return pricing_db[product_id]

# API to get all pricing
@app.get("/pricing")
async def get_all_pricing():
    return pricing_db

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)