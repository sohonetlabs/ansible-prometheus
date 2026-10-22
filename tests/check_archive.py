"""Run the role's archive options through Ansible against nested and flat tarballs."""
import io
import pathlib
import subprocess
import tarfile
import tempfile
import yaml

root = pathlib.Path(__file__).resolve().parents[1]
tasks = yaml.safe_load((root / "tasks/_install_from_binary.yml").read_text())
options = next(t["unarchive"]["extra_opts"] for t in tasks if "unarchive" in t and "extra_opts" in t["unarchive"])
with tempfile.TemporaryDirectory() as directory:
    base = pathlib.Path(directory)
    plays = []
    for name in ["node_exporter", "node_exporter-1.5.0/node_exporter"]:
        source = base / ("nested.tar.gz" if "/" in name else "flat.tar.gz")
        dest = base / source.stem
        dest.mkdir()
        with tarfile.open(source, "w:gz") as archive:
            data = b"exporter fixture\n"
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        plays.append({
            "name": name, "hosts": "localhost", "gather_facts": False,
            "vars": {"prometheus_software_binary_name": "node_exporter", "prometheus_software_archive_contents": {"files": [name]}},
            "tasks": [
                {"ansible.builtin.assert": {"that": ["archive_options is not string", "archive_options | type_debug == 'list'"]}, "vars": {"archive_options": options}},
                {"ansible.builtin.unarchive": {"src": str(source), "dest": str(dest), "remote_src": True, "extra_opts": options}},
                {"ansible.builtin.stat": {"path": str(dest / "node_exporter")}, "register": "extracted"},
                {"ansible.builtin.assert": {"that": ["extracted.stat.isreg"]}},
            ],
        })
    playbook = base / "extract.yml"
    playbook.write_text(yaml.safe_dump(plays))
    subprocess.run(["ansible-playbook", "-i", "localhost,", "-c", "local", str(playbook)], check=True)
