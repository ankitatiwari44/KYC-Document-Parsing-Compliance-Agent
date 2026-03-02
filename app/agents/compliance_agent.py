import re


def run_compliance_check(documents):

    field_validation = {}
    mismatch_flags = []
    risk_score = 0

    collected_names = {}
    collected_dobs = {}

    MIN_INCOME = 15000  # RBI income guideline

    for doc in documents:

        doc_type = doc.get("document_type")
        fields = doc.get("fields", {})

        # Collect for cross-validation
        if fields.get("full_name"):
            collected_names[doc_type] = fields.get("full_name")

        if fields.get("date_of_birth"):
            collected_dobs[doc_type] = fields.get("date_of_birth")


        # Aadhaar Validation

        if doc_type == "aadhaar_card":

            aadhaar = fields.get("aadhaar_number")
            dob = fields.get("date_of_birth")

            if not aadhaar:
                field_validation["aadhaar_number"] = {
                    "status": "MISSING",
                    "reason": "Aadhaar number not provided"
                }
                risk_score += 40
            else:
                digits_only = re.sub(r"\s+", "", aadhaar)

                if "X" in aadhaar.upper():
                    field_validation["aadhaar_number"] = {
                        "status": "INVALID",
                        "reason": "Aadhaar number is masked"
                    }
                    risk_score += 40

                elif not digits_only.isdigit():
                    field_validation["aadhaar_number"] = {
                        "status": "INVALID",
                        "reason": "Aadhaar must contain only digits"
                    }
                    risk_score += 40

                elif len(digits_only) != 12:
                    field_validation["aadhaar_number"] = {
                        "status": "INVALID",
                        "reason": f"Aadhaar must be 12 digits but found {len(digits_only)} digits"
                    }
                    risk_score += 40

            if not dob:
                field_validation["date_of_birth"] = {
                    "status": "MISSING",
                    "reason": "Date of birth is missing"
                }
                risk_score += 30
            else:
                parts = dob.split("/")
                if len(parts) != 3 or len(parts[2]) != 4:
                    field_validation["date_of_birth"] = {
                        "status": "INVALID",
                        "reason": "Date of birth must include full day/month/year"
                    }
                    risk_score += 30

        # PAN Validation

        if doc_type == "pan_card":

            pan = fields.get("pan_number")
            dob = fields.get("date_of_birth")

            if not pan:
                field_validation["pan_number"] = {
                    "status": "MISSING",
                    "reason": "PAN number not provided"
                }
                risk_score += 40
            else:
                pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
                if not re.match(pattern, pan):
                    field_validation["pan_number"] = {
                        "status": "INVALID",
                        "reason": "PAN must follow format: 5 letters + 4 digits + 1 letter"
                    }
                    risk_score += 40

            if not dob:
                field_validation["date_of_birth"] = {
                    "status": "MISSING",
                    "reason": "Date of birth is missing"
                }
                risk_score += 30
            else:
                parts = dob.split("/")
                if len(parts) != 3 or len(parts[2]) != 4:
                    field_validation["date_of_birth"] = {
                        "status": "INVALID",
                        "reason": "Date of birth must include full day/month/year"
                    }
                    risk_score += 30

        # Payslip 

        if doc_type == "payslip":

            required_fields = [
                "employee_name",
                "company_name",
                "gross_salary",
                "net_salary",
                "deductions_total"
            ]

            for field in required_fields:
                if not fields.get(field):
                    field_validation[field] = {
                        "status": "MISSING",
                        "reason": f"{field} is not provided"
                    }
                    risk_score += 20

            numeric_fields = [
                "gross_salary",
                "net_salary",
                "deductions_total"
            ]

            for field in numeric_fields:
                value = fields.get(field)
                if value is not None:
                    try:
                        value = float(value)
                        if value <= 0:
                            field_validation[field] = {
                                "status": "INVALID",
                                "reason": f"{field} must be greater than zero"
                            }
                            risk_score += 20
                    except:
                        field_validation[field] = {
                            "status": "INVALID",
                            "reason": f"{field} must be numeric"
                        }
                        risk_score += 20

            # Salary consistency check
            gross = fields.get("gross_salary")
            deductions = fields.get("deductions_total")
            net = fields.get("net_salary")

            if gross and deductions and net:
                try:
                    if float(gross) - float(deductions) != float(net):
                        field_validation["salary_mismatch"] = {
                            "status": "INVALID",
                            "reason": "Gross - Deductions does not equal Net Salary"
                        }
                        risk_score += 30
                except:
                    pass

            # RBI income rule
            if net:
                try:
                    if float(net) < MIN_INCOME:
                        field_validation["income_rule"] = {
                            "status": "INVALID",
                            "reason": f"Net salary {net} is below RBI minimum requirement of {MIN_INCOME}"
                        }
                        risk_score += 40
                except:
                    pass


    # Cross-document mismatched if

    if len(collected_names) > 1:
        names = list(collected_names.values())
        if len(set(names)) > 1:
            mismatch_flags.append("Name mismatch across documents")
            risk_score += 50

    if len(collected_dobs) > 1:
        dobs = list(collected_dobs.values())
        if len(set(dobs)) > 1:
            mismatch_flags.append("Date of birth mismatch across documents")
            risk_score += 50


    # Risk check we did

    if risk_score >= 80:
        risk_level = "HIGH"
        final_decision = "REJECTED"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
        final_decision = "MANUAL_REVIEW"
    else:
        risk_level = "LOW"
        final_decision = "APPROVED"

    return {
        "field_validation": field_validation,
        "mismatch_flags": mismatch_flags,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "final_decision": final_decision
    }