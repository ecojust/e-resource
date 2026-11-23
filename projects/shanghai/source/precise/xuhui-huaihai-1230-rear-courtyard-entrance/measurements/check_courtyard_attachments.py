"""Check each solid and reproject both outer guard frames at the recorded depth."""
from collections import Counter
from pathlib import Path
from math import dist
import hashlib,json,sys
import argparse,importlib.util
here=Path(__file__).resolve().parent
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--attachments',type=Path,default=here.parent/'source/attachments.py')
cli.add_argument('--balconies',type=Path,default=here.parent/'source/courtyard_balconies.py')
cli.add_argument('--calibration',type=Path,default=here/'registered-rear.json')
cli.add_argument('--observations',type=Path,default=here/'attachment-observations.json')
cli.add_argument('--out',type=Path,default=here/'attachment-check.json')
args=cli.parse_args()
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
attachments=load('checked_attachments',args.attachments)
balconies=load('checked_court_balconies',args.balconies)
PALETTE={**attachments.PALETTE,**balconies.PALETTE}
sys.path.insert(0,str(args.calibration.parent))
from register_court import Camera
data=json.loads(args.observations.read_bytes())
class Recorder:
    def __init__(self):self.rows=[];self.bounds=[];self.tris=0;self.objects=[]
    def add(self,pts,faces,mat,label):
        assert mat in PALETTE
        use=Counter();volume=0
        for i,j,k in faces:
            for e in [(i,j),(j,k),(k,i)]:use[e]+=1
            p,q,r=pts[i],pts[j],pts[k]
            volume += sum(p[d]*(q[(d+1)%3]*r[(d+2)%3]-q[(d+2)%3]*r[(d+1)%3]) for d in range(3))/6
        assert all(use[b,a]==n==1 for (a,b),n in use.items()) and volume>1e-10,(label,volume)
        self.objects.append((label,[[min(p[i]for p in pts),max(p[i]for p in pts)] for i in range(3)]));self.rows.append((label,len(faces),volume));self.bounds.extend(pts);self.tris+=len(faces)
camera=Camera('25',args.calibration);results=[]
for row in data['cages']:
    x0,z0,x1,z1=row['bounds_x0_z0_x1_z1'];y=row['front_y']
    corners=[(x0,y,z1),(x1,y,z1),(x1,y+.105,z0),(x0,y+.105,z0)]
    pix=[list(camera.pixel(q)) for q in corners]
    obs=row['front_pixels']
    results.append(dict(name=row['name'],picked=obs,projected=pix,errors_pixels=[round(dist(p,q),2)for p,q in zip(pix,obs)]))
runs={}
for year in (2013,2016):
    for lod in (False,True):
        b=Recorder();attachments.add_attachments(b,lod,period=year)
        runs[f'{year}_'+('far'if lod else 'near')]=dict(closed_editable_pieces=len(b.rows),triangles=b.tris,
                minimum_piece_volume=min(v[2]for v in b.rows),bounds=[[min(p[i]for p in b.bounds),max(p[i]for p in b.bounds)]for i in range(3)])
def extents(objects):
    return [[min(b[i][0]for _,b in objects),max(b[i][1]for _,b in objects)]for i in range(3)]
seams={}
for lod in (False,True):
    a=Recorder();g=Recorder();attachments.add_attachments(a,lod);balconies.add_balconies(g,lod)
    guard=[q for q in a.objects if 'east to balcony seam window guard' in q[0]]
    joins=[q for q in a.objects if 'guard seam return' in q[0]]
    grille=[q for q in g.objects if 'L1 later grille' in q[0]]
    screen=[q for q in g.objects if 'L1 later right screen' in q[0]]
    def touches(p,q):
        return all(min(x[1],y[1])-max(x[0],y[0])>0 for x,y in zip(p,q))
    overlap=[(l,r)for l,lb in guard for r,rb in grille+screen if touches(lb,rb)]
    joint_contacts=[(l,r)for l,lb in joins for r,rb in grille if touches(lb,rb)]
    assert not overlap and len(joins)==2 and joint_contacts
    seams['far'if lod else 'near']=dict(attachment_east_grid=extents(guard),balcony_lower_grille=extents(grille),
        balcony_right_screen=extents(screen),whole_grid_pairs_checked=len(guard)*(len(grille)+len(screen)),
        overlapping_grid_grid_or_grid_screen_pairs=len(overlap),two_short_returns=extents(joins),
        return_contacts_with_balcony_frame=joint_contacts,west_guard_max_x=max(box[0][1] for name,box in a.objects if 'west visible section window guard' in name))
report=dict(attachment_sha256=hashlib.sha256(args.attachments.read_bytes()).hexdigest(),balcony_sha256=hashlib.sha256(args.balconies.read_bytes()).hexdigest(),runs=runs,
            outward_oriented_closed_surfaces=True,observed_whole_frames=results,both_model_seam_checks=seams,
            datum='Photo frame-corner residuals describe the measured whole baskets. The two author modules split that east basket at X=4.10. All results retain the common ±7% door-based scale and ±0.18 m courtyard datum.')
args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(runs,seams)
