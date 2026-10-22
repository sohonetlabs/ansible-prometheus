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
# Exercise the other non-boolean selectors reached by exporter installs.
selectors = [
    ("_install_from_binary.yml", "prometheus_software_archive_file", ["node.tar.gz", "node.zip"], [True, False]),
    ("_service.yml", "prometheus_software_env_vars", [{"PATH": "/bin"}, {}], [True, False]),
    ("_setup_capabilities.yml", "prometheus_software_capabilities", [{"node": ["cap_net_raw+ep"]}, {}], [True, False]),
    ("_install_capabilities.yml", "prometheus_capabilites_packages", [["libcap2-bin"], []], [True, False]),
    ("_install_go_compiler.yml", "present_go_paths.files", [[{"path": "/go/old"}], []], [True, False]),
]
def conditions_in(tasks):
    for task in tasks:
        conditions = task.get("when", [])
        yield from ([conditions] if isinstance(conditions, str) else conditions)
        for key in ["block", "rescue", "always"]:
            yield from conditions_in(task.get(key, []))
for filename, variable, values, expected_values in selectors:
    expressions = list(conditions_in(yaml.safe_load((root / "tasks" / filename).read_text())))
    expression = next(c for c in expressions if variable + " |" in c or variable + " is defined and" in c or variable + " is search" in c)
    for value, expected in zip(values, expected_values):
        variables = {variable: value}
        if variable == "present_go_paths.files":
            variables = {"present_go_paths": {"files": value}}
        cases.append((expression, variables, expected))
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
