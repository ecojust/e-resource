"""Reproject and ray-test the two high steel sashes from the winter street photographs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import numpy as np

HERE = Path(__file__).resolve().parent


def rays(image, geometry, uv):
    """Return a 3D ray for this parametrization of the same spherical street photo."""
    def camera(meta):
        yaw, elev = np.deg2rad([meta['az'],meta['pitch']])
        ca,sa,ce,se = np.cos(yaw),np.sin(yaw),np.cos(elev),np.sin(elev)
        axes=np.column_stack(([ca,-sa,0],[sa*se,ca*se,-ce],[sa*ce,ca*ce,se]))
        width,height=meta['width'],meta['height']
        f=width/(2*np.tan(np.deg2rad(meta['hfov']/2)))
        return axes,np.array([[f,0,width/2],[0,f,height/2],[0,0,1]])
    b0,k0=camera(image['base']); b1,k1=camera(image['detail'])
    h=k0@b0.T@b1@np.linalg.solve(k1,[*uv,1])
    c=np.array(geometry['C']); ray=np.array(geometry['R']).T@np.linalg.solve(geometry['K'],h/h[2])
    return c,ray


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('result',type=Path)
    args=parser.parse_args()
    controls=json.loads((HERE/'recessed-end-winter-sashes.json').read_bytes())
    cameras=json.loads((HERE/'december-street-geometry.json').read_bytes())['photos']
    Scene=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
    scene=Scene(args.mesh)
    hits=[]
    for key,photo in controls['images'].items():
        for name,uv,material in photo['probes']:
            c,d=rays(photo,cameras[key],uv)
            hit=scene.ray(c,d,75)
            hits.append(dict(station=key,feature=name,detail_uv=uv,expected=material,actual=hit,
                             passed=bool(hit and hit['material']==material)))
    result=dict(mesh=args.mesh.name,sha256=sha256(args.mesh.read_bytes()).hexdigest(),
                passed=sum(r['passed'] for r in hits),total=len(hits),hits=hits)
    args.result.parent.mkdir(exist_ok=True,parents=True)
    args.result.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['passed'],len(hits),[(r['station'],r['feature'],(r['actual'] or {}).get('material'))for r in hits if not r['passed']])

if __name__=='__main__':
    main()
