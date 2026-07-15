from __future__ import annotations

import posixpath
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .audits import relationship_part_for, resolve_part_target
from .normalizer import normalize_internal_ids, remove_dangling_style_references, set_paragraph_style
from .ooxml import CT, CT_NS, NS, R, REL, REL_NS, W, clean_mc_ignorable, serialize_xml, visible_text
from .provenance import ProvenanceEntry, make_paragraph_provenance


@dataclass(frozen=True)
class SourceArticlePackage:
    article_id: str
    section: str
    path: Path
    paragraph_style_map: dict[int, str]


@dataclass(frozen=True)
class AssemblyResult:
    output_path: Path
    provenance: list[ProvenanceEntry]
    diagnostics: dict[str, int]


def _read_zip(path: Path) -> tuple[dict[str, bytes], dict[str, zipfile.ZipInfo]]:
    with zipfile.ZipFile(path, "r") as archive:
        return {name: archive.read(name) for name in archive.namelist()}, {info.filename: info for info in archive.infolist()}


def _write_zip(path: Path, parts: dict[str, bytes], infos: dict[str, zipfile.ZipInfo]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            old = infos.get(name)
            info = zipfile.ZipInfo(name, old.date_time if old else (2026, 1, 1, 0, 0, 0))
            info.external_attr = old.external_attr if old else 0
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)


def _content_type_for(content_types_root: ET.Element, part_name: str) -> str | None:
    part_key = "/" + part_name
    for override in content_types_root.findall(f"{CT}Override"):
        if override.get("PartName") == part_key:
            return override.get("ContentType")
    ext = part_name.rsplit(".", 1)[-1].lower() if "." in part_name else ""
    for default in content_types_root.findall(f"{CT}Default"):
        if default.get("Extension", "").lower() == ext:
            return default.get("ContentType")
    return None


def _ensure_content_type(content_types_root: ET.Element, part_name: str, content_type: str | None) -> None:
    if not content_type:
        return
    part_key = "/" + part_name
    for override in content_types_root.findall(f"{CT}Override"):
        if override.get("PartName") == part_key:
            return
    ext = part_name.rsplit(".", 1)[-1].lower() if "." in part_name else ""
    for default in content_types_root.findall(f"{CT}Default"):
        if default.get("Extension", "").lower() == ext and default.get("ContentType") == content_type:
            return
    override = ET.SubElement(content_types_root, CT + "Override")
    override.set("PartName", part_key)
    override.set("ContentType", content_type)


def _relative_target(from_part: str, to_part: str) -> str:
    from_folder = from_part.rsplit("/", 1)[0] if "/" in from_part else ""
    return posixpath.relpath(to_part, from_folder)


def _next_rid(rels_root: ET.Element) -> str:
    max_id = 0
    for rel in rels_root.findall(f"{REL}Relationship"):
        rid = rel.get("Id", "")
        if rid.startswith("rId") and rid[3:].isdigit():
            max_id = max(max_id, int(rid[3:]))
    return f"rId{max_id + 1}"


def _used_relationship_ids(element: ET.Element) -> set[str]:
    used = set()
    for node in element.iter():
        for attr, value in node.attrib.items():
            if attr in {R + "id", R + "embed", R + "link"}:
                used.add(value)
    return used


def _copy_related_part(
    source_parts: dict[str, bytes],
    final_parts: dict[str, bytes],
    source_content_types: ET.Element,
    final_content_types: ET.Element,
    source_part: str,
    article_id: str,
    cache: dict[str, str],
) -> str:
    if source_part in cache:
        return cache[source_part]
    if source_part not in source_parts:
        return source_part
    folder, filename = source_part.rsplit("/", 1)
    stem, dot, ext = filename.partition(".")
    new_part = f"{folder}/{article_id}_{stem}.{ext}" if dot else f"{folder}/{article_id}_{filename}"
    counter = 1
    while new_part in final_parts:
        new_part = f"{folder}/{article_id}_{stem}_{counter}.{ext}" if dot else f"{folder}/{article_id}_{filename}_{counter}"
        counter += 1
    cache[source_part] = new_part
    final_parts[new_part] = source_parts[source_part]
    _ensure_content_type(final_content_types, new_part, _content_type_for(source_content_types, source_part))

    rels_name = relationship_part_for(source_part)
    if rels_name in source_parts:
        rels_root = ET.fromstring(source_parts[rels_name])
        new_rels_root = ET.Element(REL + "Relationships")
        for rel in rels_root.findall(f"{REL}Relationship"):
            target = rel.get("Target")
            if not target:
                continue
            new_rel = ET.SubElement(new_rels_root, REL + "Relationship")
            for key, value in rel.attrib.items():
                new_rel.set(key, value)
            if rel.get("TargetMode") != "External":
                child_source_part = resolve_part_target(source_part, target)
                child_new_part = _copy_related_part(
                    source_parts,
                    final_parts,
                    source_content_types,
                    final_content_types,
                    child_source_part,
                    article_id,
                    cache,
                )
                new_rel.set("Target", _relative_target(new_part, child_new_part))
        final_parts[relationship_part_for(new_part)] = serialize_xml(new_rels_root, REL_NS)
    return new_part


def _make_paragraph(text: str, style_id: str = "a0") -> ET.Element:
    para = ET.Element(W + "p")
    props = ET.SubElement(para, W + "pPr")
    style = ET.SubElement(props, W + "pStyle")
    style.set(W + "val", style_id)
    run = ET.SubElement(para, W + "r")
    text_node = ET.SubElement(run, W + "t")
    text_node.text = text
    return para


