#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def read_reviewed_sha_from_manifest(proof_dir: Path) -> str:
    manifest = proof_dir / "proof_manifest.json"
    if not manifest.exists():
        return ""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return ""
    value = data.get("reviewed_commit_sha", "")
    return str(value).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic local Codex compatibility checks")
    parser.add_argument("--proof-dir", default="docs/proofpacks/2026-03-08_be-core_AUTONOMY-04")
    parser.add_argument("--reviewed-sha", default="")
    parser.add_argument("--base-ref", default="origin/feature/core-asset-ingest-01")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    proof_dir = (repo_root / args.proof_dir).resolve() if not Path(args.proof_dir).is_absolute() else Path(args.proof_dir)

    checks_failed = False

    print(f"CHECK_REPO_ROOT={repo_root}")

    git_code, git_out, git_err = run_cmd(["git", "rev-parse", "--show-toplevel"], repo_root)
    if git_code != 0:
        print("CHECK_FAIL_REPO_READABLE=git rev-parse failed")
        if git_err.strip():
            print(git_err.strip())
        return 1

    print("CHECK_REPO_READABLE=PASS")
    print(f"CHECK_GIT_TOPLEVEL={git_out.strip()}")

    route_map = repo_root / "docs/architecture/ROUTE_MAP_V1.md"
    data_map = repo_root / "docs/architecture/DATA_MAP_V1.md"
    contract_pkg = repo_root / "docs/contracts/ASSET_SURFACE_CONTRACTS_V1.md"
    bundle_validator = repo_root / "tools/validate_be_acceptance_bundle.py"
    route_guard = repo_root / "tools/check_route_downgrade_guard.py"

    for label, path in [
        ("ROUTE_MAP", route_map),
        ("DATA_MAP", data_map),
        ("CONTRACT_PACKAGE", contract_pkg),
        ("BUNDLE_VALIDATOR", bundle_validator),
        ("ROUTE_GUARD", route_guard),
    ]:
        if path.exists():
            print(f"CHECK_{label}=PASS path={path}")
        else:
            print(f"CHECK_{label}=FAIL path={path}")
            checks_failed = True

    if not proof_dir.exists():
        print(f"CHECK_FAIL_PROOF_DIR_MISSING={proof_dir}")
        return 1

    reviewed_sha = args.reviewed_sha.strip() or read_reviewed_sha_from_manifest(proof_dir)
    if not reviewed_sha:
        print("CHECK_FAIL_REVIEWED_SHA_MISSING=pass --reviewed-sha or provide manifest reviewed_commit_sha")
        return 1

    print(f"CHECK_PROOF_DIR={proof_dir}")
    print(f"CHECK_REVIEWED_SHA={reviewed_sha}")

    v_cmd = [
        sys.executable,
        str(bundle_validator),
        "--proof-dir",
        str(proof_dir),
        "--reviewed-sha",
        reviewed_sha,
        "--runtime-affecting",
    ]
    v_code, v_out, v_err = run_cmd(v_cmd, repo_root)
    print("CHECK_BUNDLE_VALIDATOR_OUTPUT_BEGIN")
    print(v_out.rstrip())
    if v_err.strip():
        print(v_err.rstrip())
    print("CHECK_BUNDLE_VALIDATOR_OUTPUT_END")
    if v_code == 0:
        print("CHECK_BUNDLE_VALIDATOR_RUNNABLE=PASS")
    else:
        print("CHECK_BUNDLE_VALIDATOR_RUNNABLE=FAIL")
        checks_failed = True

    g_cmd = [
        sys.executable,
        str(route_guard),
        "--route-map",
        "docs/architecture/ROUTE_MAP_V1.md",
        "--base-ref",
        args.base_ref,
    ]
    g_code, g_out, g_err = run_cmd(g_cmd, repo_root)
    print("CHECK_ROUTE_GUARD_OUTPUT_BEGIN")
    print(g_out.rstrip())
    if g_err.strip():
        print(g_err.rstrip())
    print("CHECK_ROUTE_GUARD_OUTPUT_END")
    if g_code == 0:
        print("CHECK_ROUTE_GUARD_RUNNABLE=PASS")
    else:
        print("CHECK_ROUTE_GUARD_RUNNABLE=FAIL")
        checks_failed = True

    if checks_failed:
        print("CHECK_RESULT=FAIL")
        return 1

    print("CHECK_RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
