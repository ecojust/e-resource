"""Visible street elevations of Hengli Bank. Dimensions in metres."""
from pathlib import Path
from math import cos,pi,sin
from shapely.geometry import box,Polygon,LineString
from shapely.ops import unary_union
from photo_architecture import Facade
from brick_mapping import BRICK, STREET_EDGES, brick_uv

STONE='Off-white cast cement'
TOP='Weathered cream paint'
RELIEF='Pale spandrel relief'
RECESS='Dark window reveal'
GLASS='Blue-grey street glazing'
FRAME='Charcoal window joinery'
METAL='Age-darkened green bronze'
GRANITE='Cool plinth stone'
GOLD='Patinated brass'
RED='Faded red enamel'
CASING='Dull grey condenser cases'
ROOF='Grey roof flashing'
PALETTE={
    BRICK:{'color':[1.,1.,1.],'roughness':.93,'texture':str(Path(__file__).with_name('brown-brick-bond.png'))},
    STONE:{'color':[.715,.706,.650],'roughness':.88},
    TOP:{'color':[.72,.702,.629],'roughness':.85},
    RELIEF:{'color':[.78,.766,.70],'roughness':.82},
    RECESS:{'color':[.15,.155,.142],'roughness':.82},
    GLASS:{'color':[.195,.242,.25],'metallic':.21,'roughness':.31},
    FRAME:{'color':[.20,.209,.195],'metallic':.21,'roughness':.52},
    METAL:{'color':[.157,.161,.129],'metallic':.40,'roughness':.55},
    GRANITE:{'color':[.60,.595,.553],'roughness':.85},
    GOLD:{'color':[.58,.442,.247],'metallic':.48,'roughness':.54},
    RED:{'color':[.58,.173,.158],'roughness':.58},
    CASING:{'color':[.51,.51,.482],'metallic':.23,'roughness':.66},
    ROOF:{'color':[.32,.327,.302],'roughness':.78},
}
SASHES=((6.13,7.73),(9.11,10.86),(12.40,13.80),(15.82,17.13))
PARAPET=19.35


def recess(face,opening,wide=False,lod=False):
    x0,z0,x1,z1=opening.bounds
    width=x1-x0
    rails=[box(x0,z1-(z1-z0)*.27,x1,z1-(z1-z0)*.27+.058)]
    columns=round(width/.65) if wide else (2 if width>1. or not lod else 1)
    for i in range(1,columns):
        x=x0+width*i/columns
        rails.append(box(x-.023,z0,x+.023,z1))
    frame=opening.difference(opening.buffer(-.058,join_style=2).difference(unary_union(rails)))
    face.prism(opening.buffer(.015,join_style=2),-.345,-.325,GLASS,'Recessed panes')
    face.prism(frame,-.298,-.216,FRAME,'Transoms and mullions')
    if wide:
        for i in range(1,round(width/.25)):
            x=x0+width*i/round(width/.25)
            face.box(x,(z0+z1)*.5,.027,z1-z0,.055,-.14,METAL,'Bank window security bars')
        for z in [z0+.47,z1-.60]:
            face.box((x0+x1)/2,z,width,.044,.075,-.129,METAL,'Bank window guard rails')


def condenser(face,x,z,multiple,lod):
    w=.69;h=.51*(2 if multiple else 1)
    face.box(x,z,w,h,.40,.26,CASING,'Air-conditioning equipment')
    for cz in ([z-.25,z+.25]if multiple else [z]):
        pts=[(x-.055+.205*cos(2*pi*i/16),cz+.205*sin(2*pi*i/16))for i in range(16)]
        face.prism(Polygon(pts),.461,.471,FRAME,'Fan recess')
        if not lod:
            for radius in (.09,.136,.18):
                path=[face.point(x-.055+radius*cos(2*pi*i/20),cz+radius*sin(2*pi*i/20),.482)for i in range(21)]
                face.builder.tube(path,.006,CASING,4,face.label+'/Fan guards')
            for a in [0,pi/3,2*pi/3]:
                face.builder.tube([face.point(x-.055+t*cos(a),cz+t*sin(a),.487)for t in (-.182,.182)],.009,CASING,4,face.label+'/Fan guards')
    if not lod:
        for dx in (-.25,.25):
            face.box(x+dx,z-h/2-.044,.05,.07,.48,.22,FRAME,'Condenser brackets')


