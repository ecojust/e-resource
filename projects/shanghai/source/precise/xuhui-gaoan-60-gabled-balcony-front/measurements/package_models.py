"""Export both original meshes, verify manifold surfaces, then independently decode the public GLBs."""
import argparse,hashlib,json,os,runpy,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'source'
sys.path.insert(0,str(SOURCE))
import build_model as model
from package_architectural_model import glb_stats,check_pair
sys.path.insert(0,str(model.PROJECT/'source/precise/hongkou-gongyi-fang-975-987-sichuan-road/source'))
from asset_rights import retain_metadata
from verify_front import inspect,render,sha
Model=runpy.run_path(str(model.PROJECT/'source/precise/changning-hengchang-li-yuyuan-road-gatehouse/measurements/check_render_uv.py'))['Model']
import numpy as np

def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def run(out,models,audit,encoder):
    for p in (out,models,audit):p.mkdir(exist_ok=True,parents=True)
    reports={};assets={};rays=[]
    for lod,role,suffix in ((False,'full','web'),(True,'lod','lod')):
        b=model.build(lod);checks=[]
        for part in b.parts:
            xyz,ix=np.unique(np.asarray(part['vertices'],dtype='<f4'),axis=0,return_inverse=True)
            tri=ix[np.asarray(part['triangles'])];edges=np.concatenate((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]));codes=edges[:,0]*len(xyz)+edges[:,1]
            t=xyz[tri]-xyz[tri[0,0]];vol=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
            ok=len(np.unique(codes))==len(codes) and np.array_equal(np.sort(codes),np.sort(edges[:,1]*len(xyz)+edges[:,0])) and vol>0
            assert ok,(part['label'],vol)
            checks.append({'part':part['label'],'volume_width_units_cubed':vol,'triangles':len(t)})
        raw=out/(role+'-source.glb');b.save(raw,model.META)
        assert len(checks)==len(b.parts)
        dest=models/(model.SLUG+'-'+suffix+'.glb')
        subprocess.run([encoder,'-i',raw,'-o',dest,'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
        retain_metadata(dest,raw);decoded=out/('decoded-'+role+'.glb');surfaces=check_pair(raw,dest,decoded)
        reports[role]={'source':sha(raw),'packed':sha(dest),'decoded':sha(decoded),'solids':checks,'surfaces':surfaces}
        records=[Model(p)for p in (raw,dest,decoded)]
        try:
            orig,packed,unpacked=records
            texture_map=orig.textures(SOURCE)
            assert set(texture_map)=={model.RENDER,model.BRICK}
            assert all(r.textures(SOURCE)==texture_map and r.doc['extras']==model.META for r in records)
            surfaces=orig.surfaces(SOURCE)
            assert surfaces==unpacked.surfaces(SOURCE)
            for material in texture_map:assert surfaces[material]['triangles']==surfaces[material]['nondegenerate_texture_triangles']
            reports[role]['material_and_uv']=surfaces
            reports[role]['embedded_images']=texture_map
        finally:
            for item in records:item.data.close()
        data=glb_stats(dest);assets[role]={'file':dest.name,'sha256':sha(dest),'bytes':dest.stat().st_size,**data}
        if not lod:
            public_raw=models/(model.SLUG+'-raw.glb');shutil.copyfile(raw,public_raw)
            assets['raw']={'file':public_raw.name,'sha256':sha(public_raw),'bytes':public_raw.stat().st_size,**glb_stats(public_raw)}
            rays.append(inspect(public_raw));render(public_raw,audit/'gabled-balcony-front.jpg')
        rays.append(inspect(decoded))
    put(audit/'web-model-verification.json',reports);put(audit/'two-date-image-rays.json',rays)
    assert assets['raw']['triangles']==assets['full']['triangles']>assets['lod']['triangles']
    put(models/'manifest.json',{**model.META,'model_id':model.SLUG,'all_dimensions_estimated':True,'third_party_models_embedded':False,'assets':assets})
    print([(r['matched'],r['total']) for r in rays],flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('work',type=Path);parser.add_argument('models',type=Path);parser.add_argument('audit',type=Path);parser.add_argument('--gltfpack',default='gltfpack');a=parser.parse_args();run(a.work,a.models,a.audit,a.gltfpack)
