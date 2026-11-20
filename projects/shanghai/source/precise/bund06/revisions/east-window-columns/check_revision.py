"""Check the complete old/revised GLBs independently of the jamb generator."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import runpy
import struct
import numpy as np


def chunks(path):
    data=path.read_bytes()
    size=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+size]),data[28+size:]


def main():
    ap=argparse.ArgumentParser()
    for key in ('source','prior','revised','decoded','helper','report'):
        ap.add_argument(key,type=Path)
    args=ap.parse_args()
    project=runpy.run_path(str(args.helper))
    frame=json.loads((args.source/'geometry-input.json').read_bytes())
    a,b=np.asarray(frame['polygon_local_east_north'])[9:11]
    axis=(b-a)/np.linalg.norm(b-a);normal=np.array([axis[1],-axis[0]])
    origins=(a+b)/2;basis=np.stack((axis,normal),axis=1)
    def facade_triangles(world):
        triangles=world.copy()
        triangles[:,:,:2]=(world[:,:,:2]-origins)@basis
        return triangles
    def depth(tri,u,z):
        _,travel,_=project['first_hit'](tri,[u,.56,z],[0,-1,0])
        return round(float(.56-travel),5)
    reference_hash='9c808a3c0442d86c44797567adea4b8457f258b1eb7b22d21df6afb0eb75066b'
    by_role={}
    for role in ('raw','web','lod'):
        before_file=args.prior/(role+'.glb')
        after_file=args.revised/(role+'.glb')
        before,old=chunks(before_file);after,new=chunks(after_file)
        assert new[:len(old)]==old
        assert before.keys()==after.keys()
        extra_arrays={'nodes':6,'accessors':8,'bufferViews':8,'meshes':6}
        for key,value in before.items():
            if key in extra_arrays:
                assert after[key][:len(value)]==value and len(after[key])-len(value)==extra_arrays[key]
            elif key=='buffers':
                assert after[key][1:]==value[1:] and set(after[key][0])==set(value[0])
            elif key=='scenes':
                assert after[key][0]['nodes'][:len(value[0]['nodes'])]==value[0]['nodes']
                assert set(after[key][0])-{'nodes'}==set(value[0])-{'nodes'}
            else:
                assert value==after[key],key
        images=[]
        for image in after.get('images',[]):
            view=after['bufferViews'][image['bufferView']]
            start=view.get('byteOffset',0)
            images.append(sha256(new[start:start+view['byteLength']]).hexdigest())
        assert images==([] if role=='lod' else [reference_hash])
        op=before_file if role=='raw' else args.decoded/'prior'/(role+'.glb')
        fp=after_file if role=='raw' else args.decoded/'output'/(role+'.glb')
        original,oldmat,names,_=project['load_triangles'](op)
        final,mat,finalnames,_=project['load_triangles'](fp)
        assert np.array_equal(original,final[:len(original)]) and np.array_equal(oldmat,mat[:len(oldmat)])
        assert finalnames==names and set(mat[len(oldmat):])=={names.index('carved pale stone')}
        assert np.array_equal(original.min((0,1)),final.min((0,1))) and np.array_equal(original.max((0,1)),final.max((0,1)))
        previous=facade_triangles(original)
        previous=previous[(previous[:,:,2].max(1)>6.23)&(previous[:,:,2].min(1)<7.8)&
                          (previous[:,:,1].max(1)>.01)&(previous[:,:,0].min(1)<3.6)&(previous[:,:,0].max(1)>-4.6)]
        additions=facade_triangles(final[len(original):])
        assembly_count=len(additions)//6
        assert assembly_count*6==len(additions)
        samples=[]
        for i in range(6):
            mesh=additions[i*assembly_count:(i+1)*assembly_count]
            left,right=mesh[:,:,0].min(),mesh[:,:,0].max()
            u=(left+right)/2
            # Independently reconstruct the six shaft axes from their triangles.
            expected=(-3.12,-.47,2.13)[i//2]+(-.915 if i%2==0 else .915)
            assert abs(u-expected)<1e-5
            assert np.all((mesh[:,:,2]>=5.96)&(mesh[:,:,2]<=7.56))
            probes=[]
            for h in (6.41,6.73,7.06,7.18):
                old_mid=depth(previous,u,h)
                rays=[depth(mesh,u+d,h) for d in (-.052,0,.052)]
                assert all(np.isfinite(v) for v in [old_mid,*rays])
                assert rays[1]-max(rays[0],rays[2])>.013
                assert rays[1]-old_mid>.065 and abs(rays[0]-rays[2])<.004
                probes.append({'height':h,'previous_depth':old_mid,'new_left_centre_right':rays})
            head=[depth(mesh,u+d,7.482)for d in (-.135,0,.135)]
            assert all(x>.24 for x in head) and max(head)-min(head)<1e-4
            window=(-3.12,-.47,2.13)[i//2]
            assert min(abs(left-window),abs(right-window))>.725
            samples.append({'window':i//2+1,'side':'left' if i%2==0 else 'right',
                            'inferred_axis_m':round(u,4),'body_sections':probes,'abacus_edge_and_centre_m':head})
        by_role[role]={'old_triangles':len(original),'unchanged_base_triangles_by_order':len(original),
                       'total_scene_triangles':len(final),'added_instances':6,'added_triangles':len(additions),
                       'original_bytes_prefix_sha256':sha256(old).hexdigest(),'all_original_bounds_unchanged':True,
                       'embedded_images':images,'unchanged_material_faces':dict(Counter(names[i]for i in oldmat)),
                       'sha256':sha256(after_file.read_bytes()).hexdigest(),'bytes':after_file.stat().st_size,'jamb_profiles':samples}
    args.report.write_text(json.dumps({'variants':by_role,'independent_reader_sha256':sha256(args.helper.read_bytes()).hexdigest(),
      'source_reference':'Four heights × three lateral rays per new shaft, plus the two outer and central abacus rays, in each variant. All old world triangles and their material indices compared in order; raw and full retain the original photo, LOD retains its former material approximation.'},indent=2)+'\n')
    print({k:v['total_scene_triangles']for k,v in by_role.items()})


if __name__=='__main__':
    main()
