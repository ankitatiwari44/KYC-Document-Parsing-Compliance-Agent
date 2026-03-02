from fastapi import FastAPI
from app.routes.parse import router as parse_router

app = FastAPI(
    title="KYC Document Parsing & Compliance Agent",
    description="Multimodal KYC document extraction and rule-based compliance validation system.",
    version="1.0.0"
)

# Include document parsing + compliance route
app.include_router(parse_router)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "KYC Document Parsing & Compliance Agent",
        "version": "1.0.0"
    }