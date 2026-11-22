"""Entrance bay above the clubhouse door at 301 Middle Fuxing Road."""
from pathlib import Path
from shapely.geometry import box, LineString
from profile_tools import cb, slab, bricks_uv, BRICK as STONE

GLASS='Blue-grey steel window glass'
METAL='Dark grey steel framing'
RIB='Dressed stone face between incisions'
SHADOW='Shaded stone in incisions'
CAP='Overhanging granite cap'
PALETTE={}
for key,col in [(STONE,(255,255,255)),(GLASS,(75,99,121)),(METAL,(65,69,69)),(RIB,(173,162,150)),(SHADOW,(124,114,105)),(CAP,(166,155,146))]:
    PALETTE[key]=dict(color=[(v/255)**2.2 for v in col],roughness=.37 if key==GLASS else .87)
PALETTE[STONE]['texture']=str(Path(__file__).with_name('finish.png'))

HALF_PANELS=((-1.01,-.085),(.085,1.01))
LEVELS=[(0.,.48,1.55), (1.55,1.95,2.87), (2.87,3.21,3.99)]

def chevrons(b,left,right,base,top,rising,lod):
    section=box(left,base,right,top)
    cb(b,left,right,-.062,.09,base,top,SHADOW,'Recesses cut into the spandrel')
    # One tapered stone strip between each pair of engraved parallel lines.
    gap=.085
    k=-12
    while True:
        x=left+k*gap
        if x>right+1.2:break
        slope=1 if rising else -1
        ray=LineString([(x,base-.12),(x+slope*(top-base+.24),top+.12)])
        band=ray.buffer(.026 if lod else .023,cap_style=2).intersection(section)
        if band.area>.00006:slab(b,band,-.084,-.062,RIB,'Diagonal face between engraved lines')
        k+=1

def model(b,lod=False):
    for side in (-1,1):
        def edge(u,v):return sorted((side*u,side*v))
        l,r=edge(1.05,1.26)
        cb(b,l,r,-.117,.185,0,4.17,STONE,'Continuous vertical jamb beside windows')
        # The wall steps in towards the divided top cap in the frontal photograph.
        for lo,hi,outer in [(0.,1.54,1.67),(1.54,2.86,1.54),(2.86,3.83,1.43),(3.83,4.14,1.33)]:
            l,r=edge(1.26,outer)
            cb(b,l,r,-.038,.24,lo+.007,hi,STONE,'Stepped stone shoulder')
    cb(b,-.086,.086,-.112,.22,0,4.15,STONE,'Single central masonry strip between both columns')
    for level,(base,glass0,top) in enumerate(LEVELS):
        for ix,(left,right) in enumerate(HALF_PANELS):
            chevrons(b,left,right,base+.012,glass0-.025,(ix==0)==(level%2==0),lod)
            cb(b,left-.017,right+.017,-.123,.12,glass0-.025,glass0+.014,METAL,'Window sill above carved stone')
            cb(b,left,right,.032,.06,glass0+.014,top-.022,GLASS,'Recessed glazing')
            for x in (left+.014,(left+right)/2,right-.014):
                cb(b,x-.014,x+.014,-.035,.035,glass0+.013,top-.014,METAL,'Steel stile')
            if not lod:
                for x in (left+.038,right-.038):
                    cb(b,x-.006,x+.006,-.022,-.010,glass0+.044,top-.045,METAL,'Narrow bead around the glazing')
                for z in (glass0+.047,top-.047):
                    cb(b,left+.037,right-.037,-.022,-.010,z-.005,z+.005,METAL,'Top and bottom glazing bead')
            for z in (glass0+.028,top-.23,top-.028):
                cb(b,left,right,-.046,.035,z-.013,z+.013,METAL,'Head, transom or sill bar')
    for x in (-.55,.55):
        cb(b,x-.54,x+.54,-.182,.245,4.00,4.11,CAP,'Lower slab at roof line')
        cb(b,x-.47,x+.47,-.134,.207,4.11,4.25,CAP,'Raised block separated by the central joint')
    bricks_uv(b)
