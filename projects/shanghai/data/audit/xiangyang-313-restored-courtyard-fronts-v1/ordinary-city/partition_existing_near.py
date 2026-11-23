"""Split only the source 3304 group from its shared near tile, preserving typed mesh bytes."""
from copy import deepcopy
from pathlib import Path
import argparse, gzip, hashlib, json, math, struct

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--checks',type=Path,required=True)
p.add_argument('--baseline',type=Path,required=True)
p.add_argument('--project',type=Path,required=True)
p.add_argument('--id',default='xuhui-xiangyang-313-restored-courtyard-fronts')
args=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def encode(d):return (json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
checks=read(args.checks);base=read(args.baseline)
src=args.source.read_bytes()
assert sha(src)==checks['decoded_view_sha256'] and checks['baseline_compressed_sha256']==base['ordinary_near']['sha256']
jl=struct.unpack_from('<I',src,12)[0]
scene=json.loads(src[20:20+jl]);blob=bytearray(src[28+jl:])
assert not scene.get('images') and len(scene['buffers'])==1 and len(scene['scenes'])==1
assert set(scene['scenes'][0]['nodes'])==set(range(len(scene['nodes'])))
node_checks={(v['node'],v['primitive']):v for v in checks['parts']}
dimensions={'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}
widths={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
def choose(accessor_id,indices):
    a=scene['accessors'][accessor_id]
    v=scene['bufferViews'][a['bufferView']]
    assert not a.get('sparse') and v['buffer']==0
    width=widths[a['componentType']]*dimensions[a['type']]
    stride=v.get('byteStride',width)
    start=v.get('byteOffset',0)+a.get('byteOffset',0)
    payload=b''.join(blob[start+i*stride:start+i*stride+width]for i in indices)
    assert len(payload)==len(indices)*width and all(0<=i<a['count']for i in indices)
    blob.extend(b'\0'*(-len(blob)%4))
    pos=len(blob);blob.extend(payload)
    dest={k:deepcopy(v)for k,v in a.items()if k not in {'byteOffset','min','max','bufferView','count'}}
    dest.update(bufferView=len(scene['bufferViews']),count=len(indices))
    view={'buffer':0,'byteOffset':pos,'byteLength':len(payload)}
    if 'target'in v:view['target']=v['target']
    scene['bufferViews'].append(view);scene['accessors'].append(dest)
    return len(scene['accessors'])-1
nodes=[]; groups=[[],[]];counts=[0,0];draws=0
def root_child(which,node):
    groups[which].append(len(nodes));nodes.append(node)
def selected(part,which):
    total=part['total'];ids=part['target_element_ordinals']
    assert ids==sorted(set(ids)) and all(0<=i<total for i in ids)
    if which==0:return ids
    selected_set=set(ids);other=[i for i in range(total)if i not in selected_set]
    assert sha(b''.join(struct.pack('<I',i)for i in other))==part['retained_ordinals_u32le_sha256']
    return other
for n,original in enumerate(scene['nodes']):
    assert not set(original)-{'mesh','extensions','name'}
    mesh=scene['meshes'][original['mesh']]
    ext=original.get('extensions',{}).get('EXT_mesh_gpu_instancing')
    if ext:
        part=node_checks[n,None]
        for which in (0,1):
            keep=selected(part,which)
            if not keep:continue
            node=deepcopy(original)
            grouped=node['extensions']['EXT_mesh_gpu_instancing']
            grouped['attributes']={k:choose(a,keep)for k,a in ext['attributes'].items()}
            counts[which]+=len(keep)*part['triangles_per_element'];draws+=len(mesh['primitives']);root_child(which,node)
    else:
        for which in (0,1):
            prims=[]
            for prim_index,primitive in enumerate(mesh['primitives']):
                part=node_checks[n,prim_index]
                keep=selected(part,which)
                if not keep:continue
                prim=deepcopy(primitive);prim['indices']=choose(primitive['indices'],[v for i in keep for v in (3*i,3*i+1,3*i+2)])
                prims.append(prim);counts[which]+=len(keep)
            if prims:
                mesh_index=len(scene['meshes']);scene['meshes'].append(dict(mesh,primitives=prims))
                root_child(which,dict(original,mesh=mesh_index));draws+=len(prims)
key=base['feature_key'];macro=base['macro_id'];target=base['old_city_row']['localId'];name='city_target_'+args.id
tag={'macro_id':macro,'landmark_id':args.id,'local_ids':[target],'feature_keys':[key]}
roots=[]
for which,children in enumerate(groups):
    roots.append(len(nodes))
    nodes.append({'name':'city_preserved_neighbors'if which else name,'children':children,'extras':{'cityPreservedLocalIds':base['remain_near_local_ids']}if which else {'cityReplacement':tag}})
scene['nodes']=nodes;scene['scenes']=[{'nodes':roots}];scene['scene']=0
blob.extend(b'\0'*(-len(blob)%4));scene['buffers']=[{'byteLength':len(blob)}];metadata=json.dumps(scene,separators=(',',':')).encode();metadata+=b' '*(-len(metadata)%4)
raw=struct.pack('<4sII',b'glTF',2,28+len(metadata)+len(blob))+struct.pack('<I4s',len(metadata),b'JSON')+metadata+struct.pack('<I4s',len(blob),b'BIN\0')+blob
assert counts==[checks['target_expanded_triangles'],checks['retained_expanded_triangles']]
packed=gzip.compress(raw,mtime=0)
relative='assets/city-overrides-xiangyang-313/'+macro+'/'+Path(base['ordinary_near']['file']).name
out=args.project/relative;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(packed)
cmp=base['ordinary_near']
group={'name':name,'landmark_id':args.id,'local_ids':[target],'feature_keys':[key],'expandedTriangles':counts[0]}
model={'file':relative,'sha256':sha(packed),'size_bytes':len(packed),'content_encoding':'gzip','decoded_sha256':sha(raw),'decoded_size_bytes':len(raw),'expandedTriangles':sum(counts),'geometryBytes':max(len(blob)*2,cmp['geometryBytes']),'drawCalls':draws,'compression':{'type':'gzip of lossless decoded baseline buffer subsets','quantization':False}}
descriptor={'id':cmp['id'],'baseline_file':cmp['file'],'baseline_sha256':cmp['sha256'],'baseline_decoded_sha256':cmp['decoded_sha256'],'featureLocalIds':cmp['featureLocalIds'],'groups':[group],'model':model}
(args.project.parent/'near-descriptor.json').write_bytes(encode(descriptor))
print('target and retained triangle counts',counts,'compressed bytes',len(packed),'SHA',sha(packed))
