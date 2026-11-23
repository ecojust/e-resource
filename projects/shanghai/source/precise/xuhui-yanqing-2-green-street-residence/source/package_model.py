"""Compare the two measured facade meshes and their decoded geometry, UVs and texture bindings."""
import runpy
from pathlib import Path
from build_model import PROJECT
if __name__=='__main__':
    script=PROJECT/'source/precise/xuhui-shaanxi-222-no20-residence-gate/source/package_model.py'
    runpy.run_path(str(script),run_name='__main__')
