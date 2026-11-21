"""Garden and street exteriors of the Woo residence, traced from the published plans."""
import math
from shapely.geometry import LineString, Polygon
from house_plans import LEVELS, METRES_PER_PIXEL, arc, ground_parts, plan_from_traces, terrace_paths, to_metres, upper_parts

TILE='moss green glazed tesserae'; GROUT='pale green glazed tile joint'; CREAM='pale stone coping'
GLASS='curved garden glazing'; GLASS2='grey blue street glazing'; FRAME='painted steel glazing bars'
RAIL='black enamel tubular rail'; DECK='red clay terrace pavers'; SOFFIT='warm plaster soffit'; ROOF='weathered flat roof'
PALETTE={key:{'color':rgb,'roughness':rough} for key,rgb,rough in (
    (TILE,[.390,.447,.347],.57),(GROUT,[.465,.510,.401],.77),(CREAM,[.681,.681,.574],.75),
    (GLASS,[.258,.355,.357],.21),(GLASS2,[.262,.332,.341],.30),(FRAME,[.112,.137,.130],.66),
    (RAIL,[.101,.128,.125],.52),(DECK,[.512,.253,.171],.78),(SOFFIT,[.756,.717,.619],.85),(ROOF,[.419,.430,.385],.88))}

def wall_band(b,path,lo,hi,depth,offset,mat,label):
    if hi<=lo or len(path)<2:return
    pts=[to_metres(p) for p in path]
    vs=[];fs=[]
    for j,(x,y) in enumerate(pts):
        px,py=pts[max(0,j-1)];qx,qy=pts[min(len(pts)-1,j+1)]
        length=math.hypot(qx-px,qy-py);nx,ny=(qy-py)/length,(px-qx)/length
        for d,z in ((offset,lo),(offset,hi),(offset-depth,hi),(offset-depth,lo)):
            vs.append((x+nx*d,y+ny*d,z))
    for j in range(len(pts)-1):
        a=4*j
        fs.extend([(a,a+4,a+5,a+1),(a+1,a+5,a+6,a+2),(a+2,a+6,a+7,a+3),(a+3,a+7,a+4,a)])
    last=4*(len(pts)-1);fs.extend([(0,1,2,3),(last+3,last+2,last+1,last)])
    b.add(vs,fs,mat,label)

def upright(b,cx,cy,z,h,size,material,label):
    b.box((cx,cy,z+h/2),(size,size,h),material,label=label)

def line_part(path,t0,t1):
    line=LineString(path);d0=t0*line.length;d1=t1*line.length
    acc=0;out=[line.interpolate(d0).coords[0]]
    for a,c in zip(path,path[1:]):
        acc+=math.dist(a,c)
        if d0+1e-6<acc<d1-1e-6:out.append(c)
    out.append(line.interpolate(d1).coords[0]);return out

