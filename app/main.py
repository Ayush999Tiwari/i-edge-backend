# ==========================================================
# Application entry point. Only: create app, configure CORS,
# register routers, startup init, global exception handler.
# No business logic lives here (was 768 lines with an entire
# live-surveillance class + every vehicle route inlined -- all of
# that moved to services/ and api/).
# ==========================================================
import os
import traceback

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import UPLOAD_VIDEO_FOLDER
from app.database import init_db
from app.api import auth, vehicle, surveillance

app = FastAPI(title="Unified AI Video Surveillance & ANPR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(vehicle.router)
app.include_router(surveillance.router)
app.include_router(surveillance.legacy_router)


@app.on_event("startup")
def on_startup():
    os.makedirs(UPLOAD_VIDEO_FOLDER, exist_ok=True)
    init_db()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": str(exc)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=3000, reload=True)