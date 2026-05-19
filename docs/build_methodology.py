"""Regenerate structured sections of methodology.md from methodology.json."""
import json
import re
from pathlib import Path

docs = Path(__file__).parent
root = docs.parent

# Sync version from pyproject.toml into methodology.json
_pyproject = root / "pyproject.toml"
_version_match = re.search(r'^version\s*=\s*"([^"]+)"', _pyproject.read_text(encoding="utf-8"), re.MULTILINE)
if not _version_match:
    raise ValueError("Could not find version in pyproject.toml")

json_path = docs / "methodology.json"
data = json.loads(json_path.read_text(encoding="utf-8"))
data["version"] = _version_match.group(1)
json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
md_path = docs / "methodology.md"
md = md_path.read_text(encoding="utf-8")


def replace_block(text, tag, content):
    return re.sub(
        rf"<!-- BEGIN:{tag} -->.*?<!-- END:{tag} -->",
        f"<!-- BEGIN:{tag} -->\n{content}\n<!-- END:{tag} -->",
        text,
        flags=re.DOTALL,
    )


# --- description ---
md = replace_block(md, "description", data["description"])

# --- sources table ---
rows = ["| Product | Resolution | Members | Horizon |", "|---|---|---|---|"]
for s in data["sources"]:
    members = f"{s['members']} perturbed runs" if s["members"] and s["members"] > 1 else (
        "1 deterministic run" if s["members"] == 1 else "—"
    )
    rows.append(f"| **{s['product']}** | ~{s['resolution_km']} km | {members} | {s['horizon_days']} days |")
md = replace_block(md, "sources", "\n".join(rows))

# --- limitations ---
items = [f"- **{lim['title']}**: {lim['body']}" for lim in data["limitations"]]
md = replace_block(md, "limitations", "\n".join(items))

md_path.write_text(md, encoding="utf-8")
print("methodology.md updated from methodology.json")
