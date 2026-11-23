"""Rebuild the signed No. 20 gate, then save and reopen its textured editable Blender counterpart."""
import runpy
from pathlib import Path

from build_model import PROJECT

if __name__ == '__main__':
    runner = PROJECT / 'source/precise/xuhui-huashan-823-827-stair-loggia/source/package_editable.py'
    runpy.run_path(str(runner), run_name='__main__')
