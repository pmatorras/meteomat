"""Regenerate structured sections of methodology.md from methodology.json."""
import json
import re
from pathlib import Path

docs = Path(__file__).parent
data = json.loads((docs / "methodology.json").read_text(encoding="utf-8"))
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
