"""Fit an ordinary city camera that identifies the original photographic details at desktop and phone sizes."""
from model import *
import gzip,subprocess
from urllib.request import urlopen
from shapely.affinity import scale,translate
m,scenes=make_scenes(Path(sys.argv[1]));contract=ri(w/'final-placement-contract.json');cam=runpy.run_path(str(project/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))
uri=frame['origin']+'feature-table.json.gz';data=urlopen(uri,timeout=30).read();assert sha(data)==next(v['sha256']for v in frame['source_hashes']if v['repository_path'].endswith('feature-table.json.gz'))
mn=math.radians(1)*6371008.8;me=mn*math.cos(math.radians(lat));meter=lambda p:scale(translate(p,xoff=-lon,yoff=-lat),xfact=me,yfact=mn,origin=(0,0))
mask=meter(G.shape(contract['replacement_geometry']));neighbors=[]
for row in json.loads(gzip.decompress(data))['features']:
    poly=G.shape(row['geometry']);
    if poly.distance(Point(lon,lat))>.002:continue
    poly=meter(poly)
    if poly.distance(Point(0,0))<=150:neighbors.append((row['localId'],poly.difference(mask) if row['localId']==1292 else poly,row['height']))
# Points on the separately modelled surfaces are first found from the garden facing directly into the portico.
survey=[('西端柱脚',-4.374,-2,.30),('西端柱身',-4.374,-2,3.15),('内西柱身',-1.458,-2,3.30),('内东柱身',1.458,-2,3.30),('东端柱身',4.374,-2,3.15),('西柱涡卷柱头',-4.374-.325,-2,6.28),('东柱柱头顶板',4.37,-2,6.43),('左券门玻璃扇',-2.813+.26,1.72,1.60),('中央券门拱缘',0,2.95,2.91),('右券门玻璃扇',2.813+.25,1.72,1.60),('内凹阳台铁栏',.30,1.74,5.225),('折面阳台挑沿',2.04,1.74,4.20),('上层中央门框',-.48,2.95,6.369),('横向石檐',-.50,-2,7.32),('屋顶石栏端柱',-5.04,-2,8.35),('屋顶中段扶手',.52,-2,8.645),('花园弧阶中央',0,-2,.049),('花园弧阶边',2.62,-2,.129)]
reference=[];locpoints=[]
for name,x,y,z in survey:
    hits={role:scenes[role].ray([x,y,z],[0,1,0],8) for role in ('full','lod')}
    assert all(hits.values()),(name,hits)
    a,b=hits.values();assert math.dist(a['point_enu_m'],b['point_enu_m'])<.14,(name,a,b)
    reference.append(dict(feature=name,**hits));locpoints.append(np.array(a['point_enu_m']))
targets=[(row['feature'],*(q[:2]@axes),q[2]) for row,q in zip(reference,locpoints)]
def evaluate(bearing,pitch):
    d={**contract,'overviewBearing':bearing,'overviewPitch':pitch};physical={k:[]for k in ('full','lod')};allviews=[]
    for label,ww,hh,pads in cam['VIEWS']:
        view=cam['evaluate'](d,dict(width=ww,height=hh,insets=dict(zip(['left','right','top','bottom'],pads))),label,neighbors,lon,lat,me,mn,targets);allviews.append(view)
        eye=np.r_[np.array(view['camera_enu'][:2])@axes.T,view['camera_enu'][2]]
        for role in physical:
            samples=[]
            for i,(q,row) in enumerate(zip(locpoints,reference)):
                dv=q-eye;dist=float(np.linalg.norm(dv));hit=scenes[role].ray(eye,dv.copy(),dist+.15)
                err=hit['distance_m']-dist if hit else None;shown=bool(view['probes'][i]['clear'] and hit and abs(err)<.125 and hit['material']==row[role]['material'])
                samples.append(dict(feature=row['feature'],point=q.tolist(),screen_visible=view['probes'][i]['clear'],expected_material=row[role]['material'],depth_error_m=err,visible=shown,first_hit=hit))
            physical[role].append(dict(screen=label,eye_local=eye.tolist(),samples=samples))
    visible=set.intersection(*[{s['feature'] for s in r['samples'] if s['visible']} for vv in physical.values() for r in vv]);major=['中央券门拱缘','左券门玻璃扇','右券门玻璃扇','内凹阳台铁栏','花园弧阶中央']
    rank=(sum(s in visible for s in major),len(visible),sum(v['clear_count']for v in allviews),-abs(bearing-334)-abs(pitch-46))
    return rank,dict(bearing=bearing,pitch=pitch,views=allviews,physical=physical,visible=sorted(visible),not_visible=[n['feature']for n in reference if n['feature'] not in visible])
best=None;comparison=[]
for bearing,pitch in [(334,64),(333,70),(340,72),(327,74),(334,78),(334,82),(334,56),(340,61),(327,61),(337,68),(331,68),(334,71),(334,74),(334,48)]:
    rank,row=evaluate(bearing,pitch);comparison.append(dict(bearing=bearing,pitch=pitch,score=rank,missing=row['not_visible']))
    if best is None or rank>best[0]:best=rank,row
    if rank[0]==5 and rank[1]==len(reference):break
rank,row=best
print('camera selection',rank,row['bearing'],row['pitch'],'obscured:',row['not_visible'],flush=True)
save(w/'camera-comparison.json',dict(projection_module_sha256=sha((project/'src/candidate-overview-camera.js').read_bytes()),probes=reference,comparisons=comparison));save(w/'selected-camera.json',row)
assert rank[1]>=11 and all(t in row['visible'] for t in ('内凹阳台铁栏','横向石檐','东端柱身','西端柱身'))
contract.update(overviewBearing=row['bearing'],overviewPitch=row['pitch']);save(w/'final-placement-contract.json',contract)
save(w/'overview-sightlines.json',dict(id=m['id'],contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),camera_module_sha256=sha((project/'src/candidate-overview-camera.js').read_bytes()),source_sha256=sha(data),retained_volumes=len(neighbors),cases={'delivered':row['views']},certified_features=row['visible']))
save(w/'model-sightlines.json',dict(passed=True,id=m['id'],contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),asset_manifest_sha256=sha((Path(sys.argv[1])/'manifest.json').read_bytes()),views=row['physical'],certified_features=row['visible'],not_visible=row['not_visible']))