def fluted_bays(face,widths,first,ends,levels,lod,upper=None):
    """Four observed sash rows with notched pale spandrels and continuous pilasters."""
    stations=[];u=first
    for width in widths:
        stations.append((u+width/2,width))
        u+=width
    openings=[]
    for i,(x,pitch) in enumerate(stations):
        for level,(bottom,top) in enumerate(levels):
            opening=box(x-pitch*.326,bottom,x+pitch*.326,top)
            openings.append(opening)
            recess(face,opening,lod=lod)
            cap=levels[level+1][0] if level+1<len(levels) else ends[i]
            if cap-top>.31:
                span=pitch*.68
                face.box(x,(top+cap)/2,span,cap-top-.04,.115,.052,RELIEF,'Fluted spandrel panels')
                if not lod or level==len(levels)-1:
                    for j in range(3 if lod else 5):
                        z=top+.13+(j+.25)*(cap-top-.25)/(3 if lod else 5)
                        for side in (-1,1):
                            face.box(x+side*(span/2-.065),z,.105,.062,.069,.123,STONE,'Spandrel edge blocks')
        for side in (-1,1):
            if side==-1 and i:continue
            edge=x+side*pitch/2
            h=ends[i]-5.47
            face.box(edge,5.47+h/2,.16,h,.235,.087,RELIEF,'Continuous cement fins')
    outline=unary_union([box(x-pitch/2,5.43,x+pitch/2+.001,ends[i])for i,(x,pitch)in enumerate(stations)])
    face.prism(outline.difference(unary_union(openings)),-.34,0,STONE,'Pale street window wall')
    return stations


def dark_bays(face,ranges,bottom,top,lod):
    openings=[]
    for x,w in ranges:
        for low,hi in SASHES:
            opening=box(x-w/2,low,x+w/2,hi)
            openings.append(opening)
            recess(face,opening,lod=lod)
    return openings


def stone_courses(face,x,z,w,h,lod):
    face.box(x,z,w,h,.18,.055,GRANITE,'Entrance ashlar')
    for i in range(1,round(h/.81)):
        face.box(x,z-h/2+i*h/round(h/.81),w,.021,.018,.15,RECESS,'Ashlar bedding joints')
    if not lod:
        for i in range(1,round(w/.75)):
            face.box(x-w/2+w*i/round(w/.75),z,.017,h,.018,.148,RECESS,'Ashlar perpends')


