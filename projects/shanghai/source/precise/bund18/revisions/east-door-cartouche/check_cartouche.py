"""Independently verify the retained issued GLB attributes, carving removal and positive-depth stonework."""
from pathlib import Path
import argparse,json,struct,hashlib,runpy
import numpy as np
from build_cartouche import chunks,read_array
HERE=Path(__file__).resolve().parent; PROJECT=HERE.parents[4]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--prior',type=Path,required=True);p.add_argument('--revised',type=Path,required=True);p.add_argument('--decoded',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    load=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
    origin=np.array([26.971,7.718]);tangent=np.array([-2.380,29.878]);tangent/=np.linalg.norm(tangent);normal=tangent[::-1]*[-1,1];height_ratio=1.037
    allow=(.414,-.576,-.459,5.46,6.30)
    def basis(t):
        return np.stack([(t[:,:,:2]-origin)@tangent,(t[:,:,:2]-origin)@normal,t[:,:,2]/height_ratio],axis=2)
    def ray(tri,u,z):
        # First plane hit from the street along the inward normal, including all facade materials.
        u0,d0,z0=tri[:,0].T;u1,d1,z1=(tri[:,1]-tri[:,0]).T;u2,d2,z2=(tri[:,2]-tri[:,0]).T
        det=u1*z2-u2*z1;ok=np.abs(det)>1e-9
        aa=np.divide((u-u0)*z2-u2*(z-z0),det,out=np.zeros_like(det),where=ok);bb=np.divide(u1*(z-z0)-(u-u0)*z1,det,out=np.zeros_like(det),where=ok)
        ok&=(aa>=-1e-6)&(bb>=-1e-6)&(aa+bb<=1+1e-6)
        return float((d0+aa*d1+bb*d2)[ok].min())
    out={}
    tests=[('plain roundel center',0,5.835,-.727),('rounded rim',.311,5.835,-.744),('central tablet',.35,5.78,-.683),('left recessed horizontal panel',-.80,5.748,-.628),('right recessed horizontal panel',.80,5.748,-.628),('left panel frame',-1.19,5.748,-.662),('right panel frame',1.19,5.748,-.662),('left upper strip',-.8,6.045,-.619),('right upper strip',.8,6.045,-.619),('projecting central crown',0,6.265,-.716),('lower sill',1.48,5.432,-.696)]
    untouched=[('left small original door rosette',-1.43,4.48),('right small original door rosette',1.43,4.48),('existing cornice',1.54,5.27),('south column',-2.2,8.2),('street sill at north',6,4.8)]
    for role in ['raw','web','lod']:
        old=a.prior/(role+'.glb');new=a.revised/(role+'.glb');b0,raw0=chunks(old);b1,raw1=chunks(new)
        assert raw1[:len(raw0)]==raw0
        for section in ('materials','textures','samplers','images','asset'):assert b0.get(section)==b1.get(section)
        assert b1['accessors'][:len(b0['accessors'])]==b0['accessors'] and b1['bufferViews'][:len(b0['bufferViews'])]==b0['bufferViews']
        if role=='raw':d0=old;d1=new
        else:d0=a.decoded/(role+'-prior.glb');d1=a.decoded/(role+'-final.glb')
        D0,B0=chunks(d0);D1,B1=chunks(d1);retired=0;kept=0
        for i,mesh in enumerate(D0['meshes']):
            for j,part in enumerate(mesh['primitives']):
                target=D1['meshes'][i]['primitives'][j];idx=read_array(D0,B0,part['indices']).ravel().reshape(-1,3)
                result=read_array(D1,B1,target['indices']).ravel().reshape(-1,3)
                assert part['attributes']==target['attributes'] and part['material']==target['material']
                if target['indices']==part['indices']:
                    assert np.array_equal(idx,result);kept+=len(idx);continue
                pos=read_array(D0,B0,part['attributes']['POSITION']).astype('d')[:,[0,2,1]]*[1,-1,1]
                coords=basis(pos[idx]);u,d,h=coords.transpose(2,0,1)
                hits=(np.abs(u)<allow[0])&(d>allow[1])&(d<allow[2])&(h>allow[3])&(h<allow[4])
                assert np.array_equal(hits.any(1),hits.all(1));assert np.array_equal(idx[~hits.all(1)],result)
                retired+=int(hits.all(1).sum());kept+=len(result)
        assert retired=={'raw':1320,'web':1320,'lod':274}[role]
        ti0=load(d0)[0];ti1=load(d1)[0]
        assert np.max(np.abs(ti1.min((0,1))-ti0.min((0,1))))<.00001
        assert np.max(np.abs(ti1.max((0,1))-ti0.max((0,1))))<.00001
        orig=basis(ti0);rev=basis(ti1);witness=[]
        for name,u,z,expected in tests:
            val=ray(rev,u,z);prior=ray(orig,u,z);assert abs(val-expected)<.009,(role,name,val,expected)
            witness.append({'name':name,'facade_u_m':u,'height_m':z*height_ratio,'old_inward_m':prior,'new_inward_m':val,'expected_inward_m':expected})
        for name,u,z in untouched:
            v=ray(rev,u,z);oldv=ray(orig,u,z);assert abs(v-oldv)<1e-6
            witness.append({'name':name,'facade_u_m':u,'height_m':z*height_ratio,'old_inward_m':oldv,'new_inward_m':v,'unchanged':True})
        imgs=[]
        for im in b0['images']:
            v=b0['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);imgs.append(sha(raw0[start:start+v['byteLength']]))
        out[role]={'baseline_SHA256':sha(old.read_bytes()),'published_SHA256':sha(new.read_bytes()),'original_triangles':len(ti0),'kept_old_triangles':kept,'removed_old_triangles':retired,'new_triangles':len(ti1)-kept,'delivered_triangles':len(ti1),'original_buffer_prefix_bytes':len(raw0),'unchanged_packed_jpeg_sha256':imgs,'probes':witness}
    a.out.write_text(json.dumps({'script_sha256':sha(Path(__file__).read_bytes()),'revised_assets':out,'passed':True},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
