"""Park Hotel: photo-form exterior candidate; all plan and tier dimensions estimated. MIT."""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,facade_ring,opening
ID='huangpu-park-hotel'
PALETTE={'brown brick':{'color':[.25,.16,.105],'roughness':.91},'brick rib':{'color':[.30,.205,.14],'roughness':.9},'black granite':{'color':[.045,.052,.053],'roughness':.38},'carved pale stone':{'color':[.25,.20,.15],'roughness':.8},'frame':{'color':[.16,.17,.16],'roughness':.48,'metallic':.2},'glass':{'color':[.10,.15,.17],'roughness':.24,'metallic':.25},'roof':{'color':[.22,.23,.22],'roughness':.95}}
LEVELS=[0,4.8,9,13.2]+[13.2+3.65*i for i in range(1,19)]+[82.6]
TIERS=[(26,25),(26,25),(23,22),(23,22),(20,19),(20,19),(16,16),(16,16)]
def footprint(i):
 if i<3:w,y0,y1,r=30,-22,23,2.2
 elif i<14:w,y0,y1,r=28,-21,23,.65
 else:
  w,d=TIERS[i-14];y0,y1,r=-8-d/2,-8+d/2,.65
 return orient(box(-w/2+r,y0+r,w/2-r,y1-r).buffer(r,quad_segs=4),sign=1)
def joined_wall(edge,previous,following,lo,hi,holes,material):
 # Miter the inside endpoints rather than overlapping rectangular corner caps.
 t=edge.t[:2];n=edge.n[:2];th=.4
 def inner_corner(point,other_normal):
  normals=np.array([n,other_normal]);return np.linalg.solve(normals,np.array([np.dot(n,point)-th,np.dot(other_normal,point)-th]))
 left=np.dot(inner_corner(edge.a[:2],previous.n[:2])-edge.a[:2],t)/th
 right=np.dot(inner_corner(edge.b[:2],following.n[:2])-edge.b[:2],t)/th
 def mapper(u,z,d):return edge.point(u+(-d)*(left+(u+edge.length/2)/edge.length*(right-left)),z,d)
 surface=box(-edge.length/2,lo,edge.length/2,hi)
 if holes:surface=surface.difference(unary_union(holes))
 edge.builder.prism(surface,-th,0,mapper,material,edge.label+'/mitered-open-wall')
def build(lod=False):
 b=Builder(PALETTE);windows=0;floors=[]
 for i,(lo,hi) in enumerate(zip(LEVELS,LEVELS[1:])):
  poly=footprint(i);edges=facade_ring(b,poly,f'estimated-layer-{i+1}')
  b.plan_prism(poly.buffer(-.42,join_style=2),lo,lo+.16,'roof','estimated-floor-slab')
  b.plan_prism(poly,hi-.15,hi,'roof','estimated-roof-slab')
  band=i in [1,2,13]
  for j,f in enumerate(edges):
   holes=[];long=f.length>3
   if long:
    n=max(1,int((f.length-1.2)/(2.25 if i>2 else 3.4)));pitch=(f.length-1.2)/n
    for k in range(n):
     u=-f.length/2+.6+(k+.5)*pitch;w=pitch-.18 if band else min(1.35,pitch-.65);z=lo+.7;h=min(2.65,hi-lo-1.15)
     sh=opening(u,z,w,h);holes.append(sh);windows+=1
     if lod:
      f.prism(sh,-.3,-.27,'glass','estimated-glass')
      f.box(u,z-.07,w+.30,.14,.60,.10,'carved pale stone','estimated-sill')
     else:f.window(sh,columns=2,rows=2,frame='frame',trim=False,glass='glass',label='estimated-window')
    if not band and i>=3:
     for k in range(n+1):
      u=-f.length/2+.6+k*pitch
      f.box(u,(lo+hi)/2,.30,hi-lo,.25,.10,'brick rib','photo-guided-vertical-rib')
   elif band and f.length>.20:
    # Segments follow the rounded plan at textual levels2/3/14; radii are estimated.
    sh=opening(0,lo+.7,max(.1,f.length-.05),min(2.65,hi-lo-1.15));holes.append(sh);windows+=1
    f.prism(sh,-.24,-.21,'glass','estimated-curved-band-segment')
   joined_wall(f,edges[j-1],edges[(j+1)%len(edges)],lo,hi,holes,'black granite' if i<3 else 'brown brick')
   if long:f.beam(hi-.08,.16,.08,'black granite' if i<3 or band else 'brown brick',label='estimated-layer-band')
  floors.append({'layer':i+1,'bottom_m':lo,'top_m':hi,'plan_bounds':list(poly.bounds),'plan_area_m2':poly.area,'long_glass_band':band})
 # Uppermost brick crown ends at83.8m, with no antennas assigned to the height datum.
 poly=footprint(21);edges=facade_ring(b,poly,'estimated-crown')
 for j,f in enumerate(edges):
  joined_wall(f,edges[j-1],edges[(j+1)%len(edges)],82.6,83.3,[],'brown brick')
  if f.length>3:
   for u in np.linspace(-f.length/2+.35,f.length/2-.35,4):f.box(float(u),83.55,.45,.5,.48,-.12,'brick rib','photo-guided-crown-pier')
 # A blank, stepped dark entrance canopy; lettering and flags not reconstructed.
 b.box((0,-23,4.0),(9,3,.30),'black granite',label='estimated-entrance-canopy')
 b.box((0,-23,4.22),(8.5,2.7,.14),'black granite',label='estimated-canopy-upper-step')
 for part in b.parts:
  v=np.array(part['vertices']);t=np.array(part['triangles']);volume=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
  assert abs(volume)>1e-9,part['label']
  if volume<0:part['triangles']=[(int(a),int(c),int(b)) for a,b,c in t]
 meta={'id':ID,'status':'standalone-photo-form-exterior-candidate','height_reference_m':83.8,'alternate_height_m':83.6,'height_interpretation':'highest authored brick crown; antennas excluded; documentary endpoints unknown','aboveground_layers':22,'underground_modeled':False,'reference_photo_period':'2007','plan_and_tiers_estimated':True,'rear_later_addition_modeled':False,'map_footprint_extruded':False,'map_replacement':False,'photos_embedded':False,'copyright':'Original geometry and code MIT; photograph reference only, no third-party image pixels'}
 return b,meta,{'floors':floors,'estimated_window_openings':windows,'author_parts':len(b.parts),'tiers_width_depth_m':TIERS,'estimated_full_base_width_depth_m':[30,45],'ground_joint_method':'mitered wall-end faces','highest_point_m':83.8}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();b,m,f=build(a.lod);a.out.mkdir(parents=True,exist_ok=True);stem=ID+('-lod' if a.lod else '-raw');r=b.save(a.out/(stem+'.glb'),m);(a.out/(stem+'-features.json')).write_text(json.dumps(f,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
if __name__=='__main__':main()
