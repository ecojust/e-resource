"""Rebuild both editable sash meshes and sample the three-dimensional glazing and its photographic position."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import sys
import numpy as np

source=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('output',type=Path)
parser.add_argument('--whole',nargs='+',type=Path,help='Recheck the same rays in decoded whole-building GLBs.')
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(source/'source'))
sys.path.insert(0,str(source.parents[2]/'source/precise/hongkou-general-post-office/source/common'))
import guiren_window_sashes as windows
from photo_architecture import Builder

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def triangles(path):
    raw=path.read_bytes()
    assert struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw))
    size,typ=struct.unpack_from('<I4s',raw,12)
    assert typ==b'JSON'
    doc=json.loads(raw[20:20+size]);buf=memoryview(raw)[28+size:]
    assert len(doc['nodes'])==1 and not set(doc['nodes'][0]).intersection(('matrix','translation','rotation','scale'))
    def access(idx):
        a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']]
        dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        return np.ndarray((a['count'],n),dt,buf,v.get('byteOffset',0)+a.get('byteOffset',0),(v.get('byteStride',n*dt.itemsize),dt.itemsize))
    mats=[v['name'] for v in doc['materials']];parts=[];ids=[];uv={}
    for prim in doc['meshes'][0]['primitives']:
        xyz=access(prim['attributes']['POSITION']);index=access(prim['indices']).ravel().reshape(-1,3)
        t=xyz[index][:,:,[0,2,1]].copy();t[:,:,1]*=-1
        parts.extend(t);ids.extend([prim['material']]*len(index));mat=mats[prim['material']]
        if mat in (windows.DARK,windows.FROST,windows.BLUE):
            data=access(prim['attributes']['TEXCOORD_0'])
            assert len(data)==len(xyz) and np.isfinite(data).all()
            uv[mat]=len(data)
    assert len(uv)==3
    return np.array(parts),np.array(ids),mats,uv

def ray(x,z,tri,ids,mats,origin=-2.):
    mask=(tri[:,:,0].min(axis=1)<=x)&(tri[:,:,0].max(axis=1)>=x)&(tri[:,:,2].min(axis=1)<=z)&(tri[:,:,2].max(axis=1)>=z)
    a,b,c=tri[mask].transpose(1,0,2);m=ids[mask];ab=b-a;ac=c-a
    det=ab[:,0]*ac[:,2]-ab[:,2]*ac[:,0];v=abs(det)>1e-10
    a,ab,ac,det,m=a[v],ab[v],ac[v],det[v],m[v]
    u=((x-a[:,0])*ac[:,2]-(z-a[:,2])*ac[:,0])/det
    v=((z-a[:,2])*ab[:,0]-(x-a[:,0])*ab[:,2])/det
    depth=a[:,1]+u*ab[:,1]+v*ac[:,1];hit=(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(depth>origin)
    return sorted((round(float(y),5),mats[k]) for y,k in zip(depth[hit],m[hit]))

def controls():
    tests=[]
    def test(kind,role,x,z,mat):
        tests.append((kind,role,x,z,mat))
    # Timber wraps the shared five masonry openings.
    for k,(l,r,b,t,y) in windows.STREET_OPENINGS.items():
        tz=6.48 if k=='right_upper' else t
        if k=='gate_upper':
            test(k,'outward leaf in front of left jamb',l+.027,b+.36*(tz-b),windows.DARK)
        else:
            test(k,'lower fixed jamb',l+.027,b+.36*(tz-b),windows.WOOD)
        test(k,'sill rail',l+.336*(r-l),b+.028,windows.WOOD)
    for row,(z,xx) in enumerate(((4.875,(-4.423,-4.228,-3.825,-3.623)),
                                  (5.073,(-4.423,-4.228,-3.825,-3.623)),
                                  (5.383,(-4.423,-4.228,-3.825,-3.623)),
                                  (5.742,(-4.423,-4.228,-3.825,-3.623)),
                                  (6.101,(-4.423,-4.228,-3.825,-3.623)))):
        for col,x in enumerate(xx):test('left_upper',f'photographic pane {row+1}.{col+1}',x,z,windows.DARK)
    for j,t in enumerate((.109,.230,.462,.575,.681,.786,.891)):
        test('left_lower',f'outer grille bar {j+1}',-4.31,1.12+t*1.7,windows.GUARD)
    for x in (-4.26,-3.74):
        for z in (1.416,2.021):test('left_lower','recessed lower glass',x,z,windows.FROST)
    for z in (5.41,5.82,6.16,6.55):
        for x in (.223,.505):test('gate_upper','eight panes on closed right leaf',x,z,windows.BLUE)
        for x in (-.547,-.715):test('gate_upper','eight panes on outward leaf',x,z,windows.DARK)
    for x in (-.364,-.145,-.035):test('gate_upper','through opened casement',x,5.97,None)
    for j,x in enumerate((3.37,3.76,4.14,4.54,4.92,5.32)):
        for i,z in enumerate((5.135,5.51,5.84,6.219)):
            test('right_upper',f'six tall sashes: pane {j+1}.{i+1}',x,z,windows.BLUE)
    for j,x in enumerate((2.66,2.98,3.37,3.76,4.14,4.54,4.92,5.32,5.74,6.11)):
        test('right_upper',f'toplight {j+1}',x,6.765,windows.DARK)
    for x in (2.79,6.04):test('right_upper','opaque rendered side panel outside glazing',x,5.65,None)
    for j,x in enumerate((3.832,4.177,4.583,5.013)):
        for z in (1.976,2.364,2.791):test('right_lower',f'lower street window {j+1}',x,z,windows.FROST)
    for j,x in enumerate((3.786,4.122,4.557,4.997)):
        # The recessed vertical iron is inside the sash rather than on its street side.
        test('right_lower',f'pale inner guard {j+1}',x,2.324,windows.LIGHT_GUARD)
    return tests

def check_export(p,whole=False):
    tri,ids,mats,uv=triangles(p);results=[];issues=[]
    for k,role,x,z,expected in controls():
        hits=ray(x,z,tri,ids,mats);first=hits[0] if hits else None
        if expected is None:
            good=first is None or whole and (not first[1].startswith('Guiren windows') and (first[0]>.28 if k=='gate_upper' else first[0]<-.62))
        else:good=bool(first and first[1]==expected)
        row=dict(group=k,role=role,x=round(x,5),z=round(z,5),expected=expected,actual=first,passed=good)
        if not good:issues.append(row)
        results.append(row)
    return dict(file=p.name,sha256=sha(p),triangles=len(tri),glass_uvs=uv,tests=len(results),issues=issues,rays=results)

def inspect(builder):
    boxes=0;tris=0;volumes=[]
    for p in builder.parts:
        v=np.array(p['vertices']);faces=np.array(p['triangles']);uv=np.array(p['texcoords'])
        assert len(v)==len(uv) and np.isfinite(uv).all()
        assert len(v)%8==0 and len(faces)==len(v)//8*12
        for j in range(len(v)//8):
            ids=faces[j*12:j*12+12]-8*j
            assert set(ids.ravel())==set(range(8))
            edge=ids[:,[[0,1],[1,2],[2,0]]].reshape(-1,2)
            counts=np.unique(np.sort(edge,axis=1),axis=0,return_counts=True)[1]
            assert (counts==2).all()
            vv=v[j*8:j*8+8];a,b,c=(vv-vv.mean(axis=0))[ids].transpose(1,0,2)
            vol=float(np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6)
            assert vol>0
            volumes.append(vol);boxes+=1
        tris+=len(faces)
    return dict(closed_solid_count=boxes,source_triangles=tris,editable_groups=len(builder.parts),volume_range_m3=[min(volumes),max(volumes)])

def photo_report():
    d=json.loads((source/'measurements/window-photo-observations.json').read_bytes())
    e=d['windows']['gate_upper'];P=np.array(e['xyz_to_image']);left,right,bottom,top,_=windows.STREET_OPENINGS['gate_upper']
    span=right-left;h=top-bottom;l=left+.14*span;w=.381*span;m=l+w;r=m+w
    lo=bottom+.064*h;hi=top-.061*h;ang=np.deg2rad(124);y=.13
    points=np.array([[l+w*np.cos(ang),y-w*np.sin(ang),hi],[l,y,hi],[l,y,lo],[l+w*np.cos(ang),y-w*np.sin(ang),lo],[m,y,hi],[r,y,hi],[r,y,lo],[m,y,lo]])
    pix=np.c_[points,np.ones(8)]@P.T;pix=pix[:,:2]/pix[:,2:]
    obs=np.array(e['left_open_leaf']['quad']+e['right_closed_leaf']['quad'])
    err=np.linalg.norm(pix-obs,axis=1)
    assert err.max()<17
    details={}
    for kind in ('left_upper','left_lower','right_upper','right_lower'):
        row=d['windows'][kind];P=np.array(row['xyz_to_image']);l,r,b,t,y=windows.STREET_OPENINGS[kind]
        if kind=='right_upper':t=6.48
        target=np.array(row['six_sash_frame' if kind=='right_upper' else 'fixed_frame']['quad'])
        world=np.array([[l,y,t],[r,y,t],[r,y,b],[l,y,b]])
        dh=np.c_[world,np.ones(4)]@P.T;proj=dh[:,:2]/dh[:,2:]
        details[kind]={'world_corners':world.tolist(),'observed':target.tolist(),'predicted_px':proj.round(2).tolist(),'residual_px':np.linalg.norm(proj-target,axis=1).round(2).tolist(),'occlusion':row['six_sash_frame' if kind=='right_upper' else 'fixed_frame']['partial']}
    return dict(central_opening=dict(original_observed=obs.tolist(),model_projected=pix.round(2).tolist(),residual_px=err.round(2).tolist(),rms_euclidean_px=round(float(np.sqrt(np.mean(err**2))),2)),adjacent_openings=details)

if args.whole:
    reports=[check_export(p,True) for p in args.whole]
    name='whole-building-sash-checks.json'
else:
    reports=[]
    for flag in (False,True):
        build=Builder(windows.PALETTE);windows.add_windows(build,flag);check=inspect(build)
        p=args.output/('sashes-lod.glb' if flag else 'sashes-full.glb');build.save(p)
        report=check_export(p);report.update(check);reports.append(report)
    name='editable-sash-checks.json'
result=dict(photo_check=photo_report(),exports=reports)
(args.output/name).write_text(json.dumps(result,indent=1)+'\n')
for row in reports:
    print(row['file'],row['tests'],len(row['issues']),[(v['role'],v['x'],v['actual']) for v in row['issues']])
if any(row['issues'] for row in reports):raise SystemExit(1)