def face(b,kind,pts,lo,hi,lod):
    label=kind.replace('_',' ')
    if kind=='solid':
        wall_band(b,pts,lo,hi,.16,0,TILE,'glazed tile returns');return
    curved=kind in ('sun_room','stair_glass','upper_round','round_ground')
    if kind=='stair_glass':sill,lintel=(.13,.10)
    elif kind=='sun_room':sill,lintel=(.77,.24) if lo>11 else ((1.0,.82) if lo>7 else (.20,.18))
    elif kind in ('garden_ground','round_ground','drive_glass','hall_glass','living_doors'):sill,lintel=(.18,.34)
    elif kind in ('north_ribbon','north_short','west_garden','west_end','east_side'):sill,lintel=(1.03,1.12)
    else:sill,lintel=(.78,.40)
    start=lo+sill;end=hi-lintel
    wall_band(b,pts,lo,start,.15,0,TILE,'green tile aprons')
    wall_band(b,pts,end,hi,.15,0,TILE,'green tile lintels')
    gap=0 if curved else (.07 if kind in ('living_doors','garden_ground','west_garden') else .125)
    if kind=='west_garden' and 4<lo<7:gap=.29
    if gap:
        wall_band(b,line_part(pts,0,gap),start,end,.15,0,TILE,'exterior masonry beside opening')
        wall_band(b,line_part(pts,1-gap,1),start,end,.15,0,TILE,'exterior masonry beside opening')
    opening=line_part(pts,gap,1-gap);span=LineString(opening).length*METRES_PER_PIXEL
    wall_band(b,opening,start,end,.042,-.085,GLASS2 if kind.startswith('north')or kind=='stair_glass' else GLASS,label+' glass')
    wall_band(b,opening,start-.045,start+.025,.185,.064,CREAM,'glazing projecting sills')
    wall_band(b,opening,end-.045,end,.13,.018,FRAME,'painted steel top rail')
    if kind in ('stair_glass','garden_ground','living_doors','drive_glass','hall_glass'):
        wall_band(b,opening,end-.52,end-.47,.10,-.018,FRAME,'steel horizontal transom')
    count=max(1,round(span/(.96 if curved else 1.04)))
    line=LineString(opening)
    for i in range(count+1):
        x,y=to_metres(line.interpolate(i/count,normalized=True).coords[0]);upright(b,x,y,start,end-start,.063 if not lod else .07,FRAME,'steel window mullions')
    if kind=='garden_ground':
        for frac in (.27,.53,.79):
            x,y=to_metres(line.interpolate(frac,normalized=True).coords[0])
            b.box((x,y,(start+end)/2),(.155,.23,end-start),TILE,label='garden room green tile structural piers')
    if not lod:
        # Represent the horizontal courses on exposed aprons, keeping the narrow
        # joints legible at building scale without baking photographs into the model.
        for bottom,top in ((lo,start),(end,hi)):
            for j in range(1,int((top-bottom)/.165)+1):
                z=bottom+.165*j
                if z+.009<top:wall_band(b,pts,z,z+.009,.012,.006,GROUT,'fine green tile bedding joints')

def railing(b,path,z,lod,label):
    route=LineString([to_metres(p)for p in path]);length=route.length
    if length<.12:return
    for h in (.39,.66,.92):
        b.tube([(x,y,z+h)for x,y in route.coords],.036 if h==.92 else .025,RAIL,6 if lod else 10,label)
    n=max(1,math.ceil(length/1.23))
    for j in range(n+1):
        x,y=route.interpolate(j/n,normalized=True).coords[0];upright(b,x,y,z,.93,.054,RAIL,'balcony railing uprights')

def deck(b,outer,inside,z,lod,index):
    poly=Polygon([to_metres(p)for p in outer+inside])
    if not poly.is_valid:poly=poly.buffer(0)
    b.plan_prism(poly,z-.205,z-.055,SOFFIT,'overhanging terrace soffits')
    b.plan_prism(poly,z-.055,z,DECK,'red paved garden terraces')
    if index:
        wall_band(b,outer,z-.20,z+.65,.16,.005,TILE,'curved green balcony fascias')
        railing(b,outer,z+.27,lod,'balcony rails above tiled fascia')
    else:
        for edge in (outer[:3],outer[3:]):
            wall_band(b,edge,z-.63,z+.07,.17,.005,TILE,'lowest garden terrace edge')
            railing(b,edge,z+.06,lod,'main terrace metal rails')

