"""Measure the delivered garden elevation against old-city mesh 1355 and the detached garden buildings."""
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
ID = 'jingan-dasheng-drummond-residence'
OWNER = 1355
NEIGHBORS = {3904:'兴趣点落位的独立小楼',2225:'西侧相邻建筑',401:'花园西南住宅',
             1345:'北侧住宅长排',2694:'东南附房'}
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
    # Cut only the portions of the three authored sections intersecting the existing hall.
    # The source-side allowance covers differences between the vector, near and far boundaries.
    source = ctx.footprints[OWNER]
    modeled_sections = model.buffer(.06, join_style="mitre").simplify(.03, preserve_topology=True)
    mask = modeled_sections.intersection(source.buffer(.30, join_style="mitre"))
    assert mask.is_valid and len(shapely.get_parts(mask)) == 3
    assert model.intersection(source).difference(mask).area < .00001
    # The stairs and raised stone podium are exterior objects. The model has no enterable hall.
    solids=[box(-3.06,2.50,3.06,9.65),box(-3.22,.26,3.22,2.72),
            box(-4.85,.195,4.85,.65)]
    for sign in [-1,1]:
        cx=sign*5.75
        solids.append(box(cx-2.335,2.94,cx+2.335,9.65))
        stair=sorted([3.08*sign,5.35*sign]);solids.append(box(stair[0],.47,stair[1],2.24))
    collision=shapely.union_all(solids)
    native={};others={}
    for oid in [OWNER,*NEIGHBORS]:
        group=next(g for g in r['near_tiles']if oid in g['feature_local_ids'])
        meshes=read_group(ctx,group,oid)
        if oid==OWNER:
            for role,(tri,peer,method) in meshes.items():
                own=ctx.project_faces(tri);neighbors=ctx.project_faces(peer);left=own.difference(mask)
                assert .89 < left.area/own.area < .96 and neighbors.distance(mask)>2,(role,left.area/own.area,neighbors.distance(mask))
                intrusion = left.intersection(model).area
                assert intrusion < .00001, (role, intrusion)
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
                assert geo.distance(mask)>2.5,(oid,role,geo.distance(mask))
                item[role]=dict(triangles=len(tri),cut_m2=geo.intersection(mask).area,gap_m=geo.distance(mask),assignment=method)
            others[oid]=item
    seams=[]
    for part in shapely.get_parts(mask):
        outline = list(part.exterior.coords)
        for a0, b0 in zip(outline, outline[1:]):
            section = LineString([a0, b0]).intersection(far)
            seams.extend(line for line in shapely.get_parts(section)
                         if line.geom_type == 'LineString' and line.length > .005)
    ready=read(ctx.files['READY.json'])
    caps=dict(base_m=0,roof_m=native['far']['height_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],
        far_sha256=sha(ctx.files['far.glb']),geometry=ctx.wgs(MultiLineString(seams)))
    tests=[('lawn path',0,-2,False),('before curved garden wall',0,.10,False),('central screen',0,.31,True),
           ('left landing stair',-4.45,1.2,True),('right landing stair',4.45,1.2,True),
           ('porch landing',0,1.65,True),('central lower entrance',0,2.91,True),
           ('space before left gallery',-6.8,2.60,False),('west gallery base',-6.8,3.12,True),
           ('space before right gallery',6.8,2.60,False),('east gallery base',6.8,3.12,True),
           ('retained northern hall',0,12.7,True)]
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
       overviewBearing=-18,overviewPitch=60,overviewZoom=19.4,maxDistance=620,lod_switch_in_m=510,lod_switch_out_m=665,
       navigation={'listed':False,'status':'展示庭院立面的门廊、双山花和石阶，室内未制作。'},
       placement={'status':'estimated','note':'按2024与2026年庭院北侧的三处屋面构件对合2014年与2022年花园实照。保留宅后体量、独立小楼3904及其他里弄住宅。'},
       partial_model=True,model_scope=read(a.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(contract[key],key,collision=key=='collision_geometry')
    write(a.out/'final-placement-contract.json',contract)
    write(a.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(fp),script_sha256=sha(Path(__file__)),
         manifest_sha256=sha(a.manifest),assets=assets,native=native,neighboring_buildings=others,model_m2=model.area,
         section_method="Three delivered mesh projections within 0.30 m of the original native footprint, with 0.06 m clearance before simplification.",
         cut_parts=len(shapely.get_parts(mask)),cut_coordinates=int(shapely.get_num_coordinates(mask)),
         ground_mesh_m2=feet.area,collision_m2=collision.area,ground_probes=probes,section_lengths_m=[line.length for line in seams],
         contract_sha256=sha(a.out/'final-placement-contract.json')))

if __name__=='__main__':
    measure()
