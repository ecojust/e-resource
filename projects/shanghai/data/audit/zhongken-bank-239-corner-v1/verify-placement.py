"""Verify the northeast corner and actual road crossing against both source meshes."""
from pathlib import Path
import argparse,sys,math,subprocess
import numpy as np
import shapely as geo
from shapely.geometry import shape,box,Polygon,Point,MultiLineString,LineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-zhongken-bank-239-corner'
OWNER=1970


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


def decode_corner_group(site,group):
    ids=np.asarray(group['feature_local_ids'],int)
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':int(i)} for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,
                   stdout=subprocess.DEVNULL)

    def triangles(role):
        mesh=np.fromfile(site.work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
        mesh[:,:,:2]=mesh[:,:,:2] @ site.axes.T
        return mesh

    far=triangles('far')
    by_feature=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
    assert len(by_feature)==len(far) and set(by_feature)==set(ids)
    far_outlines={i:site.project_faces(far[by_feature==i]) for i in ids}
    mesh=triangles('near')
    centroids=geo.points(mesh[:,:,:2].mean(1))
    vertices=geo.points(mesh[:,:,:2].reshape(-1,2))
    selection=None
    methods={}
    # The two nearest original outlines are 0.56 m apart by the closest
    # relevant sample. Verify attribution through independent centroid/vertex
    # tests and the other LOD's explicit _FEATURE_ID_0 before scoping the cut.
    for label,points,polygons in [('original_centroid',centroids,site.footprints),
                                  ('far_feature_centroid',centroids,far_outlines),
                                  ('original_mean_vertex',vertices,site.footprints)]:
        distances=np.column_stack([geo.distance(points,polygons[i]) for i in ids])
        if points is vertices:distances=distances.reshape(-1,3,len(ids)).mean(1)
        owner=ids[distances.argmin(1)]
        assert set(owner)==set(ids)
        own=owner==OWNER
        if selection is None:selection=own
        else:assert np.array_equal(selection,own),label
        ranked=np.sort(distances[own],axis=1)
        maximum=float(ranked[:,0].max())
        margin=float(np.diff(ranked[:,:2],axis=1).min())
        assert maximum<.12 and margin>5*maximum, (label,maximum,margin)
        methods[label]={'own_triangles':int(own.sum()),'largest_own_distance_m':maximum,
                        'smallest_next_owner_margin_m':margin}
    far_target=by_feature==OWNER
    return {'near':(mesh[selection],mesh[~selection],{'assignment_comparisons':methods,
                    'triangles_all_seven_owners':len(mesh),'identical_target_assignments':True}),
            'far':(far[far_target],far[~far_target],{'method':'per-vertex _FEATURE_ID_0'})}


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
    cut=box(-half-.14,-.61,half+.14,2.395)
    assert cut.covers(form),form.difference(cut).area
    group,=ref['near_tiles']
    assert set(group['feature_local_ids'])=={2685,1970,1591,2930,1411,2530,2658}
    decoded=decode_corner_group(site,group)
    src=site.footprints[OWNER]
    # Source ground behind the slanted corner remains closed. The three street steps
    # can be approached up to the bank doors, which sit back inside the stone surround.
    solid=geo.union_all([src.intersection(cut),physical],grid_size=.001)
    pocket=box(-1.91,-1.04,1.91,.153)
    collision=solid.difference(pocket).buffer(.005,join_style='mitre').buffer(-.005,join_style='mitre').simplify(.002)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 31.85<=tops[variant]<=32.16
        assert .967<remain.area/area.area<.987
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
    for x in (-3.16,-2.65,-2.22,2.22,2.65,3.16):
        probe(f'Pavement outside entrance granite x{x}',x,-.78,False,False)
        probe(f'Inside closed stone jamb x{x}',x,.31,True,True)
        probe(f'Retained main building behind cut x{x}',x,3.35,False,True)
    for x in (-1.62,-.73,0,.73,1.62):
        probe(f'Public tread outside closed iron gate x{x}',x,.08,False,False)
        probe(f'Closed gate line x{x}',x,.29,True,True)
    probe('Unchanged Beijing Road wing',9.,3.61,False,True)
    probe('Unchanged Jiangxi Road wing',-6.,6.08,False,True)
    probe('Beijing Road street surface outside wing',8.,1.25,False,False)
    probe('Jiangxi Road street surface outside wing',-7.3,3.00,False,False)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':-145.,'overviewPitch':45,'overviewZoom':18.95,
        'maxDistance':610,'lod_switch_in_m':815,'lod_switch_out_m':960,'navigation':{'listed':False,'status':'从北京东路、江西中路交界处看239号石门、三联窗带和退台塔冠。'},
        'placement':{'status':'map-aligned','note':'仅替换原城1970面向东北的斜角。两街楼翼、255号入口所在的长立面和后部沿用原模型。东北侧浙江兴业银行等邻栋均保留。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'239 northeast gate threshold',collision=True);checked_geometry(contract['replacement_geometry'],'Land Bank northeast street corner')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
