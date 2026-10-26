#!/usr/bin/env python3
"""Bind generated Float32 tile triangles to raw GLB, then measure real lap surfaces."""
from collections import Counter
import hashlib,json,re,struct
from pathlib import Path
import numpy as np
from build_model import Church

HERE=Path(__file__).resolve().parent


def tri_counter(a):
    a=a.astype('<f4').copy();a[a==0]=0
    def canonical(b):return min(b,b[12:]+b[:12],b[24:]+b[:24])
    return Counter(canonical(t.tobytes()) for t in a)


def raw_tiles(path):
    data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n]);b=data[28+n:];result=Counter()
    def ac(i):
        a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];w={'SCALAR':1,'VEC3':3}[a['type']]
        return np.frombuffer(b,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*w).reshape(-1,w)
    for p in g['meshes'][0]['primitives']:
        name=g['materials'][p['material']]['name']
        if name.startswith('tile '):result.update(tri_counter(ac(p['attributes']['POSITION'])[ac(p['indices']).ravel().reshape(-1,3)]))
    return result


def local_triangles(obj,part):
    v=np.asarray(part['vertices'],dtype='<f4').astype(float)
    origin=obj.f.center;delta=v-origin
    local=np.column_stack([delta@obj.f.t,-delta@obj.f.n,v[:,2]])
    return local[np.asarray(part['triangles'])]


def interpolate(tri,points):
    a=tri[:,0,:2];b=tri[:,1,:2];c=tri[:,2,:2]
    det=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1])
    dx=points[:,None,0]-c[None,:,0];dy=points[:,None,1]-c[None,:,1]
    aa=((b[:,1]-c[:,1])*dx+(c[:,0]-b[:,0])*dy)/det
    bb=((c[:,1]-a[:,1])*dx+(a[:,0]-c[:,0])*dy)/det
    cc=1-aa-bb;mask=(aa>=-1e-6)&(bb>=-1e-6)&(cc>=-1e-6)
    assert mask.any(1).all(),'Sample outside actual tile triangle'
    z=aa*tri[:,0,2]+bb*tri[:,1,2]+cc*tri[:,2,2]
    return np.where(mask,z,-np.inf).max(1)


def main():
    obj=Church();obj.roof_system();source=Counter();lookup={}
    for part in obj.b.parts:
        if part['material'].startswith('tile '):
            v=np.asarray(part['vertices'])[:,[0,2,1]]*[1,1,-1]
            source.update(tri_counter(v[np.asarray(part['triangles'])]))
        m=re.fullmatch(r'(.+)-tile-(\d+)-(\d+)-(\d+)',part['label'])
        if m:lookup[(m[1],int(m[2]),int(m[3]),int(m[4]))]=part
    raw=HERE/'output/hongkou-hongde-church-raw.glb';assert raw_tiles(raw)==source,'Actual raw tile triangle binding differs'
    all_top=[];all_bottom=[];pairs=0;failed=[]
    for (roof,side,row,col),part in lookup.items():
        other=lookup.get((roof,side,row+1,col))
        if other is None:continue
        # Top15 vertices form a3x5 grid. Physical lap interval is measured
        # from existing grids; test3 interior cross-camber strips at3lap stations.
        a=local_triangles(obj,part);b=local_triangles(obj,other)
        av=np.asarray(part['vertices'],dtype='<f4').astype(float)
        bv=np.asarray(other['vertices'],dtype='<f4').astype(float)
        def tolocal(v):
            d=v-obj.f.center;return np.column_stack([d@obj.f.t,-d@obj.f.n,v[:,2]])
        av,bv=tolocal(av),tolocal(bv)
        points=[]
        for k in [1,2,3]:
            # Inner tile ends at row2; outer tile begins at row0.
            inner_end=av[10+k,:2];outer_start=bv[k,:2]
            for t in [.2,.5,.8]:points.append(outer_start*(1-t)+inner_end*t)
        points=np.asarray(points)
        upper=interpolate(a[:16],points);lower=interpolate(b[:16],points)
        upper_bottom=interpolate(a[16:32],points)
        top=upper-lower;bottom=upper_bottom-lower
        all_top.extend(top.tolist());all_bottom.extend(bottom.tolist());pairs+=1
        if bottom.min()<=.001:failed.append({'roof':roof,'side':side,'row':row,'col':col,'minimum_clearance_m':float(bottom.min())})
    result={'schema':'hongde-actual-float32-tile-lap-audit-v8','passed':not failed,
            'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'actual_oriented_tile_triangle_multiset_exact':True,
            'bound_tile_triangles':sum(source.values()),'adjacent_pairs':pairs,'surface_samples':len(all_top),
            'top_vertical_gap_range_m':[min(all_top),max(all_top)],'inner_skin_clearance_range_m':[min(all_bottom),max(all_bottom)],
            'near_coplanar_pair_count':sum(x<=.001 for x in all_bottom),'failures':failed,
            'scope':'Actual emitted FLOAT32 triangles of the tile materials are matched exactly, then two triangle-interpolated surfaces are sampled at9 points per lap. No claim that all roof/nave wall intersections are covered.'}
    (HERE/'audit/tile-lap-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='failures'}));print('failed_examples',failed[:6])
    if failed:raise SystemExit(1)


if __name__=='__main__':main()
