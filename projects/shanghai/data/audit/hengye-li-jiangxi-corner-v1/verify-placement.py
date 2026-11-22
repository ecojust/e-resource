"""Verify the rounded brick corner and the preserved lane against both signed city meshes."""
from pathlib import Path
import argparse,sys,math
import numpy as np
import shapely as geo
from shapely.geometry import box,Polygon,Point,MultiLineString,LineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-hengye-li-jiangxi-corner'
OWNER=2354


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
    sys.path.insert(0,str(review_path.parent/'source'))
    from brickwork import SOUTH_LENGTH,EAST_LENGTH,EAST_AXIS,EAST_TANGENT,CENTER,RADIUS,TURN
    south=np.array([CENTER[0]-SOUTH_LENGTH,0.]);north=np.array(EAST_TANGENT)+EAST_LENGTH*np.array(EAST_AXIS)
    street=LineString([south,[0.,0.],north])
    cut=street.buffer(1.24,cap_style='square',join_style='mitre')
    assert cut.covers(form)
    group,=ref['near_tiles']
    assert set(group['feature_local_ids'])=={2354,1259,1853,2558,2166,1079,717}
    decoded=site.decode_group(group,OWNER)
    src=site.footprints[OWNER]
    angle=np.linspace(0.,TURN,61)
    outside_radius=Polygon([[0.,0.],*[np.array(CENTER)+RADIUS*np.array([math.sin(k),-math.cos(k)]) for k in angle]])
    tx=np.array(EAST_AXIS)
    nx=np.array([tx[1],-tx[0]])
    doorway=np.array(EAST_TANGENT)+4.24*tx
    pocket=Polygon([doorway+tx*u+nx*d for u,d in [(-.52,.75),(.52,.75),(.52,-.308),(-.52,-.308)]])
    # Retain solid walls and the rear city volume. Expose the measured curve and the
    # short threshold in front of the recessed door panel on Middle Jiangxi Road.
    solid=geo.union_all([src.intersection(cut).difference(outside_radius),physical],grid_size=.001)
    collision=solid.difference(pocket).buffer(.012,join_style='mitre').buffer(-.012,join_style='mitre').simplify(.006)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 19.18<=tops[variant]<=19.22
        assert .973<remain.area/area.area<.980
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
        nearbys.append({'owner':i,'model_distance_m':fp.distance(form),'mask_distance_m':fp.distance(cut),'remaining':True})
    points=[]
    def probe(name,x,y,solid,map_solid):
        pt=Point(x,y);actual=collision.covers(pt);blocked=actual or (not cut.covers(pt) and src.covers(pt))
        assert actual==solid and blocked==map_solid,(name,x,y,actual,blocked)
        points.append({'name':name,'xy':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),'model_obstacle':actual,'source_cut':cut.covers(pt),'expected_map':'building'if blocked else None})
    def test_offset(name,axis,outward,tangent,lateral,offset,occupied,map_occupied):
        x,y=axis+tangent*lateral+outward*offset
        probe(name,float(x),float(y),occupied,map_occupied)
    for street_name,start,t,n in [('Sijing',south,np.array([1.,0.]),np.array([0.,-1.])),('Jiangxi',np.array(EAST_TANGENT),tx,nx)]:
        for i,along in enumerate((.42,2.52,5.92)):
            middle=start+t*along
            test_offset(f'{street_name} pavement {i+1}',middle,n,t,0.,1.66,False,False)
            test_offset(f'{street_name} enclosed ground wall {i+1}',middle,n,t,0.,-.48,True,True)
            test_offset(f'{street_name} original building behind wall {i+1}',middle,n,t,0.,-3.1,False,True)
    test_offset('Jiangxi door walking threshold before glass',doorway,nx,tx,.18,-.22,False,False)
    test_offset('Jiangxi door closed panel',doorway,nx,tx,.18,-.35,True,True)
    for deg in [20.,46.,70.]:
        n=np.array([math.sin(math.radians(deg)),-math.cos(math.radians(deg))])
        midpoint=np.array(CENTER)+RADIUS*n
        test_offset(f'rounded brick plinth {deg:g}',midpoint,n,tx,0.,-.25,True,True)
        test_offset(f'street beyond the curved plinth {deg:g}',midpoint,n,tx,0.,.42,False,False)
    for name,x,y in [('pavement in the original square corner',-.11,.08),('street junction',1.54,-1.71)]:
        probe(name,x,y,False,False)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':-58.,'overviewPitch':38,'overviewZoom':20.25,
        'maxDistance':435,'lod_switch_in_m':610,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'从江西中路与泗泾路交口看115号弧形灰砖墙、临街券窗和连续红砖腰线。'},
        'placement':{'status':'map-aligned','note':'按源面2354东南角及两条原有街线定位，保留楼后原体量和135弄另一原房2642。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Hengye corner collision',collision=True);checked_geometry(contract['replacement_geometry'],'115 Jiangxi Road corner mask')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
