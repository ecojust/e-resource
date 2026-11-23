"""Measure the Arnhold southwest corner against both original mesh levels, all three tile owners and adjoining properties."""
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
ID='huangpu-arnhold-building-southwest-corner'
OWNER=2862


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


def decode_corner_group(site,group,cut):
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
    # Compare each affected near triangle against both feature layers, using
    # face centres as well as all three vertices.
    affected=geo.intersects(cut,geo.polygons(mesh[:,:,:2]))
    selection=None
    methods={}
    for label,points,polygons in [('original_centroid',centroids,site.footprints),
                                  ('far_feature_centroid',centroids,far_outlines),
                                  ('original_mean_vertex',vertices,site.footprints)]:
        distances=np.column_stack([geo.distance(points,polygons[i]) for i in ids])
        if points is vertices:distances=distances.reshape(-1,3,len(ids)).mean(1)
        own=ids[distances.argmin(1)]==OWNER
        if selection is None:selection=own
        contested=selection!=own
        assert not np.any(affected&contested) and np.all(own[affected]),label
        ranked=np.sort(distances[affected],axis=1)
        maximum=float(ranked[:,0].max())
        margin=float(np.diff(ranked[:,:2],axis=1).min())
        assert maximum<.12 and margin>1.5*maximum,(label,maximum,margin)
        methods[label]={'affected_count':int(affected.sum()),'affected_max_own_distance_m':maximum,
                        'affected_min_next_owner_margin_m':margin,'unchanged_disagreements_outside':int(contested.sum())}
    far_target=by_feature==OWNER
    return {'near':(mesh[selection],mesh[~selection],{'assignment_comparisons':methods,
                    'triangles_all_three_owners':len(mesh),'identical_assignments_on_every_affected_triangle':True}),
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
    cut=Polygon([(19.03,-.67),(-.17,-.67),(-1.40,-.49),(-2.51,-.01),(-3.12,.47),
                 (-3.84,1.44),(-4.37,2.98),(-5.14,16.13),(-1.00,16.37),(-.83,16.26),
                 (-.08,3.65),(19.04,3.60)])
    assert cut.is_valid and cut.covers(form),form.difference(cut).area
    group,=ref['near_tiles']
    assert set(group['feature_local_ids'])=={88,2862,2676}
    decoded=decode_corner_group(site,group,cut)
    src=site.footprints[OWNER]
    solid=geo.union_all([src.intersection(cut),physical],grid_size=.001)
    # The rounded masonry lies between the tangents of the two measured street axes.
    west=np.array([-4.450086,15.915946]);tangent=np.array([.058299,-.998299])
    tangent/=np.linalg.norm(tangent)
    turn=math.atan2(-tangent[1],tangent[0]);r=3.65
    corner=np.array([-.077557,3.650000]);arc=r*turn
    def position(side,station,depth):
        if side=='Sichuan':
            n=np.array([tangent[1],-tangent[0]])
            return west+station*tangent+depth*n
        if side=='Jiujiang':return np.array([corner[0]+station,-depth])
        bearing=-math.pi/2-turn+station/r
        return corner+(r+depth)*np.array([math.cos(bearing),math.sin(bearing)])
    gates=[('Sichuan',5.60,.79,-.32),('Jiujiang',16.55,.89,-.63),
           ('Corner',arc*.26,.64,-.32),('Corner',arc*.74,.64,-.32)]
    def pocket(side,x,w,depth):
        left=np.linspace(x-w,x+w,9) if side=='Corner' else [x-w,x+w]
        return Polygon([position(side,v,.77)for v in left]+[position(side,v,depth)for v in reversed(left)])
    pockets=[pocket(*gate)for gate in gates]
    collision=solid.difference(geo.union_all(pockets)).buffer(.012,join_style='mitre').buffer(-.012,join_style='mitre').simplify(.004)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 22.33<=tops[variant]<=22.47
        assert .80<remain.area/area.area<.89
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>2.0
        seams[variant]=cap_on_boundary(cut,area)
        seen[variant]={'assignment':assigned,'source_triangles':len(owned),'affected_source_triangles':affected,'unchanged_other_group_triangles':len(other),'other_source_distance_m':other_distance,'source_projected_m2':area.area,'retained_m2':remain.area,'retained_percent':remain.area*100/area.area,'source_roof_m':tops[variant],'mask_seam_m':seams[variant].length}
    agreement=seams['far'].hausdorff_distance(seams['near']);assert agreement<.22,agreement
    assert abs(tops['near']-tops['far'])<.06,tops
    ready=read(site.files['READY.json'])
    caps={'geometry':site.wgs(seams['far']),'base_m':0,'roof_m':tops['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(site.files['far.glb'])}
    nearbys=[]
    for i in ref['selection']['checked_neighbors']:
        fp=site.footprints[i];assert fp.distance(cut)>2.0
        nearbys.append({'owner':i,'model_distance_m':fp.distance(form),'mask_distance_m':fp.distance(cut),'center_wgs84':list(shape(ref['owners'][next(j for j,o in enumerate(ref['owners'])if o['local_id']==i)]['geometry_wgs84']).representative_point().coords[0]),'remaining':True})
    points=[]
    def probe(name,x,y,solid,map_solid):
        pt=Point(x,y);actual=collision.covers(pt);blocked=actual or (not cut.covers(pt) and src.covers(pt))
        assert actual==solid and blocked==map_solid,(name,x,y,actual,blocked)
        points.append({'name':name,'xy':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),'model_obstacle':actual,'source_cut':cut.covers(pt),'expected_map':'building'if blocked else None})
    for side,stations in [('Sichuan',[.5,2.8,4.2,7.7,9.8,11.2]),
                          ('Jiujiang',[.6,2.8,5.0,7.3,9.8,12.4,15.,18.1]),
                          ('Corner',[.24,arc*.49,arc-.28])]:
        for station in stations:
            probe(f'{side} pavement {station:.2f}',*position(side,station,1.03),False,False)
            probe(f'{side} ground wall {station:.2f}',*position(side,station,-.54),True,True)
    for side,station,width,depth in gates:
        for dx in [-width*.55,width*.55]:
            probe(f'{side} approach {station+dx:.2f}',*position(side,station+dx,depth+.065),False,False)
            probe(f'{side} closed door {station+dx:.2f}',*position(side,station+dx,depth-.08),True,True)
    probe('Original retained northern masonry',2.9,19.4,False,True)
    probe('Original retained eastern service range',24.60,7.0,False,True)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':38.,'overviewPitch':44,'overviewZoom':18.92,
        'maxDistance':610,'lod_switch_in_m':815,'lod_switch_out_m':960,'navigation':{'listed':False,'status':'从九江路、四川中路口看弧角蓝檐、红砖窗带及四川中路320号拱门。'},
        'placement':{'status':'map-aligned','note':'更新2862临西南角的两段街墙、两处石门和局部檐顶。北段、东段及后部沿用原城。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Arnhold street entrance thresholds',collision=True);checked_geometry(contract['replacement_geometry'],'Arnhold southwest corner')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
