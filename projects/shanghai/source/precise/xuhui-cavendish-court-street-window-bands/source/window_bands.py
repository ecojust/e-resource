"""Two pairs of steel windows in the red-brick bands above the 525 Hengshan Road cafe."""
from math import ceil
from photo_architecture import Facade

SURFACES = {
    'cream roughcast': ([.714,.632,.468], .94),
    'light mortar': ([.626,.571,.492], .94),
    'oxblood brick': ([.173,.086,.066], .81),
    'brown brick': ([.122,.061,.053], .79),
    'grey steel': ([.080,.092,.088], .56),
    'steel edge': ([.171,.182,.166], .52),
    'shaded glass': ([.089,.122,.127], .32),
    'daylit glass': ([.169,.199,.191], .34),
    'dark rainpipe': ([.111,.116,.107], .66),
}
PALETTE = {key:{'color':color,'roughness':rough} for key,(color,rough) in SURFACES.items()}
LEFT, RIGHT = -3.00, 2.64
# Local geometry is centred on the short elevation. Values derive from the three-station fit.
WINDOWS = [(-1.99,-1.05,2),(.06,1.98,3)]
SILL = .20
RISE = 3.15
CLEAR = 1.64
TOP = 5.29


def slab(face,left,right,low,high,front,back,material,name):
    face.box((left+right)/2,(low+high)/2,right-left,high-low,back-front,-(front+back)/2,material,name)


def bond(face,left,right,low,lod):
    """A different surface treatment for each web detail, with the same opening and courses."""
    height=CLEAR;high=low+height
    slab(face,left,right,low,high,0,.19,'light mortar','brick pointing')
    count=23
    pitch=height/count
    for row in range(count):
        z=low+row*pitch
        if lod:
            slab(face,left,right,z+.004,z+pitch-.004,-.009,.002,'oxblood brick','red horizontal courses')
            continue
        length=.236;offset=.118 if row%2 else 0
        for i in range(ceil((right-left+offset)/length)):
            start=max(left,left-offset+i*length)
            end=min(right,left-offset+(i+1)*length)
            if end-start<=.011:continue
            shade='brown brick' if (row+2*i)%7 in (2,5) else 'oxblood brick'
            slab(face,start+.0035,end-.0035,z+.004,z+pitch-.004,-.012,.002,shade,'staggered glazed brick')


def steel_window(face,left,right,low,lights,lod):
    high=low+CLEAR;transom=low+1.08;thick=.042
    for lo,hi in ((left,left+thick),(right-thick,right)):
        slab(face,lo,hi,low,high,.085,.17,'grey steel','steel jamb')
    for z in (low+thick/2,high-thick/2,transom):
        slab(face,left+thick,right-thick,z-thick/2,z+thick/2,.085,.169,'grey steel','steel transom and edge rails')
    step=(right-left)/lights
    for col in range(lights):
        a=left+col*step;b=a+step
        if col:
            slab(face,a-.016,a+.016,low+thick,high-thick,.076,.152,'grey steel','vertical glazing bars')
        for z0,z1,row in [(low+thick,transom-thick/2,0),(transom+thick/2,high-thick,1)]:
            slab(face,a+.012,b-.012,z0,z1,.181,.193,'daylit glass' if (col+row)%3==1 else 'shaded glass','separate glass lights')
            if not lod:
                for side in [a+.025,b-.025]:
                    slab(face,side-.005,side+.005,z0,z1,.158,.181,'steel edge','glazing bead')
    if not lod:
        slab(face,left+.04,right-.04,low-.012,low+.019,.012,.19,'steel edge','bottom edge of sill')


def add_building(builder,lod=False):
    face=Facade(builder,(-3,0),(3,0),'Cavendish north house')
    levels=[SILL,SILL+RISE]
    for low,high in ((0,SILL),(SILL+CLEAR,SILL+RISE),(SILL+RISE+CLEAR,TOP)):
        slab(face,LEFT,RIGHT,low,high,-.021,.25,'cream roughcast','roughcast spandrel')
    for low in levels:
        slab(face,LEFT,WINDOWS[0][0],low,low+CLEAR,-.021,.25,'cream roughcast','plastered wall by downpipe')
        bond(face,WINDOWS[0][1],WINDOWS[1][0],low,lod)
        bond(face,WINDOWS[1][1],RIGHT,low,lod)
        for left,right,lights in WINDOWS:
            steel_window(face,left,right,low,lights,lod)
    pipe_x=-2.63
    builder.tube([(pipe_x,-.122,.015),(pipe_x,-.122,TOP-.012)],.043,'dark rainpipe',sides=10 if lod else 18,label='street facade rainwater pipe')
    if not lod:
        for z in [.89,3.94]:
            slab(face,pipe_x-.066,pipe_x+.066,z-.019,z+.019,-.164,-.016,'grey steel','downpipe retaining strap')
