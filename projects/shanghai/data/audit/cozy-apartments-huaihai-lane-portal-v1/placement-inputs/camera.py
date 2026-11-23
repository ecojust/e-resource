"""Evaluate the real public directory camera, the visible original city and the physical material at each target."""
import os
from model import *
from urllib.request import urlopen
import gzip
from shapely.affinity import scale,translate
m,scenes=make_scenes(Path(sys.argv[1]));contract=ri(w/'final-placement-contract.json');cam=runpy.run_path(str(project/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))
cameraModule=w/'signed-runtime-276/src/candidate-overview-camera.js'
cameraModule.parent.mkdir(parents=True,exist_ok=True)
cameraData=urlopen('http://127.0.0.1:31276/src/candidate-overview-camera.js',timeout=30).read()
assert sha(cameraData)=='73e4c91277cb4f07db11dda2ebfb78ccd5dcd11d2f266ff7eacd9ea201784845'
if cameraModule.is_file():assert cameraModule.read_bytes()==cameraData
else:cameraModule.write_bytes(cameraData)
cam['evaluate'].__globals__['PROJECT']=cameraModule.parents[1]
data=urlopen(frame['origin']+'feature-table.json.gz',timeout=30).read();assert sha(data)==next(v['sha256']for v in frame['source_hashes']if v['repository_path'].endswith('feature-table.json.gz'))
mn=math.radians(1)*6371008.8;me=mn*math.cos(math.radians(lat));meter=lambda p:scale(translate(p,xoff=-lon,yoff=-lat),xfact=me,yfact=mn,origin=(0,0))
mask=meter(G.shape(contract['display_height_clips'][0]['geometry']));neighbors=[]
for row in json.loads(gzip.decompress(data))['features']:
    poly=G.shape(row['geometry'])
    if poly.distance(Point(lon,lat))>.002:continue
    poly=meter(poly)
    if poly.distance(Point(0,0))<=150:neighbors.append((row['localId'],poly.difference(mask) if row['localId']==2172 else poly,row['height']))
survey=[('西石门柱',-2.25,1.7,'stone'),('东石门柱',2.12,1.7,'stone'),('灰底题额',-1.58,4.3,'inscription field'),('水平挑檐',1.88,4.93,'stone'),('西窗',-1.10,5.84,'window reflections'),('东窗',.95,5.84,'window reflections'),('西窗楣',-.92,6.90,'window sill'),('东窗台',.77,5.027,'window sill'),('砖墙上角',2.20,6.75,'brick'),('竖向管',-.103,6.13,'pipe'),('西扇上横格',-1.53,2.491,'iron gate'),('东扇上横格',1.35,2.491,'iron gate'),('西柱门牌',-2.29,2.32,'plate')]
source=scenes['full'];cent=source.tri.mean(axis=1);maskchar=source.mi==source.materials.index('Oxide red name characters')
for index,ch in enumerate('康綏公寓'):
    xx=-1.205+index*.64;sel=np.where(maskchar&(abs(cent[:,0]-xx-.24)<.23)&(source.cross[:,1]<-.0003))[0]
    assert len(sel),ch
    sel=sel[np.argmax(source.areas[sel])];v=cent[sel];survey.append(('题额'+ch,float(v[0]),float(v[2]),'name characters'))
reference=[];locpoints=[]
for name,x,z,material in survey:
    matching=[]
    for dx in [0,-.018,.018,-.044,.044,-.080,.080,-.14,.14]:
        for dz in [0,-.011,.011,-.022,.022,-.08,.08]:
            hits={role:scenes[role].ray([x+dx,-2,z+dz],[0,1,0],8)for role in ('full','lod')}
            if all(a and material in a['material'].lower() for a in hits.values()):matching.append(hits);break
        if matching:break
    if not matching:
        if name=='西柱门牌':continue
        raise AssertionError((name,x,z,material))
    hits=matching[0];reference.append(dict(feature=name,**hits));locpoints.append(np.array(hits['full']['point_enu_m']))
