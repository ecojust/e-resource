"""Verify the partial street wall against the signed 473 front and its actual neighbors."""
from pathlib import Path
import argparse,sys,math
import numpy as np
import shapely as geo
from shapely.geometry import shape,box,Polygon,Point,MultiLineString,LineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-yuanyuanchang-bank-jiangxi-front'
OWNER=2729


def cap_on_boundary(cut,projection):
    raw=cut.boundary.intersection(projection)
    parts=geo.get_parts(geo.line_merge(raw))
    lines=[]
    for line in parts:
        coords=list(line.coords)
        for a,b in zip(coords,coords[1:]):
            if math.dist(a,b)>.003:lines.append([a,b])
    result=MultiLineString(lines)
    assert not result.is_empty and cut.boundary.buffer(.00002).covers(result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    opts=parser.parse_args();opts.out.mkdir(parents=True,exist_ok=True)
    review_path=PROJECT/'source/precise'/ID/'footprint-review.json'
    ref=read(review_path);site=PlacementMeshes(PROJECT,opts.work,ref)
    image_decoder=HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS']=(site.env.get('NODE_OPTIONS','')+' --require='+str(image_decoder)).strip()
    assets,bounds,form,physical=site.decode_model(opts.manifest)
    half=ref['width_m']/2
    cut=box(-half-.14,-.61,half+.14,.734)
    assert cut.covers(form),form.difference(cut).area
    group,=ref['near_tiles']
    assert set(group['feature_local_ids'])=={526,497,2729,664}
    decoded=site.decode_group(group,OWNER)
    src=site.footprints[OWNER]
    # Source ground behind the old eastern face stays closed. The three street steps
    # can be approached up to the green door, which sits back inside the reveal.
    solid=geo.union_all([src.intersection(cut),physical],grid_size=.001)
    pocket=box(-.94,-1.04,.94,.505)
    collision=solid.difference(pocket).buffer(.005,join_style='mitre').buffer(-.005,join_style='mitre').simplify(.002)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 6.34<=tops[variant]<=6.47
        assert .962<remain.area/area.area<.986
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>.5
        seams[variant]=cap_on_boundary(cut,area)
        seen[variant]={'assignment':assigned,'source_triangles':len(owned),'affected_source_triangles':affected,'unchanged_other_group_triangles':len(other),'other_source_distance_m':other_distance,'source_projected_m2':area.area,'retained_m2':remain.area,'retained_percent':remain.area*100/area.area,'source_roof_m':tops[variant],'mask_seam_m':seams[variant].length}
    agreement=seams['far'].hausdorff_distance(seams['near']);assert agreement<.22,agreement
    assert abs(tops['near']-tops['far'])<.06,tops
    ready=read(site.files['READY.json'])
    caps={'geometry':site.wgs(seams['far']),'base_m':0,'roof_m':tops['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(site.files['far.glb'])}
    nearbys=[]
    for i in ref['selection']['checked_neighbors']:
        fp=site.footprints[i];assert fp.distance(cut)>.40
        nearbys.append({'owner':i,'model_distance_m':fp.distance(form),'mask_distance_m':fp.distance(cut),'center_wgs84':list(shape(ref['owners'][next(j for j,o in enumerate(ref['owners'])if o['local_id']==i)]['geometry_wgs84']).representative_point().coords[0]),'remaining':True})
    points=[]
    def probe(name,x,y,solid,map_solid):
        pt=Point(x,y);actual=collision.covers(pt);blocked=actual or (not cut.covers(pt) and src.covers(pt))
        assert actual==solid and blocked==map_solid,(name,x,y,actual,blocked)
        points.append({'name':name,'xy':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),'model_obstacle':actual,'source_cut':cut.covers(pt),'expected_map':'building'if blocked else None})
    for x in (-8.89,-6.,-4.99,-2.7,2.7,4.99,6.,8.89):
        probe(f'Street pavement {x}',x,-.83,False,False)
        probe(f'Enclosed wall behind the street openings {x}',x,.516,True,True)
        probe(f'Former bank main volume behind the new face {x}',x,2.59,False,True)
    for x in (-.72,0.,.72):
        probe(f'Public steps to green entrance gate {x}',x,.36,False,False)
        probe(f'Closed street door behind reveal {x}',x,.62,True,True)
    for name,x,y in [('Southern lane between bank and adjoining block',-half-1.1,.35),
                      ('Northern public gap to low houses',half+.96,.18)]:
        probe(name,x,y,False,False)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':-150.,'overviewPitch':43,'overviewZoom':20.25,
        'maxDistance':435,'lod_switch_in_m':610,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'从香港路口西望江西中路473号棕砖门面、通高壁柱和横翼圆徽。'},
        'placement':{'status':'map-aligned','note':'保留2729原体与屋面，独立模型只替换江西中路东向街面。南侧麦林、北京里与北邻及路对面的自力大楼均按原位保留。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Bank east door threshold',collision=True);checked_geometry(contract['replacement_geometry'],'473 Jiangxi Road east street wall')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
