from __future__ import annotations

from typing import Any


def build_price_engine_disclaimers(
    *,
    validation_warnings: list[str],
    applied_preset_fields: list[str],
    title_quote_provider_key: str | None,
    title_quote_status: str | None,
) -> dict[str, Any]:
    calculation_warnings: list[str] = []
    data_source_warnings: list[str] = []
    use_decision_warnings: list[str] = []

    if applied_preset_fields:
        warning = (
            "Preset defaults filled missing underwriting inputs for this scenario: "
            + ", ".join(applied_preset_fields)
            + "."
        )
        calculation_warnings.append(warning)
        use_decision_warnings.append(
            "One or more underwriting assumptions were standardized from the selected scenario preset rather than supplied explicitly."
        )

    for warning in validation_warnings:
        calculation_warnings.append(warning)
        use_decision_warnings.append(warning)

    if title_quote_provider_key == "liberty" and title_quote_status == "fallback_stub":
        data_source_warnings.append(
            "Liberty quote data was unavailable, so deterministic zero-fee title fallback values were used for this response."
        )
        use_decision_warnings.append(
            "Verify title costs with an approved Liberty quote snapshot before relying on this response for an external decision."
        )

    return {
        "calculation": {
            "message": "Calculated outputs are deterministic underwriting estimates based on the inputs and modeled assumptions provided to this backend response.",
            "warnings": calculation_warnings,
        },
        "dataSources": {
            "message": "Third-party source data, including vendor quote inputs and mapped property data, is normalized for modeling but may be incomplete, delayed, or unavailable at the time of calculation.",
            "warnings": data_source_warnings,
        },
        "useDecision": {
            "message": "This response is decision-support output only and must not be treated as legal, title, lending, appraisal, or investment advice or as a binding commitment.",
            "warnings": use_decision_warnings,
        },
    }
