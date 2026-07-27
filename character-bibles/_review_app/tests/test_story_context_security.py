"""Security regression tests for the Studio story endpoints.

issue_id arrives from the /api/story/{save,generate-sample} request body and
becomes a filesystem folder name (issue_output_dir -> mkdir + write). Before
the fix it was copied over the safe MZ-DRAFT default with no validation, so a
POST body could drive an arbitrary-location directory creation and file write
(path traversal). These pin the guard at both the choke point
(normalize_setup) and the sink (issue_output_dir).
"""
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import story_context as sc  # noqa: E402


TRAVERSAL_IDS = [
    "../escape",
    "../../../../Windows/Temp/pwn",
    "..\\..\\win",
    "a/b",
    "/abs/path",
    "C:\\Windows\\Fizz",
    "..",
    ".",
    "foo..bar",
    "",
    "   ",
    "MZ-2026-07-01/../../evil",
]

LEGIT_IDS = ["MZ-TEST", "MZ-API-STORY", "MZ-2026-07-01", "MZ-DRAFT-20260717-225300"]


@pytest.mark.parametrize("bad", TRAVERSAL_IDS)
def test_safe_issue_id_rejects_traversal(bad):
    with pytest.raises(sc.StoryContextError):
        sc.safe_issue_id(bad)


@pytest.mark.parametrize("ok", LEGIT_IDS)
def test_safe_issue_id_accepts_legit(ok):
    assert sc.safe_issue_id(ok) == ok


@pytest.mark.parametrize("bad", TRAVERSAL_IDS)
def test_issue_output_dir_rejects_traversal_at_sink(tmp_path, bad):
    with pytest.raises(sc.StoryContextError):
        sc.issue_output_dir(bad, tmp_path)


def test_issue_output_dir_accepts_legit_stays_inside_workspace(tmp_path):
    out = sc.issue_output_dir("MZ-TEST", tmp_path)
    assert out == tmp_path / "issues" / "MZ-TEST"
    # resolves to a location genuinely under the workspace root
    assert tmp_path.resolve() in out.resolve().parents


@pytest.mark.parametrize("bad", TRAVERSAL_IDS)
def test_normalize_setup_rejects_traversal_issue_id(bad):
    with pytest.raises(sc.StoryContextError):
        sc.normalize_setup({"issue_id": bad, "characters": []})


def test_normalize_setup_default_draft_id_passes():
    out = sc.normalize_setup({"characters": []})
    assert out["issue_id"].startswith("MZ-DRAFT-")


def test_save_preview_traversal_creates_no_file_outside_workspace(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    # ws/issues/../../pwn_escape would land at tmp_path/pwn_escape -- outside ws
    body = {"issue_id": "../../pwn_escape", "characters": ["MZ-CHAR-STATIC"], "topic": "x"}
    with pytest.raises(sc.StoryContextError):
        sc.save_preview(body, tmp_path / "bibles", ws)
    # the guard fires before any mkdir/write -- nothing escaped
    assert not (tmp_path / "pwn_escape").exists()
    assert list(tmp_path.rglob("*pwn_escape*")) == []
