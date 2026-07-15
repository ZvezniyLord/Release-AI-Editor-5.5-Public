from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from journal_factory.assembly.audits import direct_formatting_histogram, missing_relationship_targets
from journal_factory.assembly.matcher import ArticleExpectation, CandidateEvidence, decide_match
from journal_factory.assembly.package_importer import SourceArticlePackage, assemble_articles_into_etalon
from journal_factory.assembly.synthetic_fixture import create_synthetic_etalon, create_synthetic_source


def _read(path: Path, name: str) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read(name).decode("utf-8")


def test_matcher_requires_two_independent_semantic_evidence_items() -> None:
    expected = ArticleExpectation(
        article_id="SYN-A001",
        order=1,
        section="Synthetic Section",
        authors=["Ivan Petrenko"],
        title="Synthetic Exact Title",
        doi="10.1234/test.1",
    )

    exact = CandidateEvidence(
        candidate_id="candidate-exact",
        source_authors=["Ivan Petrenko"],
        source_title="Synthetic Exact Title",
    )
    transliterated = CandidateEvidence(
        candidate_id="candidate-translit",
        source_authors=["\u041f\u0435\u0442\u0440\u0435\u043d\u043a\u043e \u0406\u0432\u0430\u043d"],
        source_title="Synthetic Exact Title",
    )
    ambiguous = CandidateEvidence(
        candidate_id="candidate-ambiguous",
        folder_hint="SYN-A001",
        unused_file_hint=True,
        source_title="Different Title",
    )

    assert decide_match(expected, exact).semantic_pair == "author+title"
    assert decide_match(expected, transliterated).status == "matched"
    ambiguous_decision = decide_match(expected, ambiguous)
    assert ambiguous_decision.status == "review"
    assert "requires_two_independent_semantic_evidence_items" in ambiguous_decision.notes


def test_ooxml_importer_regressions(tmp_path: Path) -> None:
    etalon = create_synthetic_etalon(tmp_path / "etalon.docx")
    source = create_synthetic_source(tmp_path / "source.docx")
    output = tmp_path / "assembled.docx"

    result = assemble_articles_into_etalon(
        etalon,
        [
            SourceArticlePackage(
                article_id="SYN-A001",
                section="Synthetic Section",
                path=source,
                paragraph_style_map={0: "UDC", 1: "AUTOR", 2: "11", 6: "a0"},
            )
        ],
        output,
    )

    assert output.exists()
    assert not missing_relationship_targets(output)
    assert result.provenance
    assert result.provenance[0].article_id == "SYN-A001"
    assert result.diagnostics["removed_unknown_rStyle"] >= 1
    assert result.diagnostics["removed_unknown_tblStyle"] >= 1
    assert result.diagnostics["reassigned_drawing_ids"] >= 2
    assert result.diagnostics["reassigned_bookmark_ids"] >= 2

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert any(name.startswith("word/charts/SYN-A001_") for name in names)
        assert any(name.startswith("word/embeddings/SYN-A001_") for name in names)
        assert any(name.startswith("word/media/SYN-A001_image1") for name in names)
        assert not any("unused" in name for name in names)

    document_xml = _read(output, "word/document.xml")
    root_tag = document_xml[document_xml.find("<w:document") : document_xml.find(">", document_xml.find("<w:document")) + 1]
    declared = set(re.findall(r"xmlns:([^=]+)=", root_tag))
    ignorable = set((re.search(r'Ignorable="([^"]*)"', root_tag).group(1) or "").split())
    assert not (ignorable - declared)

    assert "MissingChar" not in document_xml
    assert "MissingTable" not in document_xml
    assert "rIdUnused" not in document_xml
    assert "<m:oMath>" in document_xml
    assert "Table cell text" in document_xml

    root = ET.fromstring(document_xml)
    drawing_ids = [
        node.get("id")
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "docPr" and node.get("id")
    ]
    assert len(drawing_ids) == len(set(drawing_ids))

    bookmark_start_ids = [
        node.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id")
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "bookmarkStart"
    ]
    assert len(bookmark_start_ids) == len(set(bookmark_start_ids))


def test_direct_formatting_histogram_groups_by_rule_property_role_and_safety() -> None:
    rows = direct_formatting_histogram(
        [
            {
                "article_id": "SYN-A001",
                "rule_code": "DIRECT_FONT",
                "property": "font",
                "semantic_role": "body",
                "safe_to_auto_fix": True,
            },
            {
                "article_id": "SYN-A002",
                "rule_code": "DIRECT_FONT",
                "property": "font",
                "semantic_role": "body",
                "safe_to_auto_fix": True,
            },
            {
                "article_id": "SYN-A002",
                "rule_code": "DIRECT_COLOR",
                "property": "color",
                "semantic_role": "caption",
                "safe_to_auto_fix": False,
            },
        ]
    )
    assert rows == [
        {
            "rule_code": "DIRECT_COLOR",
            "property": "color",
            "semantic_role": "caption",
            "article_count": 1,
            "finding_count": 1,
            "safe_to_auto_fix": False,
        },
        {
            "rule_code": "DIRECT_FONT",
            "property": "font",
            "semantic_role": "body",
            "article_count": 2,
            "finding_count": 2,
            "safe_to_auto_fix": True,
        },
    ]
