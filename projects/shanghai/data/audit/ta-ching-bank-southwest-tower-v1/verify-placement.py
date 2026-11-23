"""Verify the three street facets and two short returns of the low copper-domed southwest corner against the native near and far meshes for the single retained owner."""
from pathlib import Path
import argparse,sys,math
import numpy as np
import shapely as geo
from shapely.geometry import box,Point,MultiLineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-ta-ching-bank-southwest-tower'
OWNER=59


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
    decoder=HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS']=(site.env.get('NODE_OPTIONS','')+' --require='+str(decoder)).strip()
    assets,bounds,form,physical=site.decode_model(opts.manifest)
    from shapely.geometry import Polygon
    # Model only the neighbourhood of the low southwest cupola and the first street bays.
    ap=2.66215; half=ap*(math.sqrt(2)-1); radius=ap/math.cos(math.pi/8)
    octagon=Polygon([(radius*math.cos(math.pi/8+j*math.pi/4),half+radius*math.sin(math.pi/8+j*math.pi/4)) for j in range(8)])
    left=np.array([-ap,0.]);right=np.array([ap,0.])
    ends=[(left+3.65*np.array([-.5275,.84955]),left),(right,right+3.65*np.array([.84201,.53946]))]
    strips=[]
    for a,b in ends:
        tangent=(b-a)/np.linalg.norm(b-a)
        front=np.array([tangent[1],-tangent[0]])
        strips.append(Polygon([a+.35*front,b+.35*front,b-.53*front,a-.53*front]))
    # The native near wall lies 7 cm beyond the simplified original chamfer.
    # Extend the mask 15 cm below the upper stone cornice so both levels share its rear cap.
    cut=geo.union_all([octagon.buffer(.15,join_style=2),*strips]).simplify(.012,preserve_topology=True)
    assert cut.geom_type=='Polygon' and cut.is_valid and 27<cut.area<39
    groups=ref['near_tiles']
    assert len(groups)==1 and set(groups[0]['feature_local_ids'])=={2602,1064,431,59,1618,1797}
    decoded=site.decode_group(groups[0],OWNER)
    src=site.footprints[OWNER]
    section=__import__('runpy').run_path(str(HERE.parent/'sino-french-school-v1/verify-placement.py'))['solid_section']
    ground=[]
    for item in read(site.work/'delivered-decode.json'):
        triangles=np.fromfile(item['triangle_file'],np.float64).reshape(-1,3,3)
        local=triangles[:,:,[0,2,1]]*[1,-1,1]
        ground.append(section(local,.553))
    # Original occupancy continues behind the photographed wall. The street recess ends at each sash.
    # Use the interior side of each segment, starting behind the real glazing.
    front_poly=octagon.buffer(-.345,join_style=2)
    room=front_poly.intersection(cut)
    for a,b in ends:
        tangent=(b-a)/np.linalg.norm(b-a);normal=np.array([-tangent[1],tangent[0]])
        room=room.union(Polygon([a+.343*normal,b+.343*normal,b+.54*normal,a+.54*normal]).intersection(src))
    collision=geo.union_all([room,*ground],grid_size=.001).simplify(.004,preserve_topology=True)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 12.70<=tops[variant]<=12.90,tops
        assert .969<remain.area/area.area<.998,(variant,remain.area/area.area)
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>.5
        seams[variant]=cap_on_boundary(cut,area)
        seen[variant]={'assignment':assigned,'source_triangles':len(owned),'affected_source_triangles':affected,'unchanged_other_group_triangles':len(other),'other_source_distance_m':other_distance,'source_projected_m2':area.area,'retained_m2':remain.area,'retained_percent':remain.area*100/area.area,'source_roof_m':tops[variant],'mask_seam_m':seams[variant].length}
    if opts.out.name=='placement-pilot':
        from shapely.geometry import mapping
        write(opts.out/'measured-source.json',dict(variants=seen,cap={k:mapping(g) for k,g in seams.items()},geometries={k:mapping(site.project_faces(held[0]).simplify(.02)) for k,held in decoded.items()},mask=mapping(cut),source=mapping(src)))
    agreement=seams['far'].hausdorff_distance(seams['near']);assert agreement<.21,agreement
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
    front=half-ap
    for x in (-.34,.36):
        probe('outside central arch',x,front-.64,False,False)
        probe('street recess before sash',x,front+.18,False,False)
        probe('closed central glazing',x,front+.329,True,True)
        probe('inside west corner tower',x,front+.61,True,True)
    for x in (-.88,.88):
        probe('ground floor masonry',x,front+.20,True,True)
    for x in (-1.,0.,1.):
        probe('retained original main block',x,6.8,False,True)
    for side,(a,b) in enumerate(ends):
        mid=(a+b)/2;tangent=(b-a)/np.linalg.norm(b-a);normal=np.array([-tangent[1],tangent[0]])
        for d,is_solid,n in [(-.60,False,'street'),(.19,False,'shallow recess'),(.329,True,'glazing'),(.45,True,'occupied interior')]:
            x,y=mid+.28*tangent+d*normal;probe('return '+str(side)+' '+n,x,y,is_solid,is_solid)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':17,'overviewPitch':48,'overviewZoom':19.66,
        'maxDistance':435,'lod_switch_in_m':610,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'从汉口路与四川中路路口仰看转角窗墙和低矮铜穹。'},
        'placement':{'status':'map-aligned','note':'以原城西南切角及两条街线定位，仅替换角塔与相邻首间窗墙对应的一小段，长翼、正门和高穹顶对应的原城主体保留。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Southwest street recesses',collision=True);checked_geometry(contract['replacement_geometry'],'Southwest octagonal tower')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'texture_decoder_sha256':sha(decoder),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
