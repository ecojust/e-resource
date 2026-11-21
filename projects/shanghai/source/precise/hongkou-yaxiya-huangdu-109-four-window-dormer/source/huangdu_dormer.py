"""Four windows of the long roof dormer photographed above the shop at 109 Huangdu Road."""
from math import cos,pi
from shapely.geometry import Polygon
WALL='warm ochre roughcast'
LIGHT='muted ochre window frames'
DARK='brown transom joinery'
GLASS_LIGHT='pale reflected glass'
GLASS_DARK='smoked rose glass'
GLASS_GREEN='green-grey glass'
FLASH='dark cheek and sill flashing'
SOFFIT='shaded eaves timber'
TILES=('weathered russet tile','dull brown tile','red clay tile','dark orange clay')
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [
 (WALL,[.49,.281,.137],.93),(LIGHT,[.47,.364,.194],.68),(DARK,[.120,.066,.040],.76),
 (GLASS_LIGHT,[.54,.514,.352],.36),(GLASS_DARK,[.35,.242,.206],.34),
 (GLASS_GREEN,[.245,.288,.253],.34),(FLASH,[.066,.064,.056],.82),
 (SOFFIT,[.119,.081,.055],.89),(TILES[0],[.315,.102,.042],.93),
 (TILES[1],[.269,.090,.043],.95),(TILES[2],[.350,.113,.050],.91),(TILES[3],[.317,.124,.058],.90)]}
CENTRES=(-1.56,-.52,.52,1.56)
W=.82
def box(b,x,y,z,w,deep,h,material,group):
    b.box((x,y,z),(w,deep,h),material,label=group)
def roof_sheet(b,x0,x1,y0,y1,z0,z1,thickness,material,name):
    vs=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1),
        (x0,y0,z0-thickness),(x1,y0,z0-thickness),(x1,y1,z1-thickness),(x0,y1,z1-thickness)]
    b.add(vs,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],material,name)
def courses(b,x0,x1,y0,y1,z0,z1,nx,ny,lod,label):
    roof_sheet(b,x0,x1,y0,y1,z0,z1,.075,SOFFIT,label+' boarding')
    step=(x1-x0)/nx;dy=(y1-y0)/ny
    face_offsets=(0,.14,.42,.72,.89,1)if not lod else(0,.28,.73,1)
    for j in range(ny):
        ystart=y0+j*dy;ystop=min(y1,ystart+dy*1.065)
        for i in range(nx):
            xl=x0+i*step+.002;xs=[xl+step*.987*t for t in face_offsets]
            # Trough and raised roll read from alternating channels and the darker joints.
            wave=[.031,.041,.012,.007,.022,.030] if not lod else [.031,.034,.007,.030]
            verts=[];n=len(xs)
            for yy in (ystart,ystop):
                base=z0+(z1-z0)*(yy-y0)/(y1-y0)
                lap=.012 if yy==ystart else .002
                verts.extend((xx,yy,base+depth+lap)for xx,depth in zip(xs,wave))
            front=2*n
            for xx,depth in zip(xs,wave):
                verts.append((xx,ystart,z0+(z1-z0)*(ystart-y0)/(y1-y0)+depth-.004))
            faces=[]
            for k in range(n-1):
                faces.extend([(k,k+1,n+k+1,n+k),(k,front+k,front+k+1,k+1)])
            mat=TILES[(i*7+j*11+i*j)%4]
            b.add(verts,faces,mat,label+' clay tile courses')
def window(b,c,index):
    mat=LIGHT if index<2 else DARK;glass=[GLASS_LIGHT,GLASS_LIGHT,GLASS_DARK,GLASS_GREEN][index]
    lo,hi=.21,1.52;mid=(lo+hi)/2
    box(b,c,.087,mid,W,.033,hi-lo,glass,'Four recessed glazed openings')
    for sign in (-1,1):
        box(b,c+sign*(W/2-.021),.045,mid,.049,.092,hi-lo,mat,'Window outside stiles')
    for z in (lo+.023,hi-.023):
        box(b,c,.045,z,W,.092,.046,mat,'Window heads and bottom rails')
    if index<2:
        box(b,c,.045,mid,.048,.073,hi-lo,mat,'Two pale casement meeting stiles')
    else:
        top=1.15
        box(b,c,.033,top,W-.048,.091,.060,mat,'Separate top light transoms')
        box(b,c,.040,(lo+top)/2,.056,.088,top-lo,mat,'Paired brown opening sashes')
    box(b,c,-.026,lo-.019,W+.077,.154,.039,FLASH,'Weathered individual sills')
def model(b,lod=False):
    left,right=-2.135,2.13;bottom,top=.08,1.78
    # Deep reveals are continuous returns of the solid piers between four separate openings.
    edges=[left]+[v for c in CENTRES for v in (c-W/2,c+W/2)]+[right]
    for i in range(0,len(edges),2):
        a,z=edges[i:i+2];box(b,(a+z)/2,.110,(top+bottom)/2,z-a,.22,top-bottom,WALL,'Plastered front piers')
    box(b,(left+right)/2,.11,.147,right-left,.22,.134,WALL,'Front sill wall')
    box(b,(left+right)/2,.11,1.648,right-left,.22,.256,WALL,'Ochre over-window wall')
    for i,c in enumerate(CENTRES):window(b,c,i)
    box(b,left-.025,.155,.925,.058,.33,1.74,FLASH,'Tall dark left cheek flashing')
    box(b,right+.007,.156,.940,.043,.32,1.77,FLASH,'Right cheek return')
    box(b,-.003,-.060,.102,4.30,.133,.082,FLASH,'Continuous sill apron')
    box(b,-.012,-.037,1.803,4.44,.255,.076,SOFFIT,'Underside of the projecting eaves')
    box(b,-.012,-.191,1.820,4.44,.030,.078,FLASH,'Front eaves shadow fascia')
    courses(b,-2.236,2.22,-.194,.99,1.855,2.214,42,7,lod,'Dormer shallow roof')
    courses(b,-3.60,-2.17,-.27,.99,.145,2.205,13,8,lod,'Left steep roof flank')
    # The later street view shows a dark return closing the space between the roof pitches.
    cheek=Polygon([(-.194,.275),(-.194,1.855),(.977,2.209)])
    b.prism(cheek,-2.185,-2.126,lambda y,z,x:(x,y,z),FLASH,'Closed left dormer cheek')
    # Folded flashing follows the junction where the vertical dormer side meets that pitch.
    yz=[(-.244,.16),(.986,2.21),(.986,2.15),(-.244,.10)]
    b.prism(Polygon(yz),-2.194,-2.15,lambda y,z,x:(x,y,z),FLASH,'Slanting side flashing')
