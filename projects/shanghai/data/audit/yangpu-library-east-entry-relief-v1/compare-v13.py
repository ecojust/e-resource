"""Compare the published V13 and revised complete GLBs in the same metric scene."""
from argparse import ArgumentParser
from pathlib import Path
import copy
import hashlib
import json
import runpy
import sys
import numpy as np

def digest(path):
    h=hashlib.sha256()
    with path.open('rb')as source:
        for chunk in iter(lambda:source.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def outside_summary(scene):
    # Changed meshes are enclosed by the exact photographed door, side-frieze
    # and carved arch extent. Every longer or crossing face must be preserved.
    lower=np.array([18.54,-4.23,-.03]);upper=np.array([19.22,2.00,4.10])
    inside=np.all((scene.tri>=lower)&(scene.tri<=upper),axis=(1,2))
    outside=copy.copy(scene)
    outside.tri=scene.tri[~inside];outside.mi=scene.mi[~inside]
    return dict(triangles=len(scene.tri),inside_triangles=int(np.count_nonzero(inside)),
                outside_triangles=int(np.count_nonzero(~inside)),outside_oriented_surfaces=outside.surface_digest(),
                bounds=[scene.lows.min(0).tolist(),scene.highs.max(0).tolist()])

def compare(reader,old_path,new_path):
    before=reader(old_path);old=outside_summary(before);del before
    after=reader(new_path);new=outside_summary(after);del after
    assert old['outside_oriented_surfaces']==new['outside_oriented_surfaces'], {
        k:(old['outside_oriented_surfaces'].get(k),new['outside_oriented_surfaces'].get(k))
        for k in set(old['outside_oriented_surfaces'])|set(new['outside_oriented_surfaces'])
        if old['outside_oriented_surfaces'].get(k)!=new['outside_oriented_surfaces'].get(k)}
    assert old['bounds']==new['bounds'] and new['inside_triangles']>old['inside_triangles']
    return dict(old_file=old_path.name,old_sha256=digest(old_path),new_file=new_path.name,new_sha256=digest(new_path),
                old_triangles=old['triangles'],new_triangles=new['triangles'],revised_original_triangles=old['inside_triangles'],
                revised_current_triangles=new['inside_triangles'],identical_exterior_triangles=new['outside_triangles'],
                unchanged_oriented_material_faces=new['outside_oriented_surfaces'],unchanged_bounds_enu=new['bounds'])

def main():
    cli=ArgumentParser(description=__doc__)
    for arg in ['old-full','new-full','old-lod','new-lod','project','out']:cli.add_argument('--'+arg,type=Path,required=True)
    args=cli.parse_args();reader=args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    scene=runpy.run_path(str(reader))['SerialScene'];report=dict(model='yangpu-library',refinement='yangpu-library-east-entry-relief',
        owner=1196,original_city_id_retained=True,checker_sha256=digest(Path(__file__)),reader_sha256=digest(reader),
        compared_outside_enu_box_m=[[18.54,-4.23,-.03],[19.22,2.,4.10]],
        full=compare(scene,args.old_full,args.new_full),lod=compare(scene,args.old_lod,args.new_lod))
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
