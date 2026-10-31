"""Verify author solids and exact serialized FLOAT32 surfaces, not historical accuracy."""
from pathlib import Path
import argparse, hashlib, json, struct, subprocess, tempfile
import numpy as np
import trimesh
from build_model import ID, ROOT, build
def check_parts(parts):
    failures=[];total_volume=0;minarea=float('inf')
    for p in parts:
        v=np.asarray(p['vertices'],np.float32).astype(float)
        f=np.asarray(p['triangles'],int)
        mesh=trimesh.Trimesh(vertices=v,faces=f,process=False)
        edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
        _,counts=np.unique(edges,axis=0,return_counts=True)
        area=mesh.area_faces
        status={'closed':bool(np.all(counts==2)), 'winding':bool(mesh.is_winding_consistent),
                'positive_volume':bool(mesh.volume>1e-10), 'nonzero_float32_triangles':bool(np.all(area>1e-12))}
        if not all(status.values()):failures.append({'label':p['label'],'status':status,'volume':float(mesh.volume),'counts':dict(zip(*np.unique(counts,return_counts=True)))})
        total_volume+=mesh.volume;minarea=min(minarea,float(area.min()))
    return {'parts':len(parts),'triangles':sum(len(p['triangles']) for p in parts),
            'failure_count':len(failures),'failures':failures,'min_float32_triangle_area_m2':minarea,
            'summed_component_volume_m3_not_union':total_volume}


def digest(triangles):
    v=np.array(triangles,dtype='<f4');v[v==0]=0
    starts=np.lexsort((v[:,:,2],v[:,:,1],v[:,:,0]),axis=-1)[:,0]
    v=v[np.arange(len(v))[:,None],(starts[:,None]+np.arange(3))%3]
    rows=np.ascontiguousarray(v.reshape(-1,9)).view(np.dtype((np.void,36))).ravel()
    return hashlib.sha256(np.sort(rows).tobytes()).hexdigest()


def documents(path):
    data=Path(path).read_bytes();assert struct.unpack_from('<4sII',data)==(b'glTF',2,len(data))
    n,kind=struct.unpack_from('<II',data,12);assert kind==0x4E4F534A
    return json.loads(data[20:20+n])


def converted(v):return np.asarray(v)[:,[0,2,1]]*np.array([1,1,-1])


def check_rays(meshes,probes):
    triangles=np.concatenate([m.triangles for m in meshes])
    tags=np.concatenate([np.full(len(m.faces),m.visual.material.name) for m in meshes])
    records=[]
    def first(origin,direction):
        aa,bb,cc=triangles[:,0],triangles[:,1],triangles[:,2]
        e1,e2=bb-aa,cc-aa;h=np.cross(np.broadcast_to(direction,e2.shape),e2)
        det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-10
        inv=np.zeros(len(det));inv[valid]=1/det[valid];s=np.asarray(origin)-aa
        u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1)
        v=inv*np.einsum('ij,ij->i',np.broadcast_to(direction,e2.shape),q)
        t=inv*np.einsum('ij,ij->i',e2,q)
        hit=np.flatnonzero(valid&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(t>1e-8))
        if len(hit)==0:return None
        i=hit[np.argmin(t[hit])]
        return {'distance_m':float(t[i]),'material':str(tags[i]),'point':list(np.asarray(origin)+direction*t[i])}
    def enu(p):return np.asarray([p[0],p[2],-p[1]],float)
    for p in probes:
        origin=enu(np.asarray(p['point'])+np.asarray(p['normal'])*8)
        direction=enu(-np.asarray(p['normal']))
        hit=first(origin,direction)
        passed=hit is not None and hit['material']==p['material'] and abs(hit['distance_m']-8-p['depth'])<5e-5
        records.append({'label':p['label'],'expected_material':p['material'],'expected_distance_m':8+p['depth'],'first':hit,'pass':passed})
    for name,y,z,want in [('centre',-17.6,1.5,False),('centre-south-offset',-17.98,1.5,False),
                          ('centre-north-offset',-17.22,1.5,False),('crown',-17.6,3.,False),
                          ('south-shoulder',-19.0,2.5,False),('north-shoulder',-16.2,2.5,False),
                          ('deck',-17.6,4.,True),('south-pier',-21.,1.5,True),('north-pier',-14.2,1.5,True)]:
        for sign in [-1,1]:
            hit=first(enu([-30*sign,y,z]),enu([sign,0,0]));passed=bool(hit)==want
            if want:passed=passed and hit['material']=='warm stone'
            records.append({'label':'true road arch / '+name+f' / direction {sign}','first':hit,'expect_solid':want,'pass':passed})
    return {'all_pass':all(p['pass'] for p in records),'count':len(records),'failures':[p for p in records if not p['pass']], 'records':records}


