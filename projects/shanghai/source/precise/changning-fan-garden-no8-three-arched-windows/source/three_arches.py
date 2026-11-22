"""Central three-window roof bay at Li Ming's house, No. 8 Fan Garden, May 2002."""
from math import pi,cos,sin,atan2,sqrt
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

def finish(rgb,rough=.86,metal=0):
    def linear(x):
        v=x/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return dict(color=[linear(v) for v in rgb],roughness=rough,metallic=metal)
PALETTE={'light render':finish((215,206,185)),'stone trim':finish((198,188,169)),
 'aged coping':finish((165,158,146)),'timber sash':finish((104,69,53),.76),
 'glazing':finish((103,120,125),.28,.22),'clay tile':finish((145,99,83)),
 'weathered clay':finish((131,87,74)),'tile valley':finish((105,77,66)),
 'dormer frame':finish((86,70,59))}
CENTERS=(-1.50,0,1.50);R=.570;SILL=.835;SPRING=1.57
ROOF_FOOT=2.485;BACK=2.03;PITCH=atan2(2.06,BACK);RUN=BACK/cos(PITCH)
def arch(c,r,z0,z1,n):
    crown=[(c+r*cos(pi*i/n),z1+r*sin(pi*i/n)) for i in range(n+1)]
    return Polygon([(c-r,z0),(c+r,z0)]+crown)
def eyebrow_top(x):
    t=min(1,abs(x)/.668)
    # Two flat shoulders and the lifted centre of the roof window's plaster hood.
    return 3.045+.343*((1+cos(pi*t))/2)**1.34
def add_building(b,lod=False):
    n=12 if lod else 36
    def panel(name,g,y0,y1,mat):
        b.prism(g,-y1,-y0,lambda x,z,d:(x,-d,z),mat,name)
    openings=[arch(c,R,SILL,SPRING,n) for c in CENTERS]
    panel('three-window front with real cut openings',box(-2.32,.035,2.32,2.47).difference(unary_union(openings)),0,.247,'light render')
    for i,c in enumerate(CENTERS):
        outer=arch(c,R+.042,SILL-.045,SPRING,n)
        panel('arched moulding '+str(i+1),outer.difference(openings[i]),-.033,.09,'stone trim')
        inner=arch(c,R-.039,SILL+.040,SPRING,n)
        panel('arched perimeter sash '+str(i+1),openings[i].difference(inner),.086,.158,'timber sash')
        panel('arched glazing '+str(i+1),inner,.144,.169,'glazing')
        for j,dx in enumerate((-.206,.205)):
            clip=inner.intersection(box(c+dx-.018,SILL,c+dx+.018,SPRING+R))
            panel('upper vertical sash '+str(i+1)+' '+str(j+1),clip,.074,.155,'timber sash')
        panel('horizontal sash '+str(i+1),inner.intersection(box(c-R,1.535,c+R,1.564)),.080,.156,'timber sash')
        panel('under-window panel lip '+str(i+1),box(c-.55,.255,c+.55,.758),-.038,.015,'stone trim')
        panel('under-window inset '+str(i+1),box(c-.486,.309,c+.486,.693),-.045,-.017,'light render')
    panel('front gallery sill band',box(-2.337,.015,2.337,.137),-.088,.23,'aged coping')
    panel('frieze and eaves strip',box(-2.38,2.37,2.38,2.501),-.082,.26,'stone trim')
    def roof_map(x,s,d):return (x,.024+s*cos(PITCH)-d*sin(PITCH),ROOF_FOOT+s*sin(PITCH)+d*cos(PITCH))
    outer=Polygon([(-2.425,-.06),(2.425,-.06),(0,RUN)])
    opening=box(-.210,.53,.210,.79);roof=outer.difference(opening)
    b.prism(roof,-.105,0,roof_map,'tile valley','pitched roof underlay')
    rows=19
    for j in range(rows):
        y=-.06+j*(RUN+.06)/rows;h=(RUN+.06)/rows
        for k in range(24):
            x=-2.50+k*.228+(j%2)*.114
            tile=box(x+.003,y+.002,x+.223,y+h-.002).intersection(roof)
            if tile.is_empty or tile.area<.00005:continue
            mat='weathered clay' if (k+2*j)%6==0 else 'clay tile'
            if lod:
                # Group the distant tile bed by course, retaining banded clay colours.
                if k:continue
            else:
                b.prism(tile,-.002,.018,roof_map,mat,'roof tile course '+str(j+1))
                lip=tile.intersection(box(x,y+.002,x+.228,y+.015))
                if lip.area>.00005:
                    b.prism(lip,.017,.029,roof_map,mat,'exposed tile lips '+str(j+1))
        if lod:
            strip=box(-2.5,y+.002,2.5,y+h-.002).intersection(roof)
            if strip.area>.00005:b.prism(strip,-.002,.014,roof_map,'weathered clay' if j%4==0 else 'clay tile','roof course '+str(j+1))
    m=12 if lod else 36
    path=[(-.668+i*1.336/m,eyebrow_top(-.668+i*1.336/m)) for i in range(m+1)]
    dormer=Polygon([(-.668,2.768),(.668,2.768)]+list(reversed(path)))
    small=box(-.257,2.951,.257,3.14)
    panel('curved front of the roof window',dormer.difference(small),.295,.609,'light render')
    panel('dark recessed roof window',small,.356,.375,'glazing')
    panel('small sash casing',small.difference(box(-.233,2.966,.233,3.119)),.320,.370,'dormer frame')
    for j,x in enumerate((-.144,0,.143)):
        panel('small window muntin '+str(j),box(x-.009,2.951,x+.009,3.14),.315,.366,'dormer frame')
    rim=Polygon(path+[(x,z+.045)for x,z in reversed(path)])
    panel('undulating stone cap',rim,.246,.747,'aged coping')
    panel('small opening sill',box(-.313,2.898,.313,2.946),.251,.610,'stone trim')
