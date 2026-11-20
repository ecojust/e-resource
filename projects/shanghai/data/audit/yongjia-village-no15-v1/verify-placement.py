"""Check the No. 15 garden wall, porch and east return against frozen parcel 4151."""
import argparse
from pathlib import Path
import runpy
import sys
import numpy as np
import shapely
from shapely.geometry import box, Point, LineString, MultiLineString, shape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry
ID = 'xuhui-yongjia-village-no15'
OWNER = 4151
NEIGHBORS = {4677:'东邻13、14号所在排',3242:'花园南侧小体量',4962:'西南小体量',2978:'西北附房',1204:'北侧另一排住宅'}
read_group = runpy.run_path(str(HERE.parent/'grace-church-street-front-v1/verify-placement.py'))['read_group']

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
    # Trim the original fabric only where the authored facade and the east return meet it.
    # The front fence and porch outside the source do not cut the pavement or neighboring houses.
    mask = model.buffer(.055,join_style='mitre').simplify(.045,preserve_topology=True).intersection(source.buffer(.25,join_style='mitre'))
    assert mask.is_valid and model.intersection(source).difference(mask).area < .00002
    from shapely.geometry import LineString
    yard_walls = [LineString([(-4.65,-2.86),(4.40,-2.86),(4.40,-.15)]).buffer(.102,cap_style='flat',join_style='mitre')]
    solids = [box(-4.65,-.02,4.65,1.10),box(4.25,0,4.68,4.10),
              box(-4.63,-1.40,-2.45,.01),*yard_walls]
    collision=shapely.union_all(solids)
    native={};others={}
    for oid in [OWNER,*NEIGHBORS]:
        group=next(g for g in r['near_tiles']if oid in g['feature_local_ids'])
        meshes=read_group(ctx,group,oid)
        if oid==OWNER:
            for role,(tri,peer,method) in meshes.items():
                own=ctx.project_faces(tri);neighbors=ctx.project_faces(peer);left=own.difference(mask)
                assert .72 < left.area/own.area < .99 and neighbors.distance(mask)>.15,(role,left.area/own.area,neighbors.distance(mask))
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
    tests=[('lane before garden',0,-3.25,False),('open space beyond east end',5.12,-1.51,False),
           ('garden screen wall',0,-2.86,True),('return screen wall',4.40,-1.43,True),
           ('inside garden',1.20,-1.60,False),('porch threshold',-3.54,-1.23,True),
           ('front wall',1.40,.077,True),('eastern wall',4.53,2.20,True),('retained northern rooms',.82,2.65,True)]
    addr=read(PROJECT/'source/precise'/ID/'number-and-roof.json')['address_records'];shared=[]
    for number in ['16','20','21']:
        coords=addr[number]['wgs'];xy=ctx.to_xy(np.array([coords]))[0].tolist();pt=Point(*xy)
        assert source.covers(pt) and not mask.covers(pt) and not collision.covers(pt), (number,xy)
        tests.append(('retained map address '+number,*xy,True));shared.append(dict(number=number,wgs84=coords,local=xy))
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
       overviewBearing=-74,overviewPitch=25,overviewZoom=19.4,maxDistance=620,lod_switch_in_m=510,lod_switch_out_m=665,
       navigation={'listed':False,'status':'展示小门廊、花墙和东端山墙，室内未制作。'},
       placement={'status':'estimated','note':'按2014年1月26日15号门牌立面、同名门牌点及2024与2026年航片对合4151东侧。保留同栋16、20、21号门牌和东侧13、14号住宅。'},
       partial_model=True,model_scope=read(a.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(contract[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',contract)
    write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(fp),script_sha256=sha(Path(__file__)),
         manifest_sha256=sha(a.manifest),assets=assets,native=native,neighboring_buildings=others,model_m2=model.area,
         retained_addresses=shared,section_method="Measured projections of the three GLBs within 0.25 m of the existing row house, with 5.5 cm clearance before simplification.",
         cut_parts=len(shapely.get_parts(mask)),cut_coordinates=int(shapely.get_num_coordinates(mask)),
         ground_mesh_m2=feet.area,collision_m2=collision.area,ground_probes=probes,section_lengths_m=[line.length for line in seams],
         contract_sha256=sha(a.out/'final-placement-contract.json')))

if __name__=='__main__':
    measure()
