from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

from PyQt5.QtGui import QFont, QFontDatabase

from .translations import normalize_language_code

DEFAULT_BASE_FONT_SIZE_PT = 10.5

_LANGUAGE_FONT_FAMILIES = {
    "en": ("Noto Sans", "Noto Sans KR", "Noto Sans JP", "Noto Sans SC"),
    "ko": ("Noto Sans KR", "Noto Sans", "Noto Sans JP", "Noto Sans SC"),
    "ja": ("Noto Sans JP", "Noto Sans", "Noto Sans KR", "Noto Sans SC"),
    "zh": ("Noto Sans SC", "Noto Sans", "Noto Sans KR", "Noto Sans JP"),
}

_WINDOWS_FALLBACK_FAMILIES = ("Segoe UI", "Malgun Gothic", "Arial")
_GENERIC_FALLBACK_FAMILY = "sans-serif"
_BUNDLED_FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".otc"}


def _font_root_candidates() -> Tuple[Path, ...]:
    service_root = Path(__file__).resolve().parents[3]
    package_root = Path(__file__).resolve().parents[1]
    return (
        service_root / "assets" / "fonts",
        package_root / "assets" / "fonts",
    )


def load_application_fonts() -> Tuple[str, ...]:
    loaded_families = []
    seen = set()
    for root in _font_root_candidates():
        if not root.exists():
            continue
        for font_path in sorted(root.rglob("*")):
            if not font_path.is_file() or font_path.suffix.lower() not in _BUNDLED_FONT_EXTENSIONS:
                continue
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id < 0:
                continue
            for family in QFontDatabase.applicationFontFamilies(font_id):
                if family not in seen:
                    loaded_families.append(family)
                    seen.add(family)
    return tuple(loaded_families)


def build_font_family_stack(language: str) -> str:
    language_code = normalize_language_code(language)
    ordered_families = []
    seen = set()

    for family in _LANGUAGE_FONT_FAMILIES.get(language_code, _LANGUAGE_FONT_FAMILIES["en"]):
        if family not in seen:
            ordered_families.append(family)
            seen.add(family)

    for family in _WINDOWS_FALLBACK_FAMILIES:
        if family not in seen:
            ordered_families.append(family)
            seen.add(family)

    ordered_families.append(_GENERIC_FALLBACK_FAMILY)
    return ", ".join(_quote_font_family(family) for family in ordered_families)


def resolve_primary_font_family(language: str, available_families: Iterable[str] | None = None) -> str:
    language_code = normalize_language_code(language)
    available = set(available_families) if available_families is not None else set(QFontDatabase().families())
    ordered_families = (
        *_LANGUAGE_FONT_FAMILIES.get(language_code, _LANGUAGE_FONT_FAMILIES["en"]),
        *_WINDOWS_FALLBACK_FAMILIES,
    )
    for family in ordered_families:
        if family in available:
            return family
    return QFont().family() or _WINDOWS_FALLBACK_FAMILIES[0]


def build_application_font(
    language: str,
    *,
    point_size_f: float = DEFAULT_BASE_FONT_SIZE_PT,
    available_families: Iterable[str] | None = None,
) -> QFont:
    family = resolve_primary_font_family(language, available_families=available_families)
    font = QFont(family)
    font.setPointSizeF(point_size_f)
    return font


def _quote_font_family(family: str) -> str:
    if family == _GENERIC_FALLBACK_FAMILY:
        return family
    return '"{family}"'.format(family=family)
