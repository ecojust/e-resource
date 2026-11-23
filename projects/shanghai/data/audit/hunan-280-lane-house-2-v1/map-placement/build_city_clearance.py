"""Rebuild the No. 2 city overlay with two shallow clearances for the retained No. 716."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent


def build(source, readings, output, lod):
    sys.path.insert(0,str(source))
    from build_model import Builder, META, PALETTE, add_building
    from east_face import side_measurements
    from house_finishes import WALL,GROUND
    from photo_architecture import Facade

    profile=json.loads(readings.read_bytes())
    b=Builder(PALETTE)
    add_building(b,lod)
    target='280-2 eastern wall/east wall facing adjoining plot'
    change=[i for i,p in enumerate(b.parts) if p['label']==target]
    assert len(change)==2 and {b.parts[i]['material']for i in change}=={WALL,GROUND}
    tip,far,_,windows=side_measurements()
    wall=Facade(b,tip[:2],far[:2],'280-2 eastern wall')
    half=wall.length*.5
    wall_plan=Polygon([wall.point(u,0,d)[:2] for u,d in [(-half,0),(half,0),(half,-.21),(-half,-.21)]])
    holes=unary_union(list(windows.values()))
    material_limits={GROUND:(0.,3.7),WALL:(3.7,float(tip[2]))}
    unchanged = [part for part in b.parts if part['label'] != target]
    report={}
    for index in reversed(change):
        mat=b.parts[index]['material']
        low,high=material_limits[mat]
        key='base' if mat==GROUND else 'eave'
        patch=profile['relief_bands'][key]
        zmin=max(low,patch['z_min']-profile['z_clearance_m']);zmax=min(high,patch['z_max']+profile['z_clearance_m'])
        obstacle=Polygon(patch['old_roof_or_reveal_outline_xy']).buffer(profile['xy_clearance_m'],join_style=2)
        assert obstacle.is_valid and obstacle.intersects(wall_plan)
        cut=wall_plan.intersection(obstacle); kept=wall_plan.difference(obstacle)
        old=b.parts.pop(index)
        before=len(b.parts)
        for a,z in [(low,zmin),(zmax,high)]:
            if z-a>1e-8:
                wall.prism(box(-half,a,half,z).difference(holes),-.21,0,mat,'east wall outside retained-neighbour band')
        assert holes.intersection(box(-half,zmin,half,zmax)).area<1e-10
        b.plan_prism(kept,zmin,zmax,mat,'280-2 eastern wall/locally closed clearance at garden neighbour '+key)
        # Preserve ordering of all unaffected parts and their UVs.
        new=b.parts[before:];del b.parts[before:];b.parts[index:index]=new
        report[key]={'z_interval':[zmin,zmax],'removed_plan_m2':cut.area,'removed_volume_m3':cut.area*(zmax-zmin),'original_component':old['label'],'new_closed_components':len(new)}
    from check_mesh import paired_edges
    intact = set(map(id, unchanged))
    checked = {}
    for part in b.parts:
        vertices=np.asarray(part['vertices'])
        idx=np.asarray(part['triangles'])
        _,inverse=np.unique(np.round(vertices,7),axis=0,return_inverse=True)
        if not paired_edges(idx) and not paired_edges(inverse[idx]):
            raise ValueError('Open component '+part['label'])
        triangles=vertices[idx]-vertices[idx[0,0]]
        volume=np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6.
        if volume <= 0.:
            raise ValueError('Nonpositive volume '+part['label'])
        if id(part) not in intact:
            checked.setdefault(part['label'],[]).append(float(volume))
    if [id(p)for p in b.parts if id(p)in intact]!=[id(p)for p in unchanged]:
        raise ValueError('Unexpected edit to an unrelated component')
    report['closure']={'total':len(b.parts),'untouched':len(unchanged),'new_parts_and_positive_volumes':checked}
    artifact=b.save(output,{**META,'scope':META['scope']+'；城景使用716号普通源户原有踢脚/檐口附近局部退让。',
                            'retained_ordinary_ids':[716,1629,369],
                            'city_clearance_source':hashlib.sha256(readings.read_bytes()).hexdigest()})
    return {'direction':'lod' if lod else 'full','model_sha256':artifact['sha256'],'changes':report}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source',type=Path,required=True)
    cli.add_argument('--profile',type=Path,default=HERE/'716-profile.json')
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--lod',action='store_true')
    a=cli.parse_args();r=build(a.source,a.profile,a.output,a.lod)
    a.output.with_suffix('.clearance.json').write_text(json.dumps(r,indent=2)+'\n')
