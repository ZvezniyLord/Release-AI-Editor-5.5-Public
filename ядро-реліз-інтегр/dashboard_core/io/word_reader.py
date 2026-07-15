from __future__ import annotations

import zipfile
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def _has_page_break(paragraph: Paragraph) -> bool:
    return bool(paragraph._p.xpath(".//w:br[@w:type='page'] | .//w:lastRenderedPageBreak"))


def collect_first_page_text(path: Path, chunk_limit: int = 150) -> tuple[str, list[str]]:
    document = Document(path)
    chunks: list[str] = [path.stem]

    for element in document.element.body.iterchildren():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "p":
            paragraph = Paragraph(element, document)
            text = paragraph.text.strip()
            if text:
                chunks.append(text)
            if _has_page_break(paragraph):
                break
        elif tag == "tbl":
            table = Table(element, document)
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        text = paragraph.text.strip()
                        if text:
                            chunks.append(text)
        elif tag == "sectPr":
            break

        if len(chunks) >= chunk_limit:
            break

    preview = "\n".join(chunks[1:]).strip()
    return preview, chunks


class WordPageCounter:
    def __init__(self) -> None:
        self._pythoncom = None
        self._word = None
        self._initialized = False
        self._available = True

    def close(self) -> None:
        if self._word is not None:
            try:
                self._word.Quit()
            except Exception:
                pass
            self._word = None
        if self._initialized and self._pythoncom is not None:
            try:
                self._pythoncom.CoUninitialize()
            except Exception:
                pass
        self._initialized = False

    def _ensure_word(self) -> bool:
        if not self._available:
            return False
        if self._word is not None:
            return True
        try:
            import pythoncom
            import win32com.client
        except Exception:
            self._available = False
            return False
        try:
            pythoncom.CoInitialize()
            self._pythoncom = pythoncom
            self._initialized = True
            self._word = win32com.client.DispatchEx("Word.Application")
            self._word.Visible = False
            self._word.DisplayAlerts = 0
            return True
        except Exception:
            self._available = False
            self.close()
            return False

    def count(self, path: Path) -> int | None:
        if not self._ensure_word():
            return None
        document = None
        try:
            document = self._word.Documents.Open(str(path), ReadOnly=True, AddToRecentFiles=False)
            try:
                document.Repaginate()
            except Exception:
                pass
            return int(document.ComputeStatistics(2))
        except Exception:
            return None
        finally:
            if document is not None:
                document.Close(False)

    def __enter__(self) -> "WordPageCounter":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()


def count_word_pages(path: Path) -> int | None:
    with WordPageCounter() as counter:
        return counter.count(path)


def count_package_objects(path: Path) -> tuple[int, int, list[str], list[str]]:
    media_files = 0
    embedding_files = 0
    media_names: list[str] = []
    embedding_names: list[str] = []
    try:
        with zipfile.ZipFile(path, "r") as archive:
            for name in archive.namelist():
                if name.startswith("word/media/") and not name.endswith("/"):
                    media_files += 1
                    media_names.append(name)
                if name.startswith("word/embeddings/") and not name.endswith("/"):
                    embedding_files += 1
                    embedding_names.append(name)
    except zipfile.BadZipFile:
        pass
    return media_files, embedding_files, media_names, embedding_names
