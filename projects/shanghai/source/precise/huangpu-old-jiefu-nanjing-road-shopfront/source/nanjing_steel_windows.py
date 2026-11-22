"""Double steel casement, stepped X and folded diamond spandrel at 257 Nanjing Road.

Builder world coordinates: X west along the north facade, Y inward, Z above
street grade. Width and elevation are caller supplied; callers can transform the
resulting metrically local parts to another documented elevation.
"""
import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from nanjing_photo_plane import position
from pathlib import Path
import json

def finish(colour, roughness, metallic=0):
    rgb=np.array(colour)/255.
    return dict(color=np.where(rgb<.04045,rgb/12.92,((rgb+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)
STEEL='Jiefu graphite steel'
EDGE='Jiefu grey rubbed steel edges'
RIBBON='Jiefu dark embossed diagonal ribbons'
GLASS='Jiefu recessed neutral glass'
TRANSOM='Jiefu muted transom glazing'
GUARD_GLASS='Jiefu shaded glass behind ironwork'
MORTAR='Jiefu sand mortar'
BRICKS=['Jiefu golden brown facing brick','Jiefu pale brown facing brick','Jiefu buff facing brick']
PALETTE={STEEL:finish([43,44,43],.52,.38),EDGE:finish([112,109,103],.54,.38),
         RIBBON:finish([55,56,55],.56,.34),GLASS:finish([91,94,92],.34,.20),
         GUARD_GLASS:finish([50,52,54],.44,.20),TRANSOM:finish([132,131,122],.40,.13),MORTAR:finish([142,118,91],.95),
         **{n:finish(c,.88)for n,c in zip(BRICKS,[[194,154,117],[206,169,137],[187,148,118]])}}
def plate(b,shape,y,thickness,material,label):
    if not shape.is_empty:
        b.prism(shape,-y-thickness,-y,lambda x,z,d:(x,-d,z),material,label)

def add_window(builder,left,right,bottom,upper,y=0.,lod=False,label='Nanjing Road steel sash'):
    """Build one complete opening. bottom/upper bound its guard, casement and transom.
    y is the brick pier reference plane, and the grille projects to y+0.19 m.
    """
    w=right-left;h=upper-bottom
    if min(w,h)<=0:raise ValueError('Window requires positive width and height')
    # Survey on the close photo shows the spandrel, paired glazed sash and short
    # upper transom. The top and lower rails of the dark central motif are separate.
    zguard=bottom+.46*h;zsash=bottom+.91*h;yt=y+.19
    def tr(points):return [(left+w*x,bottom+(zguard-bottom)*z) for x,z in points]
    def band(points,r):return LineString(tr(points)).buffer(r,cap_style=2,join_style=2)
    def edgebox(a,b,c,d):return box(left+w*a,bottom+h*b,left+w*c,bottom+h*d)
    def bars(points,front,depth,mat,text):
        if points:plate(builder,unary_union(points),front,depth,mat,label+' '+text)
    # Window reveals, flush front rails and reveals behind the iron.
    plate(builder,edgebox(0,0,1,1),y+.435,.032,GLASS,label+' backing glass')
    plate(builder,edgebox(.015,.009,.985,.465),y+.419,.008,GUARD_GLASS,label+' glass in shadow behind open guard')
    plate(builder,edgebox(.025,.918,.975,.985),y+.422,.010,TRANSOM,label+' transom')
    plate(builder,edgebox(.028,.472,.480,.899),y+.403,.009,GLASS,label+' first closed casement')
    plate(builder,edgebox(.520,.472,.973,.899),y+.401,.009,GLASS,label+' second closed casement')
    wbar=.031
    rect=box(left,bottom,right,upper)
    frame=rect.difference(box(left+wbar,bottom+wbar,right-wbar,upper-wbar))
    bars([frame,box(left,zsash-.027,right,zsash+.019),box(left,zguard-.012,right,zguard+.025),
          box((left+right)/2-.029,zguard,(left+right)/2+.029,zsash)],
          y+.326,.055,STEEL,'outer frame, meeting stiles and transom')
    # Upper and lower row of short balusters. The long field is open behind them.
    lower=.30;top=.74
    guard=box(left,bottom,right,zguard).difference(box(left+.021,bottom+.026,right-.021,zguard-.023))
    stiff=[guard]
    for v in [lower,top]:
        z=bottom+v*(zguard-bottom);stiff.append(box(left,z-.012,right,z+.012))
    for u in [.25,.50,.75]:
        for start,end in [(0,lower),(top,1.)]:
            stiff.append(band([(u,start),(u,end)],.0095))
    bars(stiff,yt,.029,STEEL,'guard perimeter, horizontal rails and six balusters')
    # Coordinates trace the separate wide diagonal strips and narrow raised rims
    # of the ornament; mirrored left and right folds stop short of the middle.
    def motif(u,v):return (u,lower+(top-lower)*v)
    def line(coords,radius):return band([motif(u,v) for u,v in coords],radius)
    field=box(left+.012,bottom+lower*(zguard-bottom),right-.012,bottom+top*(zguard-bottom))
    wide=[];rims=[];cross=[]
    for rev in [False,True]:
        revx=lambda u:1-u if rev else u
        core=[(revx(x),z) for x,z in [(-.10,1.02),(.06,1.02),(1.10,-.02),(.94,-.02)]]
        wide.append(Polygon(tr([motif(*u) for u in core])).intersection(field))
        for u in [-.10,.055]:
            rims.append(line([(revx(u),1.02),(revx(u+1.05),-.02)],.0080).intersection(field))
        for coords in [
            [(.015,.68),(.167,.858)],[(.015,.42),(.225,.714)],
            [(.015,.39),(.19,.18)],[(.060,.49),(.29,.79)],
            [(.060,.49),(.235,.27)],[(.207,.51),(.274,.60),(.347,.51),(.275,.419),(.207,.51)]]:
            cross.append(line([(revx(u),v) for u,v in coords],.0088).intersection(field))
    bars(wide,yt-.012,.013,RIBBON,'intersecting ribbon faces')
    bars(rims,yt-.021,.014,EDGE,'raised long diagonal rims')
    bars(cross,yt-.020,.012,EDGE,'folded side lozenges and central diamonds')
    if not lod:
        # Slender sash ridge and the two latches are read on the 2024 close shot.
        bars([box((left+right)/2-.007,zguard+.045,(left+right)/2+.007,zsash-.04)],y+.306,.018,EDGE,'meeting stile ridge')
        for u in [.465,.535]:
            x=left+w*u;z=zguard+(zsash-zguard)*.36
            builder.box([x,y+.292,z],[.026,.033,.078],STEEL,label=label+' latch')
    builder.box([(left+right)/2,yt+.092,bottom-.032],[w+.028,.229,.056],STEEL,label=label+' turned apron')

def add_brick_pier(builder,left,right,bottom,top,y=0.,lod=False,label='Jiefu pier'):
    """Approximate bond is a staggered stretcher offset on alternating courses."""
    width=right-left
    builder.box([(left+right)*.5,y+.16,(bottom+top)/2],[width,.32,top-bottom],MORTAR,label=label+' bedding')
    pitch=.235;course=.0655
    # Far view uses shallow grouped courses, retaining the changes of light at the pier face.
    if lod:
        for j,z in enumerate(np.arange(bottom,top,course)):
            high=min(top,z+course-.006)
            if high>z:builder.box([(left+right)*.5,y-.004,(z+high)/2],[width,.010,high-z],BRICKS[j%3],label=label+' bonded courses')
        return
    pieces={s:[]for s in BRICKS}
    for j,z in enumerate(np.arange(bottom,top,course)):
        high=min(top,z+course-.007)
        if high<=z:continue
        for k in range(-1,2+int(width/pitch)):
            x=left+pitch*(k+(j%2)*.46)
            l=max(left,x+.004);r=min(right,x+pitch-.004)
            if r>l:pieces[BRICKS[(7*j+5*k)%3]].append(box(l,z,r,high))
    for mat,rects in pieces.items():
        if rects:plate(builder,unary_union(rects),y-.008,.012,mat,label+' facing stretchers')

def window_pair_dimensions():
    file=Path(__file__).resolve().parents[1]/'measurements/nanjing-photo-controls.json'
    q=json.loads(file.read_bytes());out=[]
    for src in q['window_faces'].values():
        # Estimate left and right steel edges from their casing and lower railing.
        a=np.array([position(*p,.19,'b') for p in src])
        l=float(np.mean(a[[0,3,4],0]));r=float(np.mean(a[[1,2,5],0]))
        bot=float(np.mean(a[4:,2]));top=float(np.mean(a[:2,2]))+.255
        out.append(dict(left=l,right=r,bottom=bot,upper=top))
    return out
def add_window_pair(builder,lod=False):
    east,west=window_pair_dimensions()
    for name,part in [('eastern',east),('western',west)]:
        add_window(builder,**part,lod=lod,label='Lower north field '+name+' double sash')
    add_brick_pier(builder,east['right'],west['left'],min(east['bottom'],west['bottom'])-.06,max(east['upper'],west['upper'])+.03,lod=lod,label='Central wide pier')
