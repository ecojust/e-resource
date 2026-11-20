"""Bind the Fuzhou Road red-roof wing, including the neighbouring undivided tile."""
import argparse, subprocess, sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import box, Point, LineString, MultiLineString
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-caldbeck-macgregor-building'
OWNER=1960

def complete_group(layout,group):
    # Original source has no triangle owner attributes in the near GLB and the
    # two western parcels meet. Measuring the entire tile avoids assigning faces.
    layout.link('baseline-near.glb.gz',layout.files[Path(group['file']).name])
    write(layout.work/'context-features.json',[{'localId':i}for i in group['feature_local_ids']])
    subprocess.run(['node',layout.decoders/'map-decode-source.mjs'],env=layout.env,check=True,stdout=subprocess.DEVNULL)
    result={}
    for role in ['near','far']:
        tris=np.fromfile(layout.work/('baseline-'+role+'-triangles.f64'),np.float64).reshape(-1,3,3)
        tris[:,:,:2]=tris[:,:,:2]@layout.axes.T
        result[role]=(len(tris),layout.project_faces(tris))
    return result

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    cli.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
    a=cli.parse_args();a.output.mkdir(exist_ok=True,parents=True)
    site=PROJECT/'source/precise'/ID/'footprint-review.json';r=read(site);ctx=PlacementMeshes(PROJECT,a.work,r)
    assets,bounds,full,foot=ctx.decode_model(a.manifest);pieces=ctx.decode_group(r['near_tiles'][0],OWNER)
    western=complete_group(ctx,r['west_groups'][0])
    model=read(a.manifest);src=r['owner'];native={};assert src['source_key'].endswith('a601284f-259c-4286-8611-faec291b6688')
    x0,x1,y0,y1=-15.15,15.65,-.83,8.52
    cut=box(x0,y0,x1,y1);assert cut.covers(full)
    # At street level the shallow opening reaches its photographed shadow plane.
    # Side bays and the unobserved section behind that plane are closed.
    floor=box(-15.035,0,15.535,8.45).difference(box(.25-2.413,-.1,.25+2.413,1.239))
    collision=shapely.union_all([foot,floor],grid_size=.001).simplify(.008,preserve_topology=True)
    geom={};owner=ctx.footprints[OWNER];west=ctx.footprints[1787]
    for role,(tris,peers,method)in pieces.items():
        target=ctx.project_faces(tris);n=ctx.project_faces(peers);nwest=western[role][1]
        geom[role]=target;rwest=nwest.intersection(cut).area
        native[role]=dict(owner_triangles=len(tris),group_peer_triangles=len(peers),owner_assignment=method,
            whole_west_tile_triangles=western[role][0],owner_projection_m2=target.area,retained_m2=target.difference(cut).area,
            retained_fraction=target.difference(cut).area/target.area,nearest_group_peer_m=n.distance(cut),
            west_tile_model_distance_m=nwest.distance(full),west_tile_cut_distance_m=nwest.distance(cut),west_tile_overlap_m2=rwest,
            target_height_m=float(tris[:,:,2].max()))
        assert native[role]['west_tile_model_distance_m']>.4 and rwest<1e-8 and n.distance(cut)>9
        assert .73<native[role]['retained_fraction']<.77
    assert owner.intersection(west).area>2 and west.distance(cut)>.45
    seams=[]
    for a0,a1 in [((x0,y0),(x0,y1)),((x0,y1),(x1,y1)),((x1,y1),(x1,y0))]:
        line=geom['far'].intersection(LineString([a0,a1]))
        if line.geom_type=='LineString'and line.length>.1:seams.append(line)
    assert len(seams)==3
    ready=read(ctx.files['READY.json'])
    cap={'base_m':0,'roof_m':native['far']['target_height_m'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],
         'far_sha256':sha(ctx.files['far.glb']),'geometry':ctx.wgs(MultiLineString(seams))}
    checks=[]
    def probe(name,x,y,expected):
        at=Point(x,y);remainder=owner.difference(cut);neighbor=any(sh.covers(at) for i,sh in ctx.footprints.items()if i!=OWNER)
        d=collision.covers(at);g=remainder.covers(at)
        assert bool(d or g or neighbor)==expected,(name,d,g,neighbor)
        checks.append(dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building'if expected else None,detailed_hit=d,retained_hit=g,neighbor_hit=neighbor))
    for name,x,y,val in [('street before face',.25,-1.6,False),('short entrance reveal',.25,.45,False),('back of section',.25,1.35,True),('west brick bay',-9,1.1,True),('east brick bay',9,1.1,True),('unchanged northern wing',5,20,True)]:probe(name,x,y,val)
    probe('separate west building',*west.representative_point().coords[0],True)
    frame=r['author_frame'];contract={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,
        'owner':{'macro_id':r['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[src['source_key'].split(':')[1]],'building_part':[]},
        'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'replacement_geometry':ctx.wgs(cut),
        'collision_geometry':ctx.wgs(collision),'source_section_caps':cap,'overviewBearing':-13,'overviewPitch':32,'overviewZoom':19.85,
        'maxDistance':550,'lod_switch_in_m':550,'lod_switch_out_m':700,'navigation':{'listed':False,'status':'正广和公司福州路历史街翼，供俯瞰。'},
        'placement':{'status':'estimated','note':'按福州路44号登记、OSM原名地块和南端红瓦街翼定位。后翼和独立西邻保留。'},'partial_model':True,'model_scope':model['model_scope_zh']}
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    write(a.output/'final-placement-contract.json',contract)
    report=dict(id=ID,manifest_sha256=sha(a.manifest),source_review_sha256=sha(site),script_sha256=sha(Path(__file__)),assets=assets,native=native,
                full_projection_m2=full.area,foot_projection_m2=foot.area,collision_m2=collision.area,
                owner_west_vector_overlap_m2=owner.intersection(west).area,west_vector_cut_clearance_m=west.distance(cut),
                unchanged_original_vector_m2=owner.difference(cut).area,source_seam_length_m=[line.length for line in seams],
                probes=checks,contract_sha256=sha(a.output/'final-placement-contract.json'))
    write(a.output/'placement-geometry.json',report);print(native)
if __name__=='__main__':main()
