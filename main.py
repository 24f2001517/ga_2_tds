from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
import time
import jwt
from pydantic import BaseModel
from fastapi.responses import JSONResponse

ALLOWED_ORIGIN = "https://dash-wqb2m3.example.com"
EMAIL = "24f2001517@ds.study.iitm.ac.in"  # Replace with your exact login email

app = FastAPI()

# Strict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for required headers
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = time.perf_counter() - start
        response.headers["X-Request-ID"] = str(uuid4())
        response.headers["X-Process-Time"] = f"{elapsed:.6f}"

        return response

app.add_middleware(MetricsMiddleware)


@app.get("/stats")
async def stats(values: str = Query(...)):
    nums = [int(x.strip()) for x in values.split(",") if x.strip()]

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums),
    }



PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-3dcewk8a.apps.exam.local"

class TokenRequest(BaseModel):
    token: str

@app.post("/verify")
async def verify(req: TokenRequest):
    try:
        claims = jwt.decode(
            req.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": claims.get("email"),
            "sub": claims.get("sub"),
            "aud": claims.get("aud"),
        }

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"valid": False},
        )
    
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

# Simulate the assigned OS environment variable if it isn't set on Render.
# On Render you can instead define APP_API_KEY in Environment Variables.
os.environ.setdefault("APP_API_KEY", "key-mj2o78a4dt")


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).lower() in ("true", "1", "yes", "on")


@app.get("/effective-config")
async def effective_config(set: list[str] = Query(default=[])):
    cfg = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    # YAML layer
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml") as f:
            y = yaml.safe_load(f) or {}
            cfg.update(y)

    # .env layer
    if os.getenv("APP_PORT"):
        cfg["port"] = os.getenv("APP_PORT")

    if os.getenv("NUM_WORKERS"):
        cfg["workers"] = os.getenv("NUM_WORKERS")

    if os.getenv("APP_DEBUG"):
        cfg["debug"] = os.getenv("APP_DEBUG")

    if os.getenv("APP_LOG_LEVEL"):
        cfg["log_level"] = os.getenv("APP_LOG_LEVEL")

    # OS env layer
    if os.getenv("APP_API_KEY"):
        cfg["api_key"] = os.getenv("APP_API_KEY")

    # CLI overrides
    for item in set:
        if "=" in item:
            k, v = item.split("=", 1)
            cfg[k] = v

    # Type coercion
    cfg["port"] = int(cfg["port"])
    cfg["workers"] = int(cfg["workers"])
    cfg["debug"] = to_bool(cfg["debug"])
    cfg["log_level"] = str(cfg["log_level"])

    # Mask secret
    cfg["api_key"] = "****"

    return cfg
