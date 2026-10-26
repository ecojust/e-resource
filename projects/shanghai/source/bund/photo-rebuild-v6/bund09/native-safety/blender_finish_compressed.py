"""Run the frozen common finisher with only compress=True at the save call.

Executed by the parent with Blender, never by the research/geometry agent.
All CLI arguments remain those of common/blender_finish.py. No shared file is
modified. The SHA and exact replacement count prevent silently drifting code.
"""
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[1]/'common'/'blender_finish.py'
EXPECTED='d0859e6692b7a603872c14897876f3f021017f90e4938bcd3dc0eb3083cc03d1'
raw=HELPER.read_bytes()
if hashlib.sha256(raw).hexdigest()!=EXPECTED:
    raise RuntimeError('Frozen common finisher changed; review this narrow wrapper before use.')
source=raw.decode()
old='bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))'
new='bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()), compress=True)'
if source.count(old)!=1:raise RuntimeError('Expected exactly one native save call')
scope={'__name__':'__main__','__file__':str(HELPER)}
exec(compile(source.replace(old,new),str(HELPER)+'[compressed-save-only]','exec'),scope)
out=scope['out'];args=scope['args'];report=scope['report']
report.update({'save_compress_requested':True,'base_finisher_sha256':EXPECTED,
               'isolated_wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'save_change':'Only save_as_mainfile(compress=True); raw GLB import, original packed JPEG, geometry, camera and report code unchanged.',
               'stored_native_header_hex':out.read_bytes()[:12].hex(),
               'full_storage_validation':'Run validate_native_storage.py and a separate Blender reopen check.'})
(args.output/(args.glb.stem+'-blender.json')).write_text(json.dumps(report,indent=2)+'\n')
