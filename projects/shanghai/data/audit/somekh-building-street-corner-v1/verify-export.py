"""Probe the delivered walls, porch, closed door and open sky above the drum in all LODs."""
from pathlib import Path
import argparse,hashlib,json,math,runpy,struct
import numpy as np
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/huangpu-somekh-building-street-corner/source'
READER=HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'
load=runpy.run_path(READER)['load_triangles']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def norm(v):return v/np.linalg.norm(v)

def probes():
    data=read(SOURCE/'south-front-metrics.json')['planes']
    r=read(SOURCE/'frontage-registration.json')
    g=[k['x_m']for k in data['ground']['axes']];u=[k['x_m']for k in data['body']['axes']]
    rows=[]
    def add(title,origin,aim,materials,near,far,front=None):
        rows.append((title,np.array(origin),norm(np.array(aim,dtype=float)),materials,near,far,front))
    for i,(x,upper_x)in enumerate(zip(g,u)):
        if i==4:continue
        for dx in (-.23,.23):
            add('ground bank window '+str(i+1),(x+dx,-7,2.43),(0,1,0),
                ['recessed blue grey glass'],7.25,7.36,[0,-1,0])
            for z in [7.86,11.86,15.89,20.10]:
                add('office glazing '+str(i+1),(upper_x+dx,-6,z),(0,1,0),
                    ['recessed blue grey glass'],7.35,7.43,[0,-1,0])
        add('window keystone '+str(i+1),(x,-5,5.11),(0,1,0),['warm granite'],4.70,4.87,[0,-1,0])
    c=np.array(r['southeast_circle_center_m']);radius=r['radius_m'];mid=-math.pi/2+math.radians(r['corner_sweep_deg'])/2
    radial=lambda a:np.array([math.cos(a),math.sin(a)])
    n=radial(mid);u_axis=radial(mid+math.pi/2)
    pt=lambda xy,z:np.r_[xy,z]
    for dx in (-.49,.49):
        for z in (1.71,2.42,3.50):
            add('recessed round porch door',pt(c+(radius+4)*n+dx*u_axis,z),pt(-n,0),
                ['recessed blue grey glass'],5.59,5.76,pt(n,0).tolist())
    for side in (-1,1):
        a=mid+side*math.radians(r['corner_sweep_deg'])*.247
        for z in (.92,2.20,3.47):
            add('freestanding corner column',pt(c+(radius+3)*radial(a),z),pt(-radial(a),0),
                ['warm granite'],3.00,3.15,pt(radial(a),0).tolist())
    for s in (-.35,0,.35):
        add('visible open sky within drum',pt(c+s*u_axis,28.5),(0,0,-1),['grey granite plinth'],6.0,6.16,[0,0,1])
    for i in range(6):
        a=mid+i*math.pi/3
        for z in [23.64,23.86,24.00]:
            # Leftovers at >4.2 metres are permitted outside this local cylinder.
            add('daylight through drum arch',pt(c+.58*radial(a),z),pt(radial(a),0),[],radius+.5,None)
        for z in [24.81,25.15]:
            add('opaque drum above arch',pt(c+(radius+2)*radial(a),z),pt(-radial(a),0),['warm grey washed aggregate'],2.18,2.27,pt(radial(a),0).tolist())
    return rows

def first(tri,edge1,edge2,lo,hi,o,d):
    # Cull by per-triangle AABBs before Möller–Trumbore. This also keeps the
    # independent check small enough to run while the city map is being reviewed.
    parallel=np.abs(d)<1e-9;ok=np.ones(len(tri),bool)
    if parallel.any():ok&=((lo[:,parallel]<=o[parallel]+1e-8)&(hi[:,parallel]>=o[parallel]-1e-8)).all(axis=1)
    if not ok.any():return None
    ids=np.flatnonzero(ok);l=(lo[ids][:,~parallel]-o[~parallel])/d[~parallel];h=(hi[ids][:,~parallel]-o[~parallel])/d[~parallel]
    near=np.minimum(l,h).max(axis=1);far=np.maximum(l,h).min(axis=1);ids=ids[(far>=np.maximum(near,0)-1e-8)]
    if not len(ids):return None
    e,f=edge1[ids],edge2[ids];cross=np.cross(d,f);det=(e*cross).sum(axis=1);inv=np.divide(1.,det,out=np.zeros_like(det),where=np.abs(det)>1e-9)
    diff=o-tri[ids,0];u=inv*(diff*cross).sum(axis=1);q=np.cross(diff,e);v=inv*(q@d);t=inv*(q*f).sum(axis=1)
    valid=(np.abs(det)>1e-9)&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>1e-5)
    if not valid.any():return None
    t[~valid]=np.inf;j=t.argmin();return int(ids[j]),float(t[j])

def verify(path):
    tri,indices,names,info=load(path);e=tri[:,1]-tri[:,0];f=tri[:,2]-tri[:,0];lo=tri.min(axis=1);hi=tri.max(axis=1)
    out=[]
    for label,o,d,ms,nr,fr,front in probes():
        hit=first(tri,e,f,lo,hi,o,d);dist=hit[1]if hit else None;m=names[indices[hit[0]]]if hit else None
        alignment=float(norm(np.cross(e[hit[0]],f[hit[0]]))@front)if hit and front is not None else None
        ok=(hit is None or dist>=nr)if fr is None else bool(hit and nr<=dist<=fr and m in ms and (alignment is None or alignment>.75))
        out.append(dict(feature=label,origin=o.tolist(),ray=d.tolist(),material=m,distance=dist,expected_materials=ms,expected_distance_m=[nr,fr],
                        expected_normal=front,normal_alignment=alignment,passed=ok))
    with path.open('rb')as fp:fp.seek(12);size,_=struct.unpack('<II',fp.read(8));doc=json.loads(fp.read(size));length,chunk=struct.unpack('<II',fp.read(8));binary=fp.read(length)
    tex=next(v for v in doc['materials']if v['name']=='warm grey washed aggregate')['pbrMetallicRoughness']['baseColorTexture']['index']
    encoded=doc['textures'][tex];sampler=doc.get('samplers',[{}])[encoded.get('sampler',0)]
    assert sampler.get('wrapS',10497)==sampler.get('wrapT',10497)==10497
    view=doc['bufferViews'][doc['images'][encoded['source']]['bufferView']];start=view.get('byteOffset',0)
    assert hashlib.sha256(binary[start:start+view['byteLength']]).hexdigest()==sha(SOURCE/'washed-aggregate.png')
    return dict(mesh=info,triangles=len(tri),texture_sha256=sha(SOURCE/'washed-aggregate.png'),repeat_sampler=True,checks=out,passed=all(row['passed']for row in out))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('glbs',type=Path,nargs=3);a=p.parse_args()
    rows=[verify(f)for f in a.glbs]
    a.out.write_text(json.dumps({'reader_sha256':sha(READER),'variants':rows,'passed':all(r['passed']for r in rows)},indent=2)+'\n')
    for r in rows:
        bad=[(v['feature'],v['origin'],v['distance'],v['material'])for v in r['checks']if not v['passed']]
        print(r['mesh']['file'],len(r['checks']),len(bad),bad[:8])
    raise SystemExit(not all(r['passed']for r in rows))
