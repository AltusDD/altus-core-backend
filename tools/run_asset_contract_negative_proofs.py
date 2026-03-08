#!/usr/bin/env python3
import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _http_call(url: str, method: str, headers: dict[str, str], body_obj: Any | None) -> tuple[int, dict[str, str], str]:
    body_bytes: bytes | None = None
    if body_obj is not None:
        body_bytes = json.dumps(body_obj).encode("utf-8")

    request = urllib.request.Request(url=url, data=body_bytes, method=method)
    for key, value in headers.items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = int(response.getcode())
            response_headers = {k.lower(): v for k, v in response.headers.items()}
            response_body = response.read().decode("utf-8", errors="replace")
            return status, response_headers, response_body
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        response_headers = {k.lower(): v for k, v in exc.headers.items()}
        response_body = exc.read().decode("utf-8", errors="replace")
        return status, response_headers, response_body


def _is_json_object_with_keys(raw_body: str, required_keys: list[str]) -> bool:
    try:
        data = json.loads(raw_body)
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    for key in required_keys:
        if key not in data:
            return False
    return True


def _write_http_raw(path: Path, status: int, headers: dict[str, str], body: str) -> None:
    lines = [f"STATUS_CODE={status}"]
    for key in sorted(headers.keys()):
        lines.append(f"{key}: {headers[key]}")
    lines.append("")
    lines.append(body)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic negative contract proofs for accepted asset routes")
    parser.add_argument("--proof-dir", required=True)
    parser.add_argument("--base-url", default="https://altus-core-staging-func.azurewebsites.net")
    parser.add_argument("--org-id", default="d290f1ee-6c54-4b01-90e6-d701748f0851")
    parser.add_argument("--reviewed-sha", required=True)
    args = parser.parse_args()

    proof_dir = Path(args.proof_dir)
    proof_dir.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = [
        {
            "name": "negative_metrics_missing_org",
            "method": "GET",
            "route": "/api/assets/metrics",
            "headers": {},
            "body": None,
            "expected_status": 400,
            "required_body_keys": ["ok", "error"],
            "expected_error_substring": "Invalid request",
        },
        {
            "name": "negative_metrics_invalid_org_uuid",
            "method": "GET",
            "route": "/api/assets/metrics",
            "headers": {"x-altus-org-id": "not-a-uuid"},
            "body": None,
            "expected_status": 400,
            "required_body_keys": ["ok", "error"],
            "expected_error_substring": "Invalid request",
        },
        {
            "name": "negative_resolve_missing_org",
            "method": "POST",
            "route": "/api/assets/resolve",
            "headers": {"Content-Type": "application/json"},
            "body": {"asset": {"apn": "neg-proof-apn"}},
            "expected_status": 400,
            "required_body_keys": ["ok", "error"],
            "expected_error_substring": "Missing required header",
        },
        {
            "name": "negative_resolve_invalid_org_uuid",
            "method": "POST",
            "route": "/api/assets/resolve",
            "headers": {"x-altus-org-id": "not-a-uuid", "Content-Type": "application/json"},
            "body": {"asset": {"apn": "neg-proof-apn"}},
            "expected_status": 400,
            "required_body_keys": ["ok", "error"],
            "expected_error_substring": "valid UUID",
        },
        {
            "name": "negative_resolve_invalid_payload",
            "method": "POST",
            "route": "/api/assets/resolve",
            "headers": {"x-altus-org-id": args.org_id, "Content-Type": "application/json"},
            "body": {"asset": {}},
            "expected_status": 400,
            "required_body_keys": ["ok", "error"],
            "expected_error_substring": "Invalid payload",
        },
        {
            "name": "negative_ingest_missing_org",
            "method": "POST",
            "route": "/api/assets/ingest",
            "headers": {"Content-Type": "application/json"},
            "body": {"source": "MANUAL", "raw": {}},
            "expected_status": 400,
            "required_body_keys": ["ok", "error"],
            "expected_error_substring": "Missing required header",
        },
        {
            "name": "negative_ingest_invalid_org_uuid",
            "method": "POST",
            "route": "/api/assets/ingest",
            "headers": {"x-altus-org-id": "not-a-uuid", "Content-Type": "application/json"},
            "body": {"source": "MANUAL", "raw": {}},
            "expected_status": 400,
            "required_body_keys": ["ok", "error"],
            "expected_error_substring": "valid UUID",
        },
        {
            "name": "negative_ingest_invalid_payload",
            "method": "POST",
            "route": "/api/assets/ingest",
            "headers": {"x-altus-org-id": args.org_id, "Content-Type": "application/json"},
            "body": {"source": "MANUAL"},
            "expected_status": 400,
            "required_body_keys": ["ok", "error"],
            "expected_error_substring": "raw is required",
        },
    ]

    results: list[dict[str, Any]] = []
    failed_cases: list[str] = []

    for case in cases:
        url = f"{args.base_url.rstrip('/')}{case['route']}"
        status, headers, body = _http_call(
            url=url,
            method=case["method"],
            headers=case["headers"],
            body_obj=case["body"],
        )

        file_name = f"{case['name']}_http_raw.txt"
        _write_http_raw(proof_dir / file_name, status, headers, body)

        has_required_body_shape = _is_json_object_with_keys(body, case["required_body_keys"])
        body_has_expected_error = case["expected_error_substring"].lower() in body.lower()

        live_build_sha_full = headers.get("x-altus-build-sha", "")
        reviewed_matches_live = bool(live_build_sha_full) and live_build_sha_full.startswith(args.reviewed_sha)

        passed = (
            status == case["expected_status"]
            and has_required_body_shape
            and body_has_expected_error
            and reviewed_matches_live
        )

        if not passed:
            failed_cases.append(case["name"])

        results.append(
            {
                "name": case["name"],
                "route": case["route"],
                "method": case["method"],
                "status": status,
                "expected_status": case["expected_status"],
                "body_shape_ok": has_required_body_shape,
                "error_match_ok": body_has_expected_error,
                "reviewed_live_sha_match": reviewed_matches_live,
                "live_build_sha": live_build_sha_full,
                "raw_file": file_name,
                "passed": passed,
            }
        )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reviewed_sha": args.reviewed_sha,
        "base_url": args.base_url,
        "case_count": len(results),
        "passed_count": sum(1 for item in results if item["passed"]),
        "failed_count": sum(1 for item in results if not item["passed"]),
        "results": results,
    }

    summary_path = proof_dir / "negative_proof_results.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"CHECK_NEGATIVE_PROOF_DIR={proof_dir}")
    print(f"CHECK_NEGATIVE_CASE_COUNT={len(results)}")
    print(f"CHECK_NEGATIVE_FAILED_COUNT={len(failed_cases)}")
    print(f"CHECK_NEGATIVE_SUMMARY_FILE={summary_path.name}")

    if failed_cases:
        for case_name in failed_cases:
            print(f"CHECK_NEGATIVE_FAIL_CASE={case_name}")
        print("CHECK_RESULT=FAIL")
        return 1

    print("CHECK_RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


