"""Select independent analytic controls from disclosed final dimensions, never rebuild author geometry.
Usage: final-features.json final-model-parameters.json output.json
"""
from pathlib import Path
import hashlib,json,math,sys
F,P,O=map(Path,sys.argv[1:4]);features=json.loads(F.read_text());p=json.loads(P.read_text());rays=[];ground=[]
def bind(f):return {'file':f.name,'bytes':len(f.read_bytes()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
def glb(v):return [v[0],v[2],-v[1]]
def ray(name,origin,direction,maxdist,**expect):rays.append({'id':name,'origin_glb':glb(origin),'direction_glb':glb(direction),'max_distance_m':maxdist,**expect})
def inward(name,center,n,u,z,maxdist,**expect):
 t=[-n[1],n[0],0];origin=[center[i]+t[i]*u+n[i]*.45 for i in range(3)];origin[2]=z;ray(name,origin,[-v for v in n],maxdist,**expect)
def vertical(name,x,y,mat,lo,hi,z=20):ray(name,[x,y,z],[0,0,-1],z,first_material=mat,first_distance_range_m=[z-hi,z-lo])
arches=[f for f in features if f['kind']=='arched_recess']
for i,f in enumerate(arches):
 c,n=f['center_enu'],f['normal_enu'];bottom=f['threshold_top_m']-.01;apex=f['apex_m'];label=f['label'];zs=sorted(set(z for z in [.22,.45,.76,1.10,1.15,1.20,1.70,2.80,3.60,bottom+.22,bottom+.76,apex-.35]if bottom+.05<z<apex-.25))
 for u in [-.31,.31]:
  for z in zs:
   inward(f'{label}-u{u}-z{z}-clear-wall',c,n,u,z,.98,expected_open=True)
   d=.45+f['rear_stop_depth_m'];inward(f'{label}-u{u}-z{z}-stop',c,n,u,z,d+.2,first_material='interior shadow',first_distance_range_m=[d-.001,d+.001])
 z=bottom+min(1.3,(apex-bottom)/2)
 inward(label+'-real-gate-center',c,n,0,z,1.2,first_material='wrought iron',first_distance_range_m=[1.049,1.051])
 inward(label+'-adjacent-solid',c,n,f['width_m']/2+.46,z,.7,first_material_in=['warm stone','pool brick'],first_distance_range_m=[.449,.451])
 if bottom<.2:
  q=[c[j]-n[j]*.25 for j in range(3)];vertical(label+'-threshold',q[0],q[1],'granite base',f['threshold_top_m']-.002,f['threshold_top_m']+.002,z=.35)
  ground.append({'id':label+'-threshold-footprint','point_local_xy':q[:2],'expected_low_covered':True,'expected_collision_covered':True,'expected_full_covered':True})
# Five modern-photo-supported upper north slots, sampled within glass panes at two heights.
north=next(f for f in arches if f['label']=='north-main-single-arch')
for j,u in enumerate([-3.3,-1.65,0,1.65,3.3]):
 for z in [8.92,9.63]:inward(f'north-upper-{j}-z{z}',north['center_enu'],north['normal_enu'],u+.09,z,1,first_material='recessed glass',first_distance_range_m=[.769,.771])
# Exposed pool-side windows must be above the bounded lower transition cover.
side=next(f for f in arches if f['label']=='pool-side-annex-entry');z0=p['selected_pool_side_window_bottom_m'];h=p['selected_pool_side_window_height_m']
for j,u in enumerate([-12.2,-8.7,-5.2,5.2,8.7,12.2]):
 for frac in [.20,.80]:inward(f'pool-side-window-{j}-fraction-{frac}',side['center_enu'],side['normal_enu'],u+.20,z0+h*frac,1,first_material='recessed glass',first_distance_range_m=[.769,.771])
# Distinct low corners, central transition, annex, north wings, central entry and pitched shelter.
for name,x,y,mat,z in [('north-west-corner',-22.2,31.1,'green ancillary cover',p['selected_north_side_ancillary_cover_m']+.17),('north-east-corner',22.1,32.1,'green ancillary cover',p['selected_north_side_ancillary_cover_m']+.17),('north-central-west',-8.2,28.8,'terrace surface',p['selected_north_ancillary_cover_m']+.17),('north-central-east',8.3,28.4,'terrace surface',p['selected_north_ancillary_cover_m']+.17),('annex-flat',7.1,34.8,'annex roof',6.94),('north-wing-flat',12.1,39.9,'warm stone',8.16),('north-core-flat',1.2,45.8,'warm stone',p['selected_north_central_wall_m']+.18)]:vertical(name,x,y,mat,z-.002,z+.002)
vertical('small-poolside-pitched-shelter',side['center_enu'][0]+.19,32.35,'annex roof',8.3,8.5)
cover=next(f for f in features if f['kind']=='modern_broad_cover');half=cover['central_half_width_m'];edge=cover['central_edge_m'];apex=cover['central_apex_m'];rise=apex-edge;radius=(half*half+rise*rise)/(2*rise);cz=apex-radius
roofz=lambda x:cz+math.sqrt(radius*radius-x*x)
for j,band in enumerate(cover['translucent_bands']):
 y=sum(band)/2;x=1.13 if j%2 else -5.37;z=roofz(x)
 vertical(f'roof-translucent-{j}',x,y,'roof translucent panel',z-.06,z+.02)
 ray(f'roof-translucent-{j}-no-opaque-below',[x,y,z-.24],[0,0,-1],z-.29,expected_open=True)
for j,(x,y)in enumerate([(-4.17,-24.4),(6.13,-5.7),(2.37,17.2)]):vertical(f'roof-opaque-{j}',x,y,'pale roof cover',roofz(x)-.07,roofz(x)+.002)
for x,y in [(-19.17,-13.3),(19.37,2.4)]:
 z=8.72+(24.7-abs(x))*.075+.18;vertical(f'low-wing-{x}',x,y,'pale roof cover',z-.002,z+.002)
# Roof glazing points avoid all full/LOD mullions; first actual surface must be glass.
for sign in [-1,1]:inward(f'clerestory-{sign}',[sign*half,-5.13,0],[sign,0,0],0,10.1,1,first_material='roof glazing',first_distance_range_m=[.479,.481])
for name,y,sign in [('south',cover['central_y_m'][0],-1),('north',cover['central_y_m'][1],1)]:inward(name+'-end-glass',[3.13,y,0],[0,sign,0],0,10.7,1,first_material='roof glazing',first_distance_range_m=[.489,.491])
# New assembly seams disclosed after close native review: own offsets differ from author rays.
closures=next(f for f in features if f['kind']=='physical_roof_transition_closures')
for side in ['west','east']:
 sign=1 if side=='west'else-1
 q=closures['green_side_cover_to_low_annex_returns'];x=q[side+'_x_m'];ya,yb=q[side+'_y_interval_m'];y=ya+(yb-ya)*.63
 for z in [7.13,7.64]:inward(side+'-green-annex-upper-return-'+str(z),[x,y,0],[sign,0,0],0,z,.8,first_material='pool brick',first_distance_range_m=[.449,.451])
 q=closures['lower_central_ancillary_returns'];x=q[side+'_x_m'];ya,yb=q['y_interval_m'];y=ya+(yb-ya)*.37
 for z in [4.4,5.9,7.5]:inward(side+'-green-central-lower-return-'+str(z),[x,y,0],[sign,0,0],0,z,.8,first_material='pool brick',first_distance_range_m=[.449,.451])
for side,x in [('west',-18.33),('east',18.47)]:
 for z in [8.70,9.18]:inward(side+'-south-wing-cap-fascia-'+str(z),[x,closures['south_low_wing_fascias']['y_m'],0],[0,-1,0],0,z,.8,first_material='pale roof cover',first_distance_range_m=[.439,.451],required_hit_distance_range_m=[.449,.451],required_hit_material='pale roof cover')
 for z in [8.42,8.98]:inward(side+'-north-wing-fascia-'+str(z),[x,closures['north_low_wing_fascias']['y_m'],0],[0,1,0],0,z,.8,first_material='pale roof cover',first_distance_range_m=[.449,.451])
for z in [4.47,6.33,8.71]:inward('north-cover-lower-skirt-'+str(z),[3.27,closures['north_main_cover_opaque_skirt']['y_m'],0],[0,1,0],0,z,.8,first_material='pale roof cover',first_distance_range_m=[.449,.451])
# Complete L-shaped boundary where the main roof stops before the side wings.
q=closures['north_low_wing_inner_L_returns']
for sign in [-1,1]:
 for y in [23.83,24.61,25.71]:
  for z in [4.31,5.87,7.23,8.56,9.19]:inward(f'inner-L-return-{sign}-{y}-{z}',[sign*half,y,0],[-sign,0,0],0,z,.8,first_material='pale roof cover',first_distance_range_m=[.449,.451])
for x in [-15.62,-15.07,15.06,15.32]:
 for z in [4.31,5.87,7.23,8.56,9.19]:inward(f'inner-narrow-north-fascia-{x}-{z}',[x,closures['north_low_wing_fascias']['y_m'],0],[0,1,0],0,z,.8,first_material='pale roof cover',first_distance_range_m=[.449,.451])
# Sample either side of the south roof-profile kink on both external long walls.
for f in [q for q in features if q['kind']=='source_outer_edge']:
 ay,by=f['a'][1],f['b'][1]
 if not min(ay,by)<cover['central_y_m'][0]<max(ay,by):continue
 for dy in [-.09,.09]:
  y=cover['central_y_m'][0]+dy;mix=(y-ay)/(by-ay);x=f['a'][0]+mix*(f['b'][0]-f['a'][0]);ztop=(8.65+(y+44.70255)*.04 if dy<0 else 8.72+(24.7-abs(x))*.075)+.13
  for z in [8.62,(8.6+ztop)/2]:inward(f'outer-fascia-profile-kink-{x}-{y}-{z}',[x,y,0],f['normal'],0,z,.8,first_material_in=['light roof frame','warm stone','pale roof cover'],first_distance_range_m=[.36,.48])
# Closed roof/wall connection: raised full wall, closure fascia, and roof share the seam.
for f in [q for q in features if q['kind']=='source_outer_edge']:
 c=[(f['a'][i]+f['b'][i])/2 for i in range(3)]
 if c[1]>15:continue
 htop=(8.65+(c[1]+44.70255)*.04 if c[1]<cover['central_y_m'][0] else 8.72+(24.7-abs(c[0]))*.075)+.13
 for z in [8.55,8.62,(8.6+htop)/2]:
  if z>htop-.003:continue
  inward(f'wall-roof-seam-{len(rays)}',c,f['normal'],.0,z,1,first_material_in=['warm stone','light roof frame','pale roof cover'],first_distance_range_m=[.36,.48])
for j,(x,y)in enumerate([(-31.4,1.7),(31.2,-3.8),(1.7,-48.9),(2.3,52.1)]):
 ray(f'outside-no-slab-{j}',[x,y,20],[0,0,-1],19.98,expected_open=True);ground.append({'id':f'outside-{j}','point_local_xy':[x,y],'expected_low_covered':False,'expected_collision_covered':False,'expected_full_covered':False})
for name,point in [('covered-pool-unmodeled-interior',[3.1,-8.7]),('north-annex-unmodeled-room',[3.2,39.1])]:ground.append({'id':name,'point_local_xy':point,'expected_low_covered':False,'expected_collision_covered':True,'expected_full_covered':True})
O.write_text(json.dumps({'schema':'jiangwan-swimming-hall-independent-probes-v1','method':'Reviewer-selected cuts, material and depth controls, independent offsets and analytic roof expectations. Disclosed coordinates establish the intended location only; actual decoded active-scene triangles determine all results. No author construction module executed.','input_coordinate_disclosures':[bind(F),bind(P)],'section_heights_m':[.12,.5,1.15,2,5,8,10,11.5,12.5],'rays':rays,'ground_controls':ground,'script':bind(Path(__file__))},indent=2)+'\n')
print(json.dumps({'rays':len(rays),'arches':len(arches),'ground_controls':len(ground)}))
