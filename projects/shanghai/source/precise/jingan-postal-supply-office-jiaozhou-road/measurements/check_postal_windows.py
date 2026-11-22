"""Check photographed window divisions in the assembled, decoded postal office model."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

HERE = Path(__file__).resolve().parent
FIXED = 'Postal office windows | painted fixed frame'
BAR = 'Postal office windows | dark glazing bars'
GREY = 'Postal office windows | grey-green glass'
SHADE = 'Postal office windows | shaded glass'
SKY = 'Postal office windows | sky-reflecting glass'


def read_mesh(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    size, chunk = struct.unpack_from('<I4s', raw, 12)
    assert chunk == b'JSON'
    doc = json.loads(raw[20:20+size])
    buf = memoryview(raw)[28+size:]
    node, = doc['nodes']
    assert not set(node).intersection(('matrix','rotation','translation','scale'))

    def accessor(i):
        item = doc['accessors'][i]
        view = doc['bufferViews'][item['bufferView']]
        dtype = np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[item['componentType']])
        width = {'SCALAR':1,'VEC2':2,'VEC3':3}[item['type']]
        return np.ndarray((item['count'],width), dtype, buf,
                          view.get('byteOffset',0)+item.get('byteOffset',0),
                          (view.get('byteStride',width*dtype.itemsize),dtype.itemsize))

    names = [v['name'] for v in doc['materials']]
    tris, ids, uv = [], [], {}
    for part in doc['meshes'][node['mesh']]['primitives']:
        verts = accessor(part['attributes']['POSITION'])
        face = accessor(part['indices']).ravel().reshape(-1,3)
        local = verts[face][:,:,[0,2,1]].copy()
        local[:,:,1] *= -1
        tris.append(local)
        ids.append(np.full(len(face), part['material'],np.int16))
        name=names[part['material']]
        if name in (GREY,SHADE,SKY):
            coords=accessor(part['attributes']['TEXCOORD_0'])
            assert len(coords)==len(verts) and np.isfinite(coords).all()
            assert np.ptp(coords,axis=0).min()>.05
            uv[name]=uv.get(name,0)+len(coords)
    assert len(uv)==3
    return np.concatenate(tris), np.concatenate(ids), names, uv, hashlib.sha256(raw).hexdigest()


def first_depths(projected, indices, names, u, z):
    a, ab, ac, inv, low, high = projected
    which = np.flatnonzero((low[:,0]<=u)&(high[:,0]>=u)&(low[:,2]<=z)&(high[:,2]>=z)&(inv!=0))
    r, s, t, f = a[which], ab[which], ac[which], inv[which]
    dx, dz = u-r[:,0], z-r[:,2]
    b = (dx*t[:,2]-dz*t[:,0])*f
    c = (dz*s[:,0]-dx*s[:,2])*f
    depth = r[:,1]+b*s[:,1]+c*t[:,1]
    hit = (b>=-1e-6)&(c>=-1e-6)&(b+c<=1+1e-6)
    return sorted((round(float(d),4), names[i]) for d,i in zip(depth[hit],indices[which[hit]]))


def project(tri):
    a,b,c=tri.transpose(1,0,2)
    ab,ac=b-a,c-a
    det=ab[:,0]*ac[:,2]-ab[:,2]*ac[:,0]
    inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-10)
    return a,ab,ac,inv,tri.min(axis=1),tri.max(axis=1)


def tests(op):
    l,r,b,t=map(op.__getitem__,('x0','x1','z0','z1'))
    width,height=r-l,t-b
    rim=min(.040,width*.059,height*.047)
    rail=min(.066,.033*height)
    divs={'single':[], 'narrow':[.46], 'wide':[1/3,2/3], 'wide-four':[.25,.50,.75]}[op['family']]
    transom=b+height*(.65 if op['family'] in ('single','narrow') else .64)
    y=op['glass_y']
    yield 'outer jamb',l+.5*rim,b+.432*height,FIXED,y
    yield 'head',l+.31*width,t-.5*rim,FIXED,y
    yield 'main transom',l+.29*width,transom,FIXED,y
    for is_upper in (False,True):
        title='upper' if is_upper else 'lower'
        bottom,top=(transom+.5*rail+.002,t-rim-.002) if is_upper else (b+rim+.002,transom-.5*rail-.002)
        left,right=l+rim+.002,r-rim-.002
        xx=[left,*[left+v*(right-left) for v in divs],right]
        rows=op.get('upper_rows' if is_upper else 'lower_rows',2 if is_upper else 4)
        zz=np.linspace(bottom,top,rows+1)
        finish=SKY if op['storey']==4 else SHADE if op['storey']==1 and not is_upper else GREY
        for i,(lower,upper) in enumerate(zip(zz,zz[1:])):
            for j,(x0,x1) in enumerate(zip(xx,xx[1:])):
                yield f'{title} pane {i+1}.{j+1}',(x0+x1)/2,(lower+upper)/2,finish,None
        for i,x in enumerate(xx[1:-1]):
            yield f'{title} stile {i+1}',x,(zz[0]+zz[1])/2,BAR,y+.014
        for i,z in enumerate(zz[1:-1]):
            yield f'{title} rail {i+1}',(xx[0]+xx[1])/2,z,BAR,y+.014


def closed_components(tri, ids, names):
    """Weld coincident shading and texture vertices, verify each solid independently."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    summary={}
    for mi,name in enumerate(names):
        if name not in (FIXED,BAR,SHADE,GREY,SKY): continue
        part=tri[ids==mi].astype(float)
        vertices,ix=np.unique(part.reshape(-1,3),axis=0,return_inverse=True)
        faces=ix.reshape(-1,3)
        edges=faces[:,[[0,1],[1,2],[2,0]]].reshape(-1,2)
        normalized=np.sort(edges,axis=1)
        distinct,inv,counts=np.unique(normalized,axis=0,return_inverse=True,return_counts=True)
        orientations=np.bincount(inv,weights=np.where(edges[:,0]<edges[:,1],1,-1))
        graph=coo_matrix((np.ones(len(distinct)),(distinct[:,0],distinct[:,1])),shape=(len(vertices),len(vertices)))
        groups,tid=connected_components(graph,directed=False)
        face_group=tid[faces[:,0]];centres=np.array([vertices[tid==k].mean(axis=0)for k in range(groups)])
        local=part-centres[face_group,None,:];a,b,c=local.transpose(1,0,2)
        volumes=np.bincount(face_group,weights=np.einsum('ij,ij->i',a,np.cross(b,c))/6,minlength=groups)
        summary[name]=dict(components=groups,faces=len(faces),edges=len(distinct),edges_with_wrong_incidence=int(sum(counts!=2)),
                           inconsistent_winding=int(sum(orientations!=0)),smallest_volume_m3=round(float(volumes.min()),8),
                           largest_volume_m3=round(float(volumes.max()),8),all_closed=bool(np.all(counts==2)and np.all(orientations==0)and np.all(volumes>0)))
    return summary