def garden_stair(b,lod):
    # The double-line spiral in plates 20 and 21 is an outdoor flight. Its top
    # landing is to the west; the lower end meets the front of the lawn.
    n=26;center=(277.,366.);inner=29.;outer=82.;top=LEVELS[1];heights=[top*(n-i)/n for i in range(n+1)]
    for i in range(n):
        aa=180-112*i/n;ab=180-112*(i+1)/n
        shape=Polygon([to_metres(p)for p in arc(center,outer,aa,ab,2)+arc(center,inner,ab,aa,2)])
        z=heights[i];b.plan_prism(shape,max(0,z-.26),z-.03,SOFFIT,'curving outdoor stair soffit')
        b.plan_prism(shape,z-.03,z,DECK,'terracotta garden stair treads')
        wall_band(b,[arc(center,inner,ab,ab,1)[0],arc(center,outer,ab,ab,1)[0]],
                  max(0,heights[i+1]-.03),z,.034,.004,DECK,'terracotta garden stair risers')
    for r in (inner,outer):
        trace=arc(center,r,180,68,n)
        for dz in (.41,.69,.95):
            b.tube([(*to_metres(p),heights[i]+dz)for i,p in enumerate(trace)],.033,RAIL,6 if lod else 10,'sweeping handrail on garden stair')
        for j in range(0,n+1,4):
            x,y=to_metres(trace[j]);upright(b,x,y,heights[j],.94,.055,RAIL,'stair railing standards')

def add_residence(b,lod):
    for floor in range(4):
        stories=ground_parts(lod) if floor==0 else [upper_parts(floor,lod)]
        lo,hi=LEVELS[floor:floor+2]
        for story in stories:
            base=plan_from_traces(story)
            b.plan_prism(base,lo,lo+.075,DECK if floor==0 else SOFFIT,'floors above drive and rooms')
            b.plan_prism(base,hi-.13,hi,ROOF if floor==3 else SOFFIT,'flat floor and roof soffits')
            for kind,pts in story:face(b,kind,pts,lo+.075,hi-.13,lod)
    # Main exterior balconies on floors two through four have different plans.
    for i,(outer,back) in enumerate(zip(terrace_paths(lod),[
          [(559,287),(402,282),(250,282)],
          [(471,286),(251,286),(251,196)],
          [(479,301),(477,197),(250,197)]])):
        deck(b,outer,back,LEVELS[i+1],lod,i)
    eave=plan_from_traces(upper_parts(3,lod)).buffer(.28,join_style='round',quad_segs=4 if lod else 9)
    b.plan_prism(eave,14.96,15.11,CREAM,'continuous pale roof drip')
    b.plan_prism(eave.buffer(-.20),15.111,15.128,ROOF,'exposed flat roof behind pale drip')
    # The 2016 photograph clearly shows a low sweeping canopy shading the
    # highest central balcony. Its west tip is squared; the east end turns
    # back into the round living room. It never covers the full balcony.
    lip=[(267,234),(267,252),(333,252)]
    lip+=arc((413,207),92,150,91,10 if lod else 24)[1:]
    lip += [(479,304),(479,224),(387,198),(267,198)]
    canopy=Polygon([to_metres(px)for px in lip])
    if not canopy.is_valid:canopy=canopy.buffer(0)
    b.plan_prism(canopy,14.83,15.055,SOFFIT,'soffit above the highest garden balcony')
    b.plan_prism(canopy,15.055,15.16,CREAM,'pale rim of central curved canopy')
    b.plan_prism(canopy.buffer(-.17),15.16,15.175,ROOF,'top of central garden canopy')
    # Circular eave over the southeast window bank projects past the main parapet.
    z=15.13;rim=Polygon([to_metres(p)for p in arc((561,338),56,-90,270,26 if lod else 64)])
    b.plan_prism(rim,z-.08,z+.10,CREAM,'sun room circular canopy')
    stair=Polygon([to_metres(p)for p in arc((443,118),36,0,-180,12 if lod else 28)]+[to_metres((407,159)),to_metres((479,159))])
    wall_band(b,[(407,118),(407,159),(479,159),(479,118)],15.105,16.50,.16,0,TILE,'rear stair rooftop returns')
    face(b,'stair_glass',arc((443,118),36,0,-180,20 if lod else 40),15.105,16.50,lod)
    b.plan_prism(stair.buffer(.12),16.50,16.63,CREAM,'stair lantern coping')
    pipe=Polygon([to_metres(p)for p in arc((407,109),5,0,360,12 if lod else 22)])
    b.plan_prism(pipe,15.10,17.34,TILE,'slender rounded street roof vent')
    garden_stair(b,lod)
