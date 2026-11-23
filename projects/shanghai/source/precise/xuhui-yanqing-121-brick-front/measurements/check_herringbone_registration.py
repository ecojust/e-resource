"""Compare emitted UVs with the joints around individual raised herringbone bricks."""
import argparse
from pathlib import Path
import json
import numpy as np
from PIL import Image
from io import BytesIO
from check_brick_uv import glb,read_accessor

PERIOD=.64*np.sqrt(2.)

def joint_distance(x,z):
    u,v=(x+z)/(.04*np.sqrt(2.)),(x-z)/(.04*np.sqrt(2.))
    i,j=np.floor(u),np.floor(v);phase=(i+j)%8;horizontal=phase<4
    fu,fv=u-i,v-j
    long=np.where(horizontal,phase+fu,phase-4+fv)
    short=np.where(horizontal,fv,fu)
    return .04*np.minimum(np.minimum(long,4-long),np.minimum(short,1-short))


def check(path):
    doc,blob,sha=glb(path);name='Yanqing 121 | herringbone spandrel'
    p=next(p for p in doc['meshes'][0]['primitives'] if doc['materials'][p['material']]['name']==name)
    attrs=p['attributes'];idx=read_accessor(doc,blob,p['indices']).reshape(-1,3)
    vertices=read_accessor(doc,blob,attrs['POSITION']).astype(float);xyz=(vertices[:,[0,2,1]]*[1,-1,1])[idx]
    uv=read_accessor(doc,blob,attrs['TEXCOORD_0']).astype(float)[idx]
    e=xyz[:,1:]-xyz[:,:1];norm=np.cross(e[:,0],e[:,1]);norm/=np.linalg.norm(norm,axis=1)[:,None]
    # The visible raised tile faces sit 16.8 to 18.0 mm forward of the front datum.
    selected=(norm[:,1]<-.999)&(xyz[:,0,1]<-.0165)
    raised_count=int(selected.sum()); basis='front surfaces of raised clay units'
    if not raised_count:
        selected=(norm[:,1]<-.999)&(np.abs(xyz[:,0,1]+.014)<.0001)
        basis='flat LOD panel checked against the full-detail laying grid'
    tr,coords=xyz[selected],uv[selected]
    if not len(tr):raise ValueError('No front herringbone panel found')
    # Each triangulated face has the same sample count.
    rng=np.random.default_rng(1231);physical=[];mapped=[]
    for i in range(12):
        q=rng.random((len(tr),2));flip=q.sum(axis=1)>1;q[flip]=1-q[flip]
        weights=np.column_stack([1-q.sum(axis=1),q]);physical.append(np.einsum('ij,ijk->ik',weights,tr));mapped.append(np.einsum('ij,ijk->ik',weights,coords))
    xyz=np.concatenate(physical);uv=np.concatenate(mapped)
    edge=joint_distance(xyz[:,0],xyz[:,2]);texture=joint_distance(uv[:,0]*PERIOD,(1-uv[:,1])*PERIOD)
    rev=joint_distance(uv[:,0]*PERIOD,uv[:,1]*PERIOD);err=np.abs(texture-edge)
    # Also read the actual PNG buffer. Its light mortar is separated from the dark clay
    # by a midpoint luminance threshold, so this counts actual raster colour as well.
    m=doc['materials'][p['material']];tex=doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]
    view=doc['bufferViews'][doc['images'][tex['source']]['bufferView']];a=view.get('byteOffset',0)
    bitmap=np.array(Image.open(BytesIO(blob[a:a+view['byteLength']])).convert('RGB'));h,w=bitmap.shape[:2]
    pix=bitmap[np.floor((uv[:,1]%1)*h).astype(int)%h,np.floor((uv[:,0]%1)*w).astype(int)%w]
    core=edge>.004
    return dict(file=path.name,sha256=sha,basis=basis,raised_face_triangles=raised_count,sampled_triangles=int(selected.sum()),sample_count=len(edge),
                mean_joint_distance_error_mm=float(err.mean()*1000),max_joint_distance_error_mm=float(err.max()*1000),
                proportional_samples_within_2mm_texture_joint=float(np.mean(texture<.002)),
                comparison_if_texture_v_reversed_mean_error_mm=float(np.mean(np.abs(rev-edge))*1000),
                sample_points_clear_of_physical_joint_by_4mm=int(core.sum()),actual_png_mortar_on_these_core_points=int(np.sum((pix.mean(axis=1)>134)&core)),
                passed=bool(err.max()<.00001))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=check(a.mesh);a.out.write_text(json.dumps(r,indent=2)+'\n');print(r['sample_count'],r['mean_joint_distance_error_mm'],r['passed'])