def author(lod):
    b,meta,features,probes=build(lod)
    checks=check_parts(b.parts)
    assert checks['failure_count']==0,checks['failures']
    grouped={};points=[]
    for p in b.parts:
        v=np.asarray(converted(p['vertices']),np.float32)
        grouped.setdefault(p['material'],[]).append(v[np.asarray(p['triangles'])])
        points.extend(v)
    points=np.asarray(points);bounds=[points.min(0).tolist(),points.max(0).tolist()]
    assert bounds[0][1]==0
    return {'checks':checks,'metadata':meta,'features':features,'probes':probes,'bounds':bounds,
            'digests':{k:digest(np.concatenate(v)) for k,v in grouped.items()}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--gltfpack',type=Path);p.add_argument('--blender',type=Path,default=Path('/usr/bin/blender'));a=p.parse_args()
    authored={}
    for lod,key in [(False,'raw'),(True,'lod')]:
        print('Rebuilding and checking '+key+' author solids',flush=True);authored[key]=author(lod)
    manifest_path=a.assets/'manifest.json';manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    report={'id':ID,'all_dimensions_are_author_or_source_estimates':True,'author':{},'assets':{},
        'source_files_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ['build_model.py','components.py','model-parameters.json','common/photo_architecture.py','verify_geometry.py']}}
    for k,v in authored.items():report['author'][k]={t:v[t] for t in ['checks','metadata','features','bounds','digests']}
    with tempfile.TemporaryDirectory(prefix='yangpu-city-hall-verify-') as temporary:
        temp=Path(temporary)
        for role in (['raw','full','lod'] if manifest else ['raw','lod']):
            print('Checking actual asset '+role,flush=True)
            entry=manifest['assets'][role] if manifest else {'file':f'{ID}-{role}.glb'}
            path=a.assets/entry['file'];raw=path.read_bytes();doc=documents(path)
            sha=hashlib.sha256(raw).hexdigest();assert 0<len(raw)<100_000_000
            if manifest:assert len(raw)==entry['bytes'] and sha==entry['sha256']
            expected=authored['lod' if role=='lod' else 'raw']
            assert doc['extras']==expected['metadata']
            assert not doc.get('images') and not doc.get('textures')
            assert all('uri' not in b for b in doc['buffers'])
            compressed='EXT_meshopt_compression' in doc.get('extensionsRequired',[])
            decoded=path
            if compressed:
                assert a.gltfpack
                decoded=temp/(role+'.glb')
                subprocess.run([str(a.gltfpack),'-i',str(path),'-o',str(decoded),'-noq','-vnf','-km','-kn','-ke'],check=True,capture_output=True,text=True)
            scene=trimesh.load(decoded,force='scene',process=False);meshes=list(scene.dump())
            grouped={};adjacency=[];minimum_dot=1.
            for m in meshes:
                assert np.isfinite(m.vertices).all() and np.all(m.area_faces>1e-12)
                assert m.volume>0,(role,m.visual.material.name,m.volume)
                grouped.setdefault(m.visual.material.name,[]).append(m.triangles)
                if not m.is_winding_consistent:
                    adjacency.append({'material':m.visual.material.name,'triangles':len(m.faces)})
                dots=np.einsum('ijk,ik->ij',m.vertex_normals[m.faces],m.face_normals)
                minimum_dot=min(minimum_dot,float(dots.min()))
                assert dots.min()>.99,(role,m.visual.material.name,dots.min())
            values={k:digest(np.concatenate(v)) for k,v in grouped.items()}
            assert values==expected['digests'],('Exact oriented FLOAT32 triangles changed',role)
            assert not adjacency,('Unexpected material batch adjacency ambiguity',role,adjacency)
            assert np.allclose(scene.bounds,expected['bounds'],atol=2e-5,rtol=0)
            rays=check_rays(meshes,expected['probes'])
            if not rays['all_pass']:
                (a.out.with_suffix('.failed-rays.json')).write_text(json.dumps(rays,indent=2)+'\n')
            assert rays['all_pass'],rays['failures']
            report['assets'][role]={'file':path.name,'bytes':len(raw),'sha256':sha,'triangles':sum(len(m.faces) for m in meshes),
                'bounds_glb':scene.bounds.tolist(),'exact_oriented_float32_multiset':values,'coordinate_tolerance_m':0,
                'author_component_solids_closed_positive':True,'author_components_not_boolean_unioned':True,
                'material_batch_winding_consistent':True,'minimum_face_vertex_normal_dot':minimum_dot,
                'meshopt_decoded':compressed,'actual_scene_surface_probes':rays,'photos_embedded':False}
        assert report['assets']['lod']['triangles']<report['assets']['raw']['triangles']
        assert np.allclose(report['assets']['lod']['bounds_glb'],report['assets']['raw']['bounds_glb'],atol=1e-5,rtol=0), 'LOD must preserve the complete geographic envelope'
        if manifest:
            assert set(manifest['assets'])=={'raw','full','lod','native'}
            assert report['assets']['full']['exact_oriented_float32_multiset']==report['assets']['raw']['exact_oriented_float32_multiset']
            e=manifest['assets']['native'];path=a.assets/e['file'];data=path.read_bytes()
            assert 0<len(data)<100_000_000 and len(data)==e['bytes'] and hashlib.sha256(data).hexdigest()==e['sha256']
            native_out=temp/'native.json'
            expression=f'''import bpy,json\nfrom pathlib import Path\ns=bpy.context.scene\nassert s['candidate_id']=={ID!r}\nm=[bpy.data.objects[n] for n in s['model_mesh_names']]\nassert all(o['source_raw_sha256']=={report['assets']['raw']['sha256']!r} for o in m)\nassert not bpy.data.libraries\nassert not [i for i in bpy.data.images if i.type not in {{'RENDER_RESULT','COMPOSITING'}}]\nassert not [(m.name,n.name) for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE']\nPath({str(native_out)!r}).write_text(json.dumps({{'triangles':sum(len(o.data.polygons) for o in m),'metadata':json.loads(s['candidate_metadata_json']),'blender':bpy.app.version_string}}))\n'''
            result=subprocess.run([str(a.blender),'-b',str(path),'--python-exit-code','1','--python-expr',expression],capture_output=True,text=True)
            assert result.returncode==0,result.stdout+result.stderr
            native=json.loads(native_out.read_text());assert native['metadata']==authored['raw']['metadata']
            assert native['triangles']==report['assets']['raw']['triangles']
            report['assets']['native']=e|{'actual_reopen_passed':True,'photos_embedded':False,'blender':native['blender']}
    report['pass']=True;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:{t:v[t] for t in ['file','bytes','sha256']} for k,v in report['assets'].items()},indent=2))


if __name__=='__main__':main()
