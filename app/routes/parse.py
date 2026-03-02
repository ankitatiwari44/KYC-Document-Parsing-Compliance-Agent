from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.gemini_service import parse_document
from app.utils.file_utils import load_image_from_bytes, pdf_to_images
from app.agents.compliance_agent import run_compliance_check

router = APIRouter()


class DocumentInput(BaseModel):
    document_type: str
    fields: Dict[str, Any]


class ComplianceRequest(BaseModel):
    documents: List[DocumentInput]


# parsing using gemini

@router.post("/parse-document")
async def parse_document_api(file: UploadFile = File(...)):

    filename = file.filename.lower()
    file_bytes = await file.read()

    results = []

    # IMAGE INPUT
    if filename.endswith((".jpg", ".jpeg", ".png")):
        image = load_image_from_bytes(file_bytes)
        data = parse_document(image)

        results.append({
            "page": 1,
            "data": data
        })

    # PDF INPUT (Page-by-page processing)
    elif filename.endswith(".pdf"):
        images = pdf_to_images(file_bytes)

        for idx, image in enumerate(images):
            data = parse_document(image)

            results.append({
                "page": idx + 1,
                "data": data
            })

    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # Run compliance check automatically after extraction
    parsed_documents = [
        {
            "document_type": r["data"].get("document_type"),
            "fields": r["data"].get("fields", {})
        }
        for r in results
        if "data" in r and isinstance(r["data"], dict)
    ]

    compliance_report = run_compliance_check(parsed_documents)

    return {
        "total_pages": len(results),
        "results": results,
        "compliance_report": compliance_report
    }


# compilance endpoint to check for valid

@router.post("/compliance-check")
def compliance_check_api(request: ComplianceRequest):

    parsed_documents = [
        {
            "document_type": doc.document_type,
            "fields": doc.fields
        }
        for doc in request.documents
    ]

    compliance_report = run_compliance_check(parsed_documents)

    return {
        "documents_received": len(parsed_documents),
        "compliance_report": compliance_report
    }