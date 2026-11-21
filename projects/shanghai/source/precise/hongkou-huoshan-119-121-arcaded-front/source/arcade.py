"""Paired brick arches and the rectilinear, inset windows of the former Huoshan Road residences."""
import math
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union
from photo_architecture import opening
RED='Dull red facing brick';SECOND='Burnt red brick';JOINT='Arch joint mortar'
BUFF='Cream painted apron';GREY='Grey stone trim';WOOD='Dark reddish joinery'
GLASS='Smoky grey-blue glazing';REFLECT='Blue-grey reflected light'
FAN='Red-brown upper fan panel';METAL='Dark fanlight bars';DARK='Shadowed rabbet';PANEL='Weathered panel edge'


def ellipse(x,spring,rx,rz,t):
    return (x+rx*math.cos(t),spring+rz*math.sin(t))


def sector(x,spring,rx,rz,thick,lo,hi,segments):
    ts=[lo+(hi-lo)*i/segments for i in range(segments+1)]
    return Polygon([*[ellipse(x,spring,rx+thick,rz+thick,t)for t in ts],
                    *[ellipse(x,spring,rx,rz,t)for t in reversed(ts)]])


def arches(f,x,spring,span,rise,lod,label,d=0):
    rx=span/2;n=11 if lod else 23
    f.prism(sector(x,spring,rx,rise,.205,0,math.pi,36 if lod else 72),d+.015,d+.097,JOINT,label+'/voussoir joints')
    for i in range(n):
        t0=(i+.032)/n*math.pi;t1=(i+.968)/n*math.pi
        block=sector(x,spring,rx+.008,rise+.008,.18,t0,t1,2 if lod else 4)
        f.prism(block,d+.062,d+.127,RED if i%5!=2 else SECOND,label+'/red arch bricks')
    key=Polygon([(x-.063,spring+rise+.024),(x+.063,spring+rise+.024),(x+.092,spring+rise+.239),(x-.092,spring+rise+.239)])
    f.prism(key,d+.094,d+.165,GREY,label+'/crown keystone')
    if not lod:
        ring=sector(x,spring,rx+.204,rise+.204,.024,0,math.pi,64)
        f.prism(ring,d+.05,d+.118,RED,label+'/outer arch lip')


def grid_sash(f,cx,sill,width,head,columns,levels,lod,label,depth,paint=WOOD):
    case=box(cx-width/2,sill,cx+width/2,head)
    stile=.059 if width>1.2 else .042;bottom=.061;top=.055;divs=sorted(levels);openings=[]
    for col in range(columns):
        x0=cx-width/2+stile+(width-2*stile)*col/columns
        x1=cx-width/2+stile+(width-2*stile)*(col+1)/columns
        for row,(z0,z1) in enumerate(zip([sill+bottom,*divs],[*divs,head-top])):
            o=box(x0+(.017 if col else 0),z0+(.019 if row else 0),x1-(.017 if col<columns-1 else 0),z1-(.019 if row<len(divs) else 0))
            if o.area<=0:raise ValueError(label)
            openings.append(o)
            f.prism(o,depth-.059,depth-.046,REFLECT if (row+2*col)%5==1 else GLASS,label+'/window glass')
            if not lod:f.prism(o.difference(o.buffer(-.009,join_style=2)),depth-.037,depth-.019,PANEL,label+'/putty edge')
    f.prism(case.difference(unary_union(openings)),depth-.046,depth+.017,paint,label+'/frame and sash rails')


def wing(f,x,d,level,lod,label,red_panel=False,internal_side=0):
    data=d['gallery_levels'][level];span=d['gallery_span'];rx=span/2;rise=data['rise'];spring=data['spring'];sill=data['sill']
    depth=-.171;n=23 if lod else 52
    fan=Polygon([(x-rx,spring),(x+rx,spring),*[ellipse(x,spring,rx,rise,math.pi*i/n)for i in range(1,n)]])
    arch_aperture=opening(x,data['apron_bottom'],span,spring+rise-data['apron_bottom'],rise,n)
    f.prism(arch_aperture,depth-.22,depth-.199,DARK,label+'/dark rebate')
    # The 2026 upper near-side fan panels are red-brown. Their material cannot be identified from the image.
    f.prism(fan,depth-.036,depth-.027,FAN if red_panel else GLASS,label+'/arched fanlight')
    f.box(x,spring-.032,span,.067,.100,depth+.014,WOOD,label+'/impost transom')
    spokes=6 if not lod else 4
    for k in range(1,spokes):
        if red_panel and lod:continue
        end=ellipse(x,spring,rx-.031,rise-.030,k*math.pi/spokes)
        line=LineString([(x,spring+.016),end]).buffer(.007 if red_panel else .014,cap_style=2)
        f.prism(line,depth-.019,depth+(-.009 if red_panel else .012),SECOND if red_panel else METAL,label+'/radial divisions')
    if not red_panel:
        arc=sector(x,spring,rx*.29,rise*.29,.022,0,math.pi,16 if lod else 34)
        f.prism(arc,depth+.002,depth+.026,METAL,label+'/inner fanlight arc')
    w=span*(.76 if level=='upper' else .89)
    panel=box(x-rx,data['apron_bottom'],x+rx,spring-.062)
    hole=box(x-w/2,sill,x+w/2,spring-.060)
    f.prism(panel.difference(hole),depth-.175,depth+.010,BUFF,label+'/cream spandrel')
    if level=='upper':grid_sash(f,x,sill,w,spring-.067,2,[sill+(spring-.067-sill)*.73],lod,label,depth-.034)
    else:
        # Five separate rectangular transom lights sit between the fan and the lower four-by-four sash.
        rail=spring-.295
        grid_sash(f,x,sill,w,rail,4,[sill+(rail-sill)*r for r in (.25,.50,.75)],lod,label,depth-.031)
        grid_sash(f,x,rail+.006,span-.065,spring-.067,5,[],lod,label+' transom',depth-.034)
    f.box(x,sill-.035,w+.08,.068,.133,depth+.034,GREY,label+'/sill')
    for side in(-1,1):
        if side==internal_side:continue
        h=spring-data['apron_bottom'];nblocks=6 if lod else 11
        for i in range(nblocks):
            if i in (nblocks-1,0) or not lod:
                f.box(x+side*(rx+.062),data['apron_bottom']+(i+.5)*h/nblocks,.130,h/nblocks-.011,.139,.057,
                      SECOND if i%3==0 else RED,label+'/jamb blocks')
    arches(f,x,spring,span,rise,lod,label)
