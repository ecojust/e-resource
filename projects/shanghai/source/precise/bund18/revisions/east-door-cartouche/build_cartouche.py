"""Replace only the circular petal mesh; append fitted stone to three existing GLBs."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
import numpy as np
from stonework import STONE,world,local,is_old_rosette,stonework

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
HELPERS=PROJECT/'source/precise/bund17/revisions/street-wing-doors'

def chunks(file):
    b=file.read_bytes();n=struct.unpack_from('<I',b,12)[0]
    assert b[:4]==b'glTF' and len(b)==struct.unpack_from('<I',b,8)[0]
    return json.loads(b[20:20+n]),b[28+n:]

def save(file,doc,b):
    text=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();text+=b' '*((-len(text))%4)
    body=bytes(b)+b'\0'*((-len(b))%4)
    file.write_bytes(struct.pack('<III',0x46546c67,2,28+len(text)+len(body))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(body),0x004e4942)+body)

def read_array(doc,b,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']])
    n={'VEC3':3,'SCALAR':1}[a['type']]
    return np.ndarray((a['count'],n),dtype,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),
        strides=(v.get('byteStride',n*dtype.itemsize),dtype.itemsize))

def publish(prior,decoded,out,role):
    doc,old=chunks(prior);expanded,body=chunks(decoded)
    assert all(not(set(n)&{'matrix','rotation','scale','translation'}) for n in expanded['nodes'])
    data=bytearray(old);mat=next(i for i,m in enumerate(doc['materials'])if m['name']==STONE)
    def add(values,kind,component,target):
        values=np.ascontiguousarray(values,dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[component]);data.extend(b'\0'*((-len(data))%4))
        i=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':values.nbytes,'target':target});data.extend(values.tobytes())
        a={'bufferView':i,'componentType':component,'count':len(values),'type':kind}
        if kind=='VEC3':a.update(min=values.min(0).tolist(),max=values.max(0).tolist())
        n=len(doc['accessors']);doc['accessors'].append(a);return n
    removed=0;edits=[]
    for mesh_index,mesh in enumerate(expanded['meshes']):
        for part_index,part in enumerate(mesh['primitives']):
            if part['material']!=mat:continue
            pos=read_array(expanded,body,part['attributes']['POSITION'])
            idx=read_array(expanded,body,part['indices']).reshape(-1,3)
            e,h,s=pos.astype('d').T;match=is_old_rosette(*local(e,-s,h))[idx]
            selected=match.all(1)
            assert np.array_equal(selected,match.any(1)), 'A triangle crosses the isolated original carving'
            if not selected.any():continue
            n=int(selected.sum());removed+=n;new=idx[~selected].ravel()
            index=add(new,'SCALAR',expanded['accessors'][part['indices']]['componentType'],34963)
            doc['meshes'][mesh_index]['primitives'][part_index]['indices']=index
            edits.append({'mesh':mesh_index,'primitive':part_index,'removed':n})
    assert removed=={'raw':1320,'web':1320,'lod':274}[role],(role,removed)
    count=0;nodes=doc['scenes'][doc.get('scene',0)]['nodes']
    parts=stonework(role=='lod')
    delivery=parts
    if role!='raw':
        combined_points=[];combined_faces=[]
        for _,material,part_points,part_faces in parts:
            assert material==STONE
            offset=len(combined_points);combined_points.extend(part_points)
            combined_faces.extend(tuple(offset+i for i in face)for face in part_faces)
        delivery=[('East door cartouche',STONE,combined_points,combined_faces)]
    for name,material,points,faces in delivery:
        assert material==STONE
        enu=np.asarray([world(*p)for p in points]);vertices=enu[:,[0,2,1]]*[1,1,-1]
        tri=vertices[np.asarray(faces)];normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        sizes=np.linalg.norm(normals,axis=1);assert np.all(sizes>1e-10),name
        normal=(normals/sizes[:,None]).repeat(3,axis=0)
        geom={'attributes':{'POSITION':add(tri.reshape(-1,3),'VEC3',5126,34962),'NORMAL':add(normal,'VEC3',5126,34962)},'material':mat}
        mesh=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':[geom]});nodes.append(len(doc['nodes']));doc['nodes'].append({'name':name,'mesh':mesh})
        count+=len(faces)
    doc['buffers'][0]['byteLength']=len(data);save(out,doc,data)
    return {'prior_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'removed_triangles':removed,'added_triangles':count,'mesh_edits':edits,'author_parts':len(parts),'added_draw_primitives':len(delivery),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prior',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--work',type=Path,required=True);args=p.parse_args();args.out.mkdir(exist_ok=True,parents=True);args.work.mkdir(exist_ok=True,parents=True)
    register=json.loads((HERE/'baseline.json').read_bytes());report={}
    for role in ('raw','web','lod'):
        row=register['assets'][role];f=args.prior/row['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']
        decoded=f
        if role!='raw':
            decoded=args.work/(role+'-prior.glb');subprocess.run(['node',HELPERS/'decode_views.mjs',PROJECT/'vendor/meshopt_decoder.module.js',f,decoded],check=True)
        report[role]=publish(f,decoded,args.out/(role+'.glb'),role)
    (args.out/'generation.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
