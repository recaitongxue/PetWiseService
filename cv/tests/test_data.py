"""cv 数据管线单测（不依赖 torch，纯 CPU 即可跑）。

    python -m pytest tests/test_data.py -q
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

from src.data.annotation import BBox, parse_annotation
from src.data.thudogs_meta import (
    build_class_map,
    clean_lines,
    make_labels,
    parse_folder_name,
    resolve_image_path,
)


def _write_ann(path: Path, w: int, h: int, body: tuple[int, int, int, int]) -> None:
    root = Element("annotation")
    SubElement(root, "filename").text = path.stem
    size = SubElement(root, "size")
    SubElement(size, "width").text = str(w)
    SubElement(size, "height").text = str(h)
    obj = SubElement(root, "object")
    SubElement(obj, "name").text = "X_Dog"
    body_el = SubElement(obj, "bodybndbox")
    for tag, v in zip(("xmin", "ymin", "xmax", "ymax"), body):
        SubElement(body_el, tag).text = str(v)
    ElementTree(root).write(path, encoding="utf-8")


def test_parse_annotation_body_box(tmp_path: Path) -> None:
    ann = tmp_path / "n1.jpeg.xml"
    _write_ann(ann, 720, 720, (241, 47, 720, 720))
    a = parse_annotation(ann)
    assert a.size == (720, 720)
    assert a.body == BBox(241, 47, 720, 720)
    assert a.head is None


def test_bbox_scale_and_clip() -> None:
    b = BBox(100, 100, 200, 200)
    scaled = b.scaled(2.0, 0.5)
    assert scaled == BBox(200, 50, 400, 100)
    clipped = scaled.clipped(500, 80)
    assert clipped == BBox(200, 50, 400, 80)


def test_clean_lines_strips_cr_and_prefix(tmp_path: Path) -> None:
    p = tmp_path / "train.lst"
    p.write_text(".//1043-n000001-Shiba_Dog/n100001.jpeg\r\n.//1043-n000001-Shiba_Dog/n100002.jpg\r\n",
                 encoding="utf-8")
    lines = clean_lines(p)
    assert lines == ["1043-n000001-Shiba_Dog/n100001.jpeg", "1043-n000001-Shiba_Dog/n100002.jpg"]


def test_resolve_image_path_extension_mismatch(tmp_path: Path) -> None:
    breed = tmp_path / "1043-n000001-Shiba_Dog"
    breed.mkdir()
    # 磁盘上是 .jpg，lst 写的是 .jpeg
    (breed / "n100001.jpg").write_bytes(b"x")
    found = resolve_image_path(tmp_path, "1043-n000001-Shiba_Dog/n100001.jpeg")
    assert found is not None and found.suffix == ".jpg"


def test_build_class_map_sorted_and_indexed(tmp_path: Path) -> None:
    a = tmp_path / "A-x"
    b = tmp_path / "B-y"
    a.mkdir()
    b.mkdir()
    (a / "1.jpeg").write_bytes(b"x")
    (b / "2.jpeg").write_bytes(b"x")
    lst = tmp_path / "train.lst"
    lst.write_text(f"{a.name}/1.jpeg\n{b.name}/2.jpeg\n", encoding="utf-8")
    classes, c2i = build_class_map([lst])
    assert classes == ["A-x", "B-y"]  # 按文件夹名排序
    assert c2i == {"A-x": 0, "B-y": 1}


def test_parse_folder_name() -> None:
    assert parse_folder_name("1043-n000001-Shiba_Dog") == ("n000001", "Shiba Dog")


def test_make_labels_structure(tmp_path: Path) -> None:
    breed = tmp_path / "1043-n000001-Shiba_Dog"
    breed.mkdir()
    (breed / "n1.jpeg").write_bytes(b"x")
    lists = tmp_path / "TrainAndValList"
    lists.mkdir()
    (lists / "train.lst").write_text("1043-n000001-Shiba_Dog/n1.jpeg\n", encoding="utf-8")
    (lists / "validation.lst").write_text("", encoding="utf-8")

    out = tmp_path / "labels.json"
    labels = make_labels(tmp_path, out_path=out, version="v1", cn_map={"n000001": "柴犬"})
    assert len(labels) == 1
    assert labels[0] == {
        "breedId": "dog-n000001",
        "title": "柴犬",
        "nameEn": "Shiba Dog",
        "sci": "Canis lupus familiaris",
        "species": "dog",
    }
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert raw["numClasses"] == 1 and raw["imageSize"] == 224
    # 与 services/vision 的 Labels 契约对齐
    for it in raw["labels"]:
        assert {"breedId", "title", "sci", "species"} <= set(it)
