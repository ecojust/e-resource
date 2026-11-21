"""Fit the documented garden elevation to a shallow portion of city feature 1519."""
from argparse import ArgumentParser
from pathlib import Path
import sys

import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, LineString, Polygon, shape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry

ID='xuhui-yongfu-road-151-south-front'
OWNER=1519


def section(mask, footprint):
    lines=[]
    for a,b in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        for segment in geo.get_parts(LineString([a,b]).intersection(footprint)):
            if segment.geom_type=='LineString' and segment.length>.012:
                lines.append([segment.coords[0],segment.coords[-1]])
    return MultiLineString(lines)


def solid_frontage():
    # The curved part's lower storeys are glazed. Its upper balcony is open.
    cx,cy,r=-5.94,2.98,2.88
    west=Polygon([(cx+r*np.cos(t),cy+r*np.sin(t))for t in np.linspace(np.pi,2*np.pi,19)])
    central=geo.box(-3.13,2.03,3.62,3.15)
    east=geo.box(3.51,1.07,8.87,3.15)
    return geo.union_all([west,central,east]).simplify(.045,preserve_topology=True)


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    ref_path=PROJECT/'source/precise'/ID/'footprint-review.json'
    reference=read(ref_path);site=PlacementMeshes(PROJECT,args.work,reference)
    assets,bounds,visible,_=site.decode_model(args.manifest)
    mask=geo.box(-9.12,-.91,9.00,3.23);collision=solid_frontage()
    assert mask.covers(visible) and mask.covers(collision)
    group,=reference['near_tiles'];assert OWNER in group['feature_local_ids']
    originals=site.decode_group(group,OWNER)
    sections={};variants={}
    for variant,(owned,others,ownership) in originals.items():
        footprint=site.project_faces(owned);retained=footprint.difference(mask)
        hit=geo.intersects(geo.polygons(owned[:,:,:2]),mask)
        assert hit.any()and .90<retained.area/footprint.area<1
        seam=section(mask,footprint)
        assert len(seam.geoms)==1
        peer_distance=site.project_faces(others).distance(mask)
        assert peer_distance>8
        variants[variant]={'original_triangles':len(owned),'intersecting_triangles':int(hit.sum()),
            'source_projected_area_m2':footprint.area,'retained_projected_area_m2':retained.area,
            'retained_fraction':retained.area/footprint.area,'min_distance_to_other_owners_m':peer_distance,
            'section_count':len(seam.geoms),'roof_m':float(owned[hit,:,2].max()),'ownership':ownership}
        sections[variant]=seam
    gap=sections['near'].hausdorff_distance(sections['far']);assert gap<.55
    ready=read(site.files['READY.json']);caps={'geometry':site.wgs(sections['far']),'base_m':0,
            'roof_m':variants['far']['roof_m'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],
            'far_sha256':sha(site.files['far.glb'])}
    assert shape(site.wgs(mask)).boundary.buffer(1e-8).covers(shape(caps['geometry']))
    probes=[]
    for label,xy,solid in [('garden-side center',[0,-1.3],False),('terrace front',[0,-.41],False),
                            ('ground beneath first-floor terrace',[0,.74],False),('central glazing',[0,2.2],True),
                            ('curved west casements',[-5.95,1.6],True),('outside curved west corner',[-8.77,.04],False),
                            ('east arcade frames',[6.16,1.29],True),('east arcade open foreground',[6.15,.64],False),
                            ('unmodified historic-source remainder',[0,5.5],False)]:
        point=geo.Point(*xy);assert collision.covers(point)==solid
        kept=site.footprints[OWNER].covers(point) and not mask.covers(point)
        probes.append({'name':label,'xy':xy,'modelObstacle':solid,'cut':mask.covers(point),'expected':'building'if solid or kept else None})
    owner=reference['owners'][0];angle=reference['author_frame']['runtime_heading_deg']
    record={'id':ID,'owner':{'macro_id':reference['frozen_macro'],'feature_local_id':OWNER},
            'source_feature_ids':{'building':[owner['key'].removeprefix('building:')],'building_part':[]},
            'replacement_geometry':site.wgs(mask),'collision_geometry':site.wgs(collision),'source_section_caps':caps,
            'lng':site.lon,'lat':site.lat,'heading':angle,'scale':1,'altitude':0,'bounds_glb':bounds,
            'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'overviewBearing':angle,'overviewPitch':42,
            'overviewZoom':20.20,'overview_focus_bounds_glb':bounds,'maxDistance':560,'lod_switch_in_m':520,'lod_switch_out_m':660,
            'navigation':{'listed':False,'status':'三开间南立面公开外观展示。'},'placement':{'status':'estimated',
            'note':'市历史建筑保护事务中心照片与2013年正、斜照片相对照，按南侧外观和航片檐线估放，位置估计误差约三米。'},
            'partial_model':True,'model_scope':read(args.manifest)['scope']}
    checked_geometry(record['collision_geometry'],'south facade masses',collision=True)
    checked_geometry(record['replacement_geometry'],'front source section')
    neighbors={}
    for k in reference['registration']['screened_other_local_ids']:
        footprint=site.footprints[k];assert footprint.distance(mask)>8
        pt=footprint.representative_point();neighbors[str(k)]=list(site.to_wgs(np.array([[pt.x,pt.y]]))[0])
    write(args.out/'final-placement-contract.json',record)
    write(args.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(args.manifest),'source_sha256':sha(ref_path),
          'checker_sha256':sha(Path(__file__)),'assets':assets,'model_projection_m2':visible.area,'collision_m2':collision.area,
          'cut_m2':mask.area,'variants':variants,'cap_segments':1,'cap_agreement_m':gap,'ground_probes':probes,'neighbor_points_wgs84':neighbors})
    print('Source-preservation check',variants,flush=True)


if __name__=='__main__':main()
