"""Original photo-informed Shanghai Municipal Council historic street wings.

Three different concave corners, open U court and bounded historic-only seams.
Every metric datum is an author estimate; DCA's illustrated section is a scale
cross-check, not a measured elevation. No photographs become textures.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box,shape,mapping
from shapely.geometry.polygon import orient
from shapely.affinity import translate
from shapely.ops import unary_union
from common.photo_architecture import Builder,Facade,facade_ring,opening
from components import PALETTE,opened_wall,window,cornice,column

ID='huangpu-shanghai-municipal-council'
ROOT=Path(__file__).resolve().parents[1]
INPUT=json.loads((ROOT/'footprint-input.json').read_text())
P={'local_origin_wgs84':[121.48196759839806,31.237398207960258],
 'global_heading_deg':-15.154169025296817,'axes':'x east along street, y north along street, z up',
 'floor_datums_design_m':[0,4.9,9.75,14.6,19.25],'main_wall_top_design_m':19.25,
 'strong_cornice_design_m':14.6,'straight_upper_cap_design_m':19.80,'corner_upper_cap_design_m':20.20,
 'body_inset_design_m':.25,'wall_depth_design_m':.42,'ordinary_glass_recess_design_m':.32,
 'all_dimensions_author_estimated':True,'measured_height_available':False,
 'illustrated_height_crosscheck':'DCA design section 08, 236 pixels per illustrated 10m: old street wall/roof about18–19.3m, strong cornice14–15m, upper edge about20m. New roof pavilions at23.5–25m are excluded. Not a survey.',
 'historic_scope_rule':'current source intersect (y>=36 or x>=-18)',
 'artificial_join_faces_plain':True,'uncertain_join_strips_retained':True}
CENTERS={'NE':np.array([62.62932079510337,61.60729168496828]),'SE':np.array([61.983062823680896,-57.915942841403776]),'NW':np.array([-61.73400327470392,61.60729168496828])}

def plan():
 src=shape(INPUT['current_source_local_geometry']);r=list(src.exterior.coords[:-1]);out=[]
 # Elliptical author interpolation retains concavity while the source intersection
 # bounds any interpolation outside the coarse map ring. This is not surveying.
 def arc(c,rx,ry,a,b):return [(c[0]+rx*math.cos(t),c[1]+ry*math.sin(t)) for t in np.linspace(a,b,16)]
 out+=arc(CENTERS['NE'],62.62932079510337-r[0][0],r[0][1]-r[3][1],math.pi,1.5*math.pi)
 out+=arc(CENTERS['SE'],r[4][0]-r[8][0],r[4][1]-r[8][1],math.pi/2,math.pi)
 out+=r[9:13]
 out+=arc(CENTERS['NW'],r[16][0]-r[13][0],r[16][1]-r[13][1],-math.pi/2,0)
 smooth=Polygon(out,[list(q.coords) for q in src.interiors]).intersection(src)
 scope=unary_union([box(-200,36,200,200),box(-18,-200,200,200)])
 p=orient(smooth.intersection(scope).buffer(-.25,join_style=2),1.)
 assert p.is_valid and p.geom_type=='Polygon' and not p.interiors
 return p

def kind(f):
 x,y=f.center[:2]
 if x>46 and y>47 and f.n[0]>.03 and f.n[1]>.03:return 'NE'
 if x>47 and y< -41 and f.n[0]>.03 and f.n[1]<-.03:return 'SE'
 if x< -52 and y>52 and f.n[0]<-.03 and f.n[1]>.03:return 'NW'
 if (abs(y-36.25)<.02 and x< -20) or (abs(x+17.75)<.02 and y< -30):return 'join'
 if (y>60 and f.n[1]>.8) or (x>60 and f.n[0]>.8) or (y< -54 and f.n[1]<-.8) or (x< -60 and f.n[0]<-.8):return 'street'
 return 'court'

def safe_trim(f):
 a=f.a.copy();bb=f.b.copy()
 for is_a,pt in [(True,a),(False,bb)]:
  near=(pt[0]<-20 and pt[1]<37.5) or(pt[1]<-30 and pt[0]<-16.5)
  if near:
   if is_a:a+=f.t*1.0
   else:bb-=f.t*1.0
 return Facade(f.builder,a[:2],bb[:2],f.label+'-trim') if np.linalg.norm(bb-a)>1 else f

def build(lod=False):
 b=Builder(PALETTE);p=plan();ff=facade_ring(b,p,'historic-wing')
 features={'parameters':P,'design_plan_xy':list(map(list,p.exterior.coords[:-1])),
 'window_openings':0,'facades':[],'probes':[],'photos_embedded':False,'corner_groups':{}}
 def probe(f,u,z,depth,group,material='recessed glass'):
  features['probes'].append({'group':group,'point':f.point(u,z).tolist(),'normal':f.n.tolist(),'depth':depth,'material':material})
 groups={key:[] for key in CENTERS}
 for i,f in enumerate(ff):
  k=kind(f)
  if k in groups:groups[k].append((i,f))
  features['facades'].append({'label':f.label,'kind':k,'a':f.a.tolist(),'b':f.b.tolist(),'normal':f.n.tolist()})
  if k in groups:continue
  if k=='join':
   opened_wall(f,ff[i-1],ff[(i+1)%len(ff)],.05,19.25,[],material='unverified join closure',label='plain-author-join')
   continue
  street=k=='street';holes=[]
  n=max(1,round(f.length/(6.1 if street else 5.8))) if f.length>3.6 else 0
  pitch=f.length/n if n else 0
  for bay in range(n):
   u=-f.length/2+pitch*(bay+.5)
   for floor,z in enumerate([.78,5.45,10.2,15.32]):
    w=min(2.55 if street else 3.25,pitch-.95);h=[3.45,3.50,3.35,3.17][floor];arched=street and floor==3
    op=opening(u,z,w,h,arch=w/2 if arched else 0,segments=20 if not lod else 12);holes.append(op)
    window(f,op,lod,f'bay-{bay}-layer-{floor}',columns=3 if street else 4,rows=4,arch=arched)
    features['window_openings']+=1
    if bay==max(0,n//2) and floor in [1,3] and f.length>20:probe(f,u+w*.13,z+.37,.32,k+f'-layer-{floor}-'+f.label)
   if street and bay%3!=2:
    # Tall classical shafts span middle levels and flank recessed vertical bays.
    for side in [-1,1]:
     xy=f.point(u+side*(min(2.55,pitch-.95)/2+.40),0,.22)[:2]
     column(b,xy,5.05,14.12,.23,lod,f.label+f'-bay-{bay}-tall-column-{side}',ionic=False)
  opened_wall(f,ff[i-1],ff[(i+1)%len(ff)],.05,19.25,holes,rusticated=street,material='warm limestone' if street else 'courtyard plaster')
  tf=safe_trim(f)
  if street:
   cornice(tf,14.6,lod)
   for z in [4.84,9.73]:tf.box(0,z,tf.length-.06,.19,.34,.045,'cut limestone','floor-stone-stringcourse')
   tf.box(0,19.52,tf.length-.06,.38,.49,.035,'cut limestone','attic-parapet')
   tf.box(0,19.75,tf.length-.08,.10,.68,.07,'cut limestone','attic-top-cap')
   tf.box(0,.35,tf.length-.06,.62,.50,.01,'stone base','street-base')
  else:
   cornice(tf,14.6,lod,dentils=False,project=.22,label='court-modest-belt')
   tf.box(0,19.48,tf.length-.06,.36,.32,-.015,'courtyard plaster','court-low-parapet')
  if f.length>20:probe(f,-f.length/2+.55,7.1,-.025 if street else 0,k+'-solid-control','warm limestone' if street else 'courtyard plaster')

 # Each logical arched/rectangular opening is cut continuously through every
 # intersected curved-wall facet. Frames are clipped after forming the full
 # logical shape, so facet boundaries do not become invented mullions.
 refs={}
 for key,items in groups.items():
  assert items,key
  c=CENTERS[key]
  items.sort(key=lambda q:math.atan2(q[1].center[1]-c[1],q[1].center[0]-c[0]),reverse=True)
  total=sum(f.length for _,f in items);offset=-total/2;segments=[]
  for i,f in items:
   mid=offset+f.length/2;segments.append((i,f,mid,offset,offset+f.length));offset+=f.length
  def locate(u,zz,d=0):
   _,f,mid,lo,hi=min(segments,key=lambda s:0 if s[3]<=u<=s[4] else min(abs(u-s[3]),abs(u-s[4])))
   return f.point(u-mid,zz,d),f,u-mid
  specs=[]
  def add(u,z,w,h,arch=0,depth=.32,tag='window'):
   specs.append((opening(u,z,w,h,arch=arch,segments=28 if not lod else 16),depth,tag,bool(arch)))
  if key=='NE':
   add(0,.40,3.4,3.9,depth=.82,tag='main-entry')
   for u in [-6.7,6.7]:add(u,.75,2.05,3.45,depth=.50,tag='porch-side-door')
   add(0,5.32,6.4,3.56,depth=.48,tag='oriel-connection')
   for u in [-7.,7.]:add(u,5.45,2.0,3.55,tag='oriel-flank')
   for u in [-7.,-3.5,0,3.5,7.]:add(u,10.45,1.8,3.18,tag='upper-group')
   add(0,15.25,4.6,3.65,arch=2.05,tag='attic-main-arch')
   for u in [-6.4,6.4]:add(u,15.50,1.75,2.86,tag='attic-flank')
  elif key=='SE':
   add(0,.35,4.4,4.20,arch=2.05,depth=.82,tag='single-ground-arch')
   for u in [-6.4,6.4]:add(u,.78,2.05,3.45,tag='ground-flank')
   for z in [5.45,10.25]:
    for u in [-6.4,-2.2,2.2,6.4]:add(u,z,2.05,3.35,tag='upper-window')
   add(0,15.25,4.5,3.6,arch=2.0,tag='attic-arch')
   for u in [-6.3,6.3]:add(u,15.5,1.8,2.8,tag='attic-flank')
  else:
   add(0,.55,1.85,3.55,depth=.72,tag='small-ground-door')
   add(0,5.2,4.4,8.35,arch=2.2,depth=.70,tag='two-storey-arch')
   add(0,15.32,3.55,3.45,arch=1.775,tag='attic-arch')
  for i,f,mid,lo,hi in segments:
   holes=[translate(op,xoff=-mid) for op,*_ in specs]
   opened_wall(f,ff[i-1],ff[(i+1)%len(ff)],.05,19.75,holes,rusticated=True,label=key+'-curved-wall')
   clip=box(lo+.001,-1,hi-.001,22)
   for num,(op,depth,tag,arched) in enumerate(specs):
    x0,z0,x1,z1=op.bounds;inner=op.buffer(-.066,join_style=2);bars=[]
    if not lod:
     for q in [1,2]:
      x=x0+(x1-x0)*q/3;bars.append(box(x-.024,z0,x+.024,z1))
     rows=7 if tag=='two-storey-arch' else 4
     for q in range(1,rows):
      z=z0+(z1-z0)*q/rows;bars.append(box(x0,z-.024,x1,z+.024))
    panes=inner.difference(unary_union(bars)) if bars else inner
    for geom,back,front,mat,suf in [(inner,-depth-.028,-depth,'recessed glass','glass'),(op.buffer(-.018,join_style=2).difference(panes),-depth+.04,-depth+.12,'dark window frame','frame'),(op.buffer(.145,join_style=2).difference(op),-.018,.10,'cut limestone','surround')]:
     piece=geom.intersection(clip)
     if not piece.is_empty:f.prism(translate(piece,xoff=-mid),back,front,mat,tag+f'-{num}-'+suf)
   cornice(f,14.6,lod,project=.72,label=key+'-strong-cornice')
   f.box(0,19.92,f.length-.008,.32,.49,.035,'cut limestone',key+'-upper-parapet')
   f.box(0,20.145,f.length-.010,.11,.64,.045,'cut limestone',key+'-upper-cap')
  for num,(op,depth,tag,arched) in enumerate(specs):
   x0,z0,x1,z1=op.bounds;u=(x0+x1)/2+(x1-x0)*.12;z=z0+.31
   pt,f,localu=locate(u,z);probe(f,localu,z,depth,key+'-'+tag)
  features['window_openings']+=len(specs)
  refs[key]={'locate':locate,'segments':segments,'length':total}
  features['corner_groups'][key]={'logical_openings':len(specs),'arc_length_m':total,'facets':len(segments),'center_xy':c.tolist()}
  if key=='NW':
   for u in [-3.05,3.05]:
    pt,f,_=locate(u,0,.47);column(b,pt[:2],5.0,14.20,.32,lod,'NW-tall-Ionic-column',ionic=True)
  if key=='NE':
   # Three folded porch-front spans and four piers make an actual open porch.
   rear=[locate(u,0,.05)[0][:2] for u in [-10,-6.6,-3.3,0,3.3,6.6,10]]
   front=[locate(u,0,2.80)[0][:2] for u in [-10,-3.33,3.33,10]]
   porch=orient(Polygon(rear+list(reversed(front))),1.)
   assert porch.is_valid
   b.plan_prism(porch,4.60,4.89,'cut limestone','NE-open-porch-folded-roof')
   b.plan_prism(porch.buffer(.10,join_style=2),4.91,5.06,'cut limestone','NE-open-porch-top-moulding')
   for j,(u,xy) in enumerate(zip([-10,-3.33,3.33,10],front)):
    _,f,localu=locate(u,0,2.80)
    b.box((*xy,2.27),(.78,.78,4.54),'warm limestone',[f.t,f.n,[0,0,1]],label=f'NE-porch-pier-{j}')
    b.box((*xy,4.52),(1.05,1.05,.20),'cut limestone',[f.t,f.n,[0,0,1]],label='NE-porch-pier-cap')
    for side in [-1,1]:
     cxy=np.asarray(xy)+f.t[:2]*side*.80
     column(b,cxy,.28,4.47,.245,lod,'NE-porch-paired-column')
   # First-floor small half-oval oriel: separate glazed facets between slender
   # columns, open balustrade above; main-wall connection itself is opened.
   center,f0,_=locate(0,0,.12);t=f0.t[:2];n=f0.n[:2]
   pts=[center[:2]+t*(3.12*math.cos(a))+n*(2.08*math.sin(a)) for a in np.linspace(0,math.pi,13)]
   op=orient(Polygon(pts),1.)
   b.plan_prism(op,5.08,5.29,'cut limestone','NE-oriel-floor')
   b.plan_prism(op.buffer(.08,join_style=2),9.04,9.25,'cut limestone','NE-oriel-roof')
   of=facade_ring(b,op,'NE-oriel')
   for j,oface in enumerate(of):
    if oface.length>5:continue
    glass=box(-oface.length/2+.045,5.41,oface.length/2-.045,8.94)
    oface.prism(glass,-.095,-.055,'recessed glass','oriel-actual-glazing')
    oface.box(0,7.0,.040,3.5,.075,-.005,'dark window frame','oriel-center-mullion')
    for z in [6.6,7.8]:oface.box(0,z,oface.length-.06,.042,.075,-.005,'dark window frame','oriel-horizontal-bar')
    xy=oface.a[:2]
    column(b,xy,5.29,9.02,.09,lod,'NE-oriel-slender-column')
    oface.box(0,9.35,oface.length-.01,.16,.24,.035,'cut limestone','oriel-balustrade-base')
    oface.box(0,10.00,oface.length-.01,.13,.28,.045,'cut limestone','oriel-balustrade-cap')
    for u in [-oface.length*.3,oface.length*.3]:
     b.lathe(oface.point(u,0,.035)[:2],[(9.44,.058),(9.55,.085),(9.73,.045),(9.93,.065)],'cut limestone',segments=8 if lod else 12,label='oriel-open-baluster')
   pt,entryface,entryu=locate(.408,2.,0)
   features['main_entry_probe_local_xyz']=pt.tolist()
   features['porch_plan_xy']=list(map(list,porch.exterior.coords[:-1]));features['oriel_plan_xy']=list(map(list,op.exterior.coords[:-1]))
   features['main_entry_height_is_author_estimate']=True
 # Roof and ground are C-shaped closed prisms, with no court fill.
 b.plan_prism(p.buffer(-.07,join_style=2),19.04,19.20,'roof closure estimate','historic-C-roof-closure-estimate')
 b.plan_prism(p.buffer(-.07,join_style=2),0,.20,'stone base','historic-C-ground-closure')
 # Component-level seam check, including all ornaments, before export.
 for part in b.parts:
  for x,y,z in part['vertices']:
   assert y>=36-1e-7 or x>=-18-1e-7,(part['label'],x,y)
 features.update(author_parts=len(b.parts),historic_above_ground_layers=4,underground_modeled=False,
  modern_west_L_modeled=False,courtyard_buildings_modeled=False,modern_roof_pavilions_modeled=False,
  roof_and_hidden_detail_estimated=True,global_aggregate_manifold_claimed=False)
 meta={'id':ID,'name':'上海公共租界工部局历史街面翼楼外观候选','status':'exterior-candidate-with-estimated-geographic-placement',
 'current_address':'汉口路153号（名录）','official_narrative_address':'汉口路193—223号','address_correspondence_verified':False,
 'documented_existing_height_m':None,'canceled_50m_tower_modeled':False,'model_selected_architectural_top_m':20.20,
 'model_above_ground_floor_layers':4,'model_below_ground_layers':0,'all_plan_dimensions_estimated':True,'all_floor_layer_datums_estimated':True,
 'height_interpretation':P['illustrated_height_crosscheck'],'scope_kind':'bounded-historic-street-wings',
 'modern_west_L_modeled':False,'courtyard_buildings_modeled':False,'modern_roof_pavilions_modeled':False,
 'join_faces_author_closure':True,'three_corner_types_distinct':True,'court_style_separate':True,
 'street_elevations_photo_guided':True,'unseen_roof_is_author_closure':True,'complete_listed_site_modeled':False,
 'commercial_signs_modeled':False,'interiors_modeled':False,'underground_modeled':False,'photos_embedded':False,'map_replacement':False,
 'original_historic_state_claimed':False,'local_origin_wgs84':P['local_origin_wgs84'],'global_heading_deg':P['global_heading_deg'],
 'source_footprint_id':'86e8b002-5e0e-4912-9807-086c2afeb27c','geometry_license':'MIT','model_units':'metres',
 'author_axes':P['axes'],'gltf_axes':'x east, y up, z south',
 'scope':'Historical north/east/eastern-south street wings only, including distinct concave NE columned porch and small oriel, SE single arched entrance, NW tall arch and Ionic pair; four estimated layers, rusticated street walls, real rectangular and arched holes, simpler plaster court, and estimated roof closures. Current fullblock source is bounded by y>=36 OR x>=-18; artificial join faces are plain closures and modern west/southwest L, uncertain join strips, independent court buildings and modern roof pavilions are preserved/excluded. All geometry dimensions and chronology endpoint interpretations remain estimates; canceled50m tower not modeled.'}
 return b,meta,features

def main():
 q=argparse.ArgumentParser();q.add_argument('--out',type=Path,required=True);q.add_argument('--lod',action='store_true');a=q.parse_args()
 b,meta,features=build(a.lod);a.out.mkdir(parents=True,exist_ok=True);role='lod' if a.lod else 'raw'
 r=b.save(a.out/(ID+'-'+role+'.glb'),meta);(a.out/(role+'-features.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in r.items() if k!='part_summary'},ensure_ascii=False))
if __name__=='__main__':main()
