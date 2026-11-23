"""Build and reopen the registered street residence with its actual packed surface bindings."""
import importlib.util
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/verify_editable_model.py').is_file())
script=PROJECT/'source/precise/xuhui-shaanxi-222-no20-residence-gate/source/build_blender_source.py'
spec=importlib.util.spec_from_file_location('shanghai_verified_native_io',script)
io=importlib.util.module_from_spec(spec)
paths=sys.path.copy()
try:
    spec.loader.exec_module(io)
finally:
    sys.path[:]=paths
io.SOURCE=io.native.SOURCE=io.helpers.SOURCE=SOURCE
io.helpers.MODEL_ID=SOURCE.parent.name
io.helpers.UV='Yanqing 2 architectural surface UV'
io.native.NODE='Yanqing 2 procedural colour'
io.NORMAL_NAME='Yanqing 2 procedural normal' 
io.TANGENT_NAME='Yanqing 2 surface relief'
helpers,digest=io.helpers,io.digest
texture_bindings,used_textures,attribution=io.texture_bindings,io.used_textures,io.attribution

if __name__=='__main__':
    phase=os.environ['ARCHITECTURAL_NATIVE_STAGE']
    if phase=='make':
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(io.prepare))
    elif phase=='reopen':
        io.verify(*map(Path,sys.argv[sys.argv.index('--')+1:]))
    else:
        raise ValueError(phase)
