"""Verify exported West Paifang geometry, three roofs, twelve corners and actual open passage."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
import trimesh
from build_model import Paifang, ID, P

parser=argparse.ArgumentParser();parser.add_argument('--assets',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();reports={}
for role in ['raw','lod']:
    path=args.assets/f'{ID}-{role}.glb';data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size])
    assert not doc.get('images'), 'Reference photographs must not be embedded'
    scene=trimesh.load(path,force='scene',process=True);meshes=list(scene.geometry.values());assert meshes
    for mesh in meshes:
        assert np.isfinite(mesh.vertices).all() and (mesh.area_faces>1e-12).all()
        mesh.merge_vertices(merge_norm=True,merge_tex=True)
        assert mesh.is_winding_consistent and mesh.volume>0
    authored=Paifang(role=='lod').finish()
    for part in authored.b.parts:
        component=trimesh.Trimesh(part['vertices'],part['triangles'],process=True)
        assert component.is_watertight and component.is_winding_consistent and component.volume>0,part['label']
    count=sum(len(mesh.faces) for mesh in meshes)
    assert count==sum(len(part['triangles']) for part in authored.b.parts)
    total=trimesh.util.concatenate(meshes);bounds=scene.bounds;span=bounds[1]-bounds[0]
    assert np.isclose(bounds[0,1],0,atol=1e-6)
    assert np.isclose(bounds[1,1],P['estimated_total_height'],atol=1e-5),bounds
    canopies=[f for f in authored.features if f['kind']=='independent_canopy']
    corners=[f for f in authored.features if f['kind']=='upswept_roof_corner']
    assert len(canopies)==3 and len(corners)==12
    for canopy in canopies:assert sum(f['canopy']==canopy['label'] for f in corners)==4
    shells=[part for part in authored.b.parts if part['label'].endswith('-separate-closed-curved-shell')]
    assert len(shells)==3
    assert len([part for part in authored.b.parts if part['label']=='blank-title-face-no-inscription'])==2
    # These horizontal rays travel through the full model depth below the header.
    # They would detect a false door, infill wall, spanning base or hidden solid.
    origins=[[x,h,4] for x in [-1.65,0,1.65] for h in [.10,.25,1.0,2.5,4.25]]
    assert not total.ray.intersects_any(origins,[[0,0,-1]]*len(origins)).any(),'Open passage obstructed'
    assert total.ray.intersects_any([[0,4.31,4]],[[0,0,-1]]).all(),'Header lower bound absent'
    assert total.ray.intersects_any([[-2.2,2.5,4],[2.2,2.5,4]],[[0,0,-1]]*2).all(),'Stone shafts absent'
    # Measure actual inner faces from the centre, at shaft height and at footing height.
    widths={}
    for height,name,expected in [(2.5,'shaft_level',3.72),(.10,'foot_level',3.44)]:
        hits,rays,_=total.ray.intersects_location([[0,height,0]]*2,[[1,0,0],[-1,0,0]])
        right=float(hits[rays==0,0].min());left=float(hits[rays==1,0].max());widths[name]=right-left
        assert np.isclose(widths[name],expected,atol=1e-5),(name,widths[name])
    feet=[part for part in authored.b.parts if part['label']=='separate-stone-foot'];assert len(feet)==2
    actual_foot_depths=[float(np.ptp(np.asarray(part['vertices'])[:,1])) for part in feet]
    assert np.allclose(actual_foot_depths,[1.6,1.6],atol=1e-7)
    posts=[f for f in authored.features if f['kind']=='stone_post']
    spacing=max(f['axis_x_m'] for f in posts)-min(f['axis_x_m'] for f in posts)
    assert np.isclose(spacing,4.4)
    reports[role]={
        'representation':'uncompressed authored source GLB; packaged variants separately checked by manifest/browser',
        'sha256':hashlib.sha256(data).hexdigest(),'triangles':count,'authored_closed_solids':len(authored.b.parts),
        'authored_solids_watertight':True,'nondegenerate':True,'consistent_winding':True,
        'bounds_glb':bounds.tolist(),'actual_total_envelope_width_depth_height_m':span[[0,2,1]].tolist(),
        'highest_ornament_included_in_9_6m_estimate':True,'height_is_not_a_surveyed_conversion_of_three_zhang':True,
        'distinct_canopy_shells':len(shells),'upswept_corners':len(corners),'blank_plaque_faces':2,
        'post_axis_spacing_m_interpretation':spacing,'foot_support_depth_m_interpretation':actual_foot_depths,
        'actual_passage_clear_width_m':widths,'header_bottom_m_estimated':4.30,
        'horizontal_passage_rays_clear':True,'passage_ray_heights_m':[.10,.25,1.0,2.5,4.25],
        'no_photographs_embedded':True,
        'scope':'Physical west identity from text; common photo-guided structure, blank plaque faces, estimated geometry and hidden details; not full photo binding or geographic acceptance',
    }
assert reports['lod']['triangles']<reports['raw']['triangles']
args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
