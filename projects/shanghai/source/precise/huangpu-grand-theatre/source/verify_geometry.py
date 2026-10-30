"""Verify author solids, serialized geometry, recessed glazing and asset identity. MIT."""
import argparse,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
import trimesh
from build_model import build,ID

def recess_checks(mesh):
    # Probe between the five fins; front y=0 maps to glTF z=0.
    origins=np.array([[x,z,5] for x in [1.5,4.45,7.4,10.35] for z in [7.0,10.0,13.0]])
    directions=np.tile([0,0,-1],(len(origins),1))
    hits,indices,_=mesh.ray.intersects_location(origins,directions,multiple_hits=True)
    first=[]
    for i,origin in enumerate(origins):
        found=hits[indices==i];assert len(found),('Missing upper glazing',origin)
        hit=found[np.argmin(np.linalg.norm(found-origin,axis=1))]
        assert -.42<hit[2]<-.12,('Glazing not recessed or obstructed',origin,hit)
        first.append(float(hit[2]))
    # Central return window is actually cut through its enclosing shell.
    origin=np.array([[-8.1,6.1,5]])
    hits,_,_=mesh.ray.intersects_location(origin,np.array([[0,0,-1]]),multiple_hits=True)
    assert len(hits)
    hit=hits[np.argmin(np.linalg.norm(hits-origin[0],axis=1))]
    assert -.40<hit[2]<-.10,('Return glazing blocked by wall skin',hit)
    return {'upper_glazing_rays':len(origins),'first_glb_z_range':[min(first),max(first)],'return_window_rays':1,'return_glb_z':float(hit[2])}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--assets',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--gltfpack',type=Path);a=parser.parse_args();report={}
    manifest=json.loads((a.assets/'manifest.json').read_text()) if (a.assets/'manifest.json').exists() else None
    with tempfile.TemporaryDirectory(prefix='grand-decode-') as tmp:
        for role in ['raw','full','lod'] if manifest else ['raw','lod']:
            entry=manifest['assets'][role] if manifest else None
            path=a.assets/entry['file'] if entry else a.assets/f'{ID}-{role}.glb'
            data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);meta=doc['extras']
            assert meta['id']==ID and meta['frontage_only'] and not meta['auditorium_modeled'] and not meta['whole_shop_strip_modeled']
            assert meta['tower_height_chosen_interpretation_m']==30.5 and meta['alternate_reported_height_m']==16 and not meta['height_endpoints_verified']
            assert meta['all_plan_dimensions_estimated'] and meta['multi_period_reference'] and not meta['map_replacement'] and not doc.get('images')
            if entry:assert entry['bytes']==len(data) and entry['sha256']==hashlib.sha256(data).hexdigest()
            decoded=path
            if 'EXT_meshopt_compression' in doc.get('extensionsRequired',[]):
                assert a.gltfpack
                decoded=Path(tmp)/(role+'.glb');subprocess.run([str(a.gltfpack.resolve()),'-i',str(path),'-o',str(decoded),'-noq','-vnf','-km','-kn','-ke'],check=True)
            scene=trimesh.load(decoded,force='scene',process=False);meshes=list(scene.dump());assert meshes
            for m in meshes:assert np.isfinite(m.vertices).all() and (m.area_faces>1e-12).all() and m.is_winding_consistent
            count=sum(len(m.faces) for m in meshes)
            assert abs(scene.bounds[1,1]-30.5)<1e-5 and abs(scene.bounds[0,1])<1e-6
            if entry:assert count==entry['triangles']
            author_count=None
            if role in ['raw','lod']:
                authored=build(role=='lod')
                for part in authored.parts:
                    mesh=trimesh.Trimesh(part['vertices'],part['triangles'],process=True)
                    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,part['label']
                author_count=len(authored.parts);assert count==sum(len(p['triangles']) for p in authored.parts)
            report[role]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'triangles':count,'bounds_glb':scene.bounds.tolist(),'finite_vertices':True,'nondegenerate_faces':True,'consistent_winding':True,'author_solids_checked':author_count,'author_solids_closed_positive':author_count is not None,'recess_checks':recess_checks(trimesh.util.concatenate(meshes)),'photos_embedded':False}
        assert report['lod']['triangles']<report['raw']['triangles']
        for role in report:assert np.allclose(report[role]['bounds_glb'],report['raw']['bounds_glb'],atol=1e-5)
        if manifest:
            assert report['full']['triangles']==report['raw']['triangles']
            entry=manifest['assets']['native'];data=(a.assets/entry['file']).read_bytes()
            assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
        assert all(0<r['bytes']<100_000_000 for r in report.values())
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
