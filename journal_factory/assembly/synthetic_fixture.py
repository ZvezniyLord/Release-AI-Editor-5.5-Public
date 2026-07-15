from __future__ import annotations

import zipfile
from pathlib import Path


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

STYLES = """<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="a0"><w:name w:val="Normal"/></w:style>
  <w:style w:type="paragraph" w:styleId="SECTION"><w:name w:val="SECTION"/></w:style>
  <w:style w:type="paragraph" w:styleId="11"><w:name w:val="Title"/></w:style>
  <w:style w:type="paragraph" w:styleId="AUTOR"><w:name w:val="AUTOR"/></w:style>
  <w:style w:type="paragraph" w:styleId="UDC"><w:name w:val="UDC"/></w:style>
  <w:style w:type="paragraph" w:styleId="TABLETEXT"><w:name w:val="TABLETEXT"/></w:style>
  <w:style w:type="paragraph" w:styleId="REF-TITLE"><w:name w:val="REF-TITLE"/></w:style>
  <w:style w:type="paragraph" w:styleId="REFER"><w:name w:val="REFER"/></w:style>
  <w:style w:type="paragraph" w:styleId="pip"><w:name w:val="pip"/></w:style>
  <w:style w:type="paragraph" w:styleId="af6"><w:name w:val="caption"/></w:style>
</w:styles>
"""

ETALON_DOCUMENT = """<?xml version="1.0" encoding="UTF-8"?>
<w:document
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  mc:Ignorable="w14 w15 w16">
  <w:body>
    <w:p><w:r><w:t>ETALON SERVICE PAGE</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

SOURCE_DOCUMENT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdChart" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="charts/chart1.xml"/>
  <Relationship Id="rIdImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
  <Relationship Id="rIdUnused" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/unused.png"/>
</Relationships>
"""

CHART_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdWorkbook" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/package" Target="../embeddings/workbook.xlsx"/>
</Relationships>
"""

CHART_XML = """<?xml version="1.0" encoding="UTF-8"?>
<c:chartSpace
  xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <c:externalData r:id="rIdWorkbook"/>
</c:chartSpace>
"""


def source_document_xml(article_title: str = "Synthetic Exact Title") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
  mc:Ignorable="w14 w15 w16 wp14">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="SourcePara"/></w:pPr><w:r><w:t>UDC 001.1</w:t></w:r></w:p>
    <w:p>
      <w:bookmarkStart w:id="1" w:name="bm1"/>
      <w:r><w:t>Petrenko Ivan</w:t></w:r>
      <w:bookmarkEnd w:id="1"/>
    </w:p>
    <w:p>
      <w:bookmarkStart w:id="1" w:name="bm2"/>
      <w:r><w:rPr><w:rStyle w:val="MissingChar"/></w:rPr><w:t>{article_title}</w:t></w:r>
      <w:bookmarkEnd w:id="1"/>
    </w:p>
    <w:p>
      <w:r>
        <w:drawing>
          <wp:inline>
            <wp:docPr id="1" name="DuplicateDrawing"/>
            <a:graphic><a:graphicData><c:chart r:id="rIdChart"/></a:graphicData></a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:drawing>
          <wp:inline>
            <wp:docPr id="1" name="DuplicateDrawing"/>
            <a:graphic><a:graphicData><a:blip r:embed="rIdImage"/></a:graphicData></a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>
    <w:tbl>
      <w:tblPr><w:tblStyle w:val="MissingTable"/></w:tblPr>
      <w:tr><w:tc><w:p><w:r><w:t>Table cell text</w:t></w:r></w:p></w:tc></w:tr>
    </w:tbl>
    <w:p><w:r><m:oMath><m:r><m:t>x=1</m:t></m:r></m:oMath></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""


def write_docx(path: Path, parts: dict[str, bytes | str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            data = payload.encode("utf-8") if isinstance(payload, str) else payload
            archive.writestr(name, data)


def create_synthetic_etalon(path: Path) -> Path:
    write_docx(
        path,
        {
            "[Content_Types].xml": CONTENT_TYPES,
            "_rels/.rels": ROOT_RELS,
            "word/document.xml": ETALON_DOCUMENT,
            "word/_rels/document.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
            "word/styles.xml": STYLES,
        },
    )
    return path


def create_synthetic_source(path: Path, article_title: str = "Synthetic Exact Title") -> Path:
    write_docx(
        path,
        {
            "[Content_Types].xml": CONTENT_TYPES
            .replace("</Types>", '  <Override PartName="/word/charts/chart1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>\n</Types>'),
            "_rels/.rels": ROOT_RELS,
            "word/document.xml": source_document_xml(article_title),
            "word/_rels/document.xml.rels": SOURCE_DOCUMENT_RELS,
            "word/styles.xml": STYLES + "\n",
            "word/charts/chart1.xml": CHART_XML,
            "word/charts/_rels/chart1.xml.rels": CHART_RELS,
            "word/embeddings/workbook.xlsx": b"synthetic workbook bytes",
            "word/media/image1.png": b"synthetic image bytes",
            "word/media/unused.png": b"must not be copied",
        },
    )
    return path