def main_gate(face,lod):
    width=face.length;W=width/2
    hole=box(-.968,.13,.968,3.47)
    corner_upper=[box(-.53,bottom,.53,top)for bottom,top in SASHES]
    face.prism(box(-W,0,W,PARAPET).difference(unary_union([hole,*corner_upper])),-.44,-.015,BRICK,'Brown-brick chamfer')
    for z,(low,hi) in enumerate(SASHES):
        recess(face,corner_upper[z],lod=lod)
        foot=4.86 if z==0 else SASHES[z-1][1]
        if low-foot>.12:
            face.box(0,(foot+low)/2,1.10,low-foot,.18,.06,STONE,'Corner window aprons')
            for side in (-1,1):
                for i in range(3):
                    face.box(side*(.53-i*.048),low-.16-i*.096,.14,.12,.085,.167,RELIEF,'Stepped window apron')
    face.box(0,18.28,.83,2.25,.21,.06,RELIEF,'Raised corner finial')
    for j in range(4):
        face.box(0,19.35-j*.13,.69+j*.08,.072,.24,.12,STONE,'Finial fluting')
    for side in (-1,1):
        stone_courses(face,side*1.27,1.90,.60,3.80,lod)
    stone_courses(face,0,4.15,3.16,.73,lod)
    face.box(0,4.77,2.84,.58,.28,.15,GRANITE,'Pale portal frieze')
    face.box(0,5.08,3.00,.13,.39,.18,RELIEF,'Projecting portal cap')
    for side in (-1,1):
        for i in range(3):
            face.box(side*(1.36-i*.045),4.45+i*.19,.28,.09,.31,.19,STONE,'Frieze terminal blocks')
    face.prism(hole.buffer(.025,join_style=2),-.52,-.48,RECESS,'Entrance recess')
    for side in (-1,1):
        face.box(side*.466,1.61,.923,2.91,.13,-.291,METAL,'Double bronze door')
        if not lod:
            for cz in (.72,1.49,2.27):
                for i in (-1,1):
                    path=[(side*.466+i*.31,cz+.18),(side*.466+i*.15,cz+.27),(side*.466,cz+.08),(side*.466+i*.055,cz-.087)]
                    face.builder.tube([face.point(x,z,-.212)for x,z in path],.014,FRAME,5,'Chamfer/Door scrollwork')
    face.box(0,3.27,1.89,.32,.086,-.185,METAL,'Kindergarten name board')
    face.box(0,.071,2.09,.14,.34,.015,GRANITE,'Chamfer threshold')
    for side in (-1,1):face.box(side*1.07,1.67,.065,3.20,.17,.13,STONE,'Portal inside margin')


def lower_street(face,windows,doors,lod,north_gap=0.):
    half=face.length/2
    cuts=[box(x-w/2,1.29,x+w/2,4.53)for x,w in windows]
    basements=[]
    for x,w in windows:
        for i in range(max(1,round(w/1.39))):
            count=max(1,round(w/1.39));cx=x+(i+.5-count/2)*w/count
            basements.append(box(cx-.37,.24,cx+.37,.81))
    door_cuts=[box(x-w/2,.10,x+w/2,4.73)for x,w,kind in doors]
    face.prism(box(-half,0,half-north_gap,5.56).difference(unary_union([*cuts,*basements,*door_cuts])),-.43,-.016,BRICK,'Brick ground floor')
    face.prism(box(-half,.02,half-north_gap,1.14).difference(unary_union([*basements,*door_cuts])),-.02,.058,GRANITE,'Basement ashlar')
    for o in cuts:
        recess(face,o,wide=True,lod=lod)
        x0,z0,x1,z1=o.bounds
        for x in (x0-.092,x1+.092):face.box(x,(z0+z1)/2,.165,z1-z0+.14,.18,.089,STONE,'Stone shop jambs')
    for o in basements:
        face.prism(o.buffer(.015,join_style=2),-.23,-.20,RECESS,'Basement air grilles')
        x0,z0,x1,z1=o.bounds
        for j in range(3 if lod else 5):face.box(x0+.081+j*(x1-x0-.16)/(2 if lod else 4),(z0+z1)/2,.026,z1-z0,.054,-.141,FRAME,'Grille bars')
    for (x,w,kind),o in zip(doors,door_cuts):
        face.prism(o.buffer(.015,join_style=2),-.51,-.48,RECESS,'Street entrance backing')
        if kind=='brass':
            face.box(x,1.56,w-.15,2.91,.15,-.31,GOLD,'Brass double entrance')
            face.box(x,1.55,.037,2.90,.044,-.219,METAL,'Brass meeting stile')
            face.box(x,3.80,w-.08,1.56,.16,-.29,GOLD,'Upper patterned brass screen')
            if not lod:
                for j in range(4):
                    for k in range(5):
                        cx=x+(k-2)*w/5.6;cz=3.18+j*.34
                        face.prism(box(cx-.095,cz-.094,cx+.095,cz+.094),-.21,-.197,METAL,'Geometric transom cells')
                        face.box(cx,cz,.068,.068,.028,-.175,GOLD,'Brass transom bosses')
        else:
            face.box(x,2.29,w-.10,4.32,.13,-.22,FRAME,'Northern door shutter')
            for j in range(9 if lod else 25):
                face.box(x,.25+(j+.4)*3.99/(9 if lod else 25),w-.16,.023,.040,-.139,CASING,'Shutter blades')
            face.box(x,4.38,w+.10,.38,.20,.04,GRANITE,'Door lintel')


