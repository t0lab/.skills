"""Measurement report for PPTX shapes — the agent's "eyes" for alignment.

Acts as a ruler, not a judge. Emits geometric measurements (bbox, distances
to slide edges, parent-child relations, sibling gaps, roundRect corner
overlaps) so the agent can decide what is a mistake vs. intentional.

No severity, no auto-fix, no expected values. Just numbers.

Usage:
    python measure.py <input>                  # text report, all slides
    python measure.py <input> --json           # JSON for agent parsing
    python measure.py <input> --slide N        # single slide
    python measure.py <input> --shape NAME     # single shape by name or id

<input> may be a .pptx file or an unpacked/ directory.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import defusedxml.minidom as minidom

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

EMU_PER_INCH = 914400
DEFAULT_INSET = {"l": 91440, "t": 45720, "r": 91440, "b": 45720}


@dataclass
class Bbox:
    x: int
    y: int
    cx: int
    cy: int

    @property
    def right(self) -> int:
        return self.x + self.cx

    @property
    def bottom(self) -> int:
        return self.y + self.cy

    @property
    def cen_x(self) -> int:
        return self.x + self.cx // 2

    @property
    def cen_y(self) -> int:
        return self.y + self.cy // 2

    def contains(self, other: "Bbox", tol: int = 0) -> bool:
        return (
            self.x - tol <= other.x
            and self.y - tol <= other.y
            and self.right + tol >= other.right
            and self.bottom + tol >= other.bottom
        )

    def overlaps(self, other: "Bbox") -> bool:
        return not (
            self.right <= other.x
            or other.right <= self.x
            or self.bottom <= other.y
            or other.bottom <= self.y
        )


@dataclass
class TextBody:
    anchor: Optional[str] = None
    anchor_ctr: Optional[str] = None
    inset_l: int = DEFAULT_INSET["l"]
    inset_t: int = DEFAULT_INSET["t"]
    inset_r: int = DEFAULT_INSET["r"]
    inset_b: int = DEFAULT_INSET["b"]
    has_text: bool = False


@dataclass
class Shape:
    id: str
    name: str
    kind: str  # "sp", "pic", "grpSp", "cxnSp"
    z_index: int
    bbox: Bbox
    prst_geom: Optional[str] = None
    roundrect_adj: Optional[int] = None  # thousandths (0-50000 typical)
    text_body: Optional[TextBody] = None
    text_snippet: Optional[str] = None
    group_children: list[str] = field(default_factory=list)
    explicit_parent: Optional[str] = None  # from <p:grpSp>


def emu_to_in(emu: int) -> float:
    return emu / EMU_PER_INCH


def parse_int(s: Optional[str], default: int = 0) -> int:
    if s is None:
        return default
    try:
        return int(s)
    except ValueError:
        return default


def _qn(prefix: str, local: str) -> str:
    ns = NS_P if prefix == "p" else NS_A
    return f"{{{ns}}}{local}"


def _iter_shape_elements(parent, z_offset: int = 0, explicit_parent: Optional[str] = None):
    """Yield (element, z_index, explicit_parent_id) for sp/pic/cxnSp/grpSp, recursing into grpSp."""
    idx = z_offset
    for child in parent:
        tag = child.tagName if hasattr(child, "tagName") else None
        if tag in ("p:sp", "p:pic", "p:cxnSp"):
            yield child, idx, explicit_parent
            idx += 1
        elif tag == "p:grpSp":
            grp_id = _shape_id(child)
            yield child, idx, explicit_parent
            idx += 1
            spTree = child
            yield from _iter_shape_elements(spTree.childNodes, idx, grp_id)


def _shape_id(sp_elem) -> str:
    for nvSpPr in sp_elem.getElementsByTagName("p:nvSpPr"):
        for cNvPr in nvSpPr.getElementsByTagName("p:cNvPr"):
            return cNvPr.getAttribute("id") or ""
    for nvPicPr in sp_elem.getElementsByTagName("p:nvPicPr"):
        for cNvPr in nvPicPr.getElementsByTagName("p:cNvPr"):
            return cNvPr.getAttribute("id") or ""
    for nvGrpSpPr in sp_elem.getElementsByTagName("p:nvGrpSpPr"):
        for cNvPr in nvGrpSpPr.getElementsByTagName("p:cNvPr"):
            return cNvPr.getAttribute("id") or ""
    for nvCxnSpPr in sp_elem.getElementsByTagName("p:nvCxnSpPr"):
        for cNvPr in nvCxnSpPr.getElementsByTagName("p:cNvPr"):
            return cNvPr.getAttribute("id") or ""
    return ""


def _shape_name(sp_elem) -> str:
    for nv in ("p:nvSpPr", "p:nvPicPr", "p:nvGrpSpPr", "p:nvCxnSpPr"):
        for nvElem in sp_elem.getElementsByTagName(nv):
            for cNvPr in nvElem.getElementsByTagName("p:cNvPr"):
                return cNvPr.getAttribute("name") or ""
    return ""


def _first_child(elem, tag_name):
    for c in elem.childNodes:
        if hasattr(c, "tagName") and c.tagName == tag_name:
            return c
    return None


def _xfrm_bbox(sp_elem) -> Optional[Bbox]:
    spPr = _first_child(sp_elem, "p:spPr") or _first_child(sp_elem, "p:grpSpPr")
    if spPr is None:
        return None
    xfrm = _first_child(spPr, "a:xfrm")
    if xfrm is None:
        return None
    off = _first_child(xfrm, "a:off")
    ext = _first_child(xfrm, "a:ext")
    if off is None or ext is None:
        return None
    return Bbox(
        x=parse_int(off.getAttribute("x")),
        y=parse_int(off.getAttribute("y")),
        cx=parse_int(ext.getAttribute("cx")),
        cy=parse_int(ext.getAttribute("cy")),
    )


def _prst_geom(sp_elem) -> tuple[Optional[str], Optional[int]]:
    spPr = _first_child(sp_elem, "p:spPr")
    if spPr is None:
        return None, None
    prst = _first_child(spPr, "a:prstGeom")
    if prst is None:
        return None, None
    prst_name = prst.getAttribute("prst") or None
    adj = None
    avLst = _first_child(prst, "a:avLst")
    if avLst is not None:
        gd = _first_child(avLst, "a:gd")
        if gd is not None:
            fmla = gd.getAttribute("fmla") or ""
            if fmla.startswith("val "):
                adj = parse_int(fmla[4:])
    return prst_name, adj


def _text_body(sp_elem) -> Optional[TextBody]:
    txBody = _first_child(sp_elem, "p:txBody")
    if txBody is None:
        return None
    bodyPr = _first_child(txBody, "a:bodyPr")
    tb = TextBody()
    if bodyPr is not None:
        tb.anchor = bodyPr.getAttribute("anchor") or None
        tb.anchor_ctr = bodyPr.getAttribute("anchorCtr") or None
        tb.inset_l = parse_int(bodyPr.getAttribute("lIns"), DEFAULT_INSET["l"])
        tb.inset_t = parse_int(bodyPr.getAttribute("tIns"), DEFAULT_INSET["t"])
        tb.inset_r = parse_int(bodyPr.getAttribute("rIns"), DEFAULT_INSET["r"])
        tb.inset_b = parse_int(bodyPr.getAttribute("bIns"), DEFAULT_INSET["b"])
    for t in txBody.getElementsByTagName("a:t"):
        if t.firstChild and t.firstChild.nodeValue and t.firstChild.nodeValue.strip():
            tb.has_text = True
            break
    return tb


def _text_snippet(sp_elem, max_len: int = 32) -> Optional[str]:
    txBody = _first_child(sp_elem, "p:txBody")
    if txBody is None:
        return None
    parts: list[str] = []
    for t in txBody.getElementsByTagName("a:t"):
        if t.firstChild and t.firstChild.nodeValue:
            parts.append(t.firstChild.nodeValue)
    if not parts:
        return None
    s = " ".join("".join(parts).split())
    if not s:
        return None
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def _flatten_shapes(spTree) -> list[Shape]:
    shapes: list[Shape] = []
    for elem, z, parent_id in _walk(spTree, 0, None):
        bbox = _xfrm_bbox(elem)
        if bbox is None:
            continue
        tag = elem.tagName.split(":")[1]
        sid = _shape_id(elem)
        name = _shape_name(elem)
        prst, adj = (_prst_geom(elem) if tag == "sp" else (None, None))
        tb = _text_body(elem) if tag in ("sp", "cxnSp") else None
        snippet = _text_snippet(elem) if tag in ("sp", "cxnSp") else None
        children_ids: list[str] = []
        if tag == "grpSp":
            for sub in elem.childNodes:
                if hasattr(sub, "tagName") and sub.tagName in (
                    "p:sp",
                    "p:pic",
                    "p:cxnSp",
                    "p:grpSp",
                ):
                    cid = _shape_id(sub)
                    if cid:
                        children_ids.append(cid)
        shapes.append(
            Shape(
                id=sid,
                name=name,
                kind=tag,
                z_index=z,
                bbox=bbox,
                prst_geom=prst,
                roundrect_adj=adj,
                text_body=tb,
                text_snippet=snippet,
                group_children=children_ids,
                explicit_parent=parent_id,
            )
        )
    return shapes


def _walk(parent, z, explicit_parent):
    idx = z
    for child in parent.childNodes:
        if not hasattr(child, "tagName"):
            continue
        tag = child.tagName
        if tag in ("p:sp", "p:pic", "p:cxnSp"):
            yield child, idx, explicit_parent
            idx += 1
        elif tag == "p:grpSp":
            gid = _shape_id(child)
            yield child, idx, explicit_parent
            idx += 1
            yield from _walk(child, idx, gid)


def _read_slide_size(root_dir: Path) -> Bbox:
    pres = root_dir / "ppt" / "presentation.xml"
    if not pres.exists():
        return Bbox(0, 0, 9144000, 6858000)
    dom = minidom.parseString(pres.read_text(encoding="utf-8"))
    for sldSz in dom.getElementsByTagName("p:sldSz"):
        return Bbox(
            0,
            0,
            parse_int(sldSz.getAttribute("cx"), 9144000),
            parse_int(sldSz.getAttribute("cy"), 6858000),
        )
    return Bbox(0, 0, 9144000, 6858000)


def _slide_files(root_dir: Path) -> list[Path]:
    slide_dir = root_dir / "ppt" / "slides"
    if not slide_dir.exists():
        return []
    return sorted(
        [p for p in slide_dir.glob("slide*.xml")],
        key=lambda p: int("".join(c for c in p.stem if c.isdigit()) or "0"),
    )


def load_shapes_from_dir(root_dir: Path) -> tuple[Bbox, dict[int, list[Shape]]]:
    slide_size = _read_slide_size(root_dir)
    result: dict[int, list[Shape]] = {}
    for path in _slide_files(root_dir):
        num = int("".join(c for c in path.stem if c.isdigit()) or "0")
        dom = minidom.parseString(path.read_text(encoding="utf-8"))
        spTree = None
        for st in dom.getElementsByTagName("p:spTree"):
            spTree = st
            break
        if spTree is None:
            result[num] = []
            continue
        result[num] = _flatten_shapes(spTree)
    return slide_size, result


def load_shapes(input_path: Path) -> tuple[Bbox, dict[int, list[Shape]]]:
    if input_path.is_dir():
        return load_shapes_from_dir(input_path)
    if input_path.suffix.lower() == ".pptx":
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(input_path, "r") as zf:
                zf.extractall(td)
            return load_shapes_from_dir(Path(td))
    raise ValueError(f"Unsupported input: {input_path}")


# ---------- measurement computations ----------


def _infer_parent(shape: Shape, all_shapes: list[Shape], tol: int = 45720) -> Optional[Shape]:
    if shape.explicit_parent:
        for s in all_shapes:
            if s.id == shape.explicit_parent:
                return s
    candidates = [
        s
        for s in all_shapes
        if s.id != shape.id
        and s.bbox.contains(shape.bbox, tol=tol)
        and s.z_index < shape.z_index
        and s.kind != "grpSp"
    ]
    if not candidates:
        return None
    # pick tightest (smallest area) container
    return min(candidates, key=lambda s: s.bbox.cx * s.bbox.cy)


def _corner_radius_emu(shape: Shape) -> Optional[int]:
    if shape.prst_geom != "roundRect" or shape.roundrect_adj is None:
        return None
    # adj is in thousandths (0-50000), multiplier against min(cx,cy)/2
    return int(shape.roundrect_adj * min(shape.bbox.cx, shape.bbox.cy) / 100000)


def _child_in_corner_region(parent: Shape, child: Shape) -> Optional[dict]:
    """If parent is roundRect, measure how much the child bbox intrudes into
    the four rounded-corner squares. Return None if parent is not roundRect.
    """
    r = _corner_radius_emu(parent)
    if r is None or r == 0:
        return None
    p = parent.bbox
    c = child.bbox
    # corner squares are r×r at each corner of parent
    def overlap_rect(ax, ay, aw, ah, bx, by, bw, bh):
        ox = max(0, min(ax + aw, bx + bw) - max(ax, bx))
        oy = max(0, min(ay + ah, by + bh) - max(ay, by))
        return ox * oy, ox, oy

    corners = {
        "tl": (p.x, p.y, r, r),
        "tr": (p.x + p.cx - r, p.y, r, r),
        "bl": (p.x, p.y + p.cy - r, r, r),
        "br": (p.x + p.cx - r, p.y + p.cy - r, r, r),
    }
    out = {}
    any_overlap = False
    for name, (cx, cy, cw, ch) in corners.items():
        area, ox, oy = overlap_rect(cx, cy, cw, ch, c.x, c.y, c.cx, c.cy)
        out[name] = {"overlap_area_emu2": area, "overlap_x_emu": ox, "overlap_y_emu": oy}
        if area > 0:
            any_overlap = True
    out["any_corner_overlap"] = any_overlap
    out["parent_corner_radius_emu"] = r
    return out


def _concentric_outer(shape: Shape, all_shapes: list[Shape], tol: int = 45720) -> Optional[Shape]:
    """Find a shape strictly enclosing `shape`, sharing (approx) the same center,
    with lower z-index. Used to detect "border outer" relationships.
    """
    cands = []
    for s in all_shapes:
        if s.id == shape.id or s.kind == "grpSp":
            continue
        if s.bbox.cx <= shape.bbox.cx or s.bbox.cy <= shape.bbox.cy:
            continue
        if abs(s.bbox.cen_x - shape.bbox.cen_x) > tol:
            continue
        if abs(s.bbox.cen_y - shape.bbox.cen_y) > tol:
            continue
        if s.z_index >= shape.z_index:
            continue
        cands.append(s)
    if not cands:
        return None
    return min(cands, key=lambda s: s.bbox.cx * s.bbox.cy)


def _edge_alignments(a: Bbox, b: Bbox) -> dict:
    return {
        "left_to_left": b.x - a.x,
        "right_to_right": b.right - a.right,
        "top_to_top": b.y - a.y,
        "bottom_to_bottom": b.bottom - a.bottom,
        "center_x_to_center_x": b.cen_x - a.cen_x,
        "center_y_to_center_y": b.cen_y - a.cen_y,
        "left_to_right": b.x - a.right,
        "right_to_left": b.right - a.x,
        "top_to_bottom": b.y - a.bottom,
        "bottom_to_top": b.bottom - a.y,
    }


def _gap(a: Bbox, b: Bbox) -> dict:
    # horizontal gap (positive = separated horizontally)
    if b.x >= a.right:
        h = b.x - a.right
    elif a.x >= b.right:
        h = a.x - b.right
    else:
        h = -min(a.right, b.right) + max(a.x, b.x)  # negative overlap
    if b.y >= a.bottom:
        v = b.y - a.bottom
    elif a.y >= b.bottom:
        v = a.y - b.bottom
    else:
        v = -min(a.bottom, b.bottom) + max(a.y, b.y)
    return {"horizontal_emu": h, "vertical_emu": v}


def measure_slide(
    slide_num: int, shapes: list[Shape], slide_size: Bbox
) -> dict:
    shape_by_id = {s.id: s for s in shapes}
    parent_of: dict[str, Optional[Shape]] = {s.id: _infer_parent(s, shapes) for s in shapes}
    children_of: dict[str, list[Shape]] = {s.id: [] for s in shapes}
    for s in shapes:
        p = parent_of[s.id]
        if p is not None:
            children_of[p.id].append(s)

    out_shapes = []
    for s in shapes:
        if s.kind == "grpSp":
            # skip group containers themselves; their children already surface
            continue
        parent = parent_of[s.id]
        siblings = [
            o
            for o in shapes
            if o.id != s.id
            and o.kind != "grpSp"
            and parent_of[o.id] is parent
            and not s.bbox.overlaps(o.bbox)
        ]
        # sibling distances — cap to 10 nearest by centroid distance
        def centroid_dist(o: Shape) -> int:
            return abs(o.bbox.cen_x - s.bbox.cen_x) + abs(o.bbox.cen_y - s.bbox.cen_y)

        siblings_sorted = sorted(siblings, key=centroid_dist)[:10]

        entry = {
            "id": s.id,
            "name": s.name,
            "kind": s.kind,
            "z_index": s.z_index,
            "prst_geom": s.prst_geom,
            "roundrect_adj": s.roundrect_adj,
            "roundrect_corner_radius_emu": _corner_radius_emu(s),
            "bbox": {"x": s.bbox.x, "y": s.bbox.y, "cx": s.bbox.cx, "cy": s.bbox.cy},
            "center": {"x": s.bbox.cen_x, "y": s.bbox.cen_y},
            "text_body": (
                {
                    "anchor": s.text_body.anchor,
                    "anchor_ctr": s.text_body.anchor_ctr,
                    "inset": {
                        "l": s.text_body.inset_l,
                        "t": s.text_body.inset_t,
                        "r": s.text_body.inset_r,
                        "b": s.text_body.inset_b,
                    },
                    "has_text": s.text_body.has_text,
                }
                if s.text_body
                else None
            ),
            "distances_to_slide_edges_emu": {
                "left": s.bbox.x - slide_size.x,
                "right": slide_size.right - s.bbox.right,
                "top": s.bbox.y - slide_size.y,
                "bottom": slide_size.bottom - s.bbox.bottom,
            },
            "distance_to_slide_center_emu": {
                "dx": s.bbox.cen_x - slide_size.cen_x,
                "dy": s.bbox.cen_y - slide_size.cen_y,
            },
            "parent": (
                {
                    "id": parent.id,
                    "name": parent.name,
                    "explicit": s.explicit_parent is not None,
                    "inferred_via": "grpSp" if s.explicit_parent else "bbox_containment",
                }
                if parent
                else None
            ),
            "children": [
                {
                    "id": c.id,
                    "name": c.name,
                    "kind": c.kind,
                    "text_snippet": c.text_snippet,
                }
                for c in children_of[s.id]
            ],
            "text_snippet": s.text_snippet,
        }

        kids = children_of[s.id]
        if kids:
            p = s.bbox
            ins = s.text_body
            pad_l = ins.inset_l if ins else 0
            pad_t = ins.inset_t if ins else 0
            pad_r = ins.inset_r if ins else 0
            pad_b = ins.inset_b if ins else 0
            inner_cx = p.x + pad_l + (p.cx - pad_l - pad_r) // 2
            inner_cy = p.y + pad_t + (p.cy - pad_t - pad_b) // 2
            kid_entries = []
            for c in kids:
                kid_entries.append(
                    {
                        "id": c.id,
                        "name": c.name,
                        "text_snippet": c.text_snippet,
                        "bbox": {"x": c.bbox.x, "y": c.bbox.y, "cx": c.bbox.cx, "cy": c.bbox.cy},
                        "center": {"x": c.bbox.cen_x, "y": c.bbox.cen_y},
                        "padding_aware_center_delta_emu": {
                            "dx": c.bbox.cen_x - inner_cx,
                            "dy": c.bbox.cen_y - inner_cy,
                        },
                    }
                )
            # pairwise alignment suggestions: children whose centers are close on
            # one axis (likely "meant to share a row/column") but not zero.
            row_pairs = []
            col_pairs = []
            ROW_THRESH = 914400  # 1 inch — siblings within this vertical band treated as candidate row-mates
            COL_THRESH = 914400
            for i in range(len(kids)):
                for j in range(i + 1, len(kids)):
                    a, b = kids[i], kids[j]
                    dcy = b.bbox.cen_y - a.bbox.cen_y
                    dcx = b.bbox.cen_x - a.bbox.cen_x
                    # candidate row-mates: horizontally separated, small vertical center delta
                    if abs(dcy) < ROW_THRESH and (b.bbox.x >= a.bbox.right or a.bbox.x >= b.bbox.right):
                        row_pairs.append(
                            {
                                "a_id": a.id,
                                "a_name": a.name,
                                "a_snippet": a.text_snippet,
                                "b_id": b.id,
                                "b_name": b.name,
                                "b_snippet": b.text_snippet,
                                "cY_delta_emu": dcy,
                            }
                        )
                    if abs(dcx) < COL_THRESH and (b.bbox.y >= a.bbox.bottom or a.bbox.y >= b.bbox.bottom):
                        col_pairs.append(
                            {
                                "a_id": a.id,
                                "a_name": a.name,
                                "a_snippet": a.text_snippet,
                                "b_id": b.id,
                                "b_name": b.name,
                                "b_snippet": b.text_snippet,
                                "cX_delta_emu": dcx,
                            }
                        )
            entry["children_alignment"] = {
                "inner_center_emu": {"x": inner_cx, "y": inner_cy},
                "children": kid_entries,
                "candidate_row_pairs": row_pairs,
                "candidate_column_pairs": col_pairs,
            }

        if parent is not None:
            p = parent.bbox
            ins = parent.text_body
            pad_l = ins.inset_l if ins else 0
            pad_t = ins.inset_t if ins else 0
            pad_r = ins.inset_r if ins else 0
            pad_b = ins.inset_b if ins else 0
            inner_x = p.x + pad_l
            inner_y = p.y + pad_t
            inner_cx = p.cx - pad_l - pad_r
            inner_cy = p.cy - pad_t - pad_b
            entry["parent_measurements"] = {
                "offset_from_parent_origin_emu": {
                    "x": s.bbox.x - p.x,
                    "y": s.bbox.y - p.y,
                },
                "gap_to_parent_edges_emu": {
                    "left": s.bbox.x - p.x,
                    "right": p.right - s.bbox.right,
                    "top": s.bbox.y - p.y,
                    "bottom": p.bottom - s.bbox.bottom,
                },
                "center_delta_from_parent_center_emu": {
                    "dx": s.bbox.cen_x - p.cen_x,
                    "dy": s.bbox.cen_y - p.cen_y,
                },
                "padding_aware_center_delta_emu": {
                    "dx": s.bbox.cen_x - (inner_x + inner_cx // 2),
                    "dy": s.bbox.cen_y - (inner_y + inner_cy // 2),
                },
                "parent_has_inset": ins is not None,
            }
            corner = _child_in_corner_region(parent, s)
            if corner is not None:
                entry["parent_roundrect_corners"] = corner

        outer = _concentric_outer(s, shapes)
        if outer is not None:
            outer_r = _corner_radius_emu(outer)
            inner_r = _corner_radius_emu(s)
            pad_cx = (outer.bbox.cx - s.bbox.cx) // 2
            pad_cy = (outer.bbox.cy - s.bbox.cy) // 2
            ideal_outer_r = (inner_r + min(pad_cx, pad_cy)) if inner_r is not None else None
            entry["concentric_outer"] = {
                "outer_id": outer.id,
                "outer_name": outer.name,
                "outer_prst": outer.prst_geom,
                "outer_adj": outer.roundrect_adj,
                "outer_corner_radius_emu": outer_r,
                "inner_corner_radius_emu": inner_r,
                "padding_per_side_emu": {"x": pad_cx, "y": pad_cy},
                "ideal_outer_corner_radius_for_enclosure_emu": ideal_outer_r,
            }

        entry["siblings"] = [
            {
                "id": o.id,
                "name": o.name,
                "text_snippet": o.text_snippet,
                "gap_emu": _gap(s.bbox, o.bbox),
                "edge_alignments_emu": _edge_alignments(s.bbox, o.bbox),
                "size_delta_emu": {
                    "cx": o.bbox.cx - s.bbox.cx,
                    "cy": o.bbox.cy - s.bbox.cy,
                },
            }
            for o in siblings_sorted
        ]

        out_shapes.append(entry)

    return {
        "slide": slide_num,
        "slide_size_emu": {"cx": slide_size.cx, "cy": slide_size.cy},
        "shape_count": len(out_shapes),
        "shapes": out_shapes,
    }


# ---------- text rendering ----------


def _fmt_emu(v: Optional[int]) -> str:
    if v is None:
        return "n/a"
    return f"{v:+d} EMU ({emu_to_in(v):+.4f} in)" if v else "0"


def render_text(report: list[dict]) -> str:
    lines: list[str] = []
    for slide in report:
        lines.append(f"=== Slide {slide['slide']} ({slide['shape_count']} shapes) ===")
        lines.append(
            f"  slide size: {slide['slide_size_emu']['cx']} x {slide['slide_size_emu']['cy']} EMU"
        )
        for sh in slide["shapes"]:
            lines.append("")
            snip = sh.get("text_snippet")
            lines.append(
                f"  [{sh['id']}] {sh['name']!r}"
                + (f" {snip!r}" if snip else "")
                + f" ({sh['kind']}, z={sh['z_index']}"
                + (f", geom={sh['prst_geom']}" if sh["prst_geom"] else "")
                + (f", adj={sh['roundrect_adj']}" if sh["roundrect_adj"] is not None else "")
                + ")"
            )
            b = sh["bbox"]
            lines.append(
                f"    bbox: x={b['x']} y={b['y']} cx={b['cx']} cy={b['cy']}"
                f" | center=({sh['center']['x']}, {sh['center']['y']})"
            )
            if sh["text_body"]:
                tb = sh["text_body"]
                lines.append(
                    f"    text_body: anchor={tb['anchor']!r} anchorCtr={tb['anchor_ctr']!r}"
                    f" inset=L{tb['inset']['l']}/T{tb['inset']['t']}/R{tb['inset']['r']}/B{tb['inset']['b']}"
                    f" has_text={tb['has_text']}"
                )
            se = sh["distances_to_slide_edges_emu"]
            sc = sh["distance_to_slide_center_emu"]
            lines.append(
                f"    slide edges: L={se['left']} R={se['right']} T={se['top']} B={se['bottom']}"
                f" | center_delta: dx={sc['dx']} dy={sc['dy']}"
            )
            if sh.get("parent"):
                p = sh["parent"]
                pm = sh["parent_measurements"]
                lines.append(
                    f"    parent: [{p['id']}] {p['name']!r} (via {p['inferred_via']})"
                )
                lines.append(
                    f"      gap_to_parent_edges: L={pm['gap_to_parent_edges_emu']['left']}"
                    f" R={pm['gap_to_parent_edges_emu']['right']}"
                    f" T={pm['gap_to_parent_edges_emu']['top']}"
                    f" B={pm['gap_to_parent_edges_emu']['bottom']}"
                )
                lines.append(
                    f"      center_delta: dx={pm['center_delta_from_parent_center_emu']['dx']}"
                    f" dy={pm['center_delta_from_parent_center_emu']['dy']}"
                    f" | padding_aware: dx={pm['padding_aware_center_delta_emu']['dx']}"
                    f" dy={pm['padding_aware_center_delta_emu']['dy']}"
                )
                if "parent_roundrect_corners" in sh:
                    rc = sh["parent_roundrect_corners"]
                    lines.append(
                        f"      parent roundRect radius={rc['parent_corner_radius_emu']} EMU"
                        f" any_corner_overlap={rc['any_corner_overlap']}"
                    )
                    for k in ("tl", "tr", "bl", "br"):
                        if rc[k]["overlap_area_emu2"] > 0:
                            lines.append(
                                f"        corner {k}: ox={rc[k]['overlap_x_emu']}"
                                f" oy={rc[k]['overlap_y_emu']}"
                            )
            if sh.get("concentric_outer"):
                co = sh["concentric_outer"]
                lines.append(
                    f"    concentric_outer: [{co['outer_id']}] {co['outer_name']!r}"
                    f" outer_r={co['outer_corner_radius_emu']} inner_r={co['inner_corner_radius_emu']}"
                    f" ideal_outer_r={co['ideal_outer_corner_radius_for_enclosure_emu']}"
                    f" pad=(x={co['padding_per_side_emu']['x']}, y={co['padding_per_side_emu']['y']})"
                )
            if sh["children"]:
                lines.append(
                    f"    children: "
                    + ", ".join(
                        f"[{c['id']}] {c['name']!r}"
                        + (f" {c['text_snippet']!r}" if c.get("text_snippet") else "")
                        for c in sh["children"]
                    )
                )
            if sh.get("children_alignment"):
                ca = sh["children_alignment"]
                lines.append(
                    f"    children_alignment (inner_center=({ca['inner_center_emu']['x']},{ca['inner_center_emu']['y']})):"
                )
                for c in ca["children"]:
                    label = c.get("text_snippet") or c["name"]
                    pad = c["padding_aware_center_delta_emu"]
                    lines.append(
                        f"      [{c['id']}] {label!r} center=({c['center']['x']},{c['center']['y']})"
                        f" padding_aware=(dx={pad['dx']},dy={pad['dy']})"
                    )
                if ca["candidate_row_pairs"]:
                    lines.append(f"      candidate_row_pairs (same row? cY should be 0):")
                    for pr in ca["candidate_row_pairs"]:
                        la = pr.get("a_snippet") or pr["a_name"]
                        lb = pr.get("b_snippet") or pr["b_name"]
                        lines.append(
                            f"        [{pr['a_id']}] {la!r} <-> [{pr['b_id']}] {lb!r}"
                            f" cY_delta={pr['cY_delta_emu']}"
                        )
                if ca["candidate_column_pairs"]:
                    lines.append(f"      candidate_column_pairs (same column? cX should be 0):")
                    for pr in ca["candidate_column_pairs"]:
                        la = pr.get("a_snippet") or pr["a_name"]
                        lb = pr.get("b_snippet") or pr["b_name"]
                        lines.append(
                            f"        [{pr['a_id']}] {la!r} <-> [{pr['b_id']}] {lb!r}"
                            f" cX_delta={pr['cX_delta_emu']}"
                        )
            if sh["siblings"]:
                lines.append(f"    siblings ({len(sh['siblings'])} nearest):")
                for sib in sh["siblings"]:
                    g = sib["gap_emu"]
                    ea = sib["edge_alignments_emu"]
                    sd = sib["size_delta_emu"]
                    sib_snip = sib.get("text_snippet")
                    lines.append(
                        f"      [{sib['id']}] {sib['name']!r}"
                        + (f" {sib_snip!r}" if sib_snip else "")
                        + f" gap(h={g['horizontal_emu']},v={g['vertical_emu']})"
                        + f" edges(L-L={ea['left_to_left']},R-R={ea['right_to_right']},"
                        f"T-T={ea['top_to_top']},B-B={ea['bottom_to_bottom']},"
                        f"cX={ea['center_x_to_center_x']},cY={ea['center_y_to_center_y']})"
                        f" size_delta(cx={sd['cx']},cy={sd['cy']})"
                    )
    return "\n".join(lines)


# ---------- cli ----------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help=".pptx file or unpacked/ directory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--slide", type=int, default=None, help="only this slide number")
    parser.add_argument("--shape", default=None, help="only this shape (id or name)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {args.input} does not exist", file=sys.stderr)
        return 2

    try:
        slide_size, per_slide = load_shapes(input_path)
    except Exception as e:
        print(f"Error parsing input: {e}", file=sys.stderr)
        return 2

    report: list[dict] = []
    for num in sorted(per_slide.keys()):
        if args.slide is not None and num != args.slide:
            continue
        slide_report = measure_slide(num, per_slide[num], slide_size)
        if args.shape:
            slide_report["shapes"] = [
                s
                for s in slide_report["shapes"]
                if s["id"] == args.shape or s["name"] == args.shape
            ]
            slide_report["shape_count"] = len(slide_report["shapes"])
        report.append(slide_report)

    if args.json:
        print(json.dumps({"input": str(input_path), "slides": report}, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
