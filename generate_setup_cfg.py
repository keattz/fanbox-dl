import toml


license = 'MIT'

with open('pyproject.toml') as f:
    metadata = toml.load(f)['project']

setup_cfg_parts = [f"""\
# This file was automatically generated from pyproject.toml by generate_setup_cfg.py.
# You should not edit it manually.

[metadata]
name = {metadata['name']}
version = {metadata['version']}
description = {metadata['description']}
author = {metadata['authors'][0]['name']}
author_email = {metadata['authors'][0]['email']}
license = {license}
license_file = {metadata['license']['file']}
url = {metadata['urls']['repository']}

[options]
packages = fanbox_dl
install_requires =
"""]

for dep in metadata['dependencies']:
    setup_cfg_parts.append(f"    {dep}\n")

setup_cfg_parts.append("""
[options.entry_points]
console_scripts =
""")

for script_name, entry_point in metadata['scripts'].items():
    setup_cfg_parts.append(f"    {script_name} = {entry_point}\n")

with open('setup.cfg', 'w') as f:
    f.write(''.join(setup_cfg_parts))

print("Generated setup.cfg successfully.")
