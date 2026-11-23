"""Meshopt-encode the Dafu Li pair and compare decoded topology, colours, normals and UVs."""
import argparse
import importlib.util
import os
from pathlib import Path

from build_blender_source import brick_bindings
from build_model import PROJECT

shared = PROJECT / 'source/precise/xuhui-yanqing-159-garden-residence/source/package_model.py'
spec = importlib.util.spec_from_file_location('shanghai_meshopt_pair', shared)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)
check_colour_uv = packager.check_finishes


def check_finishes(source, decoded):
    result = check_colour_uv(source, decoded)
    original = brick_bindings(source)
    if original != brick_bindings(decoded):
        raise ValueError('Decoded relief bindings differ from the corresponding original GLB')
    for name, data in original.items():
        result[name]['normal_sha256'] = data['normal']['sha256']
        result[name]['shared_texcoord'] = data['normal']['texcoord']
        result[name]['normal_strength'] = data['normal']['scale']
    return result


packager.check_finishes = check_finishes
if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source_dir', type=Path)
    cli.add_argument('out', type=Path)
    cli.add_argument('--gltfpack', default=os.environ.get('GLTFPACK', 'gltfpack'))
    args = cli.parse_args()
    packager.package(args.source_dir, args.out, args.gltfpack)
