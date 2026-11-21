"""The four round posts and open stone railing of the Donghu Road entrance.
The clear space under the canopy is modeled through to the adjoining facade.
Coordinates are metres with X east along the facade, Y towards the house, and Z up.
"""
from shapely.geometry import LineString,box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE={
    'warm limestone':{'color':[.73,.70,.61],'roughness':.84},
    'light cap stone':{'color':[.79,.77,.68],'roughness':.82},
    'aged shadow stone':{'color':[.51,.49,.43],'roughness':.91},
    'joints':{'color':[.40,.39,.355],'roughness':.97},
    'canopy soffit':{'color':[.65,.63,.55],'roughness':.91},
    'weathered roof':{'color':[.32,.33,.30],'roughness':.97},
}
# Both aerial perspectives and the street grid are recorded in portico-dimensions.json.
# Tree cover partly masks the western roof edge. Keep a small overhang beyond
# each round post and place the projected rectangle on the main building's axis.
SLAB_WIDTH=8.00
SLAB_DEPTH=7.68
SOFFIT=5.03
POST_X=3.49
POST_FRONT=-7.06
POST_REAR=-.58
STREET_EDGE=-SLAB_DEPTH

def slab_part(b,name,material,x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)*.5,(y0+y1)*.5,(z0+z1)*.5),
          (x1-x0,y1-y0,z1-z0),material,label=name)

def column(b,x,y,name,lod):
    radius=.352
    sections=[(0,.496),(.090,.496),(.138,.470),(.174,.452),(.217,.449),
              (.228,.463),(.288,.472),(.343,.455),(.390,.415),
              (.455,.407),(.486,.382),(.558,.374),(.59,.357),
              (1.04,radius),(2.71,.343),(4.71,.316),
              (4.76,.320),(4.78,.346),(4.821,.348),(4.852,.333),
              (4.903,.376),(4.940,.393),(4.977,.415)]
    if lod:sections=[sections[i]for i in (0,1,2,4,6,8,11,13,14,16,18,20,22)]
    b.lathe((x,y),sections,'warm limestone',16 if lod else 44,'portico/'+name+'/shaft and circular base')
    slab_part(b,'portico/'+name+'/capital slab','light cap stone',
              x-.465,x+.465,y-.465,y+.465,4.970,SOFFIT+.025)

def panel_x(f,centre,z,w,h,lod):
    # Open diagonal crosses are visible near the corners and among the balusters.
    inset=.080 if lod else .063
    border=box(centre-w/2,z,centre+w/2,z+h).difference(
           box(centre-w/2+inset,z+inset,centre+w/2-inset,z+h-inset))
    a=(centre-w*.5+inset,z+inset);b=(centre+w*.5-inset,z+h-inset)
    c=(a[0],b[1]);d=(b[0],a[1])
    diagonal=unary_union([LineString([a,b]).buffer(.046,cap_style=2),
                          LineString([c,d]).buffer(.046,cap_style=2)])
    f.prism(border.union(diagonal),-.105,.035,'light cap stone','open crossed panel')

def baluster(f,x,z,h,lod):
    # The street photographs show rectilinear, shouldered openings.
    scale=1.10 if lod else 1
    stations=[(0,.068),(.053,.071),(.094,.057),(.170,.051),(.27,.038),
              (.41,.038),(.51,.052),(.570,.058),(.614,.078),(.671,.079)]
    if lod:stations=[stations[i]for i in (0,2,4,5,7,9)]
    from shapely.geometry import Polygon
    right=[(x+half*scale,z+rise*h/.671)for rise,half in stations]
    left=[(x-half*scale,z+rise*h/.671)for rise,half in reversed(stations)]
    f.prism(Polygon(right+left),-.115,.025,'warm limestone','stone balusters')

def rail(b,start,end,label,lod):
    f=Facade(b,start,end,label);L=((end[0]-start[0])**2+(end[1]-start[1])**2)**.5
    z=SOFFIT+.495;level=z+.155;inner=.680;top=level+inner
    for lo,hi,depth,mat,name in [(z,level,.19,'warm limestone','lower parapet block'),
            (level-.035,level+.020,.215,'light cap stone','baluster sill'),
            (top,top+.109,.202,'warm limestone','parapet rail'),
            (top+.109,top+.158,.239,'light cap stone','rail coping')]:
        f.box(0,(lo+hi)*.5,L,hi-lo,depth,-.04,mat,name)
    # Corners spell out a cross on each outside face. Long faces in the published
    # photograph contain another intervening cross; rhythm under the trees is approximated.
    num_panels=2 if L<4 else 3
    panels=[-L*.5+.35+(L-.70)*i/(num_panels-1)for i in range(num_panels)]
    for mid in panels:panel_x(f,mid,level,.57,inner,lod)
    for a,c in zip(panels,panels[1:]):
        lo=a+.34;hi=c-.34
        n=max(1,round((hi-lo)/.276))
        for i in range(n):baluster(f,lo+(hi-lo)*(i+.5)/n,level,inner,lod)

def add_building(b,lod=False):
    w=SLAB_WIDTH/2
    for x,side in [(-POST_X,'west'),(POST_X,'east')]:
        for y,end in [(POST_FRONT,'front'),(POST_REAR,'rear')]:
            column(b,x,y,side+' '+end,lod)
    slab_part(b,'flat canopy/edge and load-bearing slab','warm limestone',-w,w,STREET_EDGE,0,SOFFIT,SOFFIT+.43)
    slab_part(b,'flat canopy/soffit','canopy soffit',-w+.085,w-.085,STREET_EDGE+.085,-.02,SOFFIT-.025,SOFFIT+.016)
    slab_part(b,'flat canopy/upper weathering','weathered roof',-w+.084,w-.084,STREET_EDGE+.074,-.015,SOFFIT+.43,SOFFIT+.505)
    for a,c,name in [((-w,STREET_EDGE),(w,STREET_EDGE),'front rail'),
                      ((-w,0),(-w,STREET_EDGE),'west rail'),((w,STREET_EDGE),(w,0),'east rail')]:
        f=Facade(b,a,c,name)
        for i,(el,hi,dp) in enumerate([(SOFFIT+.12,.038,.055),(SOFFIT+.34,.074,.10),(SOFFIT+.442,.092,.13)]):
            f.box(0,el,f.length,hi,dp,.022,'light cap stone','canopy fascia '+str(i))
        rail(b,a,c,name,lod)
