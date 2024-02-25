from fastapi import FastAPI
from uvicorn import run

from network.routes import router

# Create an instance of the FastAPI application
app = FastAPI()

# Mount the router onto the FastAPI application
app.include_router(router)

if __name__ == "__main__":
    run(app, host="127.0.0.1", port=7999, log_level="info")
