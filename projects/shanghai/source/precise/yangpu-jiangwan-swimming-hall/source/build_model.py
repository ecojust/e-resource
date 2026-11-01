"""Original bounded exterior of Jiangwan swimming hall, ENU metres.

The1934open pool is not rendered as present day. The broad2006-era roof,
historic brick envelope and distinct northern entrance are separately built.
All elevations, obscured openings and ornamental dimensions are estimates.
"""
from pathlib import Path
import argparse,json,math
import numpy as np
from shapely.geometry import Polygon,Point,box as rect
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,Facade,opening,facade_ring

ID='yangpu-jiangwan-swimming-hall'
PARAMS=Path(__file__).resolve().with_name('model-parameters.json')

def build(lod=False):
 p=json.loads(PARAMS.read_text());poly=orient(Polygon(p['source_footprint_enu']['coordinates'][0]),sign=1.)
 b=Builder({'pool brick':{'color':[.43,.225,.15],'roughness':.9},'warm stone':{'color':[.70,.68,.61],'roughness':.85},'pale roof cover':{'color':[.70,.71,.64],'roughness':.85},'roof translucent panel':{'color':[.48,.56,.55],'roughness':.43},'roof glazing':{'color':[.25,.36,.37],'roughness':.3,'metallic':.12},'light roof frame':{'color':[.55,.58,.54],'roughness':.65},'annex roof':{'color':[.36,.39,.35],'roughness':.8},'terrace surface':{'color':[.45,.47,.42],'roughness':.92},'green ancillary cover':{'color':[.22,.40,.33],'roughness':.83}})
 features=[];probes=[]
 def record_probe(f,shape,label,depth=.32,material='recessed glass'):
  x0,z0,x1,z1=shape.bounds;u=x0+(x1-x0)*.39;z=z0+(z1-z0)*.41
  probes.append({'label':label,'kind':'recess','point':f.point(u,z).tolist(),'normal':f.n.tolist(),'depth':depth,'material':material})
 def win(f,shape,label,columns=1,rows=2,glass='recessed glass',trim=True):
  f.window(shape,columns=columns,rows=rows,trim=trim,glass=glass,label=label)
  assert b.parts[-1]['label'].endswith('-sill');b.parts.pop()
  x0,z0,x1,z1=shape.bounds;f.box((x0+x1)/2,z0-.055,x1-x0+.18,.11,.18,-.01,'warm stone',label+'-bounded-sill')
  record_probe(f,shape,label,material=glass)
 def belt(f,z,h=.16,projection=.075,label='coping'):
  shape=rect(-f.length/2-.015,z-h/2,f.length/2+.015,z+h/2)
  if getattr(f,'_openings',None):shape=shape.difference(unary_union(f._openings).buffer(.025,join_style=2))
  f.prism(shape,-.45,projection,'warm stone',label)
 def walls(f,holes,top,material):
  f._openings=holes
  for low,high,mat in [(0,.75,'warm stone'),(.75,top-.22,material),(top-.22,top,'warm stone')]:
   if hasattr(f,'_miter'):
    shape=rect(-f.length/2,low,f.length/2,high).difference(unary_union(holes)) if holes else rect(-f.length/2,low,f.length/2,high)
    sa,sc=f._miter
    def mapper(u,z,d):
     shift=(sa*max(0.,1-(u+f.length/2)/.85)+sc*max(0.,1-(f.length/2-u)/.85))*(-d/.60)
     return f.point(u+shift,z,d)
    b.prism(shape,-.60,0.,mapper,mat,f.label+'/mitered-continuous-open-wall')
   else:f.wall(low,high,holes,.60,mat)
 def recessed_arch(f,u,w,h,label,stone=False,depth=1.10,bottom=.12):
  sh=opening(u,bottom,w,h,arch=w/2,segments=20 if not lod else 10)
  material='warm stone' if stone else 'pool brick'
  f.prism(sh,-depth-.12,-depth,'interior shadow',label+'-bounded-interior-stop')
  ring=sh.buffer(.19,join_style=2).difference(sh).intersection(rect(-100,0,100,100));f.prism(ring,-depth,0,material,label+'-deep-reveal')
  for amount,width,front in [(.15,.11,.055),(.30,.09,.025)] if stone else [(.14,.11,.035)]:
   rim=sh.buffer(amount,join_style=2).difference(sh.buffer(amount-width,join_style=2)).intersection(rect(-100,0,100,100))
   f.prism(rim,-.04,front,'warm stone' if stone else 'pool brick',label+'-arch-ring')
  # Real narrow gate bars stand in a recessed opening. Rear closure only
  # bounds an unmodeled interior and does not certify an existing closed gate.
  for t in np.linspace(-w/2+.25,w/2-.25,5):
   bar=sh.buffer(-.12,join_style=2).intersection(rect(u+t-.035,bottom,u+t+.035,bottom+h+.2));f.prism(bar,-.66,-.60,'wrought iron',label+'-gate-bar')
  f.box(u,bottom-.055,w-.06,.13,.72,-.34,'granite base',label+'-shallow-threshold')
  for z in [.45,.76,1.20,2.00,min(3.35,h-.4)]:
   # Off-centre ray falls between the five regular gate bars.
   probes.append({'label':label+'-clear-prefix-'+str(z),'kind':'portal-clear-prefix','point':f.point(u+.13,z+bottom-.12).tolist(),'normal':f.n.tolist(),'depth':.51,'maximum_depth':depth+.05,'material':'bounded gate or rear closure'})
  features.append({'kind':'arched_recess','label':label,'center_enu':f.point(u,1.9).tolist(),'normal_enu':f.n.tolist(),'width_m':w,'apex_m':h+bottom,'rear_stop_depth_m':depth,'threshold_top_m':bottom+.01,'not_a_through_route':True,'all_dimensions_estimated':True})
  return sh

 # Original18-sided source envelope. Modern north exterior is pale stone;
 # opposite south end and long perimeter remain brick and are not mirrored.
 perimeter=p['selected_perimeter_height_m'];northlow=p['selected_north_annex_wall_m'];northhigh=p['selected_north_central_wall_m']
 northfront=None
 outer=facade_ring(b,poly,'outer')
 def inner_joint(g,h,vertex):
  a=np.asarray(vertex[:2])-.60*g.n[:2];c=np.asarray(vertex[:2])-.60*h.n[:2];matrix=np.stack([g.t[:2],-h.t[:2]],axis=1)
  return a+g.t[:2]*np.linalg.solve(matrix,c-a)[0]
 for i,f in enumerate(outer):
  ia=inner_joint(outer[i-1],f,f.a);ic=inner_joint(f,outer[(i+1)%len(outer)],f.b)
  f._miter=(float(np.dot(ia-f.a[:2],f.t[:2])),float(np.dot(ic-f.b[:2],f.t[:2])))
  x,y=f.center[:2];iscentral=y>43.5 and abs(x)<11
  isnorth=y>34.7 and abs(x)<17
  top=northhigh if iscentral else northlow if isnorth else perimeter
  material='warm stone' if isnorth else 'pool brick';holes=[];windows=[]
  if y>47:
   northfront=f
   holes.append(recessed_arch(f,0,3.05,4.45,'north-main-single-arch',True,1.2))
   for j,u in enumerate([-3.3,-1.65,0,1.65,3.3]):
    sh=opening(u,8.70,.48,1.28);holes.append(sh);windows.append((sh,'north-upper-slot-'+str(j),1,2))
   for j,u in enumerate([-7.55,7.55]):
    for k,z in enumerate([2.10,8.95]):
     sh=opening(u,z,.52,1.28);holes.append(sh);windows.append((sh,f'north-side-slot-{j}-{k}',1,2))
  elif isnorth:
   if f.length>4 and y<43.55:
    for j,u in enumerate([0] if f.length<9 else [-f.length*.25,f.length*.25]):
     sh=opening(u,2.10,.70,1.65);holes.append(sh);windows.append((sh,'annex-side-window-'+str(j),1,3))
  elif y<-35:
   # Three modern-photo-supported southern arch positions, with one in each
   # chamfer and one in the long south face; exact hidden openings uncertain.
   holes.append(recessed_arch(f,0,3.0 if f.length<15 else 3.25,4.25,'south-'+f.label,False,1.25))
  elif abs(x)>22 and f.length>30:
   # The modern view hides most long-side masonry. Historical side drawing
   # supports repeated arch bays; present distribution remains estimated.
   for j,u in enumerate(np.linspace(-f.length/2+5.3,f.length/2-5.3,7)):
    holes.append(recessed_arch(f,float(u),2.65,3.85,'long-'+f.label+'-'+str(j),False,1.15))
  elif abs(x)>22 and f.length>10:
   for j,u in enumerate(np.linspace(-f.length/2+2.4,f.length/2-2.4,5)):
    sh=opening(float(u),1.90,.72,1.35);holes.append(sh);windows.append((sh,'north-perimeter-small-'+str(j),1,2))
  walls(f,holes,top,material)
  for sh,label,cols,rows in windows:win(f,sh,label,cols,rows,trim=isnorth)
  belt(f,.76,.16,.05,'base-coping');belt(f,top-.1,.20,.07,'top-coping')
  if isnorth:belt(f,top-.50,.12,.08,'annex-top-step')
  features.append({'kind':'source_outer_edge','a':f.a.tolist(),'b':f.b.tolist(),'normal':f.n.tolist(),'height_m':top,'material':material,'opening_count':len(holes),'all_dimensions_estimated':True})
 assert northfront is not None
 # Northern low annex, brick on its pool-facing southern side. This is a
 # separate elevation from the pale public entrance photographed byKIC.
 ax0,ax1=-16.084478101696636,15.513542593730408;ay0,ay1=31.8,42.95474484382461
 annex=poly.intersection(rect(ax0,ay0,ax1,ay1));core=orient(Polygon(p['source_footprint_enu']['coordinates'][0][2:6]),sign=1.)
 f=Facade(b,[ax0,ay0],[ax1,ay0],'north-annex-pool-side');holes=[];windows=[]
 for j,u in enumerate([-12.2,-8.7,-5.2,5.2,8.7,12.2]):
  sh=opening(u,p['selected_pool_side_window_bottom_m'],1.18,p['selected_pool_side_window_height_m']);holes.append(sh);windows.append((sh,'pool-side-window-'+str(j)))
 holes.append(recessed_arch(f,0,2.9,p['selected_pool_side_door_height_m'],'pool-side-annex-entry',False,1.1,p['selected_pool_side_door_bottom_m']))
 walls(f,holes,6.7,'pool brick')
 for sh,label in windows:win(f,sh,label,2,3)
 belt(f,6.55,.20,.10,'pool-side-eave')
 # Exposed side returns close the pool-facing annex; all are in source area.
 for label,a,c in [('west',[ax0,34.8],[ax0,ay0]),('east',[ax1,ay0],[ax1,36.3297])]:
  g=Facade(b,a,c,'annex-return-'+label);g.wall(0,6.7,(),.55,'pool brick');g._openings=[];belt(g,6.55,.2,.10)
 b.plan_prism(annex.buffer(.06,join_style=2),6.65,6.94,'annex roof','north-annex-low-flat-roof')
 # Higher north stone wings have their own continuous roof, not a cap at
 # the low pool-facing eave. Their short roof strip is visible in2013.
 wingroof=poly.intersection(rect(ax0,36.8,ax1,ay1));b.plan_prism(wingroof.buffer(.06,join_style=2),7.93,8.16,'warm stone','north-wing-roof')
 g=Facade(b,[ax0,36.8],[ax1,36.8],'north-wing-height-return');g.wall(6.72,8.0,(),.5,'warm stone')
 core_edges=facade_ring(b,core,'north-high-core-return')
 for j,g in enumerate(core_edges):
  if g.n[1]>-.9:continue
  ia=inner_joint(core_edges[j-1],g,g.a);ic=inner_joint(g,core_edges[(j+1)%len(core_edges)],g.b)
  sa=float(np.dot(ia-g.a[:2],g.t[:2]));sc=float(np.dot(ic-g.b[:2],g.t[:2]))
  def mapper(u,z,d):
   shift=(sa*max(0.,1-(u+g.length/2)/.85)+sc*max(0.,1-(g.length/2-u)/.85))*(-d/.60)
   return g.point(u+shift,z,d)
  b.prism(rect(-g.length/2,8,g.length/2,northhigh),-.60,0.,mapper,'warm stone','north-high-core-miter-return')
  g._openings=[];belt(g,northhigh-.1,.2,.08)
 b.plan_prism(core.buffer(.06,join_style=2),northhigh-.06,northhigh+.18,'warm stone','north-central-flat-roof')
 # A small pitched shelter is visible on the pool side, not on top of the
 # external northern facade. Its exact framing is a bounded estimate.
 porchx=(ax0+ax1)/2;py0,py1=30.7,34.0
 porchplan=rect(porchx-2.5,py0,porchx+2.5,py1)
 verts=[(porchx-2.5,py0,6.75),(porchx+2.5,py0,6.75),(porchx+2.5,py1,6.75),(porchx-2.5,py1,6.75),(porchx,(py0+py1)/2,8.5)]
 b.add(verts,[(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'annex roof','pool-side-small-pitched-porch')
 for x in [porchx-2.15,porchx+2.15]:b.box([x,py0+.20,5.275],[.22,.22,2.95],'warm stone',label='pool-side-porch-post')
 features.append({'kind':'north_annex','public_north_single_arch':True,'upper_narrow_windows':5,'pool_side_brick_elevation':True,'pool_side_small_pitched_roof':True,'historic_large_urns_not_copied':True,'north_high_wall_m':northhigh,'north_wing_wall_m':northlow,'pool_side_eave_m':6.7,'all_dimensions_estimated':True})

 # Broad shallow modern covering: raised central barrel, two lower wings,
 # transverse light bands, a glazed south end and long clerestory strips.
 half=p['selected_roof_half_width_m'];edge=p['selected_roof_edge_height_m'];apex=p['selected_roof_apex_m'];rise=apex-edge;radius=(half*half+rise*rise)/(2*rise);cz=apex-radius
 sy0,sy1=-34.3,p['selected_cover_north_end_m'];wing_end=p['selected_low_cover_north_end_m'];northdeck=p['selected_north_ancillary_cover_m']
 def roofz(x):return cz+math.sqrt(max(0,radius*radius-x*x))
 def archshape(x0,x1,raiseby=0,thickness=.18,n=None):
  xs=np.linspace(x0,x1,n or (30 if not lod else 16));return Polygon([(float(x),roofz(float(x))+raiseby) for x in xs]+[(float(x),roofz(float(x))+raiseby-thickness) for x in xs[::-1]])
 def sweeproof(shape,y0,y1,material,label):b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),material,label)
 # Seven widely separated translucent bands avoid pretending to know the
 # dense sheet seams or the exact roof cladding material.
 bands=[(-28.5,-27.85),(-20.1,-19.45),(-11.7,-11.05),(-3.3,-2.65),(5.1,5.75),(13.5,14.15),(21.9,22.55)]
 cursor=sy0
 for j,(ya,yb) in enumerate(bands+[(sy1,sy1)]):
  if ya>cursor:sweeproof(archshape(-half,half),cursor,ya,'pale roof cover','central-modern-cover-'+str(j))
  if yb>ya:sweeproof(archshape(-half,half,.015,.10),ya,yb,'roof translucent panel','central-translucent-band-'+str(j))
  cursor=yb
 # Thin broad-profile structural bands are sparse, not subpixel dense ribs.
 for j,y in enumerate([sy0,*[v for pair in bands for v in pair],sy1]):sweeproof(archshape(-half-.04,half+.04,.075,.17),y-.055,y+.055,'light roof frame','central-cover-transverse-frame-'+str(j))
 # Lateral lower cover follows the actual source skew and stepped plan.
 poolplan=poly.intersection(rect(-100,-100,100,31.8))
 def wingheight(x,y):return 8.72+(24.7-abs(x))*.075
 def flatcover(shape,label):
  if shape.is_empty:return
  cursor=sy0
  for j,(ya,yb) in enumerate(bands+[(wing_end,wing_end)]):
   if ya>cursor:
    opaque=shape.intersection(rect(-100,cursor,100,ya)).simplify(1e-7,preserve_topology=True)
    if not opaque.is_empty:b.prism(opaque,0,.18,lambda x,y,d:(x,y,wingheight(x,y)+d),'pale roof cover',label+'-opaque-'+str(j))
   if yb>ya:
    strip=shape.intersection(rect(-100,ya,100,yb)).simplify(1e-7,preserve_topology=True)
    if not strip.is_empty:b.prism(strip,0,.12,lambda x,y,d:(x,y,wingheight(x,y)+d),'roof translucent panel',label+'-light-band-'+str(j))
   cursor=yb
 for name,sh in [('west',poolplan.intersection(rect(-100,sy0,-half,wing_end))),('east',poolplan.intersection(rect(half,sy0,100,wing_end)))]:flatcover(sh,'low-wing-'+name)
 # The chamfered southern end is lower than the raised glazed end. Its roof
 # is bounded to original wall perimeter instead of a new freestanding slab.
 southcap=poolplan.intersection(rect(-100,-100,100,sy0));b.prism(southcap,0,.18,lambda x,y,d:(x,y,8.65+(y+44.70255)*.040+d),'pale roof cover','southern-low-chamfered-roof')
 # Close both shallow triangular steps where the wing roofs meet the
 # chamfered south cover. They are actual narrow fascias, not dark voids.
 for name,x0,x1 in [('west',-24.70,-half),('east',half,24.61)]:
  g=Facade(b,[x0,sy0+.01],[x1,sy0+.01],'low-wing-south-closure-'+name)
  xs=np.linspace(x0,x1,7)
  top=[(float(x-(x0+x1)/2),max(wingheight(float(x),sy0)+.13,8.65+(sy0+44.70255)*.040+.13)) for x in xs]
  outline=Polygon([(-g.length/2,8.6),(g.length/2,8.6)]+top[::-1])
  g.prism(outline,-.22,0,'pale roof cover','south-wing-to-chamfer-fascia')
 # Close the small height transition between source wall tops and modern
 # lower cover. Fascias remain inside the source edge, not over the footway.
 for g in facade_ring(b,poly,'roof-edge-fascia'):
  if min(g.a[1],g.b[1])>=wing_end:continue
  if max(g.a[1],g.b[1])>wing_end:
   # Only the roof-covered portion receives fascia.
   a0=g.a[:2].copy();c0=g.b[:2].copy()
   t=(wing_end-a0[1])/(c0[1]-a0[1]);cut=a0+(c0-a0)*t
   if a0[1]>wing_end:a0=cut
   else:c0=cut
   g=Facade(b,a0,c0,g.label)
  def edgez(v):
   x,y=v[:2]
   return (8.65+(y+44.70255)*.040 if y<sy0 else wingheight(x,y))+.13
  top=[(-g.length/2,edgez(g.a)),(g.length/2,edgez(g.b))]
  if min(g.a[1],g.b[1])<sy0<max(g.a[1],g.b[1]):
   t=(sy0-g.a[1])/(g.b[1]-g.a[1]);v=g.a+(g.b-g.a)*t
   top.insert(1,(-g.length/2+g.length*t,max(8.65+(sy0+44.70255)*.040,wingheight(v[0],sy0))+.13))
  shape=Polygon([(-g.length/2,8.46),(g.length/2,8.46)]+top[::-1])
  if shape.is_valid and shape.area>1e-6:g.prism(shape,-.48,-.02,'light roof frame','wall-to-roof-closure')
 # Small terrace/annex roof behind the main covering, within the enclosure.
 northterrace=poly.intersection(rect(-100,sy1,100,36.3)).difference(annex).difference(porchplan).difference(rect(-100,sy1,-half,wing_end)).difference(rect(half,sy1,100,wing_end))
 sidecovers=northterrace.intersection(unary_union([rect(-100,-100,ax0,100),rect(ax1,-100,100,100)])).buffer(0)
 centralcover=northterrace.difference(sidecovers).buffer(0)
 if not centralcover.is_empty:b.plan_prism(centralcover,northdeck,northdeck+.17,'terrace surface','bounded-north-central-ancillary-roof')
 if not sidecovers.is_empty:b.plan_prism(sidecovers,p['selected_north_side_ancillary_cover_m'],p['selected_north_side_ancillary_cover_m']+.17,'green ancillary cover','bounded-north-side-ancillary-roof')
 for side,a,c in [('west',[-half,sy1],[-half,sy0]),('east',[half,sy0],[half,sy1])]:
  f=Facade(b,a,c,'raised-roof-clerestory-'+side);bottom=wingheight(half,0)+.18;top=edge-.06
  for j in range(14 if not lod else 10):
   count=14 if not lod else 10;u0=-f.length/2+f.length*j/count;u1=-f.length/2+f.length*(j+1)/count
   sh=rect(u0+.075,bottom+.06,u1-.075,top-.06);f.prism(sh,-.10,-.03,'roof glazing','clerestory-glass-'+str(j))
   probe_u=(u0+u1)/2;probes.append({'label':side+'-clerestory-'+str(j),'kind':'recess','point':f.point(probe_u,(bottom+top)/2).tolist(),'normal':f.n.tolist(),'depth':.03,'material':'roof glazing'})
   f.box(u0+.04,(bottom+top)/2,.08,top-bottom,.15,0,'light roof frame','clerestory-post')
  for z in [bottom,top]:f.box(0,z,f.length,.12,.19,0,'light roof frame','clerestory-long-frame')
  f.box(f.length/2-.04,(bottom+top)/2,.08,top-bottom,.15,0,'light roof frame','clerestory-end-post')
 # Modern lower-wing north edges close onto the higher side auxiliary
 # covers; internal returns close the height drop to the central low cover.
 for name,x0,x1 in [('west',-27.295790256273452,-half),('east',half,26.54)]:
  g=Facade(b,[x1,wing_end-.01],[x0,wing_end-.01],'low-wing-north-closure-'+name)
  # The narrow part inward of the green side cover must descend to the
  # lower central auxiliary roof; the outer part only needs the high fascia.
  junction=(x0+x1)/2-(ax0 if name=='west' else ax1)
  lower=[(-g.length/2,northdeck),(junction,northdeck),(junction,8.0),(g.length/2,8.0)] if name=='west' else [(-g.length/2,8.0),(junction,8.0),(junction,northdeck),(g.length/2,northdeck)]
  outline=Polygon(lower+[(g.length/2,wingheight(x0,wing_end)+.13),(-g.length/2,wingheight(x1,wing_end)+.13)])
  g.wall(northdeck,10,(),.24,'pale roof cover',outline)
 for name,a,c in [('west',[ax0+.01,wing_end],[ax0+.01,ay0]),('east',[ax1-.01,ay0],[ax1-.01,wing_end])]:
  g=Facade(b,a,c,'north-side-cover-internal-return-'+name);g.wall(northdeck,8.05,(),.28,'pool brick')
 # The raised central cover ends before the low wings. Their short
 # inner sides therefore need a return down to the lower auxiliary cover.
 for name,a,c in [('west',[-half,sy1],[-half,wing_end]),('east',[half,wing_end],[half,sy1])]:
  g=Facade(b,a,c,'north-low-wing-inner-L-return-'+name)
  g.wall(northdeck,wingheight(half,0)+.13,(),.24,'pale roof cover')
 # These upper returns meet the low annex roof and continue underneath
 # the green side covers. The west segment ends at the mapped wall turn.
 for name,a,c in [('west',[ax0+.01,ay0],[ax0+.01,34.80]),('east',[ax1-.01,36.30],[ax1-.01,ay0])]:
  g=Facade(b,a,c,'green-cover-to-low-annex-return-'+name);g.wall(6.65,8.05,(),.28,'pool brick')
 # The concealed north end below its glazing is explicitly bounded by a
 # closed opaque skirt down to the northern ancillary roof, not an open void.
 g=Facade(b,[half,sy1],[-half,sy1],'modern-north-cover-lower-closure');g.wall(northdeck,9.10,(),.22,'pale roof cover')
 # Actual separately glazed shallow-arched end walls, no opaque sheet under
 # their glass. Vertical mullions and small lower rail remain independent.
 for name,y,a,c in [('south',sy0,[-half,sy0],[half,sy0]),('north',sy1,[half,sy1],[-half,sy1])]:
  f=Facade(b,a,c,'central-glazed-end-'+name);bottom=9.05
  xx=np.linspace(-half,half,30 if not lod else 16);outline=Polygon([(-half,bottom),(half,bottom)]+[(float(x),roofz(float(x))-.10) for x in xx[::-1]])
  n=16 if not lod else 12
  for j in range(n):
   u0=-half+2*half*j/n;u1=-half+2*half*(j+1)/n;sh=outline.intersection(rect(u0+.055,bottom+.05,u1-.055,apex))
   f.prism(sh,-.12,-.04,'roof glazing','glazed-end-panel-'+str(j))
   mid=(u0+u1)/2;probes.append({'label':name+'-end-glass-'+str(j),'kind':'recess','point':f.point(mid,(bottom+roofz(mid)-.10)/2).tolist(),'normal':f.n.tolist(),'depth':.04,'material':'roof glazing'})
  for u in np.linspace(-half,half,n+1):
   h=roofz(float(u))-.05-bottom;f.box(float(u),bottom+h/2,.085,h,.19,0,'light roof frame','glazed-end-post')
  f.box(0,bottom,2*half,.15,.22,0,'light roof frame','glazed-end-base')
  f.prism(outline.buffer(.10,join_style=2).difference(outline),-.12,.05,'light roof frame','glazed-end-boundary')
 # Independent vertical surface/void controls are serialized with the model.
 for x,y,mat in [(0,-24,'pale roof cover'),(7,0,'pale roof cover'),(-7,18,'pale roof cover'),(2,-28.2,'roof translucent panel'),(4,13.8,'roof translucent panel'),(-19,-15,'pale roof cover'),(19,-11.3,'roof translucent panel'),(0,-40,'pale roof cover')]:
  probes.append({'label':'roof-material-'+str((x,y)),'kind':'ray','origin':[x,y,18],'direction':[0,0,-1],'max_distance':18,'material':mat})
 for x,y in [(-32,0),(32,0),(0,-50),(0,54)]:probes.append({'label':'outside-no-site-slab-'+str((x,y)),'kind':'void','origin':[x,y,20],'direction':[0,0,-1],'max_distance':19.95})
 # Light bands and clerestory are true openings in the cover, not colored
 # panels sitting above an uninterrupted opaque roof.
 for x,y in [(2,-28.2),(4,13.8)]:probes.append({'label':'under-translucent-band-open-'+str((x,y)),'kind':'void','origin':[x,y,roofz(x)-.22],'direction':[0,0,-1],'max_distance':roofz(x)-.30})
 # New source-corner and physical northern roof controls validate assembly,
 # rather than assuming per-component closure implies a closed envelope.
 for j,g in enumerate(outer):
  n=g.n+outer[j-1].n;n=n/np.linalg.norm(n);q=g.a.copy();q[2]=2.6
  probes.append({'label':'source-wall-joint-'+str(j),'kind':'solid','origin':(q+n*.25).tolist(),'direction':(-n).tolist(),'max_distance':.9})
 for x,y in [(-22,30),(22,30),(-8,29),(8,29)]:
  probes.append({'label':'north-bounded-cover-'+str((x,y)),'kind':'ray','origin':[x,y,10],'direction':[0,0,-1],'max_distance':10,'material':'green ancillary cover' if abs(x)>20 else 'terrace surface'})
 for x in [-15.5,15.5]:
  probes.append({'label':'south-wing-step-closed-'+str(x),'kind':'ray','origin':[x,sy0-.5,9.33],'direction':[0,1,0],'max_distance':1.,'material':'pale roof cover'})
 for x,n in [(ax0,[-1,0,0]),(ax1,[1,0,0])]:
  probes.append({'label':'green-cover-annex-upper-return-'+str(x),'kind':'ray','origin':[x+(.5 if x<0 else -.5),33,7.45],'direction':n,'max_distance':1.,'material':'pool brick'})
 for x in [-20,20]:
  probes.append({'label':'north-wing-step-closed-'+str(x),'kind':'ray','origin':[x,wing_end+.5,8.65],'direction':[0,-1,0],'max_distance':1.,'material':'pale roof cover'})
 # Full vertical range of the two narrow northern reentrant end walls.
 # These were missing below the fascia in the rejected v7 prototype.
 for x in [-15.5,-15.1,15.0,15.3]:
  for z in [4.05,4.5,6.5,7.4,8.3,8.8]:
   probes.append({'label':'north-reentrant-low-to-high-'+str((x,z)),'kind':'ray','origin':[x,27.3,z],'direction':[0,-1,0],'max_distance':2.,'material':'pale roof cover'})
 for side in [-1,1]:
  for y in [23.9,24.6,25.6]:
   for z in [4.05,4.5,6.5,7.4,8.3,9.0]:
    probes.append({'label':'north-inner-L-return-'+str((side,y,z)),'kind':'ray','origin':[side*13.8,y,z],'direction':[side,0,0],'max_distance':1.5,'material':'pale roof cover'})
 for j,g in enumerate(outer):
  if min(g.a[1],g.b[1])<sy0-1<sy0<max(g.a[1],g.b[1]):
   for y in [sy0-.20,sy0-1.0]:
    t=(y-g.a[1])/(g.b[1]-g.a[1]);q=g.a+(g.b-g.a)*t;q[2]=8.65+(y+44.70255)*.040-.025
    probes.append({'label':'perimeter-south-cover-step-'+str((j,y)),'kind':'ray','origin':(q+g.n*.4).tolist(),'direction':(-g.n).tolist(),'max_distance':1.,'material':'light roof frame'})
 probes.append({'label':'pool-side-pitched-roof-solid','kind':'ray','origin':[porchx,32.35,11],'direction':[0,0,-1],'max_distance':4,'material':'annex roof'})
 features.append({'kind':'physical_roof_transition_closures','all_dimensions_estimated':True,'south_low_wing_fascias':{'y_m':sy0+.01,'x_intervals_m':[[-24.70,-half],[half,24.61]],'bottom_m':8.6,'top':'maximum of wing and south-cover local heights plus0.13m','thickness_m':.22},'north_low_wing_fascias':{'y_m':wing_end-.01,'x_intervals_m':[[-27.295790256273452,-half],[half,26.54]],'outer_bottom_m':8.,'inner_narrow_closure_bottom_m':northdeck,'inner_narrow_x_intervals_m':[[ax0,-half],[half,ax1]],'top':'local wing height plus0.13m','thickness_m':.24},'green_side_cover_to_low_annex_returns':{'west_x_m':ax0+.01,'west_y_interval_m':[ay0,34.8],'east_x_m':ax1-.01,'east_y_interval_m':[ay0,36.30],'bottom_m':6.65,'top_m':8.05,'thickness_m':.28},'lower_central_ancillary_returns':{'y_interval_m':[wing_end,ay0],'bottom_m':northdeck,'top_m':8.05,'west_x_m':ax0+.01,'east_x_m':ax1-.01},'north_low_wing_inner_L_returns':{'x_m':[-half,half],'y_interval_m':[sy1,wing_end],'bottom_m':northdeck,'top_m':wingheight(half,0)+.13,'thickness_m':.24},'perimeter_fascia_profile_split_at_south_cover_join':True,'north_main_cover_opaque_skirt':{'y_m':sy1,'x_interval_m':[-half,half],'bottom_m':northdeck,'top_m':9.10}})
 features.append({'kind':'modern_broad_cover','central_half_width_m':half,'central_y_m':[sy0,sy1],'central_edge_m':edge,'central_apex_m':apex,'translucent_bands':bands,'long_clerestory':True,'south_glazed_end':True,'opaque_material_not_identified':True,'roof_first_documented_added_2006':True,'all_dimensions_estimated':True})
 meta={'id':ID,'name':'江湾游泳馆（历史池馆与现状屋盖）','status':'photo-guided-exterior-estimated-dimensions','scope':'Independent swimming hall exterior: historic brick perimeter, pale northern single-arch entrance, distinct pool-facing annex and modern shallow raised roof observed in2013; no pool interior, site slab, white external shelters, neighboring gym or stadium.','local_origin_wgs84':[p['frame']['lng'],p['frame']['lat']],'local_heading_deg':0,'source_local_ids':[1666],'source_macro':'14-13722-6690','all_elevation_datums_estimated':True,'all_architectural_detail_dimensions_estimated':True,'current_height_surveyed_m':None,'photos_embedded':False,'interiors_modeled':False,'underground_modeled':False,'site_slab_modeled':False,'outdoor_stadium_modeled':False,'gymnasium_modeled':False,'walk_integration':False,'geometry_license':'MIT','map_reference_license':'ODbL-1.0','original_1934_state_claimed':False,'historic_pool_dimensions_not_building_dimensions_m':[50,20],'roof_material_unknown':True}
 return b,meta,features,probes

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 b,m,f,probes=build(a.lod);suffix='-lod' if a.lod else '-raw';r=b.save(a.out/(ID+suffix+'.glb'),m)
 for name,data in [('features'+('-lod' if a.lod else ''),f),('surface-probes'+('-lod' if a.lod else ''),probes)]: (a.out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:r[k] for k in ['file','bytes','triangles','parts','bounds_glb']}))
if __name__=='__main__':main()