def _make_page_break() -> ET.Element:
    para = ET.Element(W + "p")
    run = ET.SubElement(para, W + "r")
    br = ET.SubElement(run, W + "br")
    br.set(W + "type", "page")
    return para


def _normalise_source_body(article: SourceArticlePackage, source_root: ET.Element) -> list[ET.Element]:
    body = source_root.find(".//w:body", NS)
    if body is None:
        raise ValueError(f"{article.article_id}: missing word body")
    imported = []
    for idx, child in enumerate(list(body)):
        if child.tag == W + "sectPr":
            continue
        clone = ET.fromstring(serialize_xml(child))
        if clone.tag == W + "p":
            set_paragraph_style(clone, article.paragraph_style_map.get(idx, "a0"))
        for para in clone.findall(".//w:p", NS):
            set_paragraph_style(para, "TABLETEXT")
        imported.append(clone)
    return imported


def _import_article_parts(
    article: SourceArticlePackage,
    imported_elements: list[ET.Element],
    source_parts: dict[str, bytes],
    final_parts: dict[str, bytes],
    final_rels_root: ET.Element,
    final_content_types: ET.Element,
) -> None:
    source_rels = source_parts.get("word/_rels/document.xml.rels")
    if not source_rels:
        return
    used_rids = set().union(*(_used_relationship_ids(element) for element in imported_elements))
    source_rels_root = ET.fromstring(source_rels)
    source_content_types = ET.fromstring(source_parts["[Content_Types].xml"])
    rid_map: dict[str, str] = {}
    copy_cache: dict[str, str] = {}
    for rel in source_rels_root.findall(f"{REL}Relationship"):
        old_id = rel.get("Id")
        target = rel.get("Target")
        rel_type = rel.get("Type")
        if not old_id or old_id not in used_rids or not target or not rel_type:
            continue
        new_id = _next_rid(final_rels_root)
        target_mode = rel.get("TargetMode")
        if target_mode == "External":
            new_target = target
        else:
            source_part = resolve_part_target("word/document.xml", target)
            copied_part = _copy_related_part(
                source_parts,
                final_parts,
                source_content_types,
                final_content_types,
                source_part,
                article.article_id,
                copy_cache,
            )
            new_target = _relative_target("word/document.xml", copied_part)
        new_rel = ET.SubElement(final_rels_root, REL + "Relationship")
        new_rel.set("Id", new_id)
        new_rel.set("Type", rel_type)
        new_rel.set("Target", new_target)
        if target_mode:
            new_rel.set("TargetMode", target_mode)
        rid_map[old_id] = new_id

    for element in imported_elements:
        for node in element.iter():
            for attr, value in list(node.attrib.items()):
                if value in rid_map and attr in {R + "id", R + "embed", R + "link"}:
                    node.set(attr, rid_map[value])


def assemble_articles_into_etalon(
    etalon_path: Path,
    articles: list[SourceArticlePackage],
    output_path: Path,
    toc_marker: str = "TOC NOT GENERATED IN THIS CYCLE",
) -> AssemblyResult:
    final_parts, final_infos = _read_zip(etalon_path)
    document_root = ET.fromstring(final_parts["word/document.xml"])
    styles_root = ET.fromstring(final_parts["word/styles.xml"])
    body = document_root.find(".//w:body", NS)
    if body is None:
        raise ValueError("ETALON missing word body")

    final_rels_name = "word/_rels/document.xml.rels"
    final_rels_root = ET.fromstring(final_parts[final_rels_name])
    final_content_types = ET.fromstring(final_parts["[Content_Types].xml"])
    final_sect = body.find("w:sectPr", NS)
    for child in list(body):
        body.remove(child)
    body.append(_make_paragraph(toc_marker, "a0"))

    provenance: list[ProvenanceEntry] = []
    current_section = None
    final_paragraph_index = 1
    for article in articles:
        body.append(_make_page_break())
        final_paragraph_index += 1
        if article.section != current_section:
            current_section = article.section
            body.append(_make_paragraph(article.section, "SECTION"))
            final_paragraph_index += 1
        source_parts, _source_infos = _read_zip(article.path)
        source_root = ET.fromstring(source_parts["word/document.xml"])
        imported = _normalise_source_body(article, source_root)
        _import_article_parts(article, imported, source_parts, final_parts, final_rels_root, final_content_types)
        source_paragraph_index = 0
        for element in imported:
            body.append(element)
            paragraphs = [element] if element.tag == W + "p" else element.findall(".//w:p", NS)
            for para in paragraphs:
                text = visible_text(para)
                style = para.find("w:pPr/w:pStyle", NS)
                style_id = style.get(W + "val") if style is not None else "a0"
                provenance.append(
                    make_paragraph_provenance(
                        article.article_id,
                        source_paragraph_index,
                        text,
                        style_id,
                        "NORMALIZE" if style_id != "a0" else "PRESERVE",
                        final_paragraph_index,
                        style_id,
                    )
                )
                source_paragraph_index += 1
                final_paragraph_index += 1
    if final_sect is not None:
        body.append(final_sect)

    diagnostics = {}
    diagnostics.update(normalize_internal_ids(document_root))
    diagnostics.update(remove_dangling_style_references(document_root, styles_root))

    final_parts["word/document.xml"] = clean_mc_ignorable(serialize_xml(document_root))
    final_parts[final_rels_name] = serialize_xml(final_rels_root, REL_NS)
    final_parts["[Content_Types].xml"] = serialize_xml(final_content_types, CT_NS)
    _write_zip(output_path, final_parts, final_infos)
    return AssemblyResult(output_path=output_path, provenance=provenance, diagnostics=diagnostics)
