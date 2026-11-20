"""Verify the six exported views of the authored triangle surfaces.

Compare full, raw, and LOD to fresh source assemblies after actual meshopt
decoding. Independently reopen the delivered .blend to count editable meshes.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project',type=Path,required=True)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--manifest',type=Path,required=True)
p.add_argument('--preview',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
root=a.project.resolve()
os.environ['SHANGHAI_PROJECT']=str(root)
def import_file(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
original=import_file(a.source,'concert_builder')
check=import_file(root/'source/precise/jingan-country-hospital/source/check_meshes.py','mesh_comparison')
manifest=json.loads(a.manifest.read_bytes())
assets=manifest['assets']
for item in assets.values():
    path=a.manifest.parent/item['file']
    assert len(path.read_bytes())==item['bytes']<100_000_000 and sha(path)==item['sha256']
with tempfile.TemporaryDirectory() as temp:
    results={}
    for key,lod in [('full',False),('lod',True)]:
        source=Path(temp)/(key+'-source.glb')
        original.assemble(lod).save(source,{})
        delivered=a.manifest.parent/assets[key]['file']
        results[key]=check.check_pair(source,delivered,Path(temp)/(key+'-decoded.glb'))
        if not lod:
            import runpy
            reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
            assert reader(a.manifest.parent/assets['raw']['file']).surface_digest()==results[key]
    native=a.manifest.parent/assets['native']['file']
    code="import bpy; m=[p for p in bpy.context.scene.objects if p.type=='MESH']; print('CHECK',len(m),sum(len(o.data.polygons)for o in m))"
    log=subprocess.check_output(['blender','-b',str(native),'--threads','1','-noaudio','--python-exit-code','1','--python-expr',code],text=True)
    mesh,triangles=map(int,re.search(r'^CHECK (\d+) (\d+)$',log,re.M).groups())
    assert mesh>20 and triangles==assets['raw']['triangles']
report={'scope':'Fresh procedural full/LOD geometric surfaces compared to shipped meshopt-decoded indexed triangles including materials and winding. Native artifact reopened from manifest path.','id':manifest['id'],'script_sha256':sha(Path(__file__)),'build_source_sha256':sha(a.source),'native_source_sha256':sha(a.source.with_name('native.py')),'parameters_sha256':sha(a.source.with_name('parameters.json')),'manifest_sha256':sha(a.manifest),'assets':assets,'full_raw_and_web_identical_oriented_surface':True,'lod_matches_authored_oriented_surface':True,'surface_digests':results,'native_editable_meshes':mesh,'native_triangles':triangles,'preview_sha256':sha(a.preview),'blender_version':subprocess.check_output(['blender','--version'],text=True).splitlines()[0]}
a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
