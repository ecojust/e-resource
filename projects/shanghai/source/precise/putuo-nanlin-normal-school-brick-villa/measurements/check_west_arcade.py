"""Read unfiltered first surfaces at the western blind arch in the earlier photograph."""
from pathlib import Path
from hashlib import sha256
import argparse,json,runpy,sys
import numpy as np

# Native independently read points on the photograph, including brick field either
# side of the ornament. The southwest corner plane is fixed by the end-pier width.
TARGETS = {
    'ring':[(445,361),(458,331),(471,315),(485,304),(502,302),(521,305),(534,326)],
    'key':[(487,300),(489,309)],
    'brick filling':[(486,354),(500,345),(511,340)],
    'cap':[(440,380),(539,350)],
    'carved shoulder':[(441,392),(543,363)],
    'brick belt':[(431,457),(535,435)]
}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('models',nargs='+',type=Path)
    ap.add_argument('--project',type=Path,default=Path.cwd())
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    m=Path(__file__).resolve().parent
    sys.path.insert(0,str(m.parent/'source'))
    from fabric import metric,LAYOUT
    s=json.loads((m/'arcade-photograph-registration.json').read_bytes())['views']['earlier-oblique']
    p=np.array(s['positive_inward_camera']['P_s_inward_z_fraction'])
    h=p[:,[1,2,3]].copy();h[:,2]-=.1225*p[:,0]
    width=LAYOUT['arcade_outer_width_m'];span=width/(1.+.245/7.);pitch=span/7.;storey=LAYOUT['arcade_storey_m']
    basis=np.array([[0,pitch,0,metric(119,452)[0]],[-pitch,0,0,width-(width-span)/2],[0,0,storey,0],[0,0,0,1]])
    eye=(basis@[*s['positive_inward_camera']['eye_local_scaled'],1])[:3]
    helper=runpy.run_path(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    groups={'ring':['Nanlin arcade | radial red brick','Nanlin arcade | dark fired face','Nanlin | lime joints'],
            'key':['Nanlin arcade | pale grey stone'],'brick filling':['Nanlin | grey facing brick'],
            'cap':['Nanlin arcade | dark fired face'],'carved shoulder':['Nanlin arcade | pale grey stone','Nanlin | warm carved stone'],
            'brick belt':['Nanlin | red stringcourse brick']}
    results=[]
    for mesh in args.models:
        scene=helper['SerialScene'](mesh);rows=[]
        for kind,uvs in TARGETS.items():
            for u,v in uvs:
                q=np.linalg.solve(h,[u,v,1]);d,z=q[:2]/q[2]
                target=(basis@[-.1225,d,z,1])[:3]
                hit=scene.ray(eye,target-eye,np.linalg.norm(target-eye)+25)
                rows.append({'source_uv':[u,v],'observation':kind,'actual':hit,
                             'matched':bool(hit and hit['material'] in groups[kind])})
        results.append({'file':mesh.name,'sha256':sha256(mesh.read_bytes()).hexdigest(),'rows':rows,
                        'total':len(rows),'matched':sum(r['matched'] for r in rows)})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'photo':s['file'],'results':results},ensure_ascii=False,indent=2)+'\n')
    for a in results:print(a['file'],a['matched'],a['total'])
if __name__=='__main__':main()
