from pathlib import Path
from services.requirements_audit import build_requirements_audit


def test_requirements_audit_detects_known_areas():
    root = Path(__file__).resolve().parents[2]
    audit = build_requirements_audit(root)
    assert audit["area_count"] >= 20
    assert audit["summary"]["missing"] == 0
    assert audit["atomic_649"]["available"] is False


def test_atomic_source_is_not_fabricated(tmp_path):
    audit = build_requirements_audit(tmp_path)
    assert audit["atomic_649"]["status"] == "SOURCE_REQUIRED"
    assert audit["atomic_649"]["available"] is False
