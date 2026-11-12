"""Guard rails for keeping credentials out of Git, logs, and evidence."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = Path(__file__).resolve()
FAKE_CREDENTIAL = "SEGREDO-FALSO-123"

SENSITIVE_ASSIGNMENT = re.compile(
    r"(?im)^[ \t]*(?:export[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*(?=\S)(.*\S)[ \t]*$"
)
AWS_ACCESS_KEY = re.compile(r"\bAKIA[A-Z0-9]{16}\b")
AWS_KEY_ASSIGNMENT = re.compile(
    r"(?im)^[ \t]*(aws_secret_access_key|aws_access_key_id)[ \t]*=[ \t]*(.*?)[ \t]*$"
)
PYTHON_STRING_LITERAL = re.compile(r"^(?:[rubfRUBF]{0,2})(['\"])(.+)\1$")


def _contains_secret(text: str, *, suffix: str = "") -> bool:
    """Detect credential-like assignments and common AWS credential forms."""
    for match in SENSITIVE_ASSIGNMENT.finditer(text):
        name = match.group(1).upper()
        if name in {"AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID"}:
            continue
        if name == "TOKEN" and match.group(2).strip() in {
            "None",
            'resp["NextContinuationToken"]',
            "resp['NextContinuationToken']",
        }:
            continue
        if name in {"S3_ACCESS_KEY", "S3_SECRET_KEY"} or any(
            marker in name for marker in ("SECRET", "PASSWORD", "TOKEN")
        ):
            return True
    for match in AWS_KEY_ASSIGNMENT.finditer(text):
        value = match.group(2).strip()
        if suffix.lower() == ".py":
            literal = PYTHON_STRING_LITERAL.fullmatch(value)
            if literal and literal.group(2):
                return True
        elif value:
            return True
    return bool(AWS_ACCESS_KEY.search(text))


def _git_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT.parent, check=True, capture_output=True
    )
    return [ROOT.parent / item.decode() for item in result.stdout.split(b"\0") if item]


def _read_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
        return raw.decode("utf-8") if b"\0" not in raw else None
    except (OSError, UnicodeDecodeError):
        return None


def _tracked_text_files(*, exclude_test: bool = True) -> list[tuple[Path, str]]:
    files = []
    for path in _git_files():
        if not (path.is_relative_to(ROOT) or path == ROOT.parent / ".github/workflows/coleta-diaria.yml"):
            continue
        if exclude_test and path.resolve() == TEST_FILE:
            continue
        text = _read_text(path)
        if text is not None:
            files.append((path, text))
    return files


def test_project_env_is_ignored_and_not_tracked() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "projeto_final/.env"],
        cwd=ROOT.parent,
        check=False,
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "projeto_final/.env"],
        cwd=ROOT.parent,
        capture_output=True,
        check=False,
    )
    assert ignored.returncode == 0, "projeto_final/.env precisa estar ignorado"
    assert tracked.returncode != 0, "projeto_final/.env não pode estar versionado"


def test_detector_finds_a_clearly_fake_credential() -> None:
    fake_text = f"S3_SECRET_KEY={FAKE_CREDENTIAL}"
    assert _contains_secret(fake_text)


def test_detector_rejects_quoted_aws_credential_literal_in_python() -> None:
    fake_python = f'aws_secret_access_key="{FAKE_CREDENTIAL}"'
    assert _contains_secret(fake_python, suffix=".py")


def test_detector_allows_aws_credential_variable_in_python() -> None:
    variable_python = "aws_secret_access_key=secret_key"
    assert not _contains_secret(variable_python, suffix=".py")


def _workflow_has_only_secret_assignments(text: str) -> bool:
    for line in text.splitlines():
        for name in ("S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_ENDPOINT"):
            assignment = re.search(rf"^\s*{name}\s*:\s*(.*?)\s*(?:#.*)?$", line)
            if assignment and assignment.group(1) != f"${{{{ secrets.{name} }}}}":
                return False
    return True


def test_workflow_detector_rejects_a_literal_secret_assignment() -> None:
    fake_workflow = f"      S3_SECRET_KEY: {FAKE_CREDENTIAL}"
    assert not _workflow_has_only_secret_assignments(fake_workflow)


def test_tracked_text_files_contain_no_credentials() -> None:
    for path, text in _tracked_text_files():
        assert not _contains_secret(text, suffix=path.suffix), f"possível credencial em arquivo rastreado: {path.relative_to(ROOT.parent)}"


def test_workflow_references_s3_values_only_through_github_secrets() -> None:
    workflow = ROOT.parent / ".github/workflows/coleta-diaria.yml"
    text = _read_text(workflow)
    assert text is not None, "workflow ausente ou não textual"
    assert _workflow_has_only_secret_assignments(text), (
        "atribuições S3_ACCESS_KEY, S3_SECRET_KEY e S3_ENDPOINT devem usar secrets.NOME"
    )


def test_env_example_sensitive_variables_are_empty() -> None:
    example = _read_text(ROOT / ".env.example")
    assert example is not None, ".env.example ausente ou não textual"
    for line in example.splitlines():
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", line)
        if match and any(marker in match.group(1).upper() for marker in ("KEY", "SECRET", "PASSWORD", "TOKEN")):
            assert match.group(2) == "", f"{match.group(1)} precisa ter valor vazio"


def test_src_does_not_log_or_print_credential_values() -> None:
    src = ROOT / "src"
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        text = _read_text(path)
        if text is None:
            continue
        assignments: set[str] = set()
        for line in text.splitlines():
            assignment = re.search(r"\b([A-Za-z_]\w*)\s*=\s*(?:os\.environ|getenv)\s*", line)
            if assignment and ("S3_SECRET_KEY" in line or "S3_ACCESS_KEY" in line):
                assignments.add(assignment.group(1))
        protected = {"S3_SECRET_KEY", "S3_ACCESS_KEY", *assignments}
        for line_number, line in enumerate(text.splitlines(), 1):
            if re.search(r"\b(?:log\w*|logging)\s*\.\s*\w+\s*\(|\bprint\s*\(", line):
                assert not any(re.search(rf"\b{re.escape(name)}\b", line) for name in protected), (
                    f"referência a credencial em saída de {path.relative_to(ROOT)}:{line_number}"
                )


def test_tracked_and_untracked_evidence_contains_no_credentials() -> None:
    evidence_root = ROOT / "docs/evidencias"
    paths = {path for path, _ in _tracked_text_files() if path.is_relative_to(evidence_root)}
    if evidence_root.exists():
        paths.update(path for path in evidence_root.rglob("*") if path.is_file())
    for path in paths:
        text = _read_text(path)
        if text is not None:
            assert not _contains_secret(text, suffix=path.suffix), f"possível credencial em evidência: {path.relative_to(ROOT.parent)}"
