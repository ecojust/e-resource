"""Read actual GLB triangles against the photographed casement or the attic design sections."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from corner_attic import attic_openings,attic_outline,BOARD,GLASS,GREEN,STEEL
from garden_finishes import IVORY_RENDER
from residence_materials import CLAY,LEAD,SILL


def casement_probes(scale):
    photo=json.loads((HERE/'entrance-upper-casement-photo.json').read_text())
    st=json.loads((HERE/'court-station.json').read_text())
    projection=np.asarray(st['pinhole'])@np.asarray(st['world_to_camera_rotation'])
    inv=np.linalg.inv(projection)
    eye=np.asarray(st['camera_centre_in_authored_frame'])*scale
    for material,pixels in photo['material_samples_190'].items():
        for pixel in pixels:
            yield {'native_photo_190_px':pixel},eye,inv@[*pixel,1.],'Yanqing 159 | '+material


def attic_probes(scale,base):
    layout={'base_z':base}
    holes=attic_openings(layout)
    def section(face,u,z,material):
        if face=='east':
            point=[u,-.63,z];direction=[0,1,0]
        elif face=='north':
            point=[.63,u,z];direction=[-1,0,0]
        else:
            point=[u,1.70,base+3.2];direction=[0,0,-1]
        return {'face':face,'section':[round(u,4),round(z,4)]},np.asarray(point)*scale,direction,material
    for name,face,cols,levels in [('east_glazed_band','east',12,(.23,.75)),
                                   ('north_paired_light','north',3,(.16,.46,.83)),
                                   ('north_end_light','north',2,(.25,.78))]:
        a,b,c,d=holes[name]
        for i in range(cols):
            u=a+(c-a)*(i+.5)/cols
            for v in levels:
                yield section(face,u,b+v*(d-b),GLASS)
        yield section(face,a+.010,b+.40*(d-b),STEEL if face=='east' else GREEN)
    yield section('east',-1.29,base+1.50,BOARD)
    yield section('east',-1.12,base+.018,SILL)
    yield section('north',2.10,base+.48,IVORY_RENDER)
    yield section('north',1.72,base+.008,SILL)
    for x in (-2.08,-.65,-1.39):
        yield section('roof',x,0.,CLAY)
    yield section('north',1.55,attic_outline(layout)['gable_spring_z']+.02,LEAD)


def check(mesh,part,scale,base):
    scene=SerialScene(mesh)
    probes=casement_probes(scale) if part=='casement' else attic_probes(scale,base)
    rows=[]
    for key,origin,direction,wanted in probes:
        hit=scene.ray(origin,direction,length=30.)
        actual=hit['material'] if hit else None
        rows.append({**key,'expected':wanted,'observed':actual,'match':actual==wanted})
    return {'asset':scene.asset,'part':part,'metric_scale':scale,
            'samples':len(rows),'matched':sum(r['match'] for r in rows),'readings':rows,
            'interpretation':('Fixed pixels marked on the original photograph 190.'
                              if part=='casement' else 'Sections through the authored surfaces. Photo observations and fit limitations are in corner-attic-photo-control.json.')}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('report',type=Path)
    parser.add_argument('part',choices=['casement','attic'])
    parser.add_argument('--scale',type=float,default=1.184)
    parser.add_argument('--base',type=float,default=5.27)
    args=parser.parse_args()
    result=check(args.mesh,args.part,args.scale,args.base)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['matched'],result['samples'],result['asset']['sha256'])
