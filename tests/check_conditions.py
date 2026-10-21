"""Exercise the role's binary/source selectors with strict Ansible conditionals."""
import pathlib
import subprocess
import tempfile
import yaml

root = pathlib.Path(__file__).resolve().parents[1]
tasks = yaml.safe_load((root / "tasks/_install.yml").read_text())
binary = next(t["when"] for t in tasks if t.get("include_tasks") == "_install_from_binary.yml")
source = next(t["when"][-1] for t in tasks if t.get("include_tasks") == "_install_from_go_source.yml")
plays = []
cases = [
    (binary, {"prometheus_software_url": "https://example.com/node.tar.gz"}, True),
    (binary, {"prometheus_software_url": ""}, False),
    (binary, {}, False),
    (binary, {"prometheus_software_metadata": {"name": "node.tar.gz"}}, True),
    (binary, {"prometheus_software_release": {"name": "v1"}, "prometheus_software_url": "https://example.com/node.tar.gz"}, False),
    (binary, {"prometheus_software_url": "https://example.com/node.tar.gz", "prometheus_always_build_from_source": True}, False),
    (source, {"prometheus_software_src_url": "https://example.com/source.tar.gz"}, True),
    (source, {"prometheus_software_src_url": ""}, False),
    (source, {}, False),
]
for i, (condition, variables, expected) in enumerate(cases):
    plays.append({
        "name": f"case {i}", "hosts": "localhost", "gather_facts": False,
        "vars": {"prometheus_always_build_from_source": False, **variables},
        "tasks": [
            {"ansible.builtin.debug": {"msg": "selected"}, "when": condition, "register": "result"},
            {"ansible.builtin.assert": {"that": ["result is not skipped" if expected else "result is skipped"]}},
        ],
    })
with tempfile.TemporaryDirectory() as directory:
    playbook = pathlib.Path(directory) / "conditions.yml"
    playbook.write_text(yaml.safe_dump(plays))
    subprocess.run(["ansible-playbook", "-i", "localhost,", "-c", "local", str(playbook)], check=True)
