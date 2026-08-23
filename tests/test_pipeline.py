"""End-to-end tests for docling-harness. Run with: python tests/test_pipeline.py"""

import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from docling_harness.extractor import extract, collect_sources
from docling_harness.chunker import chunk_document, group_chunks
from docling_harness.rules_extractor import structured_extract, merge_deterministic, requirements_from_headings, apply_requirements
from docling_harness.classifier import merge_items, resolve_llm_config
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


def test_rules_extractor():
    """11.8 Test deterministic extraction of multi-line RN rules and CA criteria."""
    text = (
        '- RQ01-RN01 - Alteração de Label do campo de data inicial: O sistema deverá alterar o texto.\n'
        '  continuando a regra em outra linha\n'
        "- o Nova opção: 'Permitir recadastramento somente durante o período da campanha'\n"
        '- RQ01-RN02 - Alteração de Label do título.\n'
        'Formulário: Documento de Requisitos Página 6 Classificação: Uso restrito\n'
        'Recad Personalizado - Melhorias Minha Área e SOU Conectado\n'
        'Recad Personalizado - Melhorias Minha Área e SOU Conectado\n'
        '- RQ01-CA01 - Validação da Label do campo de data inicial: O sistema deve exibir o texto.\n'
        '- RQ01-CA02 - Validação da Label do título.\n'
    )
    out = structured_extract(text, "7.1 RQ01", "spec.pdf")
    rules = out["specs"]["business_rules"]
    acs = out["specs"]["acceptance_criteria"]

    assert len(rules) == 2, f"expected 2 rules, got {len(rules)}"
    assert rules[0]["id"] == "RQ01-RN01"
    assert "Permitir recadastramento somente durante o período da campanha" in rules[0]["rule"]
    assert rules[1]["id"] == "RQ01-RN02"
    assert "Recad Personalizado" not in rules[1]["rule"]
    assert "Formulário" not in " ".join(r["rule"] for r in rules)

    assert len(acs) == 2, f"expected 2 criteria, got {len(acs)}"
    assert acs[0]["id"] == "RQ01-CA01"
    assert acs[0]["description"].startswith("RQ01-CA01")
    assert "spec.pdf" in acs[0]["source"]
    assert "7.1 RQ01" in acs[0]["source"]
    print("  OK: deterministic extractor captures rules and criteria verbatim")


def test_merge_deterministic_union():
    """11.9 Test union of deterministic extraction with LLM classification, dedup by rule id."""
    det = structured_extract("- RQ01-RN01 - regra exata do documento.", "7.1 RQ01", "spec.pdf")
    body = {
        "specs": {
            "business_rules": [
                {"rule": "RQ01-RN01 - parafrase do LLM"},
                {"rule": "regra livre sem id"},
            ],
            "acceptance_criteria": [
                {"description": "RQ01-CA03 - criterio novo"},
            ],
        }
    }
    merged = merge_deterministic(body, det)
    rules = merged["specs"]["business_rules"]
    assert len(rules) == 2, f"expected 2 rules (1 verbatim + 1 free-form), got {len(rules)}"
    assert "regra exata" in rules[0]["rule"], "verbatim rule must win over LLM paraphrase"
    assert len(merged["specs"]["acceptance_criteria"]) == 1, "LLM-only criterion is retained"
    print("  OK: deterministic items win over LLM duplicates by rule id")


def test_group_chunks():
    """11.10 Test section grouping reassembles fragments and drops short noise groups."""
    chunks = [
        {"index": 0, "heading_path": "", "text": "PORTFÓLIO"},
        {"index": 1, "heading_path": "7.1 RQ01: ALTERAR CONFIGURAÇÕES", "text": "Como administrador"},
        {"index": 2, "heading_path": "REGRAS DE NEGÓCIO:", "text": "- RQ01-RN01 - regra muito longa de negócio aqui"},
        {"index": 3, "heading_path": "7.2 RQ02: EDITAR PRAZO", "text": "Como administrador"},
        {"index": 4, "heading_path": "REGRAS DE NEGÓCIO:", "text": "- RQ02-RN01 - outra regra de negócio longa aqui também"},
    ]
    groups = group_chunks(chunks)
    assert len(groups) == 2, f"expected 2 section groups, got {len(groups)}"
    assert groups[0]["heading_path"].startswith("7.1 RQ01")
    assert "regra muito longa" in groups[0]["text"], "fragment must be absorbed into its section"
    assert groups[1]["heading_path"].startswith("7.2 RQ02")
    print("  OK: group_chunks yields one group per RQ section and drops noise")


