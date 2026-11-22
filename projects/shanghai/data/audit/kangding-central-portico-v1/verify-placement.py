"""Verify the rectangular south garden loggia against the native near and far meshes for the single retained owner."""
from pathlib import Path
import argparse,sys,math,subprocess,gzip
import numpy as np
import shapely as geo
from shapely.geometry import box,Point,MultiLineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='jingan-kangding-garden-central-portico'
OWNER=1431


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



def decode_for_cut(site,group,cut):
    """Check ownership for every triangle intersecting the actual cut, with the tagged far mesh as a control."""
    ids=group['feature_local_ids']
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':i} for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env={**site.env,'NODE_OPTIONS':site.env.get('NODE_OPTIONS','')+' --require='+str(HERE/'compact-source.cjs')},check=True,stdout=subprocess.DEVNULL)
    output={}
    for variant in ('near','far'):
        tris=np.frombuffer(gzip.decompress((site.work/f'baseline-{variant}-triangles.f64.gz').read_bytes()),np.float64).copy().reshape(-1,3,3)
        tris[:,:,:2]=tris[:,:,:2]@site.axes.T
        centers=geo.points(tris[:,:,:2].mean(1))
        distances=np.stack([geo.distance(centers,site.footprints[i])for i in ids],axis=1)
        inferred=np.asarray(ids)[distances.argmin(1)]
        owners=inferred if variant=='near' else np.frombuffer(gzip.decompress((site.work/'baseline-far-owners.u32.gz').read_bytes()),np.uint32)
        affected=geo.intersects(cut,geo.polygons(tris[:,:,:2]))
        assert set(owners)==set(ids) and set(owners[affected])==set(inferred[affected])=={OWNER}
        ranks=np.sort(distances[affected],axis=1);deviation=float(ranks[:,0].max());margin=float((ranks[:,1]-ranks[:,0]).min())
        assert deviation<.15 and margin>.22 and margin>2*deviation,(variant,deviation,margin)
        other_distance=site.project_faces(tris[owners!=OWNER]).distance(cut)
        assert other_distance>.20,(variant,other_distance)
        assignment=dict(method='Native far feature IDs; with near triangle centroids assigned against all source group footprints.',affected_count=int(affected.sum()),largest_affected_owner_distance_m=deviation,smallest_affected_next_margin_m=margin,nearest_other_actual_mesh_m=other_distance,source_ids=ids)
        output[variant]=tris[owners==OWNER],tris[owners!=OWNER],assignment
    return output


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
    from shapely.geometry import LineString
    frame=read(review_path.parent/'street-registration.json')
    assert 28.8<frame['edge_length_m']<29.0
    street=LineString([(-8.49,0),(8.49,0)])
    cut=box(-8.49,-1.25,8.49,5.50)
    groups=ref['near_tiles']
    assert len(groups)==1 and OWNER in groups[0]['feature_local_ids']
    decoded=decode_for_cut(site,groups[0],cut)
    src=site.footprints[OWNER]
    section=__import__('runpy').run_path(str(HERE.parent/'sino-french-school-v1/verify-placement.py'))['solid_section']
    ground=[]
    for item in read(site.work/'delivered-decode.json'):
        triangles=np.fromfile(item['triangle_file'],np.float64).reshape(-1,3,3)
        local=triangles[:,:,[0,2,1]]*[1,-1,1]
        ground.append(section(local,.553))
    # The cut extends behind the narrow model. Its back closes into the retained central house.
    back=street.offset_curve(5.45,join_style='mitre').buffer(.10,cap_style='flat',join_style='mitre')
    collision=geo.union_all([back,*ground],grid_size=.001).simplify(.004,preserve_topology=True)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 19.0<=tops[variant]<=23.0,tops
        assert .95<remain.area/area.area<.99,(variant,remain.area/area.area)
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>0.01
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
        fp=site.footprints[i];assert fp.distance(cut)>.01
        nearbys.append({'owner':i,'model_distance_m':fp.distance(form),'mask_distance_m':fp.distance(cut),'remaining':True})
    points=[]
    def probe(name,x,y,solid,map_solid):
        pt=Point(x,y);actual=collision.covers(pt);blocked=actual or (not cut.covers(pt) and src.covers(pt))
        assert actual==solid and blocked==map_solid,(name,x,y,actual,blocked)
        points.append({'name':name,'xy':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),'model_obstacle':actual,'source_cut':cut.covers(pt),'expected_map':'building'if blocked else None})
    for x in (-5.31,0.,5.31):
        for name,y,solid in [('Garden foreground',-1.62,False),('Open front of loggia',.14,False),('Gallery floor',1.27,False),('Glazing plane',2.826,True),('Deep backing section',5.43,True)]:
            probe(name+' '+str(x),x,y,solid,solid)
    for x in (-7.95,-2.68,2.68,7.95):
        probe('Original shaft or pilaster '+str(x),x,.09,True,True)
        probe('Garden foreground in front of each support '+str(x),x,-1.44,False,False)
    for x in (-4.73,1.30,6.05):
        probe('Retained fabric behind the cut '+str(x),x,6.52,False,True)
    row=next(v for v in ref['owners'] if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':332,'overviewPitch':43,'overviewZoom':19.62,
        'maxDistance':435,'lod_switch_in_m':610,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'从南侧看中楼双柱三开间凹廊及中央老虎窗。'},
        'placement':{'status':'map-aligned','note':'市表4B012及两代外景对准中楼南面；聚合1431只裁中央柱廊、坡屋前段，东西楼及廊桥保留。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Kangding central garden portico collision',collision=True);checked_geometry(contract['replacement_geometry'],'Kangding central garden portico')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'texture_decoder_sha256':sha(decoder),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
