"""Encode the Huashan Road near/far pair and verify its decoded geometry, PBR values and painted UVs."""
import argparse
import importlib.util
import os
from pathlib import Path

from build_model import PROJECT

# The packager imports this model's build_model and build_blender_source adapters.
# Its meshopt round-trip, metadata retention and oriented UV comparisons are shared.
shared = PROJECT / 'source/precise/xuhui-yanqing-159-garden-residence/source/package_model.py'
spec = importlib.util.spec_from_file_location('shanghai_meshopt_pair', shared)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)

if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source_dir', type=Path)
    cli.add_argument('out', type=Path)
    cli.add_argument('--gltfpack', default=os.environ.get('GLTFPACK', 'gltfpack'))
    args = cli.parse_args()
    packager.package(args.source_dir, args.out, args.gltfpack)