def upper_row(face,centres,low,high,left,right,top,lod,material=STONE,label='Upper street wall'):
    holes=[]
    for x,w in centres:
        shape=box(x-w/2,low,x+w/2,high);holes.append(shape);recess(face,shape,lod=lod)
    face.prism(box(left,low-.54,right,top).difference(unary_union(holes)),-.36,-.017,material,label)
    for x,w in centres:
        face.box(x,low-.03,w+.10,.085,.18,.035,RELIEF,'Upper sill')


def south(face,lod):
    half=face.length/2
    bands=fluted_bays(face,[1.46]*6,-half+4.47,[PARAPET]*6,SASHES,lod)
    high=dark_bays(face,[(-half+1.07,.95),(-half+2.75,1.04),(half-1.47,.36)],5.42,PARAPET,lod)
    flank=unary_union([box(-half,5.43,-half+4.47,PARAPET-.68),box(-half+13.23,5.43,half,PARAPET)])
    face.prism(flank.difference(unary_union(high)),-.39,-.016,BRICK,'Brick end bays')
    lower_street(face,[(-half+1.34,1.85),(-half+5.52,2.49),(-half+9.25,3.59),(-half+12.57,2.36)],[],lod)
    for x,z,double in [(-half+2.22,15.92,False),(-half+3.95,4.20,True),(bands[2][0]+.38,15.5,False),(bands[4][0]+.25,15.2,False)]:condenser(face,x,z,double,lod)
    face.builder.tube([face.point(half-2.07,z,.22)for z in (18.61,5.83)]+[face.point(half-.66,4.02,.21),face.point(half-.66,.15,.21)],.071,STONE,6,'Tianjin/Drainpipe')
    face.box(half-1.12,14.69,.647,6.31,.135,.125,RECESS,'Hotel vertical sign backing')


def east(face,lod):
    half=face.length/2; first=-half+.38; pitch=1.37
    top=[PARAPET]*7+[18.31]*11
    bays=fluted_bays(face,[pitch]*18,first,top,SASHES,lod)
    end=first+18*pitch
    # The northern half-metre meets the neighboring building at a shared source wall.
    # Keep the generic end joint between the two properties.
    flank=unary_union([box(-half,5.43,first,PARAPET),box(end,5.43,half-.52,25.60)])
    dark=[(end+1.02,.83),(end+2.53,.81)]
    holes=dark_bays(face,dark,5.43,25.6,lod)
    for x,width in dark:
        for bottom in (19.08,22.26):
            gap=box(x-width/2,bottom,x+width/2,bottom+1.65)
            holes.append(gap);recess(face,gap,lod=lod)
    face.prism(flank.difference(unary_union(holes)),-.39,-.016,BRICK,'Brick north return')
    for i,(x,pitch)in enumerate(bays):
        if i<7:continue
        rows=[(18.84,20.16)]
        if i>=11:rows.append((22.07,23.61))
        for j,(lo,hi)in enumerate(rows):
            top_eave=21.07 if i<11 else (21.54 if j==0 else 25.60)
            upper_row(face,[(x,.82)],lo,hi,x-pitch/2,x+pitch/2,top_eave,lod)
    windows=[(-half+3.04,3.91),(-half+7.01,2.98),(-half+10.41,2.45),(-half+16.43,1.02),(-half+19.12,3.90),(-half+23.16,3.59)]
    lower_street(face,windows,[(-half+13.55,1.91,'brass'),(half-1.32,1.36,'shutter')],lod,north_gap=.52)
    units=[(.55,4.71,True),(2.60,5.19,False),(4.18,5.06,False),(6.27,5.12,False),
           (8.51,5.18,True),(10.03,5.25,False),(17.01,5.48,True),(25.38,4.94,True),
           (2.75,9.43,True),(6.12,10.57,False),(7.85,12.65,False),(10.13,8.89,True),
           (2.19,12.48,False),(3.78,12.76,False),(4.91,12.44,False),(4.28,16.43,False),
           (8.46,16.59,False),(15.47,15.83,False),(16.12,12.74,True),(17.33,16.03,False),
           (21.14,15.03,True),(25.95,8.02,True),(26.23,12.64,True),(26.09,16.51,False)]
    for off,z,double in units:condenser(face,-half+off,z,double,lod)


