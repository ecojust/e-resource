"""Bind only the Bund and Jiujiang street strips and protect the two adjacent ordinary models."""
from pathlib import Path
import argparse,runpy,sys
import numpy as np
import shapely
from shapely.geometry import LineString,MultiLineString,Point,Polygon,box
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,sha,read,write
from build_candidate_city_integrations import checked_geometry
ID='huangpu-bank-of-taiwan-building'
OWNER=228
def sloping_strip(low,high,outside,inside):
    def edge(y):return -9.055-.11189*y
    return Polygon([(edge(low)+outside,low),(edge(high)+outside,high),
                    (edge(high)+inside,high),(edge(low)+inside,low)])
def check_neighbors(ctx,cut,model):
    load=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
    landmarks=read(PROJECT/'data/landmarks.json');checks={}
    for number,revision in [(15,'river-arch-relief'),(17,'street-wing-doors')]:
        ident=f'bund{number}';entry=next(r for r in landmarks if r.get('id')==ident)
        path=PROJECT/f'source/precise/{ident}/revisions/{revision}/manifest.json'
        manifest=read(path);record=manifest['assets']['raw'];asset=PROJECT/record['file']
        assert sha(asset)==record['sha256']
        tri=load(asset)[0];assert len(tri)==record['triangles']
        origin=ctx.to_xy(np.array([[entry['lng'],entry['lat']]]))[0]
        factor=np.cos(np.deg2rad(ctx.lat))/np.cos(np.deg2rad(entry['lat']))
        tri[:,:,:2]=(tri[:,:,:2]@ctx.axes.T)*factor+origin
        area=ctx.project_faces(tri)
        clearance=area.distance(cut)
        assert clearance>.08 and area.distance(model)>.08,(ident,clearance,area.distance(model))
        checks[ident]={'manifest_sha256':sha(path),'raw_sha256':record['sha256'],'triangles':len(tri),'anchor':[entry['lng'],entry['lat']],'projected_area_m2':area.area,'distance_to_model_m':area.distance(model),'distance_to_cut_m':clearance,'cut_m2':area.intersection(cut).area}
    return checks
def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    cli.add_argument('--out',type=Path,default=HERE)
    arg=cli.parse_args();arg.out.mkdir(parents=True,exist_ok=True)
    refs=PROJECT/'source/precise'/ID/'footprint-review.json';data=read(refs);ctx=PlacementMeshes(PROJECT,arg.work,data)
    assets,bounds,model,foot=ctx.decode_model(arg.manifest);doc=read(arg.manifest)
    cut=sloping_strip(-.77,40.13,-.78,1.91).union(box(-10.02,-.77,9.20,2.53))
    assert model.difference(cut.buffer(.002)).area<.0001,(model.difference(cut).area,model.bounds)
    floor=sloping_strip(.03,39.83,-.1,1.79).union(box(-9.055,.033,9.055,2.46))
    floor=floor.difference(box(-1.854,-.52,1.854,2.24))
    # Stone steps remain walkable up to the recessed door. Individual plinths and side walls are solid.
    collision=floor
    target=ctx.footprints[OWNER];sources={};far=None
    for kind,(group,neighbors,method) in ctx.decode_group(data['near_tiles'][0],OWNER).items():
        origin=ctx.project_faces(group);other=ctx.project_faces(neighbors)
        if kind=='far':far=origin
        rem=origin.difference(cut).area
        assert .80<rem/origin.area<.92 and other.distance(cut)>1.6,(kind,rem/origin.area,other.distance(cut))
        sources[kind]={'triangles':len(group),'other_triangles':len(neighbors),'assignment':method,'source_m2':origin.area,'retained_m2':rem,'fraction_retained':rem/origin.area,
            'nearest_other_source_to_cut_m':other.distance(cut),'nearest_other_source_to_model_m':other.distance(model),'other_cut_m2':other.intersection(cut).area,'roof_m':float(group[:,:,2].max())}
    protected=check_neighbors(ctx,cut,model)
    segments=[]
    for a,b in zip(cut.exterior.coords,list(cut.exterior.coords)[1:]):
        line=far.intersection(LineString([a,b]));segments.extend([g for g in shapely.get_parts(line) if isinstance(g,LineString) and g.length>.001])
    assert len(segments)>=3
    ready=read(ctx.files['READY.json'])
    caps={'base_m':0,'roof_m':sources['far']['roof_m'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(ctx.files['far.glb']),'geometry':ctx.wgs(MultiLineString(segments))}
    probes=[]
    for name,x,y,expected in [('Bund pavement',0,-2.15,False),('central steps',.05,.83,False),('entry door recess',.05,2.02,False),
            ('back of central doorway',.05,2.35,True),('north column base',7.56,.82,True),('south column base',-7.56,.82,True),
            ('continuous east plinth',-5.1,.83,True),('Jiujiang pavement',-13.6,19,False),('south street stone plinth',-10.86,19,True),
            ('retained central former bank',1.2,22,True),('retained western area',-4,44,True)]:
        pt=Point(x,y);d=collision.covers(pt);r=target.difference(cut).covers(pt);other=any(a.covers(pt)for i,a in ctx.footprints.items()if i!=OWNER)
        assert bool(d or r or other)==expected,(name,d,r,other);probes.append({'name':name,'xy':[x,y],'point':ctx.to_wgs(np.array([[x,y]]))[0].tolist(),'expected':'building'if expected else None,'modelObstacle':d,'cut':cut.covers(pt),'retained':r,'other':other})
    frame=data['author_frame'];c={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,'owner':{'macro_id':data['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[data['owner']['source_key'].split(':')[1]],'building_part':[]},'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'replacement_geometry':ctx.wgs(cut),'collision_geometry':ctx.wgs(collision),'source_section_caps':caps,'overviewBearing':-62,'overviewPitch':37,'overviewZoom':19.47,'maxDistance':600,'lod_switch_in_m':580,'lod_switch_out_m':730,'navigation':{'listed':False,'status':'台湾银行大楼中山东一路及九江路两立面，供俯瞰。'},'placement':{'status':'estimated','note':'中山东一路16号招商银行地块、东侧四柱与南侧七开间对应，北邻字林、西端低翼和街南15号独立保留。'},'partial_model':True,'model_scope':doc['model_scope_zh']}
    # Both view boxes describe real subvolumes of the delivered GLB, in metres.
    # The four column shafts are clustered at the east end of the 40 m frontage.
    c['overview_focus_bounds_glb']={'min':[-10.50,0,-13.00],'max':[9.00,23.60,.60]}
    c['label_focus_bounds_glb']={'min':[-8.54,0,-2.20],'max':[8.54,14.55,.15]}
    for field in ('overview_focus_bounds_glb','label_focus_bounds_glb'):
        focus=c[field]
        assert all(lo<=a<b<=hi for lo,a,b,hi in zip(bounds['min'],focus['min'],focus['max'],bounds['max']))
    for key in ('replacement_geometry','collision_geometry'):checked_geometry(c[key],key,collision=key=='collision_geometry')
    write(arg.out/'final-placement-contract.json',c);write(arg.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(refs),script_sha256=sha(Path(__file__)),manifest_sha256=sha(arg.manifest),model=assets,owner=OWNER,model_projected_m2=model.area,model_floor_m2=foot.area,cut_m2=cut.area,collision_m2=collision.area,native=sources,protected_ordinary_models=protected,retained_228_vector_m2=target.difference(cut).area,seams_m=[g.length for g in segments],ground_probes=probes,contract_sha256=sha(arg.out/'final-placement-contract.json')))
    print(sources,protected,flush=True)
if __name__=='__main__':main()
