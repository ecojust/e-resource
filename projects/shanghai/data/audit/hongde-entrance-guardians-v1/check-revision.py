"""Verify each untouched GLB primitive and physically intersect the old and revised front stairs."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import struct
import subprocess
import tempfile
import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/hongkou-hongde-church/revisions/entrance-guardians'
BASE=json.loads((SOURCE/'baseline.json').read_bytes())


def chunks(file):
    with file.open('rb') as inp:
        magic,version,total,n,kind=struct.unpack('<4s4I',inp.read(20))
        assert magic==b'glTF' and version==2 and total==file.stat().st_size and kind==0x4e4f534a
        doc=json.loads(inp.read(n));size,typ=struct.unpack('<II',inp.read(8));assert typ==0x004e4942
        return doc,inp.tell(),size


def interval(file,offset,length):
    digest=sha256()
    with file.open('rb')as inp:
        inp.seek(offset)
        while length:
            b=inp.read(min(length,262144));assert b;digest.update(b);length-=len(b)
    return digest.hexdigest()


def same_scene_content(before,after):
    old,start,bin_size=chunks(before);new,now,_=chunks(after)
    prior_hash=interval(before,start,bin_size)
    assert interval(after,now,bin_size)==prior_hash
    assert old.keys()==new.keys()
    for key,original in old.items():
        if key in ('materials','meshes','nodes','bufferViews','accessors'):
            assert original==new[key][:len(original)],key
        elif key=='buffers':
            assert original[1:]==new[key][1:] and new[key][0]['byteLength']>=original[0]['byteLength']
        elif key=='scenes':
            assert len(original)==len(new[key])==1
            for k,v in original[0].items():
                assert (v==new[key][0][k][:len(v)] if k=='nodes' else v==new[key][0][k]),k
        else:
            assert original==new[key],key
    receipts=[]
    for m,mesh in enumerate(old['meshes']):
        entries=[]
        for i,p in enumerate(mesh['primitives']):
            attributes={**p.get('attributes',{}),'indices':p['indices']};views={}
            for attr,accessor in attributes.items():
                a=old['accessors'][accessor];v=old['bufferViews'][a['bufferView']]
                stored=v.get('extensions',{}).get('EXT_meshopt_compression',v)
                assert stored['buffer']==0
                offset=stored.get('byteOffset',0);n=stored['byteLength']
                digest=interval(before,start+offset,n);assert interval(after,now+offset,n)==digest
                views[attr]=dict(accessor=accessor,bufferView=a['bufferView'],bytes=n,sha256=digest)
            entries.append(dict(primitive=i,material=p.get('material'),views=views))
        receipts.append(dict(mesh=m,mesh_record_sha256=sha256(json.dumps(mesh,sort_keys=True).encode()).hexdigest(),primitives=entries))
    loc=[]
    edge=BASE['north_edge'];mid=np.asarray(edge['center_local_east_north_m'])
    west=-np.asarray(edge['tangent_east_north']);inside=-np.asarray(edge['outward_normal_east_north'])
    for mesh in new['meshes'][len(old['meshes']):]:
        side=-1 if mesh['name'].startswith('East guardian') else 1
        for p in mesh['primitives']:
            acc=new['accessors'][p['attributes']['POSITION']];view=new['bufferViews'][acc['bufferView']];assert view['buffer']==0 and acc['componentType']==5126
            with after.open('rb')as inp:
                inp.seek(now+view['byteOffset']);vertices=np.frombuffer(inp.read(view['byteLength']),dtype='<f4').reshape(acc['count'],3)
            en=vertices[:,[0,2]]*[1,-1]-mid
            pts=np.column_stack((en@west,en@inside,vertices[:,1]));vmin=pts.min(0);vmax=pts.max(0)
            # Actual sculpture extents stay on each pre-existing .66 × .65 m plinth.
            assert np.all(pts[:,0]>=1.95*side-.33) and np.all(pts[:,0]<=1.95*side+.33)
            assert np.all(pts[:,1]>=-.48-.325) and np.all(pts[:,1]<=-.48+.325)
            # The bottom of the paw support beds 3 mm into the original slab.
            assert vmin[2]>=.8569 and vmax[2]<1.71
            loc.append(dict(group=mesh['name'],material=new['materials'][p['material']]['name'],min_u_depth_z=vmin.tolist(),max_u_depth_z=vmax.tolist()))
    assert len(new['meshes'])==len(old['meshes'])+8
    return dict(original_bin_bytes=bin_size,original_bin_sha256=prior_hash,unchanged_meshes=receipts,
                original_materials=len(old['materials']),original_nodes=len(old['nodes']),new_scoped_parts=loc)


def probe(file,work):
    output=work/'one-asset.json'
    subprocess.run(['node',HERE/'probe-model.mjs',PROJECT,file,SOURCE/'baseline.json',output],check=True)
    return json.loads(output.read_bytes())


def main():
    parser=ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=HERE/'geometry-revision.json');args=parser.parse_args()
    results={}
    with tempfile.TemporaryDirectory()as tmp:
        for role,original_tris in BASE['prior_triangles'].items():
            info=BASE['assets'][role];file=PROJECT/info['file'];new=file.parent/'revisions/entrance-guardians'/file.name
            assert interval(file,0,file.stat().st_size)==info['sha256']
            checks=same_scene_content(file,new);before=probe(file,Path(tmp));after=probe(new,Path(tmp))
            assert before['triangles']==original_tris and after['triangles']>original_tris
            pairs=[]
            for a,b in zip(before['probes'],after['probes'],strict=True):
                name=a['name'];assert name==b['name'];old,new_hit=a['result'],b['result']
                if ' top ' in name or ' front ' in name:
                    assert new_hit and new_hit['material'] in ['Hongde limestone carving','Hongde incised stone'],(name,new_hit)
                    assert old is None or old['distance_m']>new_hit['distance_m']+.04,(name,old,new_hit)
                elif old is None or new_hit is None:assert old==new_hit,(name,old,new_hit)
                else:assert old['material']==new_hit['material'] and abs(old['distance_m']-new_hit['distance_m'])<1e-5,name
                pairs.append(dict(name=name,origin_u_depth_z_m=a['origin_u_depth_z_m'],direction=a['direction_u_depth_z'],before=old,after=new_hit))
            results[role]=dict(original_sha256=before['sha256'],revised_sha256=after['sha256'],before_triangles=original_tris,
                 after_triangles=after['triangles'],added_triangles=after['triangles']-original_tris,**checks,probes=pairs)
    args.out.write_text(json.dumps(dict(passed=True,variants=results,checker_sha256=interval(Path(__file__),0,Path(__file__).stat().st_size),ray_reader_sha256=sha256((HERE/'probe-model.mjs').read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
