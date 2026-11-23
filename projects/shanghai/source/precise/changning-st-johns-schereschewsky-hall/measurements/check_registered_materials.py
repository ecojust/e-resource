"""Independent first intersections for a labelled pixel on each clock elevation."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from register_courtyard_stations import Camera
HERE=Path(__file__).parent
helper=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
if not helper.is_file():
 helper=next(q for root in HERE.parents for q in [root/'data/audit/postal-office-v1/independent-glb-review-helpers.py',root/'independent-glb-review-helpers.py'] if q.is_file())
NAMES={'tile':['grey butterfly tile'],'brick':['blue-grey facing brick'],'red':['warm red brick dressings'],'cream':['warm cream stucco'],'dial':['clock enamel'],'glass':['smoke grey glazing','dark iron and timber','blue floral clock glazing','pale green opalescent glazing'],'hand':['dark iron and timber'],'rail':['painted red-brown timber'],'shadow':['blue-grey facing brick','painted red-brown timber','weathered granite','warm cream stucco','dark iron and timber','smoke grey glazing']}
# Picking coordinates on a uniformly scaled version of the source is recorded as the
# equivalent original integer-pixel probe. Different physical surfaces are labelled separately.
POINTS={
'court':[(label,(u,v),m) for label,u,v,m in [
('western low roof',183,172,'tile'),('eastern low roof',361,174,'tile'),('distant roof left',133,165,'tile'),('distant roof right',408,166,'tile'),
('tower cornice roof slope',252,33,'tile'),('tower roof slope right',289,31,'tile'),('left upper cream field',239,57,'cream'),('right upper cream field',301,61,'cream'),
('enamel between figures 10 and 11',257,92,'dial'),('enamel between figures 3 and 6',282,118,'dial'),('enamel centre-left',258,105,'dial'),('hand hub',270,106,'hand'),
('west shutter under dial',251,152,'glass'),('central shutter under dial',267,153,'glass'),('east shutter under dial',288,152,'glass'),('tower brick pier left of rectangular sash',239,156,'brick'),
('brick east of rectangular sash',300,157,'brick'),('tower lower left glazing',250,214,'glass'),('tower lower middle glazing',267,216,'glass'),('tower lower right glazing',291,219,'glass'),
('court left wing upper sash',156,219,'glass'),('court right wing inner upper sash',338,222,'glass'),('court right wing centre sash',384,216,'glass'),
('court wing left spandrel',177,235,'brick'),('court wing right spandrel',357,233,'brick'),('court left arcade interior',202,289,'shadow'),('court right arcade interior',336,285,'shadow'),
('court tower masonry below sash',236,245,'brick'),('court brick between central levels',281,182,'brick'),('left wing masonry under eave',174,201,'brick')]],
'street':[(label,(u,v),m) for label,u,v,m in [
('clock roof left slope',256,54,'tile'),('clock roof right slope',305,55,'tile'),('low left tiled roofing',141,155,'tile'),('low right tiled roofing',415,157,'tile'),
('cream top under eave (west)',241,69,'cream'),('cream top under eave (east)',316,72,'cream'),('dial enamel left interior',257,99,'dial'),('dial enamel below hands',280,114,'dial'),('dial enamel right lower',292,112,'dial'),
('left clerestory pane',256,141,'glass'),('central clerestory pane',280,141,'glass'),('right clerestory pane',301,139,'glass'),('brick between south clerestory sashes',267,143,'brick'),
('brick west of dial',240,116,'brick'),('brick east of dial',322,116,'brick'),('white tablet above passage',261,228,'cream'),('white tablet right part',306,229,'cream'),
('west glazed lower light',257,193,'glass'),('centre glazed lower light',282,197,'glass'),('east glazed lower light',307,199,'glass'),('portal brick surround at crown',285,251,'red'),
('left street arcade upper interior',153,199,'shadow'),('right street arcade upper interior',394,196,'shadow'),('left street arcade lower interior',123,291,'shadow'),
('righthand low arcade interior',433,290,'shadow'),('west spandrel',199,250,'brick'),('east spandrel',381,251,'brick'),('left portal pier',229,284,'brick'),('right portal pier',342,295,'brick'),('east red dress under upper gallery',419,236,'red')]]}
BLOCKED={'court':[{'area':[497,568],'reason':'bronze bust and pedestal hide the inner ground portal'},{'area':[788,531],'reason':'shrub hides eastern ground arcade'}],'street':[{'area':[530,748],'reason':'people and devices below the street portal'},{'area':[270,754],'reason':'shrubs mask the base of the west arcade'}]}

NAMES.update({'medallion':['warm red brick dressings','weathered granite','clock enamel','warm cream stucco'],'lawn':['lawn grass'],'path':['court pebble paving'],'wood':['painted red-brown timber','dark iron and timber'],'sky':[]})
POINTS['school-01']=[(n,(u,v),m)for n,u,v,m in [
 ('west return upper corridor dark field',59,104,'shadow'),('west return second dark field',113,128,'shadow'),('western return next dark field',143,152,'shadow'),
 ('east gallery near upper corridor',585,103,'shadow'),('east upper gallery third',501,138,'shadow'),('east upper gallery next',472,152,'shadow'),
 ('west return ground aperture',57,192,'shadow'),('west return next ground aperture',111,203,'shadow'),('east return ground aperture',583,194,'shadow'),('east return second ground aperture',534,190,'shadow'),
 ('western pavilion medallion',292,154,'medallion'),('central pavilion medallion',318,153,'medallion'),('eastern pavilion medallion',345,153,'medallion'),
 ('cream wall left between circular fields',302,155,'cream'),('cream wall right between circular fields',333,155,'cream'),
 ('upper west opening of central pavilion',290,176,'shadow'),('upper middle pavilion opening',318,174,'shadow'),('upper east pavilion opening',345,176,'shadow'),
 ('west lower flanking opening',291,213,'shadow'),('east lower flanking opening',345,214,'shadow'),
 ('western low roof tile',245,153,'tile'),('eastern low roof tile',392,151,'tile'),('centre pavilion upper tile',306,143,'tile'),
 ('foreground western lawn',81,309,'lawn'),('foreground eastern lawn',553,305,'lawn'),('centre pebbled path',321,355,'path'),
 ('left sky between roof arcs',202,76,'sky'),('right sky between roof arcs',441,58,'sky'),
 ('west roof-rail junction brick pier',92,153,'brick'),('east side lower brick pier',556,206,'brick')]]
BLOCKED['school-01']=[{'area':[318,212],'reason':'Head and body of monument block the central ground and upper gallery'},{'area':[405,219],'reason':'dense foliage hides far ground openings'},{'area':[251,218],'reason':'small tree partly obscures the other wing'}]
def matches(hit,expected):
 if expected=='sky':return hit is None
 return hit is not None and hit['material'] in NAMES[expected]
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mesh',type=Path);a.add_argument('output',type=Path);args=a.parse_args()
 scene=runpy.run_path(str(helper))['SerialScene'](args.mesh)
 report={'mesh_sha256':hashlib.sha256(args.mesh.read_bytes()).hexdigest(),'stations_sha256':hashlib.sha256((Path(sys.path[0])/'registered-courtyard-stations.json').read_bytes()).hexdigest(),'photograph_occlusions':BLOCKED,'views':{}}
 for key,probes in POINTS.items():
  camera=Camera(key);scale=1 if key=='school-01' else camera.image_size[0]/540;rows=[]
  def hit(uv):
   v=camera.R.T@np.linalg.solve(camera.K,[*uv,1.]);return scene.ray(camera.C,v/np.linalg.norm(v),120)
  for name,uv,expected in probes:
   pixel=np.round((np.array(uv)+.5)*scale-.5).astype(int)
   first=hit(pixel); ok=matches(first,expected); nearest=None
   if ok:nearest=[0,0]
   else:
    for dx,dy in sorted([(int(x),int(y)) for x in [-4,-3,-2,0,2,3,4] for y in [-4,-3,-2,0,2,3,4] if 0<x*x+y*y<=16],key=lambda a:a[0]**2+a[1]**2):
     f=hit(pixel+[dx,dy])
     if matches(f,expected):nearest=[dx,dy];break
   rows.append({'feature':name,'original_pixel':pixel.tolist(),'expected':expected,'first':first,'direct':ok,'nearby_offset_within_4_px':nearest})
  report['views'][key]={'count':len(rows),'direct':sum(r['direct'] for r in rows),'within_4':sum(r['nearby_offset_within_4_px'] is not None for r in rows),'marks':rows}
 # The original 30 street marks remain in place. Record a separate photo-based amendment.
 rail=[]
 street=Camera('street')
 def street_hit(uv):
  v=street.R.T@np.linalg.solve(street.K,[*uv,1.]);return scene.ray(street.C,v/np.linalg.norm(v),120)
 for name,uv,key,rgb in [('red brick band under the upper gallery',[838,482],'red',[170,137,122]),('horizontal member of the lower timber rail',[846,466],'wood',[111, 109, 112])]:
  first=street_hit(uv)
  best=None
  for dx,dy in sorted([(x,y) for x in range(-6,7) for y in range(-6,7) if x*x+y*y<=36],key=lambda q:q[0]**2+q[1]**2):
   if matches(street_hit([uv[0]+dx,uv[1]+dy]),key):
    best=[dx,dy];break
  rail.append({'feature':name,'original_pixel':uv,'expected':key,'photo_rgb':rgb,'first':first,'direct':matches(first,key),'nearest_within_6_px':best})
 report['separate_rereading']={'original_preselected_pixel':[838,472],'original_rgb':[60,56,55],'original_reading_preserved_in':'views.street.marks','photo_reason':'The old pixel is dark within the lower railing, above the bright separator. The visible red brick occupies approximately rows 479–486. A horizontal rail stroke crosses columns 842–854 near rows 465–466.','new_marks':rail}
 args.output.write_text(json.dumps(report,indent=2)+'\n')
 print([(k,v['count'],v['direct'],v['within_4']) for k,v in report['views'].items()])
