import json
from app.config import client, MODEL_NAME


# Document classification amoung kyc

CLASSIFICATION_PROMPT = """
Identify the type of the provided document image.

Possible types:
- pan_card
- aadhaar_card
- payslip
- bank_statement
- driving_license
- passport
- unknown

Return strictly valid JSON:

{
  "document_type": ""
}
"""


# specific prompt for each document

PAN_PROMPT = """
Extract structured information from this PAN card.

Return strictly valid JSON:

{
  "document_type": "pan_card",
  "fields": {
    "full_name": null,
    "date_of_birth": null,
    "pan_number": null
  }
}
"""

AADHAAR_PROMPT = """
Extract structured information from this Aadhaar card.

Aadhaar number must be 12 digits.

Return strictly valid JSON:

{
  "document_type": "aadhaar_card",
  "fields": {
    "full_name": null,
    "date_of_birth": null,
    "gender": null,
    "aadhaar_number": null,
    "address": null
  }
}
"""

PAYSLIP_PROMPT = """
Extract structured salary information from this payslip.

Return strictly valid JSON:

{
  "document_type": "payslip",
  "fields": {
    "employee_name": null,
    "company_name": null,
    "employee_id": null,
    "designation": null,
    "pay_period": null,
    "basic_salary": null,
    "hra": null,
    "gross_salary": null,
    "net_salary": null,
    "deductions_total": null
  }
}
"""


# extracting the json response
def extract_json(text):
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


# main function
def parse_document(image):

    # document type
    classification_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[image, CLASSIFICATION_PROMPT]
    )

    if not classification_response or not classification_response.text:
        return {"error": "Document classification failed"}

    try:
        doc_info = extract_json(classification_response.text)
        doc_type = doc_info.get("document_type", "unknown")
    except Exception:
        return {
            "error": "Failed to parse classification response",
            "raw_response": classification_response.text
        }

    # prompt call
    if doc_type == "pan_card":
        prompt = PAN_PROMPT
    elif doc_type == "aadhaar_card":
        prompt = AADHAAR_PROMPT
    elif doc_type == "payslip":
        prompt = PAYSLIP_PROMPT
    else:
        return {
            "document_type": "unknown",
            "fields": {}
        }

    extraction_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[image, prompt]
    )

    if not extraction_response or not extraction_response.text:
        return {"error": "Extraction failed"}

    try:
        return extract_json(extraction_response.text)
    except Exception:
        return {
            "error": "Failed to parse extraction response",
            "raw_response": extraction_response.text
        }
