"""Compare each pre-existing object, mesh, material binding and packed texture after reopening."""
import bpy
from hashlib import sha256
from pathlib import Path
import json,runpy,sys
here=Path(__file__).resolve().parent
project=here.parents[2]
helpers=runpy.run_path(str(project/'source/precise/bund17/revisions/street-wing-doors/native_doors.py'))
old,new,output=map(Path,sys.argv[sys.argv.index('--')+1:])
def records(file):
    bpy.ops.wm.open_mainfile(filepath=str(file))
    table={}
    for ob in bpy.data.objects:
        entry=dict(type=ob.type,matrix_world=[list(r)for r in ob.matrix_world])
        if ob.type=='MESH':
            mesh=ob.data;entry.update(signature=helpers['signature'](ob),vertices=len(mesh.vertices),faces=len(mesh.polygons),loops=len(mesh.loops))
        table[ob.name]=entry
    return table,helpers['images']()
original,images=records(old);revised,new_images=records(new)
assert images==new_images and all(revised[k]==v for k,v in original.items())
assert len(set(revised)-set(original))==8
output.write_text(json.dumps(dict(passed=True,old_file_sha256=sha256(old.read_bytes()).hexdigest(),new_file_sha256=sha256(new.read_bytes()).hexdigest(),
    individually_matched_old_objects=original,unchanged_packed_images=images,added_editable_objects=sorted(set(revised)-set(original))),ensure_ascii=False,indent=2)+'\n')
