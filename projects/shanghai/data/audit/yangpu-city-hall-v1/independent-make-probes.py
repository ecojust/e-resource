from pathlib import Path
import numpy as np,json,sys
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
R=Path(sys.argv[2]);p=json.loads(Path(sys.argv[1]).read_text());rays=[]
def glb(v):return [float(v[0]),float(v[2]),float(-v[1])]
def add(name,point,normal,depth=None,mat=None,clear=None,offset=2,distance_range=None,materials=None,intent=''):
 q=np.asarray(point,float);n=np.asarray(normal,float);r={'id':name,'origin_glb':glb(q+n*offset),'direction_glb':glb(-n),'max_distance_m':clear if clear is not None else max(8,offset+abs(depth or 0)+1,max(distance_range or [0])+1),'intent':intent}
 if clear is not None:r['expected_open']=True
 elif distance_range:r.update(first_distance_range_m=distance_range,first_material_in=materials)
 else:r.update(first_material=mat,first_distance_m=offset+depth,tolerance_m=.004)
 rays.append(r)
def basis(a,b):
 a=np.array([*a,0.]);b=np.array([*b,0.]);t=(b-a)/np.linalg.norm(b-a);return (a+b)/2,t,np.array([t[1],-t[0],0]),float(np.linalg.norm(b-a))
ring=list(orient(Polygon(p['source_main']['outline']),1).exterior.coords)[:-1];fac=[basis(a,b) for a,b in zip(ring,ring[1:]+ring[:1])]
def pt(f,u,z,out=0):
 c,t,n,L=f;q=c+t*u+n*out;q[2]=z;return q,n
south=next(f for f in fac if f[3]>40 and f[0][1]<0);north=next(f for f in fac if f[3]>40 and f[0][1]>0);west=next(f for f in fac if f[2][0]<-.9 and f[3]>20);east=next(f for f in fac if f[2][0]>.9 and f[3]>20)
for label,f,central in [('south-central',south,True),('south-west-wing',next(f for f in fac if f[0][0]<-25 and f[0][1]<0 and f[3]>20 and f[2][1]<-.9),False),('south-east-wing',next(f for f in fac if f[0][0]>25 and f[0][1]<0 and f[3]>20 and f[2][1]<-.9),False)]:
 L=f[3];span=L-2*(4.65 if central else 1.3);bays=5 if central else 3;bay=span/bays;u=-span/2+bay*.5;w=bay-.85
 q,n=pt(f,u-w*.32,6.12);add(label+'-lower-glass',q,n,.55,'grey recessed glazing',intent='Real facade aperture, sampled off full and LOD lattice bars')
 q,n=pt(f,u+bay*.23+.08,1.73);add(label+'-base-window',q,n,.55,'grey recessed glazing',intent='Small opening through base wall; solid plinth is not substituted for all base glazing')
 q,n=pt(f,-span/2,7.5);add(label+'-red-column-positive',q,n,mat='vermilion timber',distance_range=[1.31,1.43],materials=['vermilion timber'],intent='Actual large red column beside glass negative wall control')
 if central:
  q,n=pt(f,u+w*.05,13.58);add('central-upper-curved-window',q,n,.55,'grey recessed glazing',intent='Upper curved opening, above the rectangular spring section')
  q,n=pt(f,u+w*.46,13.68);add('central-upper-arch-shoulder',q,n,-.085,'vermilion timber',intent='Neighboring red solid shoulder excludes rectangular or absent wall false pass')
  q,n=pt(f,L/2-2.325,8.8);add('central-pale-end-wall',q,n,0,'warm stone',intent='Pale end section must remain solid instead of repeating red glass bays')
  q,n=pt(f,L/2-2.325+.17,6.40);add('central-pale-end-small-window',q,n,.55,'grey recessed glazing',intent='Actual little opening within the pale end section')
q,n=pt(south,.47,6.67);add('main-recessed-door',q,n,.90,'door timber',intent='Entrance closed leaves behind real opening')
q,n=pt(south,.47,6.67);add('main-canopy-front-air',q,n,clear=2.2,offset=3.5,intent='Open air ahead of recessed entrance, beneath projecting canopy')
q,n=pt(north,3.1,7.5);add('north-plain-centre-wall',q,n,0,'warm stone',intent='North facade is predominantly masonry, not mirrored south columns/windows')
q,n=pt(north,.52,2.21);add('north-estimated-lower-door',q,n,.78,'door timber',intent='Separate lower rear door; north datum explicitly author estimate')
for label,f in [('west',west),('east',east)]:
 q,n=pt(f,.24,3.85);add(label+'-upper-arch-door',q,n,.77,'door timber',intent='Actual upper curved doorway with recessed timber surface')
 q,n=pt(f,1.8,3.95);add(label+'-arch-shoulder',q,n,0,'warm stone',intent='Solid neighboring arch shoulder')
 q,n=pt(f,-7.7+.08,2.1);add(label+'-small-base-window',q,n,.55,'grey recessed glazing',intent='Side base aperture separate from main door')
 q,n=pt(f,.34,5.45);add(label+'-balcony-railing-air',q,n,clear=1.0,offset=2.1,intent='Gap between real balusters, above slab and below top rail')
 q,n=pt(f,.34,4.85);add(label+'-balcony-slab-positive',q,n,-1.525,'warm stone',offset=2.1,intent='Slab positive control under balustrade gap')
# Both directions test the entire delivered model, never only named bridge parts.
for y in [-17.98,-17.6,-17.22]:
 for z in [1.5,1.825,3.05]:
  for sign in [-1,1]:
   add(f'road-through-y{y}-z{z}-dir{sign}',[-.53,y,z],[sign,0,0],clear=32,offset=16,intent='Full model transverse road clearance; centre and capsule shoulder offsets, low/high arch')
for name,y,z in [('south-pier',-21,1.5),('north-pier',-14.3,1.5),('bridge-deck',-17.6,4.05),('arch-crown-solid',-17.6,3.7)]:
 add(name,[-.53,y,z],[-1,0,0],-5.2,'warm stone',offset=16,intent='Bridge solid positive control paired with actual clear rays')
for name,x,y in [('east-campus',66,26),('west-campus',-66,26),('south-forecourt-left',-20,-36),('south-forecourt-right',20,-36)]:
 add(name,[x,y,0],[0,0,1],clear=31,offset=30,intent='No new campus/forecourt ground fill')
for name,x,y,zlo,zhi in [('central-roof',3.6,-5.8,22,25),('east-roof',38.39,-2.95,20,23.5),('west-roof',-34.47,-3.32,20,23.5),('east-roof-junction',22.5,-.12,17,21.5)]:
 add(name,[x,y,0],[0,0,1],offset=35,distance_range=[35-zhi,35-zlo],materials=['glazed green tile','green tile roll','golden glazed crest'],intent='Independent broad geometric height range for connected roof volume, not a surveyed dimension')
for sign in [-1,1]:
 add('central-gable-decor-'+str(sign),[-.53+sign*20.3,.11,23.45],[sign,0,0],offset=6,distance_range=[5.84,6.06],materials=['painted gable ground','green painted bracket','ochre painted line'],intent='Distinct pale/gold/green vertical gable face; cannot be undifferentiated green roof skin')
R.write_text(json.dumps({'schema':'yangpu-city-hall-independent-probes-v1','section_heights_m':[1.5,5.5,11,17,22,26],'rays':rays},indent=2)+'\n');print(len(rays),'independent probes')
