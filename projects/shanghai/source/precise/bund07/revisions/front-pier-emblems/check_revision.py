"""Compare all Bund 7 triangles, photographic glazing and the open lotus emblems in three delivered variants."""
import argparse,json,runpy
from hashlib import sha256
from pathlib import Path
import numpy as np

SOURCE=Path(__file__).resolve().parent
DOORS=SOURCE.parents[2]/'bund17/revisions/street-wing-doors'
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('existing_glb',DOORS/'check_revision.py')
existing=module_from_spec(spec);spec.loader.exec_module(existing)
read_glb=existing.glb
FACE='Bund 7 satin-gilt lotus'
SAMPLES=[('top fold',0,.955,True),('left diamond strip',-.355,.58,True),
         ('right diamond strip',.355,.58,True),('outer left leaf',-.43,.30,True),
         ('outer right leaf',.43,.30,True),('bottom point',0,.05,True),
         ('central stem',0,.235,True),('diamond aperture',0,.60,False),
         ('left leaf aperture',-.267,.26,False),('right leaf aperture',.267,.26,False),
         ('masonry at left edge',-.538,.48,False),('masonry at right edge',.538,.48,False)]

def main():
    ap=argparse.ArgumentParser()
    for k in ('prior','revised','decoded','helper','report'):ap.add_argument(k,type=Path)
    args=ap.parse_args();math=runpy.run_path(str(args.helper))
    inp=json.loads((SOURCE/'geometry-input.json').read_bytes())
    tangent=np.asarray(inp['tangent_east_north']);outward=np.asarray(inp['outward_east_north']);center=np.asarray(inp['facade_origin_east_north_m'])
    baseline=json.loads((SOURCE/'baseline.json').read_bytes())['assets']
    results={}
    for role in ('raw','web','lod'):
        prior=args.prior/(role+'.glb');new=args.revised/(role+'.glb')
        assert sha256(prior.read_bytes()).hexdigest()==baseline[role]['sha256']
        previous,old=read_glb(prior);current,updated=read_glb(new)
        assert old==updated[:len(old)] and previous.keys()==current.keys()
        for key,v in previous.items():
            if key in ('meshes','materials','bufferViews','nodes','accessors'):
                assert current[key][:len(v)]==v and len(current[key])>len(v),key
            elif key=='buffers':assert current[key][1:]==v[1:]
            elif key=='scenes':
                assert current[key][0]['nodes'][:len(v[0]['nodes'])]==v[0]['nodes']
                assert len(current[key][0]['nodes'])==len(v[0]['nodes'])+2
            else:assert current[key]==v,key
        assert current.get('images',[])==previous.get('images',[])
        images=[]
        for im in previous.get('images',[]):
            v=previous['bufferViews'][im['bufferView']];off=v.get('byteOffset',0)
            payload=old[off:off+v['byteLength']]
            images.append({'mime':im['mimeType'],'bytes':len(payload),'sha256':sha256(payload).hexdigest()})
        assert len(images)==(0 if role=='lod' else 1),role
        if role=='raw':assert images[0]['sha256']=='4cce7f5272e949eff1f874a8f10a9c44f0e61085322cc1f2fb5174d802c7cfe9'
        p1=prior if role=='raw' else args.decoded/'prior'/(role+'.glb')
        p2=new if role=='raw' else args.decoded/'output'/(role+'.glb')
        original,om,labels,_=math['load_triangles'](p1);revised,rm,rl,_=math['load_triangles'](p2)
        assert np.array_equal(original,revised[:len(original)]) and np.array_equal(om,rm[:len(om)]) and rl[:len(labels)]==labels
        assert np.array_equal(original.min((0,1)),revised.min((0,1))) and np.array_equal(original.max((0,1)),revised.max((0,1)))
        rel=revised[:,:,:2]-center;xyz=np.stack((rel@tangent,revised[:,:,2],rel@outward),axis=2)
        append=xyz[len(original):]
        assert -.013<append[:,:,2].min()<-.007 and .251<append[:,:,2].max()<.257
        assert 1.80<append[:,:,1].min()<1.82 and 3.23<append[:,:,1].max()<3.25
        for tri in append:
            assert min(abs(tri[:,0].mean()-m)for m in inp['origin_of_each_pier_u_m'])<.56
        all_probes=[]
        for side,u in zip(('south','north'),inp['origin_of_each_pier_u_m']):
            group=(xyz[:,:,0].max(1)>u-.65)&(xyz[:,:,0].min(1)<u+.65)&(xyz[:,:,1].max(1)>1.72)&(xyz[:,:,1].min(1)<3.30)&(xyz[:,:,2].max(1)>-.5)&(xyz[:,:,2].min(1)<1.)
            revised_group=xyz[group];newm=rm[group]
            original_group=xyz[:len(original)][group[:len(original)]];oldm=om[group[:len(original)]]
            for label,rx,ry,metal in SAMPLES:
                x=u+rx*inp['width_m'];z=inp['bottom_m']+ry*inp['height_m'];pt=np.array([x,z,1.]);direction=np.array([0.,0.,-1.])
                hit,ds,_=math['first_hit'](revised_group,pt,direction);oh,os,_=math['first_hit'](original_group,pt,direction)
                assert np.isfinite(ds) and np.isfinite(os) and labels[oldm[oh]] in ('limestone','carved pale stone')
                if metal:
                    assert rl[newm[hit]]==FACE and os-ds>.068,(role,side,label,rl[newm[hit]],os-ds)
                else:
                    assert rl[newm[hit]]==labels[oldm[oh]] and abs(ds-os)<1e-6,(role,side,label)
                all_probes.append({'pier':side,'probe':label,'u_m':round(x,4),'height_m':round(z,4),'old':labels[oldm[oh]],'new':rl[newm[hit]],'old_outward_m':round(1-os,6),'new_outward_m':round(1-ds,6)})
        results[role]={'old_triangles':len(original),'unchanged_triangles_in_order':len(original),'total_scene_triangles':len(revised),'added_triangles':len(revised)-len(original),'all_original_materials_and_bounds_unchanged':True,'original_binary_payload_sha256':sha256(old).hexdigest(),'embedded_images':images,'sha256':sha256(new.read_bytes()).hexdigest(),'bytes':new.stat().st_size,'probes':all_probes}
    args.report.write_text(json.dumps({'variants':results,'reader_sha256':sha256(args.helper.read_bytes()).hexdigest(),'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
    print({k:r['total_scene_triangles']for k,r in results.items()})
if __name__=='__main__':main()
