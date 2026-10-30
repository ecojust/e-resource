"""Check actual GLBs, author solids and open galleries; no survey acceptance. MIT."""
import argparse,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
import trimesh
from build_model import build,ID,P

def openness(mesh):
    probes=[]
    for interval,bays in zip(P['gallery_intervals'],[6,8]):
        xs=np.linspace(interval[0]+.25,interval[1]-.25,bays+1)
        for x in (xs[:-1]+xs[1:])/2:
            for z in [7.5,13.5,20.5]:probes.append([float(x),z,15])
    origins=np.array(probes);directions=np.tile([0,0,-1],(len(origins),1))
    hits,ray_indices,_=mesh.ray.intersects_location(origins,directions,multiple_hits=True)
    first=[]
    for i in range(len(origins)):
        ray_hits=hits[ray_indices==i]
        assert len(ray_hits),f'No gallery back wall at {origins[i]}'
        point=ray_hits[np.argmin(np.linalg.norm(ray_hits-origins[i],axis=1))]
        assert 6.55<=point[2]<=7.5,f'Gallery opening blocked at {origins[i]} by {point}'
        first.append(point[2])
    # Above the shaft, two crossing rays pass through the actual open lantern.
    tx,ty=P['tower_center']
    lantern_origins=np.array([[tx+2,48,15],[-65,48,-ty-2]])
    lantern_directions=np.array([[0,0,-1],[1,0,0]])
    assert not mesh.ray.intersects_any(lantern_origins,lantern_directions).any()
    return {'gallery_rays':len(probes),'first_hits_glb_z_range': [float(min(first)),float(max(first))], 'open_lantern_rays':2}

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',type=Path);a=p.parse_args();report={}
    manifest=json.loads((a.assets/'manifest.json').read_text()) if (a.assets/'manifest.json').exists() else None
    with tempfile.TemporaryDirectory(prefix='race-decode-') as tmp:
        for role in ['raw','full','lod'] if manifest else ['raw','lod']:
            entry=manifest['assets'][role] if manifest else None
            path=a.assets/entry['file'] if entry else a.assets/f'{ID}-{role}.glb'
            data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);extra=doc['extras']
            assert extra['id']==ID and extra['tower_height_secondary_reference_m']==53
            assert not doc.get('images') and not extra['map_replacement'] and extra['all_plan_dimensions_estimated']
            assert extra['east_body_only'] and not extra['west_building_modeled'] and not extra['secondary_clock_tower_modeled']
            assert extra['clock_dials_modeled']==2 and not extra['height_endpoints_verified']
            if entry:assert entry['bytes']==len(data) and entry['sha256']==hashlib.sha256(data).hexdigest()
            decoded=path
            if 'EXT_meshopt_compression' in doc.get('extensionsRequired',[]):
                assert a.gltfpack
                decoded=Path(tmp)/(role+'.glb');subprocess.run([str(a.gltfpack.resolve()),'-i',str(path),'-o',str(decoded),'-noq','-vnf','-km','-kn','-ke'],check=True)
            scene=trimesh.load(decoded,force='scene',process=False);meshes=list(scene.dump());assert meshes
            for m in meshes:assert np.isfinite(m.vertices).all() and (m.area_faces>1e-12).all() and m.is_winding_consistent
            count=sum(len(m.faces) for m in meshes);assert 0<count and abs(scene.bounds[1,1]-53)<1e-4 and abs(scene.bounds[0,1])<1e-6
            if entry:assert count==entry['triangles']
            author_count=None
            if role in ['raw','lod']:
                authored,_,features=build(role=='lod')
                for part in authored.parts:
                    m=trimesh.Trimesh(part['vertices'],part['triangles'],process=True)
                    assert m.is_watertight and m.is_winding_consistent and m.volume>0,part['label']
                author_count=len(authored.parts)
                assert count==sum(len(q['triangles']) for q in authored.parts)
                assert features['clock_face_count']==2 and features['estimated_window_openings']>200
            opening_checks=openness(trimesh.util.concatenate(meshes))
            report[role]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'triangles':count,'bounds_glb':scene.bounds.tolist(),'finite_vertices':True,'nondegenerate_faces':True,'consistent_winding':True,'author_solids_checked':author_count,'author_solids_closed_positive':author_count is not None,'opening_checks':opening_checks,'photos_embedded':False}
        assert report['lod']['triangles']<report['raw']['triangles']
        for role in report:assert np.allclose(report[role]['bounds_glb'],report['raw']['bounds_glb'],atol=1e-5)
        if manifest:
            assert report['full']['triangles']==report['raw']['triangles']
            native=manifest['assets']['native'];d=(a.assets/native['file']).read_bytes();assert len(d)==native['bytes'] and hashlib.sha256(d).hexdigest()==native['sha256']
        assert all(x['bytes']<100_000_000 for x in report.values())
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