def test_merge_items():
    """11.11 Test lossless merge preserves all items, dedups exact text, assigns stable ids."""
    items = [
        ChunkItem(category="classified", items={"specs": {"requirements": [{"description": "req A"}], "business_rules": [{"rule": "rule X"}]}}, source="f1", model_used="m"),
        ChunkItem(category="classified", items={"specs": {"requirements": [{"description": "req A"}], "business_rules": [{"rule": "rule X"}]}}, source="f2", model_used="m"),
        ChunkItem(category="classified", items={"specs": {"acceptance_criteria": [{"description": "ac B"}], "data_models": [{"name": "M1", "fields": []}]}}, source="f3", model_used="m"),
    ]
    out = merge_items(items)
    s = out["specs"]

    assert len(s["requirements"]) == 1, "exact duplicate requirement must be deduped"
    assert s["requirements"][0]["id"] == "REQ-01"
    assert len(s["business_rules"]) == 1
    assert s["business_rules"][0]["id"] == "BR-01"
    assert "f1" in s["business_rules"][0]["source"] and "f2" in s["business_rules"][0]["source"], "sources merged"
    assert len(s["acceptance_criteria"]) == 1
    assert s["acceptance_criteria"][0]["id"] == "AC-01"
    assert len(s["data_models"]) == 1
    assert s["data_models"][0]["id"] == "DM-01"
    assert s["summary"]
    print("  OK: merge_items preserves items, dedups exact text, assigns stable ids")


def test_merge_items_dedups_by_id():
    """12.6 Test merge collapses items sharing a natural id, merging sources."""
    items = [
        ChunkItem(category="classified", items={"specs": {"business_rules": [
            {"id": "RQ07-RN03", "rule": "RQ07-RN03 - Criação de Tooltip ... DADOS PESSOAIS"},
            {"id": "RQ07-RN03", "rule": "RQ07-RN03 - Criação de Tooltip ... DEPENDENTES"},
        ]}}, source="f", model_used="m"),
    ]
    out = merge_items(items)
    rules = out["specs"]["business_rules"]
    assert len(rules) == 1, f"same-id rules must collapse, got {len(rules)}"
    assert rules[0]["id"] == "RQ07-RN03"
    print("  OK: merge_items dedups by natural id, merging sources")


def test_resolve_llm_config_defaults():
    """13.1 Test config resolution defaults to local Ollama."""
    for k in ("HARNESS_LLM_BASE_URL", "HARNESS_LLM_API_KEY", "HARNESS_LLM_MODEL"):
        os.environ.pop(k, None)
    base, key, model = resolve_llm_config()
    assert base == "http://localhost:11434/v1"
    assert key == "ollama"
    assert model == "qwen2.5:14b"
    print("  OK: resolve_llm_config defaults to local Ollama")


def test_resolve_llm_config_env():
    """13.2 Test config resolution honors environment variables."""
    os.environ["HARNESS_LLM_BASE_URL"] = "https://api.deepseek.com"
    os.environ["HARNESS_LLM_API_KEY"] = "sk-test"
    os.environ["HARNESS_LLM_MODEL"] = "deepseek-chat"
    try:
        base, key, model = resolve_llm_config()
        assert base == "https://api.deepseek.com"
        assert key == "sk-test"
        assert model == "deepseek-chat"
    finally:
        for k in ("HARNESS_LLM_BASE_URL", "HARNESS_LLM_API_KEY", "HARNESS_LLM_MODEL"):
            os.environ.pop(k, None)
    print("  OK: resolve_llm_config honors env vars")


def test_resolve_llm_config_model_override():
    """13.3 Test --model override takes precedence over HARNESS_LLM_MODEL."""
    os.environ["HARNESS_LLM_MODEL"] = "deepseek-chat"
    try:
        _, _, model = resolve_llm_config("custom-model")
        assert model == "custom-model"
    finally:
        os.environ.pop("HARNESS_LLM_MODEL", None)
    print("  OK: --model override wins over env var")


