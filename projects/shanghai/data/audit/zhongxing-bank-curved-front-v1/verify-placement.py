"""Verify the continuous round corner of the six-storey street building against the native near and far meshes for the single retained owner."""
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
ID='huangpu-zhongxing-bank-curved-front'
OWNER=2362


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
    radius=9.733486353059083
    half_arc=6.523359974253377
    def plan(s,d):
        t=s/radius
        return ((radius+d)*math.sin(t),radius-(radius+d)*math.cos(t))
    def strip(arc,front,back):
        # A shared pair of sampled arcs follows the named corner without modifying either long wing.
        stations=np.linspace(-arc,arc,13)
        return Polygon([plan(s,front)for s in stations]+[plan(s,back)for s in reversed(stations)])
    cut=strip(half_arc+.035,.56,-1.45)
    assert cut.is_valid and 22<cut.area<31
    groups=ref['near_tiles']
    assert len(groups)==1 and OWNER in groups[0]['feature_local_ids']
    decoded=site.decode_group(groups[0],OWNER)
    src=site.footprints[OWNER]
    section=__import__('runpy').run_path(str(HERE.parent/'sino-french-school-v1/verify-placement.py'))['solid_section']
    ground=[]
    for item in read(site.work/'delivered-decode.json'):
        triangles=np.fromfile(item['triangle_file'],np.float64).reshape(-1,3,3)
        local=triangles[:,:,[0,2,1]]*[1,-1,1]
        ground.append(section(local,.553))
    # All three street bays are closed by windows. At the sampled 55 cm height,
    # the section captures the solid lower wall so its face follows the real curvature.
    room=strip(half_arc-.015,-.335,-1.46).intersection(cut)
    collision=geo.union_all([room,*ground],grid_size=.001).simplify(.004,preserve_topology=True)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 18.9<=tops[variant]<=19.45,tops
        assert .96<remain.area/area.area<.999,(variant,remain.area/area.area)
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>.5
        seams[variant]=cap_on_boundary(cut,area)
        seen[variant]={'assignment':assigned,'source_triangles':len(owned),'affected_source_triangles':affected,'unchanged_other_group_triangles':len(other),'other_source_distance_m':other_distance,'source_projected_m2':area.area,'retained_m2':remain.area,'retained_percent':remain.area*100/area.area,'source_roof_m':tops[variant],'mask_seam_m':seams[variant].length}
    if opts.out.name=='placement-pilot':
        from shapely.geometry import mapping
        write(opts.out/'measured-source.json',dict(variants=seen,cap={k:mapping(g) for k,g in seams.items()},geometries={k:mapping(site.project_faces(held[0]).simplify(.02)) for k,held in decoded.items()},mask=mapping(cut),source=mapping(src)))
    agreement=seams['far'].hausdorff_distance(seams['near']);assert agreement<.55,agreement
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
    for s in (-4.3489,0.,4.3489):
        for label,depth,solid,blocked in [('open pavement',1.05,False,False),('upper eave over pavement',.43,False,False),('before shop wall',.10,False,False),('stone plinth',-.08,True,True),('back of fascia',-.8,True,True)]:
            x,y=plan(s+.18,depth);probe(f'arc {s:.2f} '+label,x,y,solid,blocked)
    for s in (-5.94,-2.18,2.18,5.90):
        x,y=plan(s,-.25);probe(f'arc pier {s:.2f}',x,y,True,True)
    x,y=plan(.16,-3.5);probe('retained building behind street wall',x,y,False,True)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':215.54,'overviewPitch':48,'overviewZoom':19.63,
        'maxDistance':435,'lod_switch_in_m':610,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'从福州路与四川中路路口观看前楼圆弧窗墙。'},
        'placement':{'status':'map-aligned','note':'依据福州路89号东北街角的五个节点定位前楼圆弧，沿两街长翼及后院维持原城几何。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Rounded base and pavement',collision=True);checked_geometry(contract['replacement_geometry'],'Zhongxing northeast frontage')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'texture_decoder_sha256':sha(decoder),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
