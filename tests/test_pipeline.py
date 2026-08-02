"""End-to-end tests for docling-harness. Run with: python tests/test_pipeline.py"""

import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from docling_harness.extractor import extract, collect_sources
from docling_harness.chunker import chunk_document
from docling_harness.token_counter import count_tokens, compute_comparison
from docling_harness.models import ChunkItem, HarnessOutput, CostComparison
from docling_harness.output import write_output


PDF = pathlib.Path(__file__).parent.parent / "fixture.pdf"


def test_extract_pdf():
    """11.1 Test extraction with the local PDF fixture."""
    if not PDF.exists():
        print("SKIP: PDF fixture not found")
        return

    result = extract(str(PDF))
    assert hasattr(result, "document"), "Result must have .document attribute"
    md = result.document.export_to_markdown()
    assert len(md) > 100, f"Expected >100 chars, got {len(md)}"
    print(f"  OK: Extracted {len(md)} chars of markdown")


def test_token_comparison():
    """11.2 Test token comparison output (raw > processed)."""
    raw_text = "This is a long text that represents document content " * 200
    processed = {"specs": {"requirements": [{"id": "REQ-01", "description": "Short requirement"}]}}

    comp = compute_comparison(raw_text, processed)
    assert comp.raw_tokens > comp.processed_tokens, f"Raw ({comp.raw_tokens}) should exceed processed ({comp.processed_tokens})"
    assert comp.reduction_pct > 0, f"Expected positive reduction, got {comp.reduction_pct}"
    print(f"  OK: {comp.raw_tokens} raw → {comp.processed_tokens} processed ({comp.reduction_pct}% reduction)")


def test_tokens_only():
    """11.5 Test --tokens-only concept (token counting without LLM)."""
    raw = "Test document " * 100
    count = count_tokens(raw)
    assert count > 0, f"Expected >0 tokens, got {count}"
    print(f"  OK: {count} tokens counted without LLM call")


def test_harness_json_structure():
    """11.6 Test harness.json has correct top-level keys and item source references."""
    output = HarnessOutput(
        meta={},
        specs={
            "summary": "test",
            "requirements": [{"id": "REQ-01", "description": "Test req", "source": "pdf:test.pdf:§3.2"}],
        },
        loop_engineering={
            "summary": "test",
            "automation_triggers": [{"trigger": "push", "action": "test", "verifiable": True, "source": "pdf:test.pdf:§4.1"}],
        },
        harness_engineering={
            "summary": "test",
            "context_rules": [{"rule": "Always use tabs", "enforced_by": "lint", "source": "pdf:test.pdf:§5.1"}],
        },
    )
    comparison = CostComparison(raw_tokens=1000, processed_tokens=100, reduction_pct=90.0, break_even_queries=1)

    with tempfile.TemporaryDirectory() as td:
        write_output(output, comparison, td, 1)

        json_path = os.path.join(td, "harness.json")
        assert os.path.exists(json_path), "harness.json not created"

        data = json.loads(pathlib.Path(json_path).read_text())

        assert "_meta" in data, "Missing _meta key"
        assert "specs" in data, "Missing specs key"
        assert "loop_engineering" in data, "Missing loop_engineering key"
        assert "harness_engineering" in data, "Missing harness_engineering key"

        reqs = data["specs"]["requirements"]
        assert len(reqs) == 1
        assert "source" in reqs[0]
        assert "pdf:test.pdf" in reqs[0]["source"]

        meta = data["_meta"]
        assert "cost_comparison" in meta
        assert meta["cost_comparison"]["raw_tokens"] == 1000
        assert meta["sources_processed"] == 1

        print("  OK: harness.json structure and source references correct")


def test_agents_md():
    """11.7 Test AGENTS.md is generated and under 100 lines."""
    output = HarnessOutput(
        meta={},
        specs={"summary": "test summary", "requirements": [], "acceptance_criteria": [], "data_models": [], "business_rules": []},
        loop_engineering={"summary": "loop summary", "automation_triggers": [], "verification_points": [], "feedback_loops": []},
        harness_engineering={"summary": "harness summary", "context_rules": [], "validation_gates": [], "tool_requirements": []},
    )
    comparison = CostComparison(raw_tokens=1000, processed_tokens=100, reduction_pct=90.0, break_even_queries=1)

    with tempfile.TemporaryDirectory() as td:
        write_output(output, comparison, td, 1)

        agents_path = os.path.join(td, "AGENTS.md")
        assert os.path.exists(agents_path), "AGENTS.md not created"

        content = pathlib.Path(agents_path).read_text()
        lines = content.strip().split("\n")
        assert len(lines) <= 100, f"AGENTS.md should be <=100 lines, got {len(lines)}"
        assert "harness.json" in content, "Should reference harness.json"
        print(f"  OK: AGENTS.md generated ({len(lines)} lines)")


def test_collect_sources():
    """Test source collection from directory."""
    with tempfile.TemporaryDirectory() as td:
        pathlib.Path(td, "doc.pdf").write_text("pdf")
        pathlib.Path(td, "notes.md").write_text("md")
        pathlib.Path(td, "config.json").write_text("json")
        pathlib.Path(td, "data.yaml").write_text("yaml")

        files = collect_sources(td)
        names = [pathlib.Path(f).name for f in files]
        assert "doc.pdf" in names
        assert "notes.md" in names
        assert "config.json" not in names  # excluded
        assert "data.yaml" not in names    # excluded
        print(f"  OK: collected {len(files)} of 4 files, excluded json/yaml")


def test_dataclasses():
    """Test model dataclasses instantiate correctly."""
    item = ChunkItem(category="specs", items={"requirements": []}, source="pdf:test.pdf", model_used="test-model")
    assert item.model_used == "test-model"

    comp = CostComparison(raw_tokens=1000, processed_tokens=100, reduction_pct=90.0, break_even_queries=1)
    assert comp.reduction_pct == 90.0

    output = HarnessOutput()
    assert output.specs == {}
    print("  OK: all dataclasses instantiate")


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            print(f"\n--- {name} ---")
            try:
                fn()
            except Exception as e:
                print(f"  FAIL: {e}")
                failures += 1

    print(f"\n{'='*40}")
    if failures:
        print(f"{failures} test(s) FAILED")
        sys.exit(1)
    else:
        print("All tests passed!")
