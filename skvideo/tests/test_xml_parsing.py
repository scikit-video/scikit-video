"""Pins the xmltodictparser mapping semantics (previously provided by a
vendored 2012 xmltodict.py, now a small ElementTree-based parser). The
@attr / #text / repeated-tag-list shape is public API surface: ffprobe()
returns it to callers and the INFO_* keys in the io readers index into it."""
import skvideo
import skvideo.datasets
import skvideo.io
import pytest
from skvideo.utils import xmltodictparser


def test_mapping_semantics():
    xml = b"""<?xml version="1.0"?>
<root version="1">
  <item type="a" n="1"/>
  <item type="b"/>
  <textonly>hello</textonly>
  <mixed attr="x">some text</mixed>
  <empty/>
  <nested><leaf k="v"/></nested>
</root>"""
    d = xmltodictparser(xml)
    r = d["root"]
    assert r["@version"] == "1"
    # repeated sibling tags -> list, in document order
    assert r["item"] == [{"@type": "a", "@n": "1"}, {"@type": "b"}]
    # text-only element -> the text itself
    assert r["textonly"] == "hello"
    # attributes + text -> #text key
    assert r["mixed"] == {"@attr": "x", "#text": "some text"}
    # fully empty element -> None
    assert r["empty"] is None
    # nesting
    assert r["nested"]["leaf"] == {"@k": "v"}


@pytest.mark.skipif(not skvideo._HAS_FFMPEG, reason="FFmpeg required")
def test_ffprobe_shape_end_to_end():
    """The @-prefixed stream-attribute shape consumed by the readers."""
    info = skvideo.io.ffprobe(skvideo.datasets.bigbuckbunny())
    v = info["video"]
    assert v["@width"] == "1280"        # attribute values stay strings
    assert v["@height"] == "720"
    assert v["@codec_type"] == "video"
    assert info["video_streams"][0] is v
