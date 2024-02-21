from fastapi import FastAPI
from uvicorn import run
from routes import router
import logging
# Create an instance of the FastAPI application
app = FastAPI()

# Mount the router onto the FastAPI application
app.include_router(router)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

if __name__ == "__main__":
    run(app, host="127.0.0.1", port=8000, log_level="info")