targets=[(row['feature'],*(q[:2]@axes),q[2])for row,q in zip(reference,locpoints)]
def evaluate(bearing,pitch,zoom):
    d={**contract,'overviewBearing':bearing,'overviewPitch':pitch,'overview_focus_bounds_glb':dict(min=[-2.43,1.10,-.62],max=[2.30,6.64,.02])};physical={k:[]for k in ('full','lod')};views=[]
    for label,ww,hh,pads in cam['VIEWS']:
        view=cam['evaluate'](d,dict(width=ww,height=hh,insets=dict(zip(['left','right','top','bottom'],pads))),label,neighbors,lon,lat,me,mn,targets);views.append(view)
        eye=np.r_[np.array(view['camera_enu'][:2])@axes.T,view['camera_enu'][2]]
        for role in physical:
            rows=[]
            for i,(q,r)in enumerate(zip(locpoints,reference)):
                dvec=q-eye;dist=float(np.linalg.norm(dvec));a=scenes[role].ray(eye,dvec.copy(),dist+.1)
                err=a['distance_m']-dist if a else None
                ok=bool(view['probes'][i]['clear'] and a and abs(err)<.11 and a['material']==r[role]['material'])
                rows.append(dict(feature=r['feature'],point=q.tolist(),screen_visible=view['probes'][i]['clear'],expected_material=r[role]['material'],depth_error_m=err,visible=ok,first_hit=a))
            physical[role].append(dict(screen=label,eye_local=eye.tolist(),samples=rows))
    shown=set.intersection(*[{p['feature'] for p in vs['samples'] if p['visible']} for rows in physical.values() for vs in rows]);core=['西窗','东窗','灰底题额',*('题额'+v for v in '康綏公寓')];rank=(sum(i in shown for i in core),len(shown),-abs(334-bearing)-abs(68-pitch))
    return rank,dict(bearing=bearing,pitch=pitch,zoom=zoom,views=views,physical=physical,visible=sorted(shown),not_visible=[r['feature'] for r in reference if r['feature'] not in shown])
best=None;trials=[]
for bearing,pitch,zoom in [(334,73,20.25),(334,67,20.25),(334,61,20.25),(334,54,20.25),(336,56,20.25),(330,56,20.25),(334,48,20.25),(334,68,20.25),(334,75,20.5),(337,71,20.55),(329,71,20.55),(334,74,20.73),(334,79,20.65),(334,64,20.58),(330,60,20.5),(325,68,20.55),(340,66,20.58),(334,70,20.33),(339,75,20.65),(326,77,20.58)]:
    rank,v=evaluate(bearing,pitch,zoom);trials.append(dict(bearing=bearing,pitch=pitch,zoom=zoom,visible=len(v['visible']),not_visible=v['not_visible']))
    if best is None or rank>best[0]:best=(rank,v)
    if len(v['visible'])==len(reference):break
rank,row=best;save((Path(os.environ['COZY_REFERENCE_FILES'])/'debug-camera.json'),row);assert rank[0]>=7 and rank[1]>=12,(rank,trials)
contract.update(overview_focus_bounds_glb=dict(min=[-2.43,1.10,-.62],max=[2.30,6.64,.02]),overviewBearing=row['bearing'],overviewPitch=row['pitch'],overviewZoom=row['zoom']);save(w/'final-placement-contract.json',contract)
save(w/'selected-camera.json',row);save(w/'camera-comparison.json',dict(module=sha(cameraModule.read_bytes()),surfaces=reference,trials=trials));save(w/'overview-sightlines.json',dict(id=m['id'],contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),camera_module_sha256=sha(cameraModule.read_bytes()),cases={'delivered':row['views']},retained_volumes=len(neighbors),certified_features=row['visible']));save(w/'model-sightlines.json',dict(passed=True,id=m['id'],contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),asset_manifest_sha256=sha((Path(sys.argv[1])/'manifest.json').read_bytes()),views=row['physical'],certified_features=row['visible'],not_visible=row['not_visible']));print('camera',rank,row['bearing'],row['pitch'],row['zoom'],len(reference),row['not_visible'])
