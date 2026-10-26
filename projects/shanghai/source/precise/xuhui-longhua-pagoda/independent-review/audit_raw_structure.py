#!/usr/bin/env python3
"""Small independent audit of an actual uncompressed photo_architecture raw GLB.

Uses the hash-bound .geometry.json part order to reconstruct serialized parts.
No generation, rendering, network, model rewriting or appearance acceptance.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

HERE=Path(__file__).resolve().parent

def need(ok,msg):
    if not ok: raise ValueError(msg)

def digest(data): return hashlib.sha256(data).hexdigest()

def audit(raw_path,geometry_path):
    data=raw_path.read_bytes(); bound=geometry_path.read_bytes(); report=json.loads(bound)
    need(len(data)<100_000_000,'Raw must be strictly below 100,000,000 bytes')
    need(struct.unpack_from('<4sII',data)==(b'glTF',2,len(data)),'Bad GLB header')
    chunks=[]; offset=12
    while offset<len(data):
        length,kind=struct.unpack_from('<II',data,offset); offset+=8
        need(offset+length<=len(data),'Chunk out of bounds')
        chunks.append((kind,data[offset:offset+length]));offset+=length
    need(len(chunks)==2 and chunks[0][0]==0x4e4f534a and chunks[1][0]==0x004e4942,'Expected JSON and one BIN')
    doc=json.loads(chunks[0][1]); binary=chunks[1][1]
    need(report['sha256']==digest(data) and report['bytes']==len(data),'Part manifest not bound to actual raw')
    need(len(doc['meshes'])==1 and len(doc['nodes'])==1 and doc['nodes'][0].get('mesh')==0,'Only helper raw schema supported')
    need(not any(k in doc['nodes'][0] for k in ('matrix','translation','rotation','scale')),'Unexpected transformed raw node')
    need(len(doc['buffers'])==1 and 'uri' not in doc['buffers'][0],'Raw must be embedded')
    need(not doc.get('images') and not doc.get('textures'),'Expected zero photographic textures; do not silently change scope')
    need(doc['asset'].get('copyright'),'Missing asset copyright')
    need(doc.get('extras',{}).get('id')=='xuhui-longhua-pagoda','Unexpected model identity')
    for field, filename in [('source_geometry_sha256','geometry-input.json'),('calibration_sha256','calibration.json')]:
        need(doc['extras'].get(field)==digest((HERE.parent/filename).read_bytes()),'Frozen source binding differs: '+filename)
    kinds={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
    widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
    def accessor(i):
        a=doc['accessors'][i];need('sparse' not in a,'Sparse raw unsupported')
        v=doc['bufferViews'][a['bufferView']];need(v.get('buffer',0)==0 and not v.get('extensions'),'Compressed/external accessor unsupported')
        dt=np.dtype(kinds[a['componentType']]); width=widths[a['type']]; count=a['count']
        step=v.get('byteStride',width*dt.itemsize);start=v.get('byteOffset',0)+a.get('byteOffset',0)
        need(count>=0 and step>=width*dt.itemsize and start+max(0,count-1)*step+width*dt.itemsize<=len(binary),'Accessor bounds invalid')
        return np.ndarray((count,width),dtype=dt,buffer=binary,offset=start,strides=(step,dt.itemsize))
    by_material=defaultdict(list)
    for item in report['part_summary']: by_material[item['material']].append(item)
    issues=[];part_count=0;triangle_count=0;max_normal_error=0.;min_double_area=float('inf');min_volume=float('inf');per_prefix=defaultdict(int)
    for primitive in doc['meshes'][0]['primitives']:
        need(primitive.get('mode',4)==4,'Nontriangle primitive')
        mat=doc['materials'][primitive['material']]['name'];need(mat in by_material,'No part list for material')
        x=accessor(primitive['attributes']['POSITION']).astype(np.float64)
        normals=accessor(primitive['attributes']['NORMAL']).astype(np.float64)
        indices=accessor(primitive['indices']).ravel()
        need(len(indices)%3==0 and (not len(indices) or indices.max()<len(x)),'Invalid triangles')
        tris=indices.reshape(-1,3);need(np.isfinite(x).all() and np.isfinite(normals).all(),'Nonfinite positions/normals')
        need(sum(p['triangles'] for p in by_material[mat])==len(tris),'Part triangle order/count does not match primitive')
        normal_lengths=np.linalg.norm(normals,axis=1);need(np.all(normal_lengths>0),'Zero normal')
        cross=np.cross(x[tris[:,1]]-x[tris[:,0]],x[tris[:,2]]-x[tris[:,0]]);areas=np.linalg.norm(cross,axis=1)
        need(np.all(areas>1e-12),'Serialized degenerate triangle')
        cross/=areas[:,None]
        # Check all three serialized flat normals rather than only first corner.
        dots=np.einsum('tj,tkj->tk',cross,normals[tris]/normal_lengths[tris,None])
        angles=np.degrees(np.arccos(np.clip(dots,-1,1)))
        max_normal_error=max(max_normal_error,float(angles.max())); min_double_area=min(min_double_area,float(areas.min()))
        need(angles.max()<.001,'Actual geometric normals disagree with serialized normals')
        cursor=0
        for item in by_material[mat]:
            count=item['triangles'];t=x[tris[cursor:cursor+count]];cursor+=count
            # Exact equality after Float32 serialization; no tolerance weld hides cracks.
            unique,inverse=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);weld=inverse.reshape(-1,3)
            directed=np.concatenate((weld[:,[0,1]],weld[:,[1,2]],weld[:,[2,0]]))
            sorted_edges=np.sort(directed,axis=1);_,ei,ec=np.unique(sorted_edges,axis=0,return_inverse=True,return_counts=True)
            signs=np.where(directed[:,0]<directed[:,1],1,-1);balances=np.bincount(ei,weights=signs,minlength=len(ec))
            bad_count=int(np.sum(ec!=2));bad_winding=int(np.sum(balances!=0))
            centered=t-unique.mean(axis=0); volume=float(np.einsum('ij,ij->i',centered[:,0],np.cross(centered[:,1],centered[:,2])).sum()/6)
            min_volume=min(min_volume,volume)
            if bad_count or bad_winding or volume<=0:
                if len(issues)<80: issues.append({'label':item['label'],'material':mat,'triangles':count,'non_two_edges':bad_count,'unpaired_winding_edges':bad_winding,'signed_volume_m3':volume})
            part_count+=1;triangle_count+=count;per_prefix[item['label'].split('/')[0]]+=1
    need(part_count==report['parts'] and triangle_count==report['triangles'],'Overall part/triangle count differs')
    return {'schema':'longhua-independent-actual-raw-structure-v1','structure_passed':not issues,
        'raw':{'file':str(raw_path),'bytes':len(data),'sha256':digest(data)},
        'part_manifest':{'file':str(geometry_path),'sha256':digest(bound)},
        'triangles':triangle_count,'parts':part_count,'part_prefix_counts':dict(per_prefix),
        'minimum_double_triangle_area_m2':min_double_area,'maximum_flat_normal_error_degrees':max_normal_error,
        'minimum_part_signed_volume_m3':min_volume,'first_at_most_80_part_failures':issues,
        'model_appearance_accepted':False,'browser_or_native_reviewed':False,
        'scope':'Actual Float32 triangles, all-corner geometric normals, exact-position per-part closed edge pairing/orientation/positive signed volume. Does not prove no self-intersections, no inter-part overlap, eave seam continuity between separate parts, real doors, roof-tile clearance, railing holes or photographic accuracy.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--geometry',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();dest=a.output.resolve()
    need(dest.is_relative_to(HERE) and not dest.exists(),'Output must be a new file inside this independent review directory')
    try:
        report=audit(a.raw.resolve(),(a.geometry or a.raw.with_suffix('.geometry.json')).resolve())
    except Exception as exc:
        report={'schema':'longhua-independent-actual-raw-structure-v1','structure_passed':False,'error':str(exc),'model_appearance_accepted':False}
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'report':str(dest),'structure_passed':report['structure_passed']}))
    raise SystemExit(0 if report['structure_passed'] else 1)

if __name__=='__main__':main()
