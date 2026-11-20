"""Check the three elevations of the 501 Yongjia Road residence against frozen source 340."""
import argparse
from pathlib import Path
import sys
import numpy as np
import shapely
from shapely.geometry import box, Point, LineString, MultiLineString, shape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry
ID = 'xuhui-yongjia-road-501-residence'
OWNER = 340
NEIGHBORS = {2048:'西侧另一栋花园住宅',3116:'东侧独立小楼',4888:'西侧临街附屋',976:'东北独立楼',1680:'东南园内另一栋'}

def measure():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=HERE)
    a=parser.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    fp=PROJECT/'source/precise'/ID/'footprint-review.json';r=read(fp);ctx=PlacementMeshes(PROJECT,a.work,r)
    for o in r['owners']:
        if o['local_id'] not in ctx.footprints:
            ctx.footprints[o['local_id']]=shapely.transform(shape(o['geometry']),ctx.to_xy)
    assets,bounds,model,feet=ctx.decode_model(a.manifest)
    source = ctx.footprints[OWNER]
    # The east end has no reliable facade photograph. Leave an independent strip of the native source,
    # including its ground collision. The tower and west annexe project beyond the existing rectangle.
    mask = model.buffer(.055,join_style='mitre').simplify(.05,preserve_topology=True).intersection(source.buffer(.25,join_style='mitre'))
    assert mask.is_valid and model.intersection(source).difference(mask).area < .00003
    solids = [box(-7.12,0,8.31,8.34), Point(6.98,.22).buffer(1.48,quad_segs=24),box(8.30,2.69,9.68,6.34)]
    collision=shapely.union_all(solids)
    native={};others={}
    for oid in [OWNER,*NEIGHBORS]:
        group=next(g for g in r['near_tiles']if oid in g['feature_local_ids'])
        meshes=ctx.decode_group(group,oid)
        if oid==OWNER:
            for role,(tri,peer,method) in meshes.items():
                own=ctx.project_faces(tri);neighbors=ctx.project_faces(peer);left=own.difference(mask)
                assert .025 < left.area/own.area < .23 and neighbors.distance(mask)>.15,(role,left.area/own.area,neighbors.distance(mask))
                intrusion = left.intersection(model).area
                assert intrusion < .00003, (role, intrusion)
                native[role]=dict(triangles=len(tri),assignment=method,area_m2=own.area,
                    retained_intersection_with_model_m2=intrusion,actual_model_overlap_m2=own.intersection(model).area,
                    cut_m2=own.intersection(mask).area,
                    retained_m2=left.area,retained_fraction=left.area/own.area,
                    peer_model_gap_m=neighbors.distance(model),peer_cut_gap_m=neighbors.distance(mask),
                    peer_cut_m2=neighbors.intersection(mask).area,height_m=float(tri[:,:,2].max()))
                if role=='far':far=own
        else:
            item={'name':NEIGHBORS[oid], 'source_gap_m':ctx.footprints[oid].distance(mask)}
            for role,(tri,_,method) in meshes.items():
                geo=ctx.project_faces(tri)
                assert geo.distance(mask)>.25,(oid,role,geo.distance(mask))
                item[role]=dict(triangles=len(tri),cut_m2=geo.intersection(mask).area,gap_m=geo.distance(mask),assignment=method)
            others[oid]=item
    seams=[]
    for part in shapely.get_parts(mask):
        outline = list(part.exterior.coords)
        for a0, b0 in zip(outline, outline[1:]):
            section = LineString([a0, b0]).intersection(far)
            seams.extend(line for line in shapely.get_parts(section)
                         if line.geom_type == 'LineString' and line.length > .005)
    assert seams
    ready=read(ctx.files['READY.json'])
    caps=dict(base_m=0,roof_m=native['far']['height_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],
        far_sha256=sha(ctx.files['far.glb']),geometry=ctx.wgs(MultiLineString(seams)))
    tests=[('north garden edge beyond tower',6.98,-1.75,False),('north grass beyond facade',0,-.85,False),
           ('south garden lawn',0,9.25,False),('west side path',10.23,4.5,False),
           ('north street-facing wall',-.4,.085,True),('south garden windows',-.62,8.17,True),
           ('northwest tower',6.98,-.56,True),('west annexe',9.1,4.5,True),
           ('preserved source east end',-7.85,4.1,True),('known interior mass',1,5.33,True)]
    east=Point(-7.85,4.1)
    assert source.covers(east) and not mask.covers(east) and not collision.covers(east)
    for oid in NEIGHBORS:tests.append((NEIGHBORS[oid],*ctx.footprints[oid].representative_point().coords[0],True))
    probes=[]
    for name,x,y,want in tests:
        pt=Point(x,y);own=collision.covers(pt);ret=source.difference(mask).covers(pt)
        neighbor=[i for i,g in ctx.footprints.items()if i!=OWNER and g.covers(pt)]
        assert bool(own or ret or neighbor)==want,(name,own,ret,neighbor)
        item=dict(name=name,xy=[x,y],point=ctx.to_wgs(np.array([[x,y]]))[0].tolist(),
                  expected='building' if want else None,modelObstacle=own,cut=mask.covers(pt),retained=ret)
        if neighbor:item['ownerLocalId']=neighbor[0]
        probes.append(item)
    frame=r['author_frame']
    contract=dict(id=ID,**frame['anchor'],heading=frame['runtime_heading_deg'],scale=1,altitude=0,
       owner={'macro_id':r['frozen_macro'],'feature_local_id':OWNER},source_feature_ids={'building':[r['owner']['source_key'].removeprefix('building:')],'building_part':[]},
       bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
       replacement_geometry=ctx.wgs(mask),collision_geometry=ctx.wgs(collision),source_section_caps=caps,
       overviewBearing=139,overviewPitch=51,overviewZoom=19.2,maxDistance=620,lod_switch_in_m=510,lod_switch_out_m=665,
       navigation={'listed':False,'status':'可环绕观看北街面、西北圆塔、西端及花园立面。'},
       placement={'status':'estimated','note':'按2014年街照、天平街道旧档、杨浦图书馆塔照、两期屋面与501号实名点对合340。东端原有建筑、园区、岳阳路145号及独立邻楼保留。'},
       partial_model=True,model_scope=read(a.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(contract[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',contract)
    write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(fp),script_sha256=sha(Path(__file__)),
         manifest_sha256=sha(a.manifest),assets=assets,native=native,neighboring_buildings=others,model_m2=model.area,
         retained_east_end_xy=[-7.85,4.1],section_method="Measured projections of the three GLBs within 0.25 m of the original 501 residence, with 5.5 cm clearance before simplification.",
         cut_parts=len(shapely.get_parts(mask)),cut_coordinates=int(shapely.get_num_coordinates(mask)),
         ground_mesh_m2=feet.area,collision_m2=collision.area,ground_probes=probes,section_lengths_m=[line.length for line in seams],
         contract_sha256=sha(a.out/'final-placement-contract.json')))

if __name__=='__main__':
    measure()
