from __future__ import annotations

from dashboard_core.io.excel_reader import match_section_label


SECTIONS = [
    {
        "block_number": 36,
        "section_ua": "Медичні науки та громадське здоров’я",
        "section_en": "Medical Sciences and Public Health",
    },
    {
        "block_number": 39,
        "section_ua": "Історія, археологія та культурологія",
        "section_en": "History, Archaeology and Cultural Studies",
    },
]


def test_match_section_with_modifier_letter_apostrophe() -> None:
    assert match_section_label("36. Медичні науки та громадське здоровʼя", SECTIONS) == (
        36,
        "Медичні науки та громадське здоров’я",
        "Medical Sciences and Public Health",
    )


def test_match_section_with_missing_space_inside_title() -> None:
    assert match_section_label("Історія, археологія такультурологія", SECTIONS) == (
        39,
        "Історія, археологія та культурологія",
        "History, Archaeology and Cultural Studies",
    )


def test_match_section_with_y_conjunction() -> None:
    sections = [
        {
            "block_number": 34,
            "section_ua": "Педагогіка та освіта",
            "section_en": "Pedagogy and Education",
        },
    ]
    assert match_section_label("Педагогіка й освіта", sections) == (
        34,
        "Педагогіка та освіта",
        "Pedagogy and Education",
    )


def test_match_section_with_omitted_conjunction_after_number() -> None:
    sections = [
        {
            "block_number": 39,
            "section_ua": "Історія, археологія та культурологія",
            "section_en": "History, Archaeology and Cultural Studies",
        },
    ]
    assert match_section_label("39. Історія, археологія, культурологія", sections) == (
        39,
        "Історія, археологія та культурологія",
        "History, Archaeology and Cultural Studies",
    )
