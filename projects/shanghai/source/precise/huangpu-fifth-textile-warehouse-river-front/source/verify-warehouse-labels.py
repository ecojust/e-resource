from pathlib import Path
import bpy,json,sys
blend,raw,report=map(Path,sys.argv[sys.argv.index('--')+1:])
assert Path(bpy.data.filepath).samefile(blend)
d=json.loads(report.read_bytes())
found={o.name:o['full_source_group'] for o in bpy.context.scene.objects if 'full_source_group' in o}
assert found and all(len(k.encode())<=63 and len(v.encode())>63 for k,v in found.items())
for k,v in found.items():assert k=='Warehouse/'+v.split('/',1)[1]
d['names_preserved_as_object_properties']=found
report.write_text(json.dumps(d,indent=2)+'\n')