def test_group_chunks_merges_same_heading():
    """12.1 Test consecutive same-section fragments merge into a single group."""
    chunks = [
        {"index": 0, "heading_path": "7.1 RQ01: ALTERAR CONFIGURAÇÕES", "text": "Como administrador"},
        {"index": 1, "heading_path": "7.1 RQ01: ALTERAR CONFIGURAÇÕES", "text": "Quero visualizar as novas frases"},
        {"index": 2, "heading_path": "REGRAS DE NEGÓCIO:", "text": "- RQ01-RN01 - regra muito longa de negócio aqui"},
        {"index": 3, "heading_path": "7.2 RQ02: EDITAR PRAZO", "text": "Como administrador"},
        {"index": 4, "heading_path": "REGRAS DE NEGÓCIO:", "text": "- RQ02-RN01 - outra regra de negócio longa aqui também"},
    ]
    groups = group_chunks(chunks)
    assert len(groups) == 2, f"expected 2 groups, got {len(groups)}"
    assert groups[0]["heading_path"].startswith("7.1 RQ01")
    assert "Quero visualizar" in groups[0]["text"], "same-heading fragment must merge, not split"
    assert "regra muito longa" in groups[0]["text"]
    assert groups[1]["heading_path"].startswith("7.2 RQ02")
    print("  OK: group_chunks merges consecutive same-heading fragments")


def test_merge_deterministic_drops_near_duplicates():
    """12.2 Test id-less LLM paraphrase of a verbatim rule is dropped; distinct rule kept."""
    det = structured_extract(
        "- RQ01-RN01 - O sistema deverá exibir a seção Dados Funcionais ao cadastrar uma campanha",
        "7.4 RQ04", "spec.pdf",
    )
    body = {
        "specs": {
            "business_rules": [
                {"rule": "Exibir a seção de Dados Funcionais durante o cadastro da campanha"},
                {"rule": "Confirmar cadastro sem seleção de campos bloqueia o botão concluir recadastramento"},
            ],
        }
    }
    out = merge_deterministic(body, det)
    texts = [r["rule"] for r in out["specs"]["business_rules"]]
    assert any("RQ01-RN01" in t for t in texts), "verbatim rule must be kept"
    assert not any("Exibir a seção de Dados Funcionais durante" in t for t in texts), "paraphrase must be dropped"
    assert any("Confirmar cadastro sem seleção" in t for t in texts), "distinct rule must be kept"
    print("  OK: near-duplicate LLM paraphrases dropped, distinct rules kept")


def test_requirements_from_headings():
    """12.3 Test requirements derive from headings, filtering changelog/scope noise."""
    reqs = requirements_from_headings(
        "7.15 RQ15: INCLUSÃO DE CAMPOS DE CONTATO DE EMERGÊNCIA NA SEÇÃO CONTATOS",
        "file:spec.pdf",
    )
    assert len(reqs) == 1
    assert reqs[0]["id"] == "RQ15"
    assert "CONTATO DE EMERGÊNCIA" in reqs[0]["description"]
    assert "§7.15" in reqs[0]["source"]

    assert requirements_from_headings("8 REGRAS DE VALIDAÇÃO", "file:spec.pdf", "") == []
    fallback = requirements_from_headings("", "file:spec.pdf", "RQ01-RN01 - regra qualquer")
    assert fallback == [{"id": "RQ01", "description": "RQ01", "source": "file:spec.pdf"}]

    body = apply_requirements({"specs": {"requirements": [{"description": "ruído do histórico"}]}},
                              "7.2 RQ02: EDITAR O PRAZO", "file:spec.pdf", "")
    assert body["specs"]["requirements"][0]["id"] == "RQ02"
    assert "ruído" not in body["specs"]["requirements"][0]["description"]
    print("  OK: requirements derived from headings, LLM noise replaced")


def test_llm_item_source_carries_heading():
    """12.4 Test an LLM-classified item's source includes the section heading."""
    items = [
        ChunkItem(category="classified", items={"specs": {"requirements": [{"id": "RQ15", "description": "x"}]}},
                  source="file:spec.pdf§7.15 RQ15", model_used="m"),
    ]
    out = merge_items(items)
    assert "§7.15 RQ15" in out["specs"]["requirements"][0]["source"]
    print("  OK: LLM item source carries section heading")


def test_comparison_negative_reduction():
    """12.5 Test negative reduction when processed output exceeds raw input."""
    raw = "short document"
    processed = {"specs": {"requirements": [{"description": "long " * 200}]}}
    comp = compute_comparison(raw, processed)
    assert comp.processed_tokens > comp.raw_tokens
    assert comp.reduction_pct < 0, f"expected negative reduction, got {comp.reduction_pct}"
    assert comp.break_even_queries == 999
    print(f"  OK: negative reduction reported ({comp.reduction_pct}%)")


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