def setback(builder,lod):
    # Only the two street-facing planes are documented, at the triangulated southeast wall corner.
    a=(-11.65,6.54);b=(-2.16,6.54);c=(-2.16,15.95)
    south=Facade(builder,a,b,'Upper south');east=Facade(builder,b,c,'Upper east')
    for f in [south,east]:
        half=f.length/2
        holes=[]
        for z in [21.82,25.65]:
            for x in [-f.length*.31,0.,f.length*.31]:
                wi=1.35 if f is south else 1.62
                h=box(x-wi/2,z,x+wi/2,z+1.61);holes.append(h);recess(f,h,lod=lod)
        f.prism(box(-half,19.13,half,29.15).difference(unary_union(holes)),-.40,0,TOP,'Two visible upper floors')
        f.box(0,29.19,f.length,.105,.43,-.13,STONE,'Plain setback parapet')
    builder.plan_prism(Polygon([a,b,c,(-11.65,15.95)]),29.02,29.13,ROOF,'Observable setback roof plane')
    # The visible terrace closes the area between the pictured corner roof edge and
    # the two set-back walls. Its unphotographed inner edge stops inside the source.
    terrace=Polygon([(-15.8184,0),(0,0),(2.8775,3.2731),(2.19,13.20),
                     (-2.30,13.20),(-2.30,6.69),(-12.04,6.69),(-12.04,3.72),(-15.96,3.72)])
    builder.plan_prism(terrace,18.78,19.14,ROOF,'Continuous terrace below the upper corner')
    east=Facade(builder,*STREET_EDGES['Henan'],'East terrace')
    bounds=[-east.length/2,-east.length/2+9.97,-east.length/2+15.45,east.length/2-.52]
    h=[19.10,20.77,25.43]
    for i,(left,right)in enumerate(zip(bounds,bounds[1:])):
        back=4.58 if i<2 else 2.38
        plan=[east.point(left,0,0)[:2],east.point(right,0,0)[:2],east.point(right,0,-back)[:2],east.point(left,0,-back)[:2]]
        builder.plan_prism(Polygon(plan),h[i]-.19,h[i],ROOF,'Henan street roof edges')
        if i:
            ret=Facade(builder,plan[-1],plan[0],'Height change')
            ret.prism(box(-ret.length/2,h[i-1]-.12,ret.length/2,h[i]+.06),-.23,0,TOP,'Stepped terrace end wall')



def add_building(builder,lod=False):
    faces={side:Facade(builder,*ends,side)for side,ends in STREET_EDGES.items()}
    south(faces['Tianjin'],lod)
    main_gate(faces['Chamfer'],lod)
    east(faces['Henan'],lod)
    setback(builder,lod)
    from signs import letter_signs
    letter_signs(faces,lod)
    for part in builder.parts:
        if part['material']==BRICK:
            part['texcoords']=[(u,1-v)for u,v in (brick_uv(part['label'],v)for v in part['vertices'])]
