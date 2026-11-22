"""Cast metric rays through the three sides of the tower, its dome and the first open veranda bay."""
import argparse
import json
import math
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent
Scene=runpy.run_path(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py')['SerialScene']
MASONRY='Warm ivory ashlar'
PALE='carved pale stone'
STONE='Sand-coloured moulding'
GLASS='Grey-green glazing'
FRAME='Dark painted sash'
FLOOR='Veranda stone floor'
IRON='Painted iron'
COPPER='Weathered red metal panels'
JOINT='Aged copper seams'
FINIAL='Dark copper finial'


def cases(d):
    checks=[]
    def add(name,point,direction,length,materials=None,limits=None):
        checks.append(dict(name=name,origin=list(point),direction=list(direction),length=length,
                           materials=materials,distance_interval_m=limits))
    a=d['central_face_width_m']/2;dx,dy=d['return_x_y_m']
    belt=d['assumed_first_belt_m'];levels=d['fitted_elevations_m']
    upper,cornice,cap,top=[levels[z] for z in ('upper','cornice','parapet','finial')]
    ring=[(-a-dx,dy),(-a,0),(a,0),(a+dx,dy)]
    for side,(first,last) in enumerate(zip(ring,ring[1:])):
        px,py=(first[0]+last[0])/2,(first[1]+last[1])/2
        w=math.dist(first,last);tx=(last[0]-first[0])/w;ty=(last[1]-first[1])/w
        def face(label,u,z,m,limits,dist=.6):
            add(f'facet {side+1} / '+label,(px+tx*u+ty*dist,py+ty*u-tx*dist,z),(-ty,tx,0),1.4,m,limits)
        for tag,z in [('ground arch',1.39),('middle sash',belt+1.44),('attic sash',upper+1.48)]:
            for sign in (-1,1):face(tag+' pane '+str(sign),sign*.23,z,[GLASS],[.896,.905])
            face(tag+' central mullion',0,z,[FRAME],[.755,.769])
        face('arch keystone',0,belt-.38,[PALE],[.422,.438])
        face('wall beside the ground arch',w*.37,1.73,[MASONRY],[.597,.604])
        face('centre of the hanging cord',0,belt+.08+1.08-.19-.31-.08,[STONE,PALE],[.39,.52])
        face('masonry above the upper sash',0,cornice-.62,[MASONRY],[.594,.605])
        face('upper cornice pale lip',w*.24,upper-.10,[PALE],[.433,.449])
        face('roof frieze',w*.20,cornice-.34,[STONE,PALE],[.476,.527])
    east=a+dx;left=east+.12;span=3.54;right=left+span;front=dy+.38;rear=front+2.42;mid=(left+right)/2
    for name,x in [('left',left),('right',right)]:
        for level,z in [('lower',2.29),('upper',belt+2.03)]:
            add(name+' '+level+' detached column',(x,front-1.02,z),(0,1,0),1.8,[PALE],[.75,.89])
        add(name+' roof parapet pier',(x+(-.06 if name=='left'else .06),front-.57,upper+.36),(0,1,0),1,[PALE],[.37,.42])
    for level,z in [('ground',1.6),('balcony',belt+1.60)]:
        for k in (.67,1.24,1.93):
            add(level+' passage '+str(k),(right+.62,front+k,z),(-1,0,0),span+.30)
        add(level+' door glass behind the colonnade',(mid+.28,front-.35,z),(0,1,0),3.4,[GLASS],[2.98,3.05])
        add(level+' pair of door stiles',(mid,front-.35,z),(0,1,0),3.4,[FRAME],[2.90,2.96])
    for level,z in [('ground',.18),('middle',belt+.054),('roof',upper+.054)]:
        add(level+' horizontal veranda slab',(mid,front+1.15,z+.64),(0,0,-1),1,[FLOOR],[.635,.645])
    for k in (1,3,7,10):
        x=left+k*span/11
        add('turned stone baluster '+str(k),(x,front-.62,upper+.39),(0,1,0),1.28,[PALE],[.53,.58])
    for k in (1.5,3.5,7.5,9.5):
        x=left+k*span/11
        add('daylight between roof balusters '+str(k),(x,front-.44,upper+.39),(0,1,0),.92)
    for t in (.17,.77,.84):
        add('upper veranda iron rail '+str(t),(mid-.39,front-.43,belt+t),(0,1,0),1.0,[IRON],[.44,.48])
    y=d['dome_axis_setback_m']
    for j in range(8):
        heading=(j+.31)*math.pi/4
        ux,uy=math.cos(heading),math.sin(heading)
        add('red dome field '+str(j),(3.3*ux,y+3.3*uy,cap+1.0),(-ux,-uy,0),2.5,[COPPER],[1.15,1.50])
    add('highest copper finial',(0,y,top+.38),(0,0,-1),1.2,[FINIAL],[.372,.389])
    return checks


def verify(mesh,cases):
    scene=Scene(mesh);observed=[]
    for probe in cases:
        first=scene.ray(probe['origin'],probe['direction'],probe['length'])
        material=probe['materials']
        assert (first is None if material is None else first and first['material'] in material),(mesh,probe['name'],first)
        if probe['distance_interval_m']:
            lo,hi=probe['distance_interval_m']
            assert lo<=first['distance_m']<=hi,(probe['name'],first,lo,hi)
        observed.append({**probe,'first_hit':first})
    return {'asset':scene.asset,'triangles':len(scene.tri),'cases':observed}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for role in ('raw','full','lod','output'):parser.add_argument(role,type=Path)
    args=parser.parse_args()
    model=HERE.parents[2]/'source/precise/jingan-rong-residence-garden-tower/measurements/two-photo-fit.json'
    probes=cases(json.loads(model.read_bytes()))
    data={role:verify(getattr(args,role),probes)for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