def photograph_landmarks():
    data=json.loads((HERE/'west-window-sash-photo-traces.json').read_bytes())
    checks=[]
    for view,record in data['observations'].items():
        for row in record['traces']:
            if 'jambs_x' not in row:continue
            l,r=row['jambs_x']
            if 'central_bar_x' in row and row['central_bar_x'] is not None:
                predicted=l+.46*(r-l)
                checks.append([view,row['member'],'interior vertical',row['central_bar_x'],round(predicted,2),round(row['central_bar_x']-predicted,2)])
            if 'transom_height_fraction_from_bottom' in row:
                head,bottom=row['head_y'],row['sill_y'];predicted=bottom-.65*(bottom-head)
                checks.append([view,row['member'],'strong horizontal',row['main_transom_y'],round(predicted,2),round(row['main_transom_y']-predicted,2)])
            if 'verticals_x' in row:
                for j,observed in enumerate(row['verticals_x']):
                    predicted=l+(r-l)*(j+1)/3;checks.append([view,row['member'],'broad stair light '+str(j+1),observed,round(predicted,2),round(observed-predicted,2)])
    upper=json.loads((HERE/'west-upper-photo-registration.json').read_bytes())['window_schedule']
    for view,l,r,observed in [('gate-three-mid-15',139,373,[199,254,313]),('measured-C3-2021',374,605,[424,483,539]),('measured-C4-jan2015',300,471,[348,391,435])]:
        for i,x in enumerate(observed):
            expected=l+(r-l)*(i+1)/4
            checks.append([view,'wide-four','broad stair light '+str(i+1),x,round(expected,2),round(x-expected,2)])
    end=json.loads((HERE/'south-window-section-pixels.json').read_bytes())['observations']
    families={q['id']:q['family'] for q in json.loads((HERE/'west-front-masonry.json').read_bytes())['south_windows']}
    for n,v in end.items():
        member=v['opening'];l,r=v['jambs_u']
        assert (families[member]=='single')==(len(v['stiles_u'])==0)
        for x in v['stiles_u']:
            expected=l+.46*(r-l)
            checks.append([n,member,'end window interior vertical',x,round(expected,2),round(x-expected,2)])
        top,sill=v['head_sill_v'];expected=sill-.65*(sill-top)
        checks.append([n,member,'strong transom',v['coarse_transom_v'],round(expected,2),round(v['coarse_transom_v']-expected,2)])
    assert upper['central-3']['family']=='wide-four'
    return {'method':'Within each independently read opening, compare the photographed stile or transom position to the fitted sash proportion. Units are original image pixels. The fitted comparison uses photographed jamb or head/sill endpoints; subject distance, occlusion and perspective are retained as measurement variation.',
            'columns':['image','field','member','observed_px','predicted_px','observed_minus_predicted_px'],'measurements':checks}


