#!/usr/bin/env python3
"""Portable original main-house exterior. Run: python source/build_model.py"""
import json,gzip,hashlib,sys,platform,copy
from pathlib import Path
import numpy as np
import shapely
from bajin_base import construct,D
ROOT=Path(__file__).resolve().parent.parent
ASSET_METADATA=json.loads((ROOT/'source/asset-metadata.json').read_text())

def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def describe(path):return {'file':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def world_uv(part):
    old=np.asarray(part['vertices']);verts=[];uv=[];tris=[];basis={}
    for tri in part['triangles']:
        pts=old[list(tri)];n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);n/=np.linalg.norm(n)
        key=tuple(np.round(n,9))
        if key not in basis:
            if abs(n[2])<.999999:u=np.cross([0,0,1.],n);u/=np.linalg.norm(u)
            else:u=np.array([1.,0.,0.])-n*n[0];u/=np.linalg.norm(u)
            v=-np.cross(n,u);basis[key]=(u,v)
        u,v=basis[key];start=len(verts)
        verts.extend(pts.tolist());uv.extend([[float(np.dot(p,u)/.4),float(np.dot(p,v)/.4)] for p in pts]);tris.append((start,start+1,start+2))
    part['vertices']=verts;part['texcoords']=uv;part['triangles']=tris
    return len(basis)

def main():
    (ROOT/'exports').mkdir(exist_ok=True)
    b,roof,rm=construct();print('Geometry constructed:',len(b.parts),flush=True)
    dump(ROOT/'roof-planar-contract.json',rm)
    dump(ROOT/'features.json',{'schema':'bajin-openings-v1','coordinate_frame':'Construction architecture XYZ, before baked EN rotation','source_main_only':True,'features':b.features,'portal_probe_caution':'Low side parapets are allowed closure below 1.24m; entry door/backwall is 1.05m behind front plane; no interior reconstruction.'})
    uv_groups=0
    for p in b.parts:
        if b.palette[p['material']].get('texture'):uv_groups+=world_uv(p)
    frame=D['frame'];x=np.asarray(frame['architecture_X_EN']);y=np.asarray(frame['architecture_Y_EN']);rot=np.array([[x[0],y[0],0],[x[1],y[1],0],[0,0,1.]])
    for p in b.parts:p['vertices']=(np.asarray(p['vertices'])@rot.T).tolist()
    metadata={'name':'巴金旧居主楼 · photo-informed exterior','author':'agent','copyright':ASSET_METADATA['copyright'],
        'model_id':D['model_id'],'source_owner':D['source_owner'],'anchor':frame['anchor'],'coordinates':'Anchor-local East/Up/-North in GLB; building rotation baked; heading 0 degrees','architecture_X_EN':x.tolist(),'architecture_Y_EN':y.tolist(),'height_and_hidden_roof_estimated':True,'scope':'Main house exterior only; no annex, garden, street gate, neighbors or interior. Unobserved flank windows not invented.','roof_contract':'roof-planar-contract.json','door_leaf_prior_m':2.2,'normal_contract':'No TANGENT; negative raw UV handedness; 0.40m world tile repeat','not_accepted_or_installed':True}
    report=b.save(ROOT/'exports/bajin-main-detailed.glb',metadata)
    print('Full raw',report['bytes'],report['triangles'],flush=True)
    rawparts={'schema':'bajin-actual-construction-parts-v1','coordinates':'anchor-local East/North/Up; raw GLB converts (E,N,U) to (E,U,-N)','parts':b.parts}
    with gzip.GzipFile(filename=str(ROOT/'construction-parts.json.gz'),mode='wb',mtime=0) as f:f.write(json.dumps(rawparts,separators=(',',':')).encode())
    # LOD is explicitly geometric: retain all wall apertures and joinery, omit
    # individual overlapping tiles and small door handles, not the roof planes.
    lod=copy.copy(b);lod.parts=[p for p in b.parts if not p['label'].startswith('flat-tiles/') and not p['label'].endswith('/door-handle') and '/panel-bead-' not in p['label']]
    lr=lod.save(ROOT/'exports/bajin-main-lod.glb',{**metadata,'name':'巴金旧居主楼 · aperture-preserving LOD','lod_omissions':['individual overlapping flat tiles','small door handles','lower panel fine beads']})
    dump(ROOT/'uv-contract.json',{'schema':'bajin-world-repeat-uv-v1','repeat_metres':.4,'frame':'Architecture metres before EN rotation','vertical_u':'normalize(cross(Z,outward_normal))','vertical_v':'-cross(normal,U), equal -Z for vertical walls','horizontal_u':'project architecture X on plane; normalize','horizontal_v':'-cross(normal,U)','per_triangle_corners_split':True,'raw_U_cross_V':'opposite outward normal','tangent_attribute':False,'float32_storage_only_metric_tolerance':True,'normalScale':.35,'AO_strength':.35,'basis_group_count':uv_groups,'native_AO':'Importer export preservation route, not Principled shading equivalence'})
    dump(ROOT/'build-report.json',{'schema':'bajin-detailed-build-v2','author':'agent','python':platform.python_version(),'numpy':np.__version__,'shapely':shapely.__version__,'raw':describe(ROOT/'exports/bajin-main-detailed.glb'),'lod_raw':describe(ROOT/'exports/bajin-main-lod.glb'),'triangles':report['triangles'],'lod_triangles':lr['triangles'],'parts':len(b.parts),'baked_rotation_determinant':float(np.linalg.det(rot)),'height_m':report['bounds_glb']['max'][1],'source_geometry':describe(ROOT/'source/geometry-input.json'),'geometry_and_material_original':True,'MAIN_modified':False,'accepted':False})
    print('BUILD_COMPLETE',report['bytes'],lr['bytes'],flush=True)
if __name__=='__main__':main()
