"""Bind the measured cut corner, neighboring buildings and pavement to the delivered meshes."""
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

ID='huangpu-ningpo-commercial-bank-corner'
OWNER=3201


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
    for street,(first,last) in zip(('北京东路','斜切主门','江西中路'),zip(reg['visible_edges_local_m'],reg['visible_edges_local_m'][1:])):
        a=np.array(first);b=np.array(last);t=(b-a)/np.linalg.norm(b-a);out=np.array([t[1],-t[0]])
        for fraction in (.20,.50,.80):
            for offset,expected,description in ((-.40,True,'室内一侧'),(1.45,False,'门前人行道'),(2.55,False,'街侧通行点')):
                v=a+(b-a)*fraction+out*offset;pt=Point(v)
                blocked=collision.covers(pt) or (not cut.covers(pt) and src.covers(pt))
                assert blocked==expected,(street,fraction,offset,blocked)
                probes.append({'name':street+' '+description,'xy':v.tolist(),'wgs84':site.to_wgs(np.array([v]))[0].tolist(),'expected_map':'building'if blocked else None,'model_obstacle':collision.covers(pt),'source_cut':cut.covers(pt)})
    manifest=read(args.manifest)
    contract={'id':ID,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':OWNER},
              'source_feature_ids':{'building':[review['owner']['source_key'].split(':',1)[1]],'building_part':[]},
              'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,
              'lng':site.lon,'lat':site.lat,'heading':review['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
              'model_geometry_sha256':{key:asset['sha256']for key,asset in assets.items()},'bounds_glb':bounds,
              'overviewBearing':-58.37,'overviewPitch':37,'overviewZoom':19.85,'maxDistance':460,'lod_switch_in_m':590,'lod_switch_out_m':755,
              'navigation':{'listed':False,'status':'从北京东路与江西中路交口查看斜切门楼双柱、椭圆窗、两道曲栏和邻近的拱窗。'},
              'placement':{'status':'map-aligned','note':'取底图3201和OSM 446936782的东南斜面，保留同一建筑未建的长街墙及相邻地块。'},
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
