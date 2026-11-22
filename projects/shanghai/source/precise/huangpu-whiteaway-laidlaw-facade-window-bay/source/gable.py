"""Two photographed pairs of windows on the upper floors of Whiteaway Laidlaw, Shanghai."""
from pathlib import Path
from shapely.geometry import Polygon,box
from profile_tools import BRICK as STUCCO,cb,slab,bricks_uv

RIDGE='Cream projecting facade bands'
REVEAL='Inside of the recessed opening'
SILL='Slender projecting window ledge'
SASH='Dark frame and transoms'
GLASS='Cool grey blue glazing'
JOINT='Fine horizontal joint'
PALETTE={}
for key,rgb in [(STUCCO,(255,255,255)),(RIDGE,(207,200,180)),(REVEAL,(157,152,136)),
                (SILL,(184,177,155)),(SASH,(55,58,56)),(GLASS,(114,128,133)),(JOINT,(172,167,152))]:
    PALETTE[key]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.80)
PALETTE[STUCCO]['texture']=str(Path(__file__).with_name('finish.png'))
CENTRES=(-.866,.866)
WIDTH=2.06
HALF=.646
HEIGHT=1.54
FLOORS=(.48,3.12)
TOP=5.15

def strip(b,centre,width,extra,detail):
    # A shallow raised central fillet between two planar shoulders catches side light.
    cross=[(-width,.06),(-width,-.062),(-.146,-.076),(-.121,-.116),(-.077,-.148),
           (.077,-.148),(.121,-.116),(.146,-.076),(width,-.062),(width,.06)]
    if not detail:cross=[(-width,.06),(-width,-.063),(-.078,-.144),(.078,-.144),(width,-.063),(width,.06)]
    verts=[(centre+x,y-extra,z)for z in (0,TOP) for x,y in cross];cnt=len(cross)
    faces=[tuple(reversed(range(cnt))),tuple(range(cnt,2*cnt))]
    faces.extend((i,(i+1)%cnt,(i+1)%cnt+cnt,i+cnt) for i in range(cnt))
    b.add(verts,faces,RIDGE,'Running shallow vertical flute and shoulders')

def model(b,lod=False):
    segment=box(-WIDTH,0,WIDTH,TOP)
    for z in FLOORS:
        for x in CENTRES:
            segment=segment.difference(box(x-HALF,z,x+HALF,z+HEIGHT))
    slab(b,segment,.023,.36,STUCCO,'Pale street wall surrounding two floors with paired windows')
    for c in [-1.83,1.83]:strip(b,c,.22,.014,not lod)
    # Finely rusticated spandrel panels extend between the front bands.
    for z in (0.30,2.18,2.43,2.68,2.92,4.85):
        cb(b,-1.61,1.61,.015,.029,z-.005,z+.005,JOINT,'Narrow horizontal line across stone panels')
    for z in FLOORS:
        for x in CENTRES:
            outside=box(x-HALF,z,x+HALF,z+HEIGHT)
            inside=box(x-HALF+.050,z+.046,x+HALF-.050,z+HEIGHT-.048)
            slab(b,outside.difference(inside),.083,.166,REVEAL,'Stone lining of the recessed aperture')
            frame=box(x-HALF+.080,z+.074,x+HALF-.080,z+HEIGHT-.079)
            slab(b,inside.difference(frame),.154,.227,SASH,'Square steel perimeter of each sash')
            slab(b,frame,.231,.264,GLASS,'Individual pane behind transoms')
            # A wide top light is undivided. The lower central stile ends beneath its rail.
            divide=z+1.097
            cb(b,x-.021,x+.021,.160,.224,z+.07,divide,SASH,'Central vertical sash below the transom')
            for offset,thick in [(0.415,.012),(.749,.012),(1.097,.026)]:
                cb(b,x-HALF+.065,x+HALF-.065,.144,.222,z+offset-thick,z+offset+thick,SASH,'Main transom or narrow horizontal rail')
        # The photographed horizontal ledge goes across the small pier between the two apertures.
        cb(b,-1.56,1.56,-.081,.106,z-.069,z-.023,SILL,'Continuous narrow ledge below paired windows')
        cb(b,-1.53,1.53,-.046,.091,z-.023,z+.001,RIDGE,'Sloped upper lip of paired sill')
    bricks_uv(b)
