"""Measured silhouette, timber field and supporting plaster for the projecting front gable."""
import numpy as np
from shapely.geometry import Polygon,LineString,box
from scipy.interpolate import PchipInterpolator
from projection import world

PLASTER='Cream lime infill'
WOOD='Tarred structural timber'
WANE='Worn underside of timber'
CAP='Weathered grey roof rim'
ROOF='Muted slate return'
SOFFIT='Pale verge soffit'
STONE='Grey dressed surround'
BLACK='Deep reveal shadow'
ROOF_CONTROLS=[[187,257],[207,229],[230,189],[249,154],[269,118],[282,94],[289,82],
               [295,85],[325,109],[357,132],[381,148],[400,157],[420,162],[429,168]]
UNDER=[[188,279],[203,273],[225,240],[251,194],[276,150],[292,122],[311,139],[345,159],[380,177],[410,187],[432,196]]
GABLE=[[200,431],[442,396],[428,189],[416,182],[383,171],[350,158],[316,136],[291,115],[265,159],[240,201],[214,249],[203,268]]
# These coordinates refer to a rectification of the documented photograph, with 120 pixels per metre.
def chart(uv):
    u,v=np.array(uv,float).T
    return np.column_stack([-2+u*4.25/509,8.85-v*6.1/731])

def pixel_outline(points,depth=0):return Polygon(world(points,depth))

def add_frame(f,lod):
    wall=pixel_outline(GABLE)
    opening=Polygon(chart([[168,408],[298,407],[298,617],[168,619]]))
    f.prism(wall.difference(opening),-.31,0,PLASTER,'cream panel backing with through opening')
    def timber(points,w,label):
        geom=LineString(chart(points)).buffer(w*.5,cap_style='flat',join_style='round',quad_segs=3)
        shape=geom.intersection(wall).difference(opening.buffer(-.042))
        if shape.area>1.e-6:f.prism(shape,.006,.079,WOOD,label)
    # Posts are interrupted at the tall central opening and continue into the short skirt beneath.
    for i,u in enumerate([-9,56,111,167,232,297,355,413,481]):
        timber([(u,105),(u+(2 if i in [0,8]else 0),710)],.15 if i in [0,8]else .092,
               'upright %02d'%(i+1))
    for i,(v,width)in enumerate([(700,.21),(617,.11),(414,.18),(347,.086)]):
        timber([(-19,v+2),(491,v-3)],width,'horizontal rail %02d'%(i+1))
    braces=[
        [(-12,424),(34,467),(77,527),(110,584),(128,619)],
        [(305,692),(323,636),(338,595),(362,547),(393,501),(433,454),(472,414)],
        [(232,344),(230,310),(221,275),(208,247),(186,225),(162,207)],
        [(232,344),(240,301),(250,272),(264,249),(282,223),(302,204)]]
    for i,line in enumerate(braces):timber(line,.126 if i<2 else .103,'swept brace %02d'%(i+1))
    # Broad sloping side boards meet at a distinct, slightly left-of-centre ridge.
    timber([(-18,414),(52,327),(111,250),(167,178),(205,131)],.15,'left slope at inner gable')
    timber([(206,129),(299,213),(359,269),(411,313),(485,359)],.13,'right slope at inner gable')
    return opening

def add_verge(f,lod):
    xc,zc=np.asarray(ROOF_CONTROLS).T
    sample=np.unique(np.r_[xc,np.linspace(xc[0],xc[-1],35 if lod else 87)])
    px=np.column_stack([sample,PchipInterpolator(xc,zc)(sample)])
    top=world(px,-.21);bottom=world(UNDER,-.21)
    profile=Polygon([*(top+np.array([0,-.052])),*bottom[::-1]])
    f.prism(profile,.045,.21,WOOD,'continuous dark bargeboard and hooked right eave')
    top_skin=Polygon([*top,*((top+np.array([0,-.057]))[::-1])])
    f.prism(top_skin,-.39,.217,CAP,'weathered rim along two roof slopes')
    # The short covered return gives the cropped eave real depth in side views.
    return_skin=Polygon([*top,*((top+np.array([0,-.031]))[::-1])])
    f.prism(return_skin,-.58,-.39,ROOF,'short roof return behind the gable edge')
    stripe=LineString(world([[201,271],[221,242],[245,201],[268,163],[286,133]],-.214))
    f.prism(stripe.buffer(.052,cap_style='flat',join_style='round'),.208,.225,SOFFIT,'pale underside of left verge')
    for i,t in enumerate(np.linspace(.09,.92,9)):
        v=np.array(stripe.interpolate(t,normalized=True).coords[0])
        f.prism(box(v[0]-.032,v[1]+.006,v[0]+.018,v[1]+.088),.215,.232,WANE,'visible rafter tail %02d'%(i+1))
    mould=LineString(world([[422,164],[428,169],[434,180],[437,193]],-.18)).buffer(.047,cap_style='flat')
    f.prism(mould,.13,.185,STONE,'pale right eave stop')
