"""Check original photograph coordinates against the foremost actual labelled triangle of either authored mesh."""
from argparse import ArgumentParser
from pathlib import Path
import hashlib,json,math
import numpy as np
from photo_ray_mesh import ProjectedMesh,material_appearance
HERE=Path(__file__).absolute().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
labels={'disk':'sun/half disk','ray':'sun/radial facet','chevron':'crown/chevron','cap':'cornices/cap','sill':'cornices/name sill','lamp-west':'west lantern/','lamp-east':'lantern/','gate-west':'gate west/','gate-east':'gate east/','planter':'planter/','green-number':'west pier/green','flute':'plaque field/flute','tablet':'plaques/municipal','plaque':'plaques/lane'}
for num in range(1,5): labels[f'char{num}']=f'cast name/character {num} stroke'
for num in range(1,4): labels[f'white-digit-{num}']=f'address plate/white number {num}'

def matches(hit,feature):
    if hit is None:return False
    if feature.startswith('white-digit-'):return hit['part']==labels[feature]
    return hit['part'].startswith(labels[feature])

def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('model',type=Path)
    ap.add_argument('out',type=Path)
    ap.add_argument('--cameras',type=Path,default=HERE/'registered-views.json')
    ap.add_argument('--observations',type=Path,default=HERE/'independent-original-photo-pixels.json')
    args=ap.parse_args();src=read(args.observations)['sources'];cams=read(args.cameras)
    scene=ProjectedMesh(args.model,read(args.model.with_suffix('.geometry.json')))
    shifts=sorted([(x,y) for x in range(-12,13) for y in range(-12,13) if x*x+y*y<=144],key=lambda q:(q[0]*q[0]+q[1]*q[1],abs(q[0]),q))
    all_rows={}
    for station,table in src.items():
        scene.station(cams[station])
        ratio=np.array(cams[station]['size'])/table['native_size']
        measures=[]
        for point in table['observations']:
            name=point['feature'];uv=np.array(point['uv']);first=None;best=None
            for dx,dy in shifts:
                registered=(uv+[dx,dy]+.5)*ratio-.5
                hit=scene.hit(*registered)
                if dx==0 and dy==0:first=hit
                if matches(hit,name):
                    best={'offset_native_px':[dx,dy],'distance_px':round(math.hypot(dx,dy),3),'part':hit['part'],'material':hit['material']};break
            measures.append(dict(point,first=first,direct=bool(best and best['distance_px']==0),nearest_12px=best))
        all_rows[station]=measures
    summary={s:{'total':len(v),'direct':sum(row['direct'] for row in v),'within_4px':sum(x['nearest_12px'] is not None and x['nearest_12px']['distance_px']<=4 for x in v),'within_12px':sum(x['nearest_12px'] is not None for x in v)} for s,v in all_rows.items()}
    output={'model':scene.asset,'matrix_sha256':sha(args.cameras),'native_observations_sha256':sha(args.observations),'driver_sha256':sha(Path(__file__)),'ray_reader_sha256':sha(HERE/'photo_ray_mesh.py'),'summary':summary,'material_bindings':material_appearance(args.model),'stations':all_rows}
    args.out.parent.mkdir(exist_ok=True,parents=True)
    args.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(summary)
if __name__=='__main__':main()