def inspect(path,windows,wall):
    tri,idx,names,uv,digest=read_mesh(path)
    west=project(tri)
    south=tri[:,:,[1,0,2]].copy()
    south[:,:,1]=wall['south_return_x_m']-south[:,:,1]
    side=project(south)
    records=[]
    for face,opens,cast in [('west',windows,west),('south',wall['south_windows'],side)]:
        for op in opens:
            for kind,u,z,expected,y in tests(op):
                hits=first_depths(cast,idx,names,u,z)
                match=next((d for d,m in hits if m==expected),None)
                first=hits[0] if hits else None
                delta=None if match is None else round(match-op['glass_y'],4)
                good=match is not None and (abs(match-y)<.003 if y is not None else min(abs(delta-.033),abs(delta-.054))<.003)
                if first and first[1].startswith('Postal office windows') and first[1]!=expected:good=False
                records.append([face,op['id'],kind,round(u,4),round(z,4),expected,delta,first,bool(good)])
    return {'file':path.name,'sha256':digest,'triangles':len(tri),'glass_uv_vertices':uv,
            'closed_window_components':closed_components(tri,idx,names),'tests':len(records),'passed':sum(r[-1] for r in records),'foreground_occlusions':sum(r[7] is not None and r[7][1]!=r[5] for r in records),'rays':records}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('meshes',nargs='+',type=Path)
    args=p.parse_args();windows=json.loads((HERE/'west-front-openings.json').read_bytes())['openings']
    wall=json.loads((HERE/'west-front-masonry.json').read_bytes())
    result=[inspect(f,windows,wall) for f in args.meshes]
    doc={'units':'metres','ray_columns':['facade','opening','feature','u','z','expected_material','intersection_behind_frame_m','first_hit_depth_and_material','passed'],'photo_reprojection':photograph_landmarks(),'exports':result}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n')
    for r in result:
        failed=[v for v in r['rays'] if not v[-1]]
        print(r['file'],r['passed'],r['tests'],r['foreground_occlusions'],failed[:2])
    raise SystemExit(0 if all(r['tests']==r['passed'] and all(v['all_closed'] for v in r['closed_window_components'].values()) for r in result) else 1)
