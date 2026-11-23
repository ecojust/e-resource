"""Compare vertices, oriented triangles and material assignments after actual meshopt decoding."""
from pathlib import Path
import runpy
import subprocess

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
PREVIOUS=PROJECT/'source/precise/hongkou-general-post-office/source'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'


def check_pair(reference, packed, decoded):
    subprocess.run(['node',str(PREVIOUS/'decode_meshopt.mjs'),str(packed),str(decoded),
                    str(PROJECT/'vendor/meshopt_decoder.module.js')],check=True)
    scene=runpy.run_path(str(READER))['SerialScene']
    expected=scene(reference).surface_digest()
    actual=scene(decoded).surface_digest()
    assert expected == actual, 'Decoded mesh differs in position, connectivity, orientation, or material assignment'
    return actual
