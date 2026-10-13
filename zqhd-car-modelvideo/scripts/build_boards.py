#!/usr/bin/env python3
"""只读图片与人工核验清单，生成自包含 SVG 汽车参考看板。"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import html
import io
import json
import math
from pathlib import Path
import re
import struct
import sys
import tempfile
import unicodedata
import zlib

try:
    from PIL import Image
except ImportError:
    Image = None


VIEW_LABELS = {
    "F": "正前", "B": "正后", "L": "左侧", "R": "右侧",
    "FL45": "左前 45°", "FR45": "右前 45°",
    "RL45": "左后 45°", "RR45": "右后 45°",
}
SIDES = {"left", "right", "front", "rear", "roof", "bilateral", "unknown"}
SIDE_LABELS = {
    "left": "车身左侧", "right": "车身右侧", "front": "车头",
    "rear": "车尾", "roof": "车顶", "bilateral": "两侧分别核验", "unknown": "侧别未确认",
}
MIMES = {"JPEG": "image/jpeg", "MPO": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
FONT = "PingFang SC,Noto Sans CJK SC,Microsoft YaHei,sans-serif"


class ManifestError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def string(value, location: str, default: str = "") -> str:
    if value is None:
        return default
    require(isinstance(value, str), f"{location} 必须是字符串")
    require(all(ord(char) >= 32 or char in "\n\t" for char in value), f"{location} 包含控制字符")
    return value


def item_id(value, location: str) -> str:
    value = string(value, location)
    require(bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value)), f"{location} 只能含英文字母、数字、短横线与下划线，长度 1–64")
    return value


def array(value, location: str) -> list:
    require(isinstance(value, list), f"{location} 必须是数组")
    return value


def object_value(value, location: str) -> dict:
    require(isinstance(value, dict), f"{location} 必须是对象")
    return value


def unique_ids(items: list, location: str) -> None:
    seen = set()
    for index, item in enumerate(items):
        object_value(item, f"{location}[{index}]")
        ident = item_id(item.get("id"), f"{location}[{index}].id")
        require(ident not in seen, f"{location} 有重复 id：{ident}")
        seen.add(ident)


def local_path(value, manifest_dir: Path, location: str) -> Path:
    value = string(value, location)
    require(bool(value.strip()), f"{location} 缺少路径")
    require(not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value), f"{location} 只允许本地文件路径")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = manifest_dir / path
    path = path.resolve()
    require(path.is_file(), f"{location} 文件不存在或不是普通文件：{path}")
    return path


def reset_tiff_orientation(payload: bytearray, start: int, end: int) -> bool:
    """仅把嵌入副本的 TIFF 方向标签改成 1；不接触压缩像素数据。"""
    if end - start < 8:
        return False
    order = bytes(payload[start:start + 2])
    if order not in (b"II", b"MM"):
        return False
    endian = "<" if order == b"II" else ">"
    if struct.unpack_from(endian + "H", payload, start + 2)[0] != 42:
        return False
    offset = struct.unpack_from(endian + "I", payload, start + 4)[0]
    table = start + offset
    if table < start + 8 or table + 2 > end:
        return False
    count = struct.unpack_from(endian + "H", payload, table)[0]
    if table + 2 + count * 12 > end:
        return False
    for index in range(count):
        entry = table + 2 + index * 12
        tag, kind, length = struct.unpack_from(endian + "HHI", payload, entry)
        if tag == 274 and kind == 3 and length == 1:
            payload[entry + 8:entry + 10] = struct.pack(endian + "H", 1)
            return True
    return False


def normalize_embedded_orientation(raw: bytes, format_name: str, orientation: int) -> tuple[bytes, bool]:
    if orientation == 1:
        return raw, False
    data = bytearray(raw)
    changed = False
    if format_name == "JPEG":
        position = 2
        while position + 4 <= len(data):
            if data[position] != 255:
                break
            while position < len(data) and data[position] == 255:
                position += 1
            if position >= len(data):
                break
            marker = data[position]
            position += 1
            if marker in (0xDA, 0xD9):
                break
            if marker == 0x01 or 0xD0 <= marker <= 0xD7:
                continue
            if position + 2 > len(data):
                break
            length = struct.unpack_from(">H", data, position)[0]
            end = position + length
            if length < 2 or end > len(data):
                break
            start = position + 2
            if marker == 0xE1 and bytes(data[start:start + 6]) == b"Exif\x00\x00":
                changed = reset_tiff_orientation(data, start + 6, end) or changed
            position = end
    elif format_name == "PNG":
        position = 8
        while position + 12 <= len(data):
            length = struct.unpack_from(">I", data, position)[0]
            end = position + 12 + length
            if end > len(data):
                break
            if bytes(data[position + 4:position + 8]) == b"eXIf":
                did_change = reset_tiff_orientation(data, position + 8, position + 8 + length)
                if did_change:
                    checksum = zlib.crc32(data[position + 4:position + 8 + length]) & 0xFFFFFFFF
                    data[position + 8 + length:end] = struct.pack(">I", checksum)
                    changed = True
            position = end
    elif format_name == "WEBP":
        position = 12
        while position + 8 <= len(data):
            length = struct.unpack_from("<I", data, position + 4)[0]
            start, end = position + 8, position + 8 + length
            if end > len(data):
                break
            if bytes(data[position:position + 4]) == b"EXIF":
                if bytes(data[start:start + 6]) == b"Exif\x00\x00":
                    start += 6
                changed = reset_tiff_orientation(data, start, end) or changed
            position = end + length % 2
    require(changed, "图片带非标准 EXIF 方向，无法在不重写像素的情况下处理；请提供正常方向的导出图")
    return bytes(data), True


@dataclass
class Picture:
    path: Path
    raw_width: int
    raw_height: int
    orientation: int
    mime: str
    sha256: str
    data: bytes
    metadata_normalized: bool
    source_format: str

    @property
    def width(self) -> int:
        return self.raw_height if self.orientation >= 5 else self.raw_width

    @property
    def height(self) -> int:
        return self.raw_width if self.orientation >= 5 else self.raw_height

    def record(self) -> dict:
        return {
            "path": str(self.path), "sha256": self.sha256, "mime": self.mime,
            "raw_size": [self.raw_width, self.raw_height], "display_size": [self.width, self.height],
            "exif_orientation": self.orientation,
            "embedded_orientation_metadata_normalized": self.metadata_normalized,
            "pixel_data_reencoded": False,
            "source_format": self.source_format,
            "display_mode": "primary-display" if self.source_format == "MPO" else "single-image",
            "hdr_note": "MPO 以 JPEG 主图供显示；辅助图与 HDR 增益保真未核验，浏览器色调映射可能不同" if self.source_format == "MPO" else "未进行色彩或 HDR 像素保真检测",
        }


def read_picture(path: Path, cache: dict[Path, Picture]) -> Picture:
    if path in cache:
        return cache[path]
    require(Image is not None, "缺少 Pillow；请在可用的 Python 环境安装 Pillow 后运行。Pillow 只用于读取尺寸与 EXIF")
    raw = path.read_bytes()
    try:
        with Image.open(io.BytesIO(raw)) as picture:
            format_name = picture.format
            require(format_name in MIMES, f"只接受 PNG、JPEG（含 MPO 主 JPEG）、WebP：{path}")
            require(format_name == "MPO" or getattr(picture, "n_frames", 1) == 1, f"不接受动画或普通多帧图片：{path}")
            # 苹果照片库的 HDR JPEG 可能由 Pillow 识别为 MPO；仅取主图尺寸和 EXIF。
            if format_name == "MPO":
                picture.seek(0)
            width, height = picture.size
            orientation = picture.getexif().get(274, 1)
            require(type(orientation) is int and 1 <= orientation <= 8, f"无效 EXIF 方向：{path}")
            require(width > 0 and height > 0, f"图片尺寸无效：{path}")
    except ManifestError:
        raise
    except Exception as exc:
        raise ManifestError(f"无法读取图片尺寸或 EXIF：{path}（{exc}）") from exc
    embedded, normalized = normalize_embedded_orientation(raw, "JPEG" if format_name == "MPO" else format_name, orientation)
    result = Picture(path, width, height, orientation, MIMES[format_name], hashlib.sha256(raw).hexdigest(), embedded, normalized, format_name)
    cache[path] = result
    return result


def load_manifest(manifest_path: Path) -> tuple[dict, dict[Path, Picture]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"无法读取 JSON manifest：{exc}") from exc
    object_value(manifest, "manifest")
    vehicle = object_value(manifest.get("vehicle", {}), "vehicle")
    for key in ("name", "body_color", "note"):
        vehicle[key] = string(vehicle.get(key), f"vehicle.{key}")
    vehicle["side_designs_differ"] = vehicle.get("side_designs_differ", False)
    require(type(vehicle["side_designs_differ"]) is bool, "vehicle.side_designs_differ 必须是布尔值")
    manifest["vehicle"] = vehicle
    sources = array(manifest.get("sources", []), "sources")
    details = array(manifest.get("details", []), "details")
    views = array(manifest.get("views", []), "views")
    require(bool(sources), "至少提供一张 sources 原图")
    for items, location in ((sources, "sources"), (details, "details"), (views, "views")):
        unique_ids(items, location)
    cache: dict[Path, Picture] = {}
    source_map = {}
    for source in sources:
        source["role"] = string(source.get("role"), f"sources.{source['id']}.role")
        source["_picture"] = read_picture(local_path(source.get("path"), manifest_path.parent, f"sources.{source['id']}.path"), cache)
        source_map[source["id"]] = source
    for detail in details:
        prefix = f"details.{detail['id']}"
        detail["source_id"] = string(detail.get("source_id"), prefix + ".source_id")
        require(detail["source_id"] in source_map, prefix + ".source_id 未找到对应原图")
        bbox = array(detail.get("bbox"), prefix + ".bbox")
        require(len(bbox) == 4, prefix + ".bbox 必须是 [x0,y0,x1,y1]")
        require(all(type(value) in (int, float) and math.isfinite(value) for value in bbox), prefix + ".bbox 必须是有限数值，不能用布尔值")
        x0, y0, x1, y1 = bbox
        require(0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1, prefix + ".bbox 必须在 0..1 内且不得越界，右下角要大于左上角")
        detail["bbox"] = [float(value) for value in bbox]
        for key in ("title", "position", "text_exact"):
            detail[key] = string(detail.get(key), prefix + "." + key)
        lock = detail.get("lock", "")
        if isinstance(lock, list):
            lock = "；".join(string(value, prefix + ".lock[]") for value in lock)
        detail["lock"] = string(lock, prefix + ".lock")
        detail["side"] = string(detail.get("side"), prefix + ".side", "unknown")
        require(detail["side"] in SIDES, prefix + ".side 不在支持的侧别列表中")
        detail["status"] = string(detail.get("status"), prefix + ".status", "uncertain")
        require(detail["status"] in ("confirmed", "uncertain"), prefix + ".status 只能是 confirmed 或 uncertain")
        detail["critical"] = detail.get("critical", True)
        require(type(detail["critical"]) is bool, prefix + ".critical 必须是布尔值")
        detail["question"] = string(detail.get("question"), prefix + ".question")
        detail["options"] = [string(option, prefix + ".options[]") for option in array(detail.get("options", []), prefix + ".options")]
        detail["_picture"] = source_map[detail["source_id"]]["_picture"]
    for view in views:
        prefix = f"views.{view['id']}"
        require(view["id"] in VIEW_LABELS, prefix + ".id 只能是 F/B/L/R/FL45/FR45/RL45/RR45")
        view["status"] = string(view.get("status"), prefix + ".status", "draft")
        require(view["status"] in ("draft", "approved"), prefix + ".status 只能是 draft 或 approved")
        view["qa_note"] = string(view.get("qa_note"), prefix + ".qa_note")
        view["_picture"] = read_picture(local_path(view.get("path"), manifest_path.parent, prefix + ".path"), cache)
    manifest["sources"], manifest["details"], manifest["views"] = sources, details, views
    return manifest, cache


def readiness(manifest: dict) -> dict:
    view_map = {view["id"]: view for view in manifest["views"]}
    missing = [ident for ident in VIEW_LABELS if ident not in view_map]
    unverified = [ident for ident in VIEW_LABELS if ident in view_map and view_map[ident]["status"] != "approved"]
    critical = [detail for detail in manifest["details"] if detail["critical"]]
    uncertain = [{"id": detail["id"], "status": detail["status"], "side": detail["side"]} for detail in critical if detail["status"] != "confirmed" or detail["side"] == "unknown"]
    reasons = []
    if missing:
        reasons.append("缺少角度：" + "、".join(VIEW_LABELS[ident] for ident in missing))
    if unverified:
        reasons.append("角度尚未人工通过：" + "、".join(VIEW_LABELS[ident] for ident in unverified))
    if uncertain:
        reasons.append("关键细节尚未确认或侧别未知：" + "、".join(detail["id"] for detail in uncertain))
    if not critical:
        reasons.append("未提供任何关键细节约束")
    return {
        "ready": not reasons, "missing_views": missing, "unverified_views": unverified,
        "unconfirmed_critical_details": uncertain, "critical_detail_count": len(critical),
        "reasons": reasons,
        "pending_questions": [{"id": detail["id"], "title": detail["title"], "question": detail["question"], "options": detail["options"]} for detail in manifest["details"] if detail["question"] and (detail["status"] != "confirmed" or detail["side"] == "unknown")],
        "readiness_basis": "人工核验元数据；脚本不做车色、文字、左右侧或一致性的像素检测",
    }


def escape(value) -> str:
    return html.escape(str(value), quote=True)


def fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def orientation_transform(picture: Picture) -> str:
    width, height = picture.raw_width, picture.raw_height
    return {
        1: "", 2: f"matrix(-1 0 0 1 {width} 0)",
        3: f"matrix(-1 0 0 -1 {width} {height})", 4: f"matrix(1 0 0 -1 0 {height})",
        5: "matrix(0 1 1 0 0 0)", 6: f"matrix(0 1 -1 0 {height} 0)",
        7: f"matrix(0 -1 -1 0 {height} {width})", 8: f"matrix(0 -1 1 0 0 {width})",
    }[picture.orientation]


def wrapped_lines(value: str, max_units: int) -> list[str]:
    lines = []
    for paragraph in value.splitlines() or [""]:
        current, units = "", 0
        for char in paragraph:
            weight = 2 if unicodedata.east_asian_width(char) in "WF" else 1
            if current and units + weight > max_units:
                lines.append(current)
                current, units = "", 0
            current += char
            units += weight
        lines.append(current)
    return lines


def text_block(value: str, x: float, y: float, width: float, size: int = 22, fill: str = "#243044", max_lines: int | None = None) -> str:
    lines = wrapped_lines(value, max(4, int(width / size * 1.8)))
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + "…"
    tspans = "".join(f'<tspan x="{fmt(x)}" dy="{0 if index == 0 else size * 1.4}">{escape(line)}</tspan>' for index, line in enumerate(lines))
    return f'<text x="{fmt(x)}" y="{fmt(y)}" font-size="{size}" fill="{fill}" font-family="{FONT}">{tspans}</text>'


class SVG:
    def __init__(self, width: int, height: int, pictures: list[Picture], title: str, background: str = "#f2f5f9"):
        self.width, self.height = width, height
        self.clip_count = 0
        # HTML 内同时内嵌多个 SVG，必须使用唯一前缀，避免跨看板引用到别的原图。
        self.prefix = "board-" + hashlib.sha256(title.encode("utf-8")).hexdigest()[:12]
        self.picture_ids = {}
        definitions = []
        for picture in pictures:
            if picture.path in self.picture_ids:
                continue
            ident = self.prefix + "-photo-" + str(len(self.picture_ids))
            self.picture_ids[picture.path] = ident
            data_uri = f"data:{picture.mime};base64," + base64.b64encode(picture.data).decode("ascii")
            transform = orientation_transform(picture)
            definitions.append(f'<g id="{ident}" transform="{transform}"><image width="{picture.raw_width}" height="{picture.raw_height}" href="{data_uri}" preserveAspectRatio="none"/></g>')
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><title>{escape(title)}</title><defs>{"".join(definitions)}</defs><rect width="{width}" height="{height}" fill="{background}"/>']

    def add(self, value: str) -> None:
        self.parts.append(value)

    def rect(self, x, y, width, height, fill="#ffffff", stroke="none", radius=0) -> None:
        self.add(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(width)}" height="{fmt(height)}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

    def photo(self, picture: Picture, x, y, width, height, bbox: list[float] | None = None) -> None:
        crop = [0, 0, picture.width, picture.height] if bbox is None else [bbox[0] * picture.width, bbox[1] * picture.height, (bbox[2] - bbox[0]) * picture.width, (bbox[3] - bbox[1]) * picture.height]
        scale = min(width / crop[2], height / crop[3])
        draw_width, draw_height = crop[2] * scale, crop[3] * scale
        left, top = x + (width - draw_width) / 2, y + (height - draw_height) / 2
        clip_id = f"{self.prefix}-crop-{self.clip_count}"
        self.clip_count += 1
        self.add(f'<defs><clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse"><rect x="{fmt(left)}" y="{fmt(top)}" width="{fmt(draw_width)}" height="{fmt(draw_height)}"/></clipPath></defs><g clip-path="url(#{clip_id})"><use href="#{self.picture_ids[picture.path]}" transform="matrix({fmt(scale)} 0 0 {fmt(scale)} {fmt(left - crop[0] * scale)} {fmt(top - crop[1] * scale)})"/></g>')

    def overview(self, picture: Picture, bbox: list[float], x, y, width, height) -> None:
        self.photo(picture, x, y, width, height)
        scale = min(width / picture.width, height / picture.height)
        left = x + (width - picture.width * scale) / 2
        top = y + (height - picture.height * scale) / 2
        bx, by, x1, y1 = bbox
        bw, bh = x1 - bx, y1 - by
        self.add(f'<rect x="{fmt(left + bx * picture.width * scale)}" y="{fmt(top + by * picture.height * scale)}" width="{fmt(bw * picture.width * scale)}" height="{fmt(bh * picture.height * scale)}" fill="none" stroke="#ffcf38" stroke-width="5"/><rect x="{fmt(left + bx * picture.width * scale)}" y="{fmt(top + by * picture.height * scale)}" width="{fmt(bw * picture.width * scale)}" height="{fmt(bh * picture.height * scale)}" fill="none" stroke="#111827" stroke-width="1"/>')

    def finish(self) -> str:
        return "".join(self.parts) + "</svg>"


def board_sources(manifest: dict) -> SVG:
    sources = manifest["sources"]
    width, columns, margin, gap, card_height = 2400, 3, 32, 24, 590
    rows = math.ceil(len(sources) / columns)
    board = SVG(width, 130 + rows * (card_height + gap) + margin, [source["_picture"] for source in sources], "汽车原图索引")
    board.add(text_block((manifest["vehicle"]["name"] or "汽车") + "｜原图索引", margin, 54, width - 2 * margin, 34))
    board.add(text_block("保持原始图片与证据来源；所有裁切框以 EXIF 旋正后的图像为坐标基础。", margin, 94, width - 2 * margin, 22))
    card_width = (width - 2 * margin - (columns - 1) * gap) / columns
    for index, source in enumerate(sources):
        x, y = margin + index % columns * (card_width + gap), 126 + index // columns * (card_height + gap)
        board.rect(x, y, card_width, card_height, radius=16)
        board.photo(source["_picture"], x + 18, y + 58, card_width - 36, 422)
        board.add(text_block(source["id"], x + 20, y + 37, card_width - 40, 27))
        board.add(text_block(source["role"] or "原图用途待标注", x + 20, y + 515, card_width - 40, 22, max_lines=2))
        picture = source["_picture"]
        board.add(text_block(f"{picture.width} × {picture.height}｜源文件 SHA256 {picture.sha256[:12]}…", x + 20, y + 568, card_width - 40, 18, "#627086"))
    return board


def board_details(manifest: dict, clean: bool = False) -> SVG:
    details = manifest["details"]
    width, columns, margin, gap = 2400, 2, 32, 24
    card_width = (width - 2 * margin - gap) / columns
    card_height, top = (760, 32) if clean else (990, 130)
    rows = max(1, math.ceil(len(details) / columns))
    board = SVG(width, top + rows * (card_height + gap) + margin, [detail["_picture"] for detail in details], "汽车细节参考图" if clean else "汽车细节约束证据看板", "#ffffff" if clean else "#f2f5f9")
    if not clean:
        board.add(text_block((manifest["vehicle"]["name"] or "汽车") + "｜细节锁定与证据", margin, 54, width - 2 * margin, 34))
        board.add(text_block("大图是原图局部；小图黄色框对应来源位置。未确认项不能靠生成图反推为真实细节。", margin, 94, width - 2 * margin, 22))
    for index, detail in enumerate(details):
        x, y = margin + index % columns * (card_width + gap), top + index // columns * (card_height + gap)
        board.rect(x, y, card_width, card_height, radius=0 if clean else 16)
        if clean:
            board.photo(detail["_picture"], x + 10, y + 10, card_width - 20, card_height - 20, detail["bbox"])
            continue
        status = "已确认" if detail["status"] == "confirmed" else "未确认"
        color = "#167348" if detail["status"] == "confirmed" else "#ab5910"
        title = f"{detail['id']}｜{detail['title'] or '细节'}｜{status}"
        board.add(text_block(title, x + 22, y + 40, card_width - 44, 26, color, max_lines=1))
        board.rect(x + 18, y + 62, card_width - 36, 536, "#eef1f5")
        board.photo(detail["_picture"], x + 24, y + 68, card_width - 48, 524, detail["bbox"])
        board.overview(detail["_picture"], detail["bbox"], x + 20, y + 624, 330, 216)
        board.add(text_block(f"来源 {detail['source_id']}｜{SIDE_LABELS[detail['side']]}", x + 368, y + 644, card_width - 388, 21, max_lines=2))
        board.add(text_block("位置：" + (detail["position"] or "待确认"), x + 368, y + 710, card_width - 388, 21, max_lines=3))
        exact = detail["text_exact"] or "未提供可逐字核验的文字"
        board.add(text_block("文字：" + exact, x + 368, y + 806, card_width - 388, 21, max_lines=2))
        board.add(text_block("锁定：" + (detail["lock"] or "尚未填写锁定条件"), x + 20, y + 880, card_width - 40, 21, max_lines=3))
        board.add(text_block("关键细节" if detail["critical"] else "辅助细节", x + 20, y + 966, card_width - 40, 18, "#627086"))
    if not details and not clean:
        board.add(text_block("没有 details 条目，细节看板仍是草稿。", margin, 210, width - 2 * margin, 30, "#ab5910"))
    return board


def board_views(manifest: dict, clean: bool = False) -> SVG:
    width, columns, margin, gap = 2400, 4, 32, 20
    top, card_height = (32, 438) if clean else (134, 490)
    card_width = (width - 2 * margin - (columns - 1) * gap) / columns
    view_map = {view["id"]: view for view in manifest["views"]}
    board = SVG(width, top + 2 * (card_height + gap) + margin, [view["_picture"] for view in manifest["views"]], "汽车八视图干净版" if clean else "汽车标准八视图", "#ffffff" if clean else "#f2f5f9")
    if not clean:
        board.add(text_block((manifest["vehicle"]["name"] or "汽车") + "｜标准八视图", margin, 54, width - 2 * margin, 34))
        board.add(text_block("左右以车辆行驶方向定义；每格独立核验。缺角度留空，草稿角度标记未核验。", margin, 94, width - 2 * margin, 22))
    for index, (ident, label) in enumerate(VIEW_LABELS.items()):
        x, y = margin + index % columns * (card_width + gap), top + index // columns * (card_height + gap)
        board.rect(x, y, card_width, card_height, "#ffffff" if ident in view_map else "#edf0f4", radius=0 if clean else 12)
        if ident in view_map:
            view = view_map[ident]
            board.photo(view["_picture"], x + 8, y + (8 if clean else 64), card_width - 16, card_height - (16 if clean else 76))
            if not clean:
                approved = view["status"] == "approved"
                board.add(text_block(f"{ident} · {label}｜{'人工通过' if approved else '未核验'}", x + 14, y + 39, card_width - 28, 22, "#167348" if approved else "#ab5910", max_lines=1))
        elif not clean:
            board.add(text_block(f"{ident} · {label}", x + 14, y + 39, card_width - 28, 22))
            board.add(text_block("缺少该角度", x + 110, y + 256, card_width - 150, 30, "#627086"))
    return board


def single_detail(detail: dict) -> SVG:
    picture = detail["_picture"]
    crop_width, crop_height = (detail["bbox"][2] - detail["bbox"][0]) * picture.width, (detail["bbox"][3] - detail["bbox"][1]) * picture.height
    scale = 1600 / max(crop_width, crop_height)
    width, height = max(1, round(crop_width * scale)), max(1, round(crop_height * scale))
    board = SVG(width, height, [picture], "原图细节局部 " + detail["id"], "#ffffff")
    board.photo(picture, 0, 0, width, height, detail["bbox"])
    return board


def single_view(view: dict) -> SVG:
    picture = view["_picture"]
    board = SVG(1600, 1200, [picture], VIEW_LABELS[view["id"]], "#ffffff")
    board.photo(picture, 0, 0, 1600, 1200)
    return board


def atomic_write(path: Path, content: str) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=".board-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def build(manifest: dict, manifest_path: Path, output_dir: Path, cache: dict[Path, Picture], single_views: bool) -> dict:
    boards = {
        "sources.svg": board_sources(manifest), "details.svg": board_details(manifest),
        "details-clean.svg": board_details(manifest, clean=True), "multiview.svg": board_views(manifest),
        "multiview-clean.svg": board_views(manifest, clean=True),
    }
    for index, detail in enumerate(manifest["details"], 1):
        boards[f"detail-{index:02d}.svg"] = single_detail(detail)
    separate_views = [view for view in manifest["views"] if single_views or (manifest["vehicle"]["side_designs_differ"] and view["id"] in ("L", "R", "FL45", "FR45", "RL45", "RR45"))]
    if separate_views:
        for view in separate_views:
            boards[f"view-{view['id']}.svg"] = single_view(view)
    protected = set(cache) | {manifest_path.resolve()}
    planned = list(boards) + ["index.html", "receipt.json"]
    for filename in planned:
        target = output_dir / filename
        require(not target.is_symlink(), f"输出文件是符号链接，拒绝覆盖：{target}")
        require(target.resolve() not in protected, f"输出路径会覆盖输入文件：{target}")
        require(not target.exists() or target.is_file(), f"输出路径不是普通文件：{target}")
    output_dir.mkdir(parents=True, exist_ok=True)
    board_text = {filename: board.finish() for filename, board in boards.items()}
    state = readiness(manifest)
    board_names = ["sources.svg", "details.svg", "details-clean.svg", "multiview.svg", "multiview-clean.svg"]
    labels = ["原图索引", "细节约束证据", "细节干净版", "标准八视图", "八视图干净版"]
    sections = "".join(f'<section><h2>{label}</h2>{board_text[filename]}</section>' for filename, label in zip(board_names, labels))
    detail_links = "".join(f'<li><a href="detail-{index:02d}.svg">{escape(detail["id"])} · {escape(detail["title"] or "细节")}</a></li>' for index, detail in enumerate(manifest["details"], 1))
    view_links = "".join(f'<li><a href="view-{view["id"]}.svg">{escape(VIEW_LABELS[view["id"]])} 单图</a></li>' for view in separate_views)
    reasons = "；".join(state["reasons"]) if state["reasons"] else "八视图与关键细节的人工核验元数据已通过。"
    document = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>汽车参考看板</title><style>body{{margin:0;background:#e8edf3;color:#243044;font-family:{FONT};padding:28px}}main{{max-width:1600px;margin:auto}}section{{margin:32px 0}}svg{{display:block;width:100%;height:auto;background:white}}h1{{font-size:28px}}h2{{font-size:21px}}p{{line-height:1.7}}a{{color:#1e5bb8}}.state{{padding:20px;background:white;border-radius:12px}}</style><main><h1>{escape(manifest['vehicle']['name'] or '汽车')} · 参考看板</h1><div class="state"><strong>{'人工核验清单已通过' if state['ready'] else '草稿／尚未通过核验'}</strong><p>{escape(reasons)}</p><p>{escape(state['readiness_basis'])}</p></div>{sections}<section><h2>独立参考图</h2><ul>{detail_links}{view_links}</ul><p>SVG 使用原始编码图像，局部以几何视窗裁切；源照片不改写。上传视频模型前，请按工具支持情况导出为 PNG，并打开核对文字、左右侧与裁切范围。</p></section></main></html>'''
    for filename, content in board_text.items():
        atomic_write(output_dir / filename, content)
    atomic_write(output_dir / "index.html", document)
    for picture in cache.values():
        require(hashlib.sha256(picture.path.read_bytes()).hexdigest() == picture.sha256, f"运行期间源图发生变化：{picture.path}")
    receipt = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "manifest_path": str(manifest_path),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "vehicle": manifest["vehicle"], "output_dir": str(output_dir), **state,
        "source_files_unchanged_after_build": True,
        "sources": [{"id": source["id"], "role": source["role"], **source["_picture"].record()} for source in manifest["sources"]],
        "views": [{"id": view["id"], "status": view["status"], "qa_note": view["qa_note"], **view["_picture"].record()} for view in manifest["views"]],
        "details": [{key: value for key, value in detail.items() if not key.startswith("_")} for detail in manifest["details"]],
        "outputs": [{"file": filename, "size": [board.width, board.height], "sha256": hashlib.sha256(board_text[filename].encode("utf-8")).hexdigest()} for filename, board in boards.items()] + [{"file": "index.html", "sha256": hashlib.sha256(document.encode("utf-8")).hexdigest()}],
        "rendering": "自包含 SVG；只读源图；EXIF 非 1 时仅归一嵌入副本方向标签并使用 SVG 几何变换；不重编码像素、不联网、不提交生成",
    }
    atomic_write(output_dir / "receipt.json", json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="从 JSON 清单生成汽车原图索引、细节证据与八视图 SVG 看板")
    parser.add_argument("manifest", type=Path, help="JSON manifest 路径")
    parser.add_argument("--output-dir", "--out", dest="output_dir", type=Path, help="输出目录，默认 manifest 同级 board-output")
    parser.add_argument("--validate-only", action="store_true", help="只验证清单与源图，不写输出")
    parser.add_argument("--require-ready", action="store_true", help="人工核验元数据未通过则退出且不写输出")
    parser.add_argument("--single-views", action="store_true", help="另外输出已提供角度的无字 view-ID.svg")
    args = parser.parse_args()
    try:
        manifest_path = args.manifest.expanduser().resolve()
        require(manifest_path.is_file(), f"manifest 文件不存在：{manifest_path}")
        manifest, cache = load_manifest(manifest_path)
        state = readiness(manifest)
        if args.require_ready:
            require(state["ready"], "清单未达到可交付状态：" + "；".join(state["reasons"]))
        if args.validate_only:
            print(json.dumps({"valid": True, **state, "source_count": len(manifest["sources"]), "detail_count": len(manifest["details"]), "view_count": len(manifest["views"])}, ensure_ascii=False, indent=2))
            return 0
        requested_dir = (args.output_dir or manifest_path.parent / "board-output").expanduser()
        require(not requested_dir.is_symlink(), f"输出目录是符号链接，拒绝写入：{requested_dir}")
        output_dir = requested_dir.resolve()
        require(not output_dir.exists() or output_dir.is_dir(), f"输出目录不是文件夹：{output_dir}")
        receipt = build(manifest, manifest_path, output_dir, cache, args.single_views)
        print(json.dumps({"valid": True, "ready": receipt["ready"], "output_dir": str(output_dir), "receipt": str(output_dir / "receipt.json"), "reasons": receipt["reasons"]}, ensure_ascii=False, indent=2))
        return 0
    except (ManifestError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
