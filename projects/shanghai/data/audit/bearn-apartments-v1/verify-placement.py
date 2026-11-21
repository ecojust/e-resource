"""Verify the two street faces against the separate Bearn apartment and courtyard source meshes."""
from argparse import ArgumentParser
from pathlib import Path
import sys
import numpy as np
import shapely as geo
from shapely.geometry import LineString,MultiLineString,Polygon,shape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='huangpu-bearn-apartments'
SOURCE=PROJECT/'source/precise'/ID
sys.path[:0]=[str(PROJECT/'tools'),str(SOURCE/'source')]
from candidate_placement_meshes import PlacementMeshes,read,sha,write
from build_candidate_city_integrations import checked_geometry


def outline(points,front,back):
    points=np.asarray(points,dtype=float)
    edges=points[1:]-points[:-1]
    normals=np.column_stack([-edges[:,1],edges[:,0]])/np.linalg.norm(edges,axis=1)[:,None]
    shifts=[normals[0]]
    for left,right in zip(normals,normals[1:]):
        shifts.append((left+right)/(1+left@right))
    shifts.append(normals[-1])
    shift=np.asarray(shifts)
    return Polygon([*(points+front*shift),*reversed(points+back*shift)])


def seams(cut,foot):
    lines=[]
    for a,b in zip(cut.exterior.coords,list(cut.exterior.coords)[1:]):
        segment=LineString([a,b]).intersection(foot)
        for part in geo.get_parts(segment):
            if part.geom_type=='LineString' and part.length>.03:
                lines.append([part.coords[0],part.coords[-1]])
    return MultiLineString(lines)


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    args=parser.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    cfg=read(SOURCE/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,cfg)
    params=read(SOURCE/'source/parameters.json')
    assets,bounds,projection,ground=site.decode_model(args.manifest)
    front=params['outer_front'];depth=params['roof_cut_depth_m']
    collision=outline(front,0,depth).simplify(.005)
    cut=outline(front,-.80,depth+.13).buffer(.12,join_style='mitre').simplify(.01)
    assert collision.is_valid and cut.covers(projection) and cut.covers(collision)
    assert collision.symmetric_difference(ground).area<3.3,(collision.area,ground.area,collision.symmetric_difference(ground).area)
    group,=cfg['near_tiles'];owner_id=97
    selected=site.decode_group(group,owner_id);variants={};sections={};all_heights={}
    for role,(tris,other,assignment) in selected.items():
        native=site.project_faces(tris);retained=native.difference(cut);neighbor=site.project_faces(other)
        assert native.area>2500 and .45<retained.area/native.area<.75
        assert neighbor.distance(cut)>4
        section=seams(cut,native);assert not section.is_empty
        sections[role]=section
        meets=geo.intersects(geo.polygons(tris[:,:,:2]),cut)
        assert meets.any()
        height=float(tris[meets,:,2].max());all_heights[role]=height
        assert 21<height<34
        variants[role]=dict(assignment=assignment,triangles=len(tris),hit_triangles=int(meets.sum()),native_area_m2=native.area,
                            retained_area_m2=retained.area,retained_fraction=retained.area/native.area,roof_m=height,
                            other_draw_clearance_m=neighbor.distance(cut),section_segments=len(section.geoms))
    mismatch=sections['near'].hausdorff_distance(sections['far']);assert mismatch<1
    ready=read(site.files['READY.json']);caps=dict(geometry=site.wgs(sections['far']),base_m=0,roof_m=all_heights['far'],
        height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    assert shape(site.wgs(cut)).boundary.buffer(1e-8).covers(shape(caps['geometry']))
    g=site.footprints[owner_id];tests=[]
    for name,x,y,blocked,existing in [
        ('Huaihai Road carriageway',0,-4,False,False),('pavement below shop canopy',4,-.46,False,False),
        ('central shopfront',0,.85,True,False),('red brick street bays',12,3.25,True,False),
        ('western end of visible north wing',31,4.25,True,False),('central crown footprint',0,8,True,False),
        ('curved eastern street facade',-45,6.5,True,False),('east side return',-48,12.5,True,False),
        ('rear retained north wing',0,15,False,True),('retained outer west wing',45,14,False,True),
        ('Chongqing Road outside the corner',-59,12,False,False),('road outside the long street wall',24,-2.75,False,False)]:
        pt=geo.Point(x,y);obs=collision.covers(pt);old=g.covers(pt) and not cut.covers(pt)
        assert obs==blocked and old==existing,(name,x,y,obs,old)
        tests.append(dict(name=name,xy=[x,y],modelObstacle=obs,cut=cut.covers(pt),expected='building' if old or obs else None))
    preserve={}
    for i in cfg['registration']['screened_other_local_ids']:
        poly=site.footprints[i];distance=poly.distance(cut)
        assert distance>.5,(i,distance)
        point=poly.representative_point();wgs=site.to_wgs(np.array([[point.x,point.y]]))[0]
        preserve[str(i)]={'inside_position':wgs.tolist(),'clearance_m':distance}
    owner=next(r for r in cfg['owners'] if r['local_id']==owner_id);heading=cfg['author_frame']['runtime_heading_deg']
    record=dict(id=ID,owner=dict(macro_id=cfg['frozen_macro'],feature_local_id=owner_id),
        source_feature_ids=dict(building=[owner['key'].removeprefix('building:')],building_part=[]),
        lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:r['sha256'] for k,r in assets.items()},replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),
        source_section_caps=caps,overviewBearing=heading+8,overviewPitch=47,overviewZoom=18.45,
        maxDistance=880,lod_switch_in_m=610,lod_switch_out_m=770,navigation={'listed':False,'status':'淮海中路与重庆南路公开街面。'},
        placement={'status':'estimated','note':'97号U形街楼北段与东端圆弧，保留97的其余两翼及院内1180号同名楼、979号配楼。'},
        partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(record['collision_geometry'],'Bearn street front',collision=True)
    checked_geometry(record['replacement_geometry'],'Bearn cut')
    write(args.out/'final-placement-contract.json',record)
    write(args.out/'placement-geometry.json',dict(id=ID,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest),
        footprint_sha256=sha(SOURCE/'footprint-review.json'),assets=assets,variants=variants,
        model_ground_m2=ground.area,model_projection_m2=projection.area,physical_obstacle_m2=collision.area,cut_m2=cut.area,
        near_far_section_gap_m=mismatch,cap_segments=len(sections['far'].geoms),ground_probes=tests,preserved_neighbors=preserve))
    print('Passed',variants,flush=True)


if __name__=='__main__':
    main()
