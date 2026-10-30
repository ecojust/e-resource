"""Grand Theatre entrance/light-tower exterior candidate. Original code MIT.
Only bounded frontage; all plan dimensions and hidden details estimated.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from common.photo_architecture import Builder,Facade,opening
ID='huangpu-grand-theatre'
PAL={
 'cream':{'color':[.78,.74,.61],'roughness':.78},
 'tower glass':{'color':[.81,.84,.78],'roughness':.46},
 'amber glass':{'color':[.58,.39,.12],'roughness':.32,'metallic':.12},
 'dark glass':{'color':[.09,.14,.15],'roughness':.3,'metallic':.15},
 'black marble':{'color':[.07,.075,.075],'roughness':.35},
 'metal frame':{'color':[.16,.17,.15],'roughness':.4},
 'canopy glass':{'color':[.85,.86,.76],'roughness':.4},
 'roof':{'color':[.36,.38,.35],'roughness':.9},
 'letter':{'color':[.035,.04,.038],'roughness':.5},
 'panel seam':{'color':[.57,.61,.57],'roughness':.65},
}
P={'scope':'Street entrance, light tower and bounded adjacent curved return only; no auditorium or entire shop strip.',
 'tower_design_top_m':30.5,'unresolved_height_claims_m':[16,30.5],
 'height_endpoints_verified':False,'plan_dimensions_measured':False,
 'entrance_width_m_estimated':12.4,'frontage_depth_m_estimated':7,
 'body_top_m_estimated':16.2,'fin_top_m_estimated':22.5,'upper_screen_top_m_estimated':21.0,
 'light_tower_plan_m_estimated':[3.8,3.8],'return_corner_radius_m_estimated':1.2,'source_photo_periods':['2010','undated historical','undated repaired night view'],
 'materials':'Opaque stand-ins for translucent glass; no copied photograph pixels.',
 'full_building_accepted':False,'geographic_registration':False}
GLYPHS={
 'G':[[(.85,.85),(.65,1),(.15,1),(0,.8),(0,.2),(.15,0),(.8,0),(.85,.42),(.5,.42)]],
 'R':[[(0,0),(0,1),(.6,1),(.85,.8),(.8,.6),(0,.55)],[(.4,.55),(.9,0)]],
 'A':[[(0,0),(.4,1),(.8,0)],[(.17,.4),(.65,.4)]],
 'N':[[(0,0),(0,1),(.8,0),(.8,1)]],
 'D':[[(0,0),(0,1)],[(0,1),(.5,1),(.8,.8),(.8,.2),(.5,0),(0,0)]],
 'T':[[(0,1),(.9,1)],[(.45,1),(.45,0)]],
 'H':[[(0,0),(0,1)],[(.8,0),(.8,1)],[(0,.5),(.8,.5)]],
 'E':[[(.8,1),(0,1),(0,0),(.8,0)],[(0,.5),(.65,.5)]],
}
def letter(b,ch,x,y,z,height,label,lod):
 for stroke in GLYPHS[ch]:
  b.tube([(x+(u-.45)*height,y,z+v*height) for u,v in stroke],height*.045,'letter',8,label)

def build(lod=False):
 b=Builder(PAL);seg=12 if lod else 48
 # A bounded curved return, deliberately cut before the unbound shop frontage.
 radius=1.2;cx=-5.75;cy=1.2
 arc=[(cx+radius*math.cos(t),cy+radius*math.sin(t)) for t in np.linspace(-math.pi/2,0,seg+1)]
 plan=Polygon([(-11,0),*arc,(-4.55,6.4),(-11,6.4)])
 shell=plan.difference(plan.buffer(-.3,join_style=2))
 # Upper three horizontal bands wrap into a rounded edge by the tower.
 b.plan_prism(shell,4.25,5.25,'cream','bounded-left-return-lower-wall')
 b.plan_prism(shell.difference(box(-9.8,-.1,-6.2,.40)),5.25,6.75,'cream','return-wall-with-opening')
 b.plan_prism(shell,6.75,14.8,'cream','bounded-left-return-upper-wall')
 for lo,hi in [(4.2,4.55),(7.8,8.2),(11,11.4),(14.45,14.9)]:
  band=plan.buffer(.20,join_style=1,quad_segs=seg).difference(plan.buffer(-.25,join_style=1,quad_segs=seg))
  b.plan_prism(band,lo,hi,'cream','rounded-horizontal-band')
 b.plan_prism(plan,14.82,15.0,'roof','return-roof')
 # Deliberately bounded front-window inset, unrelated shops excluded.
 fleft=Facade(b,(-9.8,0),(-6.2,0),'return-window')
 shleft=opening(0,5.3,3.5,1.4)
 if lod:fleft.prism(shleft,-.34,-.32,'dark glass','glazing')
 else:fleft.window(shleft,6,1,'metal frame',False,'dark glass','glazing')
 for x in [-10.7,-5.1]:b.box((x,.2,2.15),(.45,.6,4.3),'black marble',label='return-base-pier')
 b.box((-7.9,.28,1.95),(5.1,.15,3.7),'dark glass',label='return-base-infill-estimate')
 # Upper entrance has true recessed glazing; no solid wall behind its front face.
 b.box((12.15,3.5,8.1),(.35,7,16.2),'cream',label='bounded-right-end-wall')
 b.box((6.2,6.83,8.1),(12.2,.34,16.2),'cream',label='estimated-rear-cut-closure')
 b.box((6.2,3.5,16.08),(12.2,7,.24),'roof',label='frontage-roof')
 b.box((6.2,3.5,.10),(12.2,7,.20),'roof',label='frontage-floor')
 f=Facade(b,(.2,0),(12,0),'entrance')
 shape=opening(0,4.6,11.5,10.75)
 if lod:f.prism(shape,-.38,-.35,'amber glass','upper-glazing')
 else:f.window(shape,4,4,'metal frame',False,'amber glass','upper-glazing')
 # Tall projecting fins have a sloping estimated cap; photo-visible order is retained.
 for x in np.linspace(.3,12,5):
  yz=Polygon([(0,4.45),(5.7,4.45),(5.7,21.5),(0,22.5)])
  b.prism(yz,-.18,.18,lambda y,z,d,x=x:(x+d,y,z),'cream','upper-vertical-fin')
 # Recessed upper screen and horizontal bands observed behind the projecting fins.
 # This is a bounded facade interpretation, not an auditorium or surveyed roof.
 b.box((6.15,3.2,18.6),(11.9,.35,4.8),'cream',label='estimated-recessed-upper-screen')
 for z in [16.6,18.6,20.6]:b.box((6.15,2.95,z),(11.9,.4,.20),'cream',label='upper-screen-horizontal-band')
 # Four main entry bays with dark stone perimeter and recessed doors.
 for x in [.25,3.2,6.15,9.1,12.05]:
  b.box((x,.05,1.85),(.24,.55,3.7),'black marble',label='entry-dark-pier')
 for x in [1.725,4.675,7.625,10.575]:
  f2=Facade(b,(x-1.3,.2),(x+1.3,.2),'entry-bay')
  sh=opening(0,.18,2.50,3.32)
  if lod:f2.prism(sh,-.20,-.17,'dark glass','door')
  else:f2.window(sh,2,2,'metal frame',False,'dark glass','door')
 # Projecting milk-white canopy with an actual underside grid.
 canopy=box(-4.9,-2.2,12.65,1.0)
 b.plan_prism(canopy,3.62,4.12,'canopy glass','projecting-entry-canopy')
 b.box((3.875,-2.24,4.11),(17.55,.10,.16),'cream',label='canopy-fascia-cap')
 if not lod:
  for x in np.arange(-4.8,12.6,.65):b.box((float(x),-.6,3.60),(.035,3.15,.035),'metal frame',label='canopy-underside-grid')
  for y in [-1.9,-1.2,-.5,.2,.9]:b.box((3.875,y,3.60),(17.5,.035,.035),'metal frame',label='canopy-underside-grid')
 # Square panelled light tower, photo-based location and authored dimensions.
 tx=-2.6;ty=1.1;w=3.8
 b.box((tx,ty,15.25),(w,w,30.5),'tower glass',label='square-light-tower')
 # Front and left panel divisions; round-number panel spacing is explicitly estimated.
 for z in np.arange(.8,30.5,.95):
  b.box((tx,-.815,float(z)),(w,.045,.035),'panel seam',label='tower-front-panel-joint')
  b.box((tx-w/2-.015,ty,float(z)),(.045,w,.035),'panel seam',label='tower-side-panel-joint')
 for x in [tx-w/6,tx+w/6]:b.box((x,-.815,15.25),(.035,.045,30.5),'panel seam',label='tower-front-panel-joint')
 for y in [ty-w/6,ty+w/6]:b.box((tx-w/2-.015,y,15.25),(.045,.035,30.5),'panel seam',label='tower-side-panel-joint')
 # Letter strokes are original symbolic geometry, not copied historic typography.
 for word,z0 in [('GRAND',28.45),('THEATRE',20.85)]:
  for i,ch in enumerate(word):letter(b,ch,tx-.2 if i==0 else tx+.55,-.91,z0-i*1.26,1.85 if i==0 else 1.02,'illustrative-vertical-lettering',lod)
 for i,ch in enumerate('GRANDTHEATRE'):letter(b,ch,-2.0+i*1.05,-2.30,3.73,.27,'illustrative-canopy-lettering',lod)
 # All authored elements are closed separate solids. Normalize sign only.
 for part in b.parts:
  v=np.array(part['vertices']);t=np.array(part['triangles'])
  vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
  assert abs(vol)>1e-9,part['label']
  if vol<0:part['triangles']=[(int(a),int(c),int(d)) for a,d,c in t]
 return b

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
 b=build(a.lod);a.out.mkdir(parents=True,exist_ok=True);stem=ID+('-lod' if a.lod else '-raw')
 meta={'id':ID,'name':'Grand Theatre street entrance and light tower exterior candidate','status':'standalone-partial-exterior-candidate-not-geographically-registered','tower_height_chosen_interpretation_m':30.5,'alternate_reported_height_m':16,'height_endpoints_verified':False,'all_plan_dimensions_estimated':True,'frontage_only':True,'auditorium_modeled':False,'whole_shop_strip_modeled':False,'map_replacement':False,'photos_embedded':False,'multi_period_reference':True,'lettering_original_simplification':True,'copyright':'Original code and geometry MIT; no source photographs embedded'}
 r=b.save(a.out/(stem+'.glb'),meta)
 features={'parameters':P,'author_parts':len(b.parts),'curved_return_segments':12 if a.lod else 48,'upper_glazing_bays_estimated':4,'vertical_fins_estimated':5,'entry_bays_estimated':4,'rear_is_cut_closure_not_surveyed_elevation':True,'original_symbolic_lettering':True}
 (a.out/(stem+'-features.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
if __name__=='__main__':main()
