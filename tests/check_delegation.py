"""Verify the actual service task's loop/delegate/when evaluation without connections."""
import copy
import pathlib
import subprocess
import tempfile
import yaml

root = pathlib.Path(__file__).resolve().parents[1]
tasks = yaml.safe_load((root / "tasks/_service.yml").read_text())
original = next(t for t in tasks if t.get("loop_control", {}).get("loop_var") == "prometheus_server_name")
plays = []
for servers, enabled, expected in [([], True, False), (["localhost"], False, False), (["localhost"], True, True)]:
    task = copy.deepcopy(original)
    task["name"] = "Evaluate service delegation"
    del task["wait_for"]
    task["ansible.builtin.debug"] = {"msg": "selected"}
    task["register"] = "result"
    plays.append({
        "name": f"servers={servers}, enabled={enabled}", "hosts": "localhost", "gather_facts": False,
        "vars": {"prometheus_servers": servers, "prometheus_software_server_side_connect_test": enabled, "prometheus_software_port_num": 9100},
        "tasks": [task, {"ansible.builtin.assert": {"that": ["result is not skipped" if expected else "result is skipped"]}}],
    })
with tempfile.TemporaryDirectory() as directory:
    playbook = pathlib.Path(directory) / "delegation.yml"
    playbook.write_text(yaml.safe_dump(plays))
    subprocess.run(["ansible-playbook", "-i", "localhost,", "-c", "local", str(playbook)], check=True)
