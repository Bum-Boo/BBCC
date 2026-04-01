from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainterPath, QPolygonF
from PyQt5.QtSvg import QSvgRenderer


@dataclass(frozen=True)
class DiagramControlSpec:
    control: str
    node_id: str
    hit_path: QPainterPath


@dataclass(frozen=True)
class DiagramAsset:
    diagram_kind: str
    svg_path: Path
    hitmap_path: Path
    renderer: QSvgRenderer
    view_box: QRectF
    controls: Dict[str, DiagramControlSpec]
    control_order: Tuple[str, ...]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _candidate_files(*parts: str) -> Iterable[Path]:
    for root in (_repo_root(), _package_root()):
        yield root.joinpath(*parts)


def _resolve_existing_file(*parts: str) -> Optional[Path]:
    for candidate in _candidate_files(*parts):
        if candidate.exists():
            return candidate
    return None


def _load_json(path: Path) -> Dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _rect_from_value(value) -> Optional[QRectF]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        x, y, width, height = (float(component) for component in value)
    except (TypeError, ValueError):
        return None
    return QRectF(x, y, width, height)


def _view_box_from_value(value) -> QRectF:
    rect = _rect_from_value(value)
    if rect is not None:
        return rect
    return QRectF(0.0, 0.0, 1000.0, 560.0)


def _path_from_shape_spec(spec) -> QPainterPath:
    if not isinstance(spec, dict):
        return QPainterPath()

    shape_type = str(spec.get("type", "")).strip().lower()
    path = QPainterPath()

    if shape_type in {"rect", "rectangle"}:
        rect = _rect_from_value(spec.get("rect"))
        if rect is not None:
            path.addRect(rect)
        return path

    if shape_type in {"roundrect", "roundedrect", "round_rect", "rounded_rect"}:
        rect = _rect_from_value(spec.get("rect"))
        if rect is not None:
            radius = float(spec.get("radius", 10.0))
            path.addRoundedRect(rect, radius, radius)
        return path

    if shape_type in {"ellipse", "circle"}:
        rect = _rect_from_value(spec.get("rect"))
        if rect is not None:
            path.addEllipse(rect)
        return path

    if shape_type == "polygon":
        points = spec.get("points", ())
        polygon = QPolygonF()
        if isinstance(points, (list, tuple)):
            for point in points:
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    continue
                try:
                    polygon.append(QPointF(float(point[0]), float(point[1])))
                except (TypeError, ValueError):
                    continue
        if not polygon.isEmpty():
            path.addPolygon(polygon)
            path.closeSubpath()
        return path

    return path


@lru_cache(maxsize=None)
def load_diagram_asset(diagram_kind: str) -> Optional[DiagramAsset]:
    normalized_kind = (diagram_kind or "").strip().lower()
    if not normalized_kind or normalized_kind in {"unknown", "standard_controller", "unknown_controller"}:
        return None

    svg_path = _resolve_existing_file("assets", "diagrams", "{kind}.svg".format(kind=normalized_kind))
    hitmap_path = _resolve_existing_file("config", "hitmaps", "{kind}_hitmap.json".format(kind=normalized_kind))
    if svg_path is None or hitmap_path is None:
        return None

    renderer = QSvgRenderer(str(svg_path))
    if not renderer.isValid():
        return None

    hitmap_payload = _load_json(hitmap_path)
    view_box = _view_box_from_value(hitmap_payload.get("viewBox"))
    controls_payload = hitmap_payload.get("controls", {})
    if not isinstance(controls_payload, dict):
        return None

    controls: Dict[str, DiagramControlSpec] = {}
    for control, raw_spec in controls_payload.items():
        if not isinstance(raw_spec, dict):
            continue
        node_id = str(raw_spec.get("node", control)).strip()
        if node_id and not renderer.elementExists(node_id):
            continue
        hit_spec = raw_spec.get("hit", {})
        hit_path = _path_from_shape_spec(hit_spec)
        if hit_path.isEmpty() and node_id:
            element_bounds = renderer.boundsOnElement(node_id)
            if not element_bounds.isNull():
                hit_path.addRect(element_bounds)
        if hit_path.isEmpty():
            continue
        controls[str(control)] = DiagramControlSpec(
            control=str(control),
            node_id=node_id or str(control),
            hit_path=hit_path,
        )

    if not controls:
        return None

    return DiagramAsset(
        diagram_kind=normalized_kind,
        svg_path=svg_path,
        hitmap_path=hitmap_path,
        renderer=renderer,
        view_box=view_box,
        controls=controls,
        control_order=tuple(controls.keys()),
    )
