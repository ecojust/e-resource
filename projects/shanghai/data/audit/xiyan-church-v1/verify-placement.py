"""Bind four real macro files and the three emitted chapel meshes; preserve the belfry and surrounding properties."""
import argparse,math,os,sys,tempfile
from pathlib import Path
import shapely as sg
from shapely.geometry import Point,Polygon,shape
import numpy as np
A=Path(__file__).resolve().parent;P=A.parents[2];ID='changning-xiyan-church';OWNER=850
sys.path.insert(0,str(P/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry


def solid_outline(g):
    rings=[g] if g.geom_type=='Polygon' else [f for f in g.geoms if f.geom_type=='Polygon']
    return sg.union_all([Polygon(f.exterior)for f in rings])


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--manifest',type=Path,default=P/'assets/models/candidates'/ID/'manifest.json');cli.add_argument('--macro',type=Path);cli.add_argument('--out',type=Path,required=True);args=cli.parse_args()
    src=read(P/'source/precise'/ID/'footprint-review.json');study=read(P/'source/precise'/ID/'tower-exclusion.json');frozen=src['frozen_bindings'];model=read(args.manifest)
    with tempfile.TemporaryDirectory()as tmp:
        d=Path(tmp)
        if args.macro:
            for ref in frozen:
                path=ref['repository_path'].split(src['frozen_macro']+'/')[1];os.link(args.macro/path,d/Path(path).name)
        layout=PlacementMeshes(P,d,src);source=layout.decode_group(src['near_tiles'][0],OWNER)
        assets,bounds,visual,ground=layout.decode_model(args.manifest)
        roof={};others={};report={}
        for role,(tri,adj,explain) in source.items():
            roof[role]=layout.project_faces(tri);others[role]=layout.project_faces(adj)
            report[role]={'triangles':len(tri),'other_triangles':len(adj),'source_height_m':float(tri[:,:,2].max()),'old_area_m2':roof[role].area,'assignment':explain}
        joint=sg.union_all([*roof.values(),layout.footprints[OWNER]])
        # Buffer the registry's simple exterior, then measure every native triangle. A close offset
        # permits the streamed wall mouldings to project beyond the polygon without leaving slivers.
        mask=layout.footprints[OWNER].buffer(.39,join_style='mitre')
        assert joint.difference(mask).area<.001
        # These solid closed-door walls enclose the nave. Fill only interiors connected to the
        # surveyed ground ring; neither the cemetery nor the space below a high roof is appended.
        walk=solid_outline(ground.buffer(.024,join_style='mitre')).simplify(.06,preserve_topology=True)
        assert walk.is_valid and walk.geom_type=='Polygon' and 235<walk.area<376,(walk.geom_type,walk.area)
        assert walk.area>=.75*visual.area and walk.area<visual.area*1.025

        tower_wgs=study['tower']['coordinates'];tower=sg.transform(Point(tower_wgs),layout.to_xy)
        assert not walk.covers(tower) and not mask.covers(tower) and mask.distance(tower)>1.80
        near_owner=dict.fromkeys(src['near_tiles'][0]['feature_local_ids'])
        for role,g in roof.items():
            item=report[role];item.update({'original_removed_m2':g.intersection(mask).area,'residual_m2':g.difference(mask).area,'closest_neighbor_to_mask_m':others[role].distance(mask),'closest_neighbor_to_rendered_model_m':others[role].distance(visual),'closest_neighbor_to_collision_m':others[role].distance(walk),'source_to_northeast_tower_m':g.distance(tower)})
            assert item['residual_m2']<.001 and item['closest_neighbor_to_mask_m']>13 and item['closest_neighbor_to_rendered_model_m']>13
        neighbors={}
        for i,g in layout.footprints.items():
            if i==OWNER:continue
            if i in near_owner or g.distance(mask)<63:
                assert g.intersection(mask).area<.001 and walk.intersection(g).area<.001
                neighbors[i]={'clip_clearance_m':g.distance(mask),'model_clearance_m':g.distance(visual),'collision_clearance_m':g.distance(walk),'in_near_group':i in near_owner}
        witnesses=[('closed northeast door',(.12,-9.10),True),('main nave',(.35,2.25),True),('riverside semicircular apse',(-9.45,.20),True),('lower ritual room',(3.1,5.6),True),('approach in front of the thresholds',(0,-11.65),False),('river-edge walkway',(-13.4,0),False),('northwest side path',(12,0),False),('rear of body',(0,12.1),False),('detached tower point',list(tower.coords[0]),False)]
        groundchecks=[]
        for name,xy,inside in witnesses:
            pt=Point(xy);actual=walk.covers(pt);assert actual==inside,(name,actual,inside)
            groundchecks.append({'name':name,'local_xy':list(xy),'expected_obstacle':inside,'cut':mask.covers(pt),'point_wgs84':layout.wgs(pt)['coordinates']})
        camera=read(P/'source/precise'/ID/'camera-preflight.json');_,bearing,pitch=camera['recommendation']
        frame=src['author_frame'];cut_geo=layout.wgs(mask);coll_geo=layout.wgs(walk)
        checked_geometry(cut_geo,'replacement_geometry');checked_geometry(coll_geo,'collision_geometry',collision=True)
        contract={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,'owner':{'macro_id':src['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[src['owner']['source_key'].split(':')[1]],'building_part':[]},'replacement_geometry':cut_geo,'osm_replacement_geometry':src['source_geometry_wgs84'],'collision_geometry':coll_geo,'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'overviewBearing':bearing,'overviewPitch':pitch,'overviewZoom':19.5,'maxDistance':500,'lod_switch_in_m':550,'lod_switch_out_m':700,'navigation':{'listed':False,'status':'主堂现状外观，仅供俯瞰。'},'placement':{'status':'estimated','note':'据具名宗堂w502997517@3与东侧河岸配准。现状外轮廓约357平方米，教区另记239平方米。独立北钟楼位于东偏北的源面以外，墓园与周边无新增碰撞。'},'partial_model':False,'model_scope':model['model_scope_zh']}
        args.out.mkdir(exist_ok=True,parents=True);write(args.out/'final-placement-contract.json',contract);write(args.out/'footprint-review.json',{'id':ID,'frozen_source_bindings':frozen,'source_sha256':sha(P/'source/precise'/ID/'footprint-review.json'),'manifest_sha256':sha(args.manifest),'script_sha256':sha(Path(__file__)),'contract_sha256':sha(args.out/'final-placement-contract.json'),'asset_sha256':assets,'verified_owner':src['owner'],'bounds_glb':bounds,'near_and_far':report,'near_feature_count':len(near_owner),'collision_area_m2':walk.area,'cut_area_m2':mask.area,'model_projection_m2':visual.area,'river_path_and_tower':{'separate_tower_node':study['tower'],'tower_to_mask_m':mask.distance(tower),'tower_to_model_projection_m':visual.distance(tower),'tower_to_walk_m':walk.distance(tower)},'neighbors':neighbors,'ground_witnesses':groundchecks})
        print('verified',[(k,q['triangles'],q['residual_m2'])for k,q in report.items()],len(neighbors),walk.area,mask.distance(tower),flush=True)


if __name__=='__main__':main()
