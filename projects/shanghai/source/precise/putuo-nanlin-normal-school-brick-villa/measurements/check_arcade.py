"""Trace original photo observations through a complete exported GLB, retaining real first hits."""
import argparse
import json
import runpy
from pathlib import Path
from hashlib import sha256
import numpy as np

FAMILIES={
    'grey-brick':['Nanlin | grey facing brick'], 'red-brick':['Nanlin | red stringcourse brick','Nanlin | deep red coping brick','Nanlin arcade | radial red brick','Nanlin arcade | dark fired face'],
    'stone':['Nanlin arcade | pale grey stone','Nanlin | warm carved stone'],
    'open':[], 'clay-arch':['Nanlin arcade | radial red brick','Nanlin arcade | dark fired face','Nanlin | lime joints'],
}
# Native-image coordinates read from three original photographs, including the
# worn, partly blank guard visible in the earlier view. Checks concern shared
# permanent masonry, or the restored guard in the two later images.
SITES={
    'restored-oblique': {
        'grey-brick':[(389,393),(550,345),(541,115),(389,158),(114,347)],
        'red-brick':[(178,374),(266,382),(176,225),(256,184)],
        'stone':[(382,114),(538,76),(266,145),(345,268),(460,255),(336,177),(452,27)],
        'clay-arch':[(431,38),(306,78),(205,110)],
        'open':[(76,311),(144,306),(212,320),(320,336),(450,325),(52,211),(93,194),(140,182),(217,145),(325,129),(455,103)]},
    'restored-complete':{
        'grey-brick':[(405,238),(313,248),(103,261),(400,142),(308,153),(109,179)],
        'red-brick':[(220,256),(150,274),(233,166),(171,179),(515,143)],
        'stone':[(312,129),(400,115),(233,138),(448,161),(367,154),(279,160)],
        'clay-arch':[(249,125),(432,86),(370,105)],
        'open':[(36,256),(76,260),(125,265),(180,269),(265,258),(352,247),(449,245),
                (91,182),(133,165),(190,154),(265,145),(352,137),(449,118)]},
    'earlier-oblique': {
        # Earlier view was marked on a 760 × 570 working copy; converted to 1280 below.
        'grey-brick':[(440,271),(517,282),(633,316)],
        'red-brick':[(346,270),(346,345)],
        'stone':[(344,217),(444,241),(515,260)],
        'clay-arch':[(376,189),(482,213),(541,235)],
        'open':[(397,228),(480,251),(551,265),(611,287),(400,383),(474,385),(551,391)]},
}


def check(model, study, pitch, storey, origin, tangent, inside, project):
    scene=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['SerialScene'](model)
    origin=np.array(origin,float);A=np.column_stack((tangent,inside,[0,0,1.]))
    rows=[]
    for name,groups in SITES.items():
        source=study['views'][name]; H=np.array(source['H_local_plane_to_native'])
        camera=source['positive_inward_camera'];eye=np.array(camera['eye_local_scaled'])*[pitch,pitch,storey]
        camera_eye=origin+A@eye
        for group,sites in groups.items():
            for uv0 in sites:
                uv=np.array(uv0,float)*(1280/760 if name=='earlier-oblique' else 1.)
                pt=np.linalg.solve(H,[*uv,1.]);pt=pt[:2]/pt[2]
                at=origin+A@np.array([pt[0]*pitch,0,pt[1]*storey])
                vec=at-camera_eye;ray=scene.ray(camera_eye,vec/np.linalg.norm(vec),length=np.linalg.norm(vec)+30)
                dep=float((np.linalg.solve(A,np.array(ray['point_enu_m'])-origin))[1]) if ray else None
                ok=(ray is None or dep>.44) if group=='open' else bool(ray and ray['material'] in FAMILIES[group])
                rows.append(dict(view=name,native_uv=np.round(uv,3).tolist(),expected=group,passed=ok,
                                 first_hit=ray,first_hit_inward_m=dep))
    return dict(sha256=sha256(model.read_bytes()).hexdigest(),file=model.name,passed=sum(r['passed'] for r in rows),
                total=len(rows),rows=rows)


def main():
    parse=argparse.ArgumentParser(description=__doc__)
    parse.add_argument('models',nargs='+',type=Path);parse.add_argument('--project',type=Path,default=Path.cwd())
    parse.add_argument('--output',required=True,type=Path);parse.add_argument('--layout',type=Path)
    args=parse.parse_args();m=Path(__file__).absolute().parent
    study=json.loads((m/'arcade-photograph-registration.json').read_text())
    layout=json.loads(args.layout.read_bytes()) if args.layout else json.loads((m.parent/'source/building-layout.json').read_bytes())
    if 'arcade_outer_width_m' in layout:
        import sys
        sys.path.insert(0,str(m.parent/'source'))
        from fabric import metric
        width=layout['arcade_outer_width_m']; span=width/(1.+.245/7.)
        layout={'arcade_length':span,'arcade_storey':layout['arcade_storey_m'],
                'arcade_origin':[metric(119,452)[0],width-(width-span)/2,0.],
                'arcade_tangent':[0.,-1.,0.],'arcade_inward':[1.,0.,0.]}
    out=[check(f,study,layout.get('arcade_length',25.8)/7,layout.get('arcade_storey',4.90),
               layout.get('arcade_origin',[0,0,0]),layout.get('arcade_tangent',[1,0,0]),
               layout.get('arcade_inward',[0,1,0]),args.project.resolve())for f in args.models]
    unit=dict(note='Unfiltered first triangle from each registered photograph. Clear openings may reach the pavement, interior soffit, rear wall or background; a clear depth greater than the outer masonry is required. Earlier missing balusters are held aside.',results=out)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temp=args.output.with_suffix('.tmp');temp.write_text(json.dumps(unit,ensure_ascii=False,indent=2)+'\n');temp.replace(args.output)
    for item in out:print(item['file'],item['passed'],item['total'])
if __name__=='__main__':main()
