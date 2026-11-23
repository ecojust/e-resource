"""Build and reopen both registered garden photo cameras, the glazing, and the authors' mesh groups."""
import runpy
from pathlib import Path
import sys
from build_model import PROJECT

# Re-enter the building-specific Blender adapter after the shared geometry modules load.
sys.path.insert(0,str(Path(__file__).resolve().parent))

if __name__=='__main__':
    runpy.run_path(str(PROJECT/'source/precise/xuhui-huashan-823-827-stair-loggia/source/package_editable.py'),run_name='__main__')
