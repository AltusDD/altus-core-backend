import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path


DB_PR_MARKER_START = "<!-- db-proof-gate:start -->"
DB_PR_MARKER_END = "<!-- db-proof-gate:end -->"
DOC_SCAN_ROOTS = (
    "docs/database/",
    "docs/contracts/",
    "docs/governance/",
    "docs/architecture/DATA_MAP_V1.md",
)
BANNED_PHRASES = (
    "confirmed live schema",
    "definitive live schema",
    "guaranteed current production schema",
    "guaranteed live state",
    "no unknowns",
)


class GuardError(RuntimeError):
    pass


def run_git_diff(base_sha: str, head_sha: str) -> list[str]:
    if not base_sha or not head_sha:
        return []
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}..{head_sha}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def parse_event(path: Path) -> tuple[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    pull_request = data.get("pull_request") or {}
    body = pull_request.get("body") or ""
    number = int(pull_request.get("number") or 0)
    return body, number


def parse_metadata(body: str) -> dict[str, object]:
    match = re.search(
        re.escape(DB_PR_MARKER_START) + r"(.*?)" + re.escape(DB_PR_MARKER_END),
        body,
        flags=re.S,
    )
    if not match:
        raise GuardError("missing DB proof metadata block in PR body")

    block = match.group(1).strip().splitlines()
    data: dict[str, object] = {}
    current_key: str | None = None
    current_list: list[str] = []

    for raw_line in block:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if re.match(r"^[a-z_]+:\s*", line):
            if current_key and current_list:
                data[current_key] = current_list[:]
                current_list.clear()
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = value
                current_key = None
            else:
                current_key = key
                data[current_key] = []
        elif line.lstrip().startswith("-") and current_key:
            current_list.append(line.split("-", 1)[1].strip())
            data[current_key] = current_list[:]
        else:
            raise GuardError(f"unparseable DB proof metadata line: {line}")

    required = {
        "schema_change_claimed",
        "verification_sql_present",
        "changed_objects",
        "rollback_note",
        "contract_or_data_map_changed",
        "unknowns",
    }
    missing = sorted(required - set(data))
    if missing:
        raise GuardError("missing DB proof metadata keys: " + ",".join(missing))
    return data


def normalize_bool(value: object, key: str) -> bool:
    if not isinstance(value, str):
        raise GuardError(f"{key} must be yes or no")
    lowered = value.strip().lower()
    if lowered not in {"yes", "no"}:
        raise GuardError(f"{key} must be yes or no")
    return lowered == "yes"


def ensure_nonempty_list(value: object, key: str) -> list[str]:
    if not isinstance(value, list):
        raise GuardError(f"{key} must be a list")
    cleaned = [item.strip() for item in value if item.strip()]
    if not cleaned:
        raise GuardError(f"{key} must not be empty")
    return cleaned


def has_prefix(files: list[str], prefix: str) -> bool:
    return any(path.startswith(prefix) for path in files)


def has_exact(files: list[str], target: str) -> bool:
    return any(path == target for path in files)


def scan_docs_for_fake_certainty(files: list[str]) -> list[str]:
    hits: list[str] = []
    for file_name in files:
        if not any(file_name == root or file_name.startswith(root) for root in DOC_SCAN_ROOTS):
            continue
        content = Path(file_name).read_text(encoding="utf-8").lower()
        for phrase in BANNED_PHRASES:
            if phrase in content:
                hits.append(f"{file_name}:{phrase}")
    return hits


def build_manifest(proof_dir: Path, changed_files: list[str], metadata: dict[str, object], pr_number: int) -> None:
    proof_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "pr_number": pr_number,
        "changed_files": changed_files,
        "metadata": metadata,
    }
    (proof_dir / "db_proof_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate DB proof requirements for PRs")
    parser.add_argument("--event-path", default="")
    parser.add_argument("--base-sha", default="")
    parser.add_argument("--head-sha", default="")
    parser.add_argument("--proof-dir", required=True)
    args = parser.parse_args()

    proof_dir = Path(args.proof_dir)
    pr_body = ""
    pr_number = 0
    if args.event_path:
        pr_body, pr_number = parse_event(Path(args.event_path))

    changed_files = run_git_diff(args.base_sha, args.head_sha)
    if pr_body:
        metadata = parse_metadata(pr_body)
    else:
        metadata = {
            "schema_change_claimed": "no",
            "verification_sql_present": "no",
            "changed_objects": ["manual-run-without-pr-context"],
            "rollback_note": "Manual workflow dispatch without PR body context.",
            "contract_or_data_map_changed": "no",
            "unknowns": ["PR body was not provided to the manual run."],
        }

    schema_change = normalize_bool(metadata["schema_change_claimed"], "schema_change_claimed")
    verification_present = normalize_bool(metadata["verification_sql_present"], "verification_sql_present")
    contract_or_data_map_changed = normalize_bool(
        metadata["contract_or_data_map_changed"], "contract_or_data_map_changed"
    )
    changed_objects = ensure_nonempty_list(metadata["changed_objects"], "changed_objects")
    unknowns = ensure_nonempty_list(metadata["unknowns"], "unknowns")
    rollback_note = str(metadata["rollback_note"]).strip()
    if not rollback_note:
        raise GuardError("rollback_note must not be empty")

    failures: list[str] = []

    if schema_change and not has_prefix(changed_files, "supabase/migrations/"):
        failures.append("schema change claimed but no file changed under supabase/migrations/")
    if schema_change and not has_prefix(changed_files, "supabase/verification/"):
        failures.append("schema change claimed but no file changed under supabase/verification/")
    if verification_present and not has_prefix(changed_files, "supabase/verification/"):
        failures.append("verification_sql_present=yes but no file changed under supabase/verification/")
    if contract_or_data_map_changed and not has_exact(changed_files, "docs/architecture/DATA_MAP_V1.md"):
        failures.append("contract_or_data_map_changed=yes but docs/architecture/DATA_MAP_V1.md was not updated")
    if len(changed_objects) == 1 and changed_objects[0].strip().lower() == "none" and schema_change:
        failures.append("changed_objects cannot be 'none' when schema_change_claimed=yes")
    fake_certainty_hits = scan_docs_for_fake_certainty(changed_files)
    if fake_certainty_hits:
        failures.append("fake certainty language detected in docs: " + ", ".join(fake_certainty_hits))

    build_manifest(proof_dir, changed_files, metadata, pr_number)

    lines = [
        f"CHECK_PR_NUMBER={pr_number}",
        f"CHECK_CHANGED_FILE_COUNT={len(changed_files)}",
        f"CHECK_SCHEMA_CHANGE={'yes' if schema_change else 'no'}",
        f"CHECK_VERIFICATION_SQL={'yes' if verification_present else 'no'}",
        f"CHECK_CONTRACT_OR_DATA_MAP_CHANGED={'yes' if contract_or_data_map_changed else 'no'}",
        f"CHECK_CHANGED_OBJECTS={';'.join(changed_objects)}",
        f"CHECK_UNKNOWNS={';'.join(unknowns)}",
    ]
    if failures:
        lines.extend(f"CHECK_FAIL={failure}" for failure in failures)
        lines.append("CHECK_RESULT=FAIL")
        (proof_dir / "db_proof_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        raise GuardError("; ".join(failures))

    lines.append("CHECK_RESULT=PASS")
    (proof_dir / "db_proof_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except GuardError as exc:
        print("CHECK_RESULT=FAIL")
        print(f"CHECK_ERROR={exc}")
        raise SystemExit(1)
