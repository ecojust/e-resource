"""Verify the recessed street frontage, entrance columns, pavement and neighboring footprints."""
from pathlib import Path
import argparse,math,sys
import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString,Point,Polygon,shape
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,sha,write
from build_candidate_city_integrations import checked_geometry,check_source_section_caps

ID='huangpu-rockbund-lyceum-building'
OWNER=2358


def main(args):
    source=PROJECT/'source/precise'/ID
    review=read(source/'footprint-review.json')
    proof=read(args.cut)
    assert proof['id']==ID and proof['passed'] and proof['source_review_sha256']==sha(source/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    decoder=HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS']=(site.env.get('NODE_OPTIONS','')+' --require='+str(decoder)).strip()
    assets,bounds,profile,physical=site.decode_model(args.manifest)
    cut=Polygon(proof['mask_local_m']);assert cut.covers(profile),profile.difference(cut).bounds
    src=site.footprints[OWNER]
    collision=geo.union_all([src.intersection(cut),physical],grid_size=.001).buffer(.018,join_style='mitre').buffer(-.018,join_style='mitre').simplify(.008)
    # Far street walls carry explicit IDs. The separately recorded near check
    # establishes a clear ownership margin throughout the replaced area.
    triangles=np.fromfile(args.work/'baseline-far-triangles.f64',np.float64).reshape(-1,3,3)
    labels=np.fromfile(args.work/'baseline-far-owners.u32',np.uint32)
    assert len(triangles)==len(labels)
    selected=triangles[labels==OWNER].copy()
    selected[:,:,:2]=selected[:,:,:2]@site.axes.T
    outline=site.project_faces(selected)
    sections=geo.get_parts(geo.line_merge(cut.boundary.intersection(outline)))
    edges=[]
    for section in sections:
        for a,b in zip(section.coords,list(section.coords)[1:]):
            if math.dist(a,b)>.003:edges.append([a,b])
    seam=MultiLineString(edges);assert not seam.is_empty and cut.boundary.buffer(.00002).covers(seam)
    ready=read(site.files['READY.json'])
    caps={'geometry':site.wgs(seam),'base_m':0,'roof_m':proof['source_levels']['far']['roof_m'],
          'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(site.files['far.glb'])}
    reg=read(source/'source/frontage-registration.json')
    probes=[]
    def check_ground(name, xy, expected):
        v=np.asarray(xy);pt=Point(v)
        model_blocked=collision.covers(pt);in_cut=cut.covers(pt)
        blocked=model_blocked or (not in_cut and src.covers(pt))
        assert blocked==expected,(name,v.tolist(),blocked)
        probes.append({'name':name,'xy':v.tolist(),'wgs84':site.to_wgs(np.array([v]))[0].tolist(),
                       'expected_map':'building' if expected else None,'model_obstacle':model_blocked,'source_cut':in_cut})
    for x,part in [(-12.9,'塔南'),(-10.6,'门洞'),(-6.5,'塔旁'),(-3.7,'翼南'),(1.0,'翼中'),(7.8,'店窗'),(12,'北端')]:
        for y,expected,detail in [(-1.15,False,'街侧'),(-2.4,False,'人行道'),(.65,True,'建筑内部'),(4.4,True,'保留旧楼')]:
            check_ground(part+detail,[x,y],expected)
    manifest=read(args.manifest)
    contract={'id':ID,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':OWNER},
              'source_feature_ids':{'building':[review['owner']['source_key'].split(':',1)[1]],'building_part':[]},
              'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,
              'lng':site.lon,'lat':site.lat,'heading':review['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
              'model_geometry_sha256':{key:asset['sha256']for key,asset in assets.items()},'bounds_glb':bounds,
              'overviewBearing':-100,'overviewPitch':44,'overviewZoom':19.78,'maxDistance':460,'lod_switch_in_m':590,'lod_switch_out_m':755,
              'navigation':{'listed':False,'status':'从圆明园路可见塔楼两扇高低券窗、三角窗楣、双语石门额和北翼退台。'},
              'placement':{'status':'map-aligned','note':'以圆明园路185号的OSM门牌及原底图2358东边配准。保留西部主体、南侧882、北侧真光大楼和街道人行空间。'},
              'partial_model':True,'model_scope':manifest['scope']}
    for k in ('replacement_geometry','collision_geometry'):checked_geometry(contract[k],k,collision=k=='collision_geometry')
    check_source_section_caps(contract,shape(contract['replacement_geometry']))
    args.out.mkdir(parents=True,exist_ok=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',{'id':ID,'passed':True,'source_cut_sha256':sha(args.cut),'manifest_sha256':sha(args.manifest),'checker_sha256':sha(Path(__file__)),'texture_decoder_sha256':sha(decoder),'assets':assets,'native_variants':proof['source_levels'],'ground_probes':probes,'neighbors':proof['neighbor_distance_m'],'area_model_m2':profile.area,'area_collision_m2':collision.area,'area_cut_m2':cut.area,'seam_segments':len(edges)})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--cut',type=Path,default=HERE/'source-cut.json')
    parser.add_argument('--out',type=Path,default=HERE)
    main(parser.parse_args())
