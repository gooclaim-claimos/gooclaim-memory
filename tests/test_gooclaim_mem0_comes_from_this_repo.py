"""GOOCLAIM DEVIATION guard: the server runs THIS repository's mem0, never PyPI's.

Upstream's compose command ran `pip install --force-reinstall --no-deps mem0ai`
on every start and requirements.txt floored `mem0ai>=0.1.48`, so a restart ran
whatever PyPI served that day — not the fork, not its litellm cap, not a
reviewed commit. These checks read the files that build and start the server.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"


def _requirement_names(path: Path) -> list[str]:
    names = []
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.append(re.split(r"[\s\[<>=!~;]", line, maxsplit=1)[0].lower())
    return names


def test_requirements_never_name_mem0ai() -> None:
    assert "mem0ai" not in _requirement_names(SERVER / "requirements.txt")


def test_the_compose_start_command_installs_nothing() -> None:
    compose = (SERVER / "docker-compose.yaml").read_text()
    assert "pip install" not in compose
    assert "mem0ai" not in compose


def test_both_images_install_mem0_from_the_checkout() -> None:
    for name in ("Dockerfile", "dev.Dockerfile"):
        text = (SERVER / name).read_text()
        assert "COPY mem0 " in text, name
        assert re.search(r"pip install [^\n]*/opt/mem0-src|pip install [^\n]*\"\.\[graph\]\"", text), name
        assert not re.search(r"pip install[^\n]*\bmem0ai\b", text), name


def test_an_instance_env_file_never_enters_an_image() -> None:
    ignored = (ROOT / ".dockerignore").read_text().splitlines()
    assert "**/.env" in ignored and ".git" in ignored
