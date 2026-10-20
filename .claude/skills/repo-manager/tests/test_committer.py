import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("repo_committer", Path(__file__).parent.parent / "scripts" / "committer.py")
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def test_req_name_and_norm():
    assert mod.req_name("Python_Dotenv==1.0") == "python-dotenv"
    assert mod.req_name("pkg[extra]>=2") == "pkg"


def test_vtuple():
    assert mod.vtuple("3.14.6") == (3, 14, 6)
    assert mod.vtuple("v22.1") == (22, 1)


def test_rules_load():
    for name in ("repos.json", "tools.json", "commit.json"):
        assert mod.load(name)


def test_check_pyproject_flags_missing_package(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"\nrequires-python=">=3.11"\ndependencies=["foo==1.0","bar>=2"]\n', encoding="utf-8")
    rc = {"pyproject": True, "rule_file": None}
    rows = mod.check_pyproject("x", rc, tmp_path, {"foo": "1.0"})
    assert any(s == mod.FAIL and "bar" in d for s, _, d in rows)
    rows = mod.check_pyproject("x", rc, tmp_path, {"foo": "1.0", "bar": "2.1"})
    assert not any(s == mod.FAIL for s, _, _ in rows)
