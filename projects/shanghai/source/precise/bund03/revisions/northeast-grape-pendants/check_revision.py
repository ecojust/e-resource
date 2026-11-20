"""Compare all original Bund 3 triangles, texture state and both entrance reliefs in three delivered variants."""
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
STONE='Bund 3 carved fruit limestone'
BAND='Bund 3 recessed ribbon limestone'
SAMPLES=[('top fixing',0,4.68,STONE),('left curled stem bud',-.367,4.45,STONE),
         ('right curled stem bud',.367,4.45,STONE),('top berry',.01,4.31,STONE),
         ('first sloping ribbon',.026,4.187,BAND),('middle exposed berry',-.01,4.04,STONE),
         ('second sloping ribbon',-.08,3.884,BAND),('low fruit',.035,3.69,STONE),
         ('pointed bottom leaf',.002,3.46,STONE)]

def main():
    ap=argparse.ArgumentParser()
    for k in ('prior','revised','decoded','helper','report'):ap.add_argument(k,type=Path)
    args=ap.parse_args();math=runpy.run_path(str(args.helper))
    inp=json.loads((SOURCE/'geometry-input.json').read_bytes());start,end=np.asarray(inp['chamfer_ends_east_north_m'])
    tangent=(end-start)/np.linalg.norm(end-start);outward=np.array([tangent[1],-tangent[0]])
    center=(start+end)/2
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
        assert current.get('images',[])==previous.get('images',[])==[]
        p1=prior if role=='raw' else args.decoded/'prior'/(role+'.glb')
        p2=new if role=='raw' else args.decoded/'output'/(role+'.glb')
        original,om,labels,_=math['load_triangles'](p1);revised,rm,rl,_=math['load_triangles'](p2)
        assert np.array_equal(original,revised[:len(original)]) and np.array_equal(om,rm[:len(om)]) and rl[:len(labels)]==labels
        assert np.array_equal(original.min((0,1)),revised.min((0,1))) and np.array_equal(original.max((0,1)),revised.max((0,1)))
        rel=revised[:,:,:2]-center;xyz=np.stack((rel@tangent,revised[:,:,2],rel@outward),axis=2)
        append=xyz[len(original):]
        assert .005<append[:,:,2].min()<.04 and .26<append[:,:,2].max()<.34
        assert 3.40<append[:,:,1].min()<3.45 and 4.71<append[:,:,1].max()<4.75
        assert (np.abs(append[:,:,0])>2.17).all() and (np.abs(append[:,:,0])<3.06).all()
        all_probes=[]
        for sign in (-1,1):
            u=sign*inp['distance_from_chamfer_axis_m'];mask=(xyz[:,:,0].max(1)>u-.44)&(xyz[:,:,0].min(1)<u+.44)&(xyz[:,:,1].max(1)>3.35)&(xyz[:,:,1].min(1)<4.79)&(xyz[:,:,2].max(1)>-.30)
            origxyz=xyz[:len(original)][mask[:len(original)]];origmat=om[mask[:len(original)]];sub=xyz[mask];submat=rm[mask]
            for label,x,z,expected in SAMPLES:
                ray=(np.array([u+x,z,1.]),np.array([0.,0.,-1.]))
                b,db,_=math['first_hit'](origxyz,*ray);a,da,_=math['first_hit'](sub,*ray)
                assert np.isfinite(db) and np.isfinite(da) and db-da>.018,(role,sign,label,db,da)
                assert rl[submat[a]]==expected,(role,sign,label,rl[submat[a]],expected)
                all_probes.append({'part':label,'jamb_side':sign,'lateral_from_chamfer_axis_m':round(u+x,3),'height_m':z,'old_material':labels[origmat[b]],'new_material':rl[submat[a]],'original_outward_m':round(1-db,5),'revised_outward_m':round(1-da,5)})
        results[role]={'old_triangles':len(original),'unchanged_triangles_in_order':len(original),'total_scene_triangles':len(revised),'added_triangles':len(revised)-len(original),'all_original_materials_and_bounds_unchanged':True,'original_binary_payload_sha256':sha256(old).hexdigest(),'embedded_images':[],'sha256':sha256(new.read_bytes()).hexdigest(),'bytes':new.stat().st_size,'probes':all_probes}
    args.report.write_text(json.dumps({'variants':results,'reader_sha256':sha256(args.helper.read_bytes()).hexdigest(),'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
    print({k:r['total_scene_triangles']for k,r in results.items()})
if __name__=='__main__':main()
