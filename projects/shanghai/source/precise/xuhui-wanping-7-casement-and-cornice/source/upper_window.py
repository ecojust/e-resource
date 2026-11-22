"""Upper-storey casement, rusticated pilasters and cornice at 7 Wanping Road."""
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import box

ID = 'xuhui-wanping-7-casement-and-cornice'
RENDER = 'Ochre lime render'
STONE = 'Buff dressed pilaster stones'
DRIP = 'Light buff sill and bevel'
DENTIL = 'Square stone dentils'
BED = 'Recessed pilaster joint'
STEEL = 'Charcoal painted outer frame'
BAR = 'Dark narrow glazing bar'
REVEAL = 'Ochre reveal inside the opening'
GLASS = 'Soft grey reflected light'
PALETTE = {key: dict(color=colour, roughness=roughness) for key, colour, roughness in [
    (RENDER, [1,1,1], .92), (STONE, [.72,.65,.461], .88), (DRIP,[.797,.725,.534],.85),
    (DENTIL,[.723,.677,.563],.89), (BED,[.425,.375,.26],.92), (STEEL,[.153,.154,.141],.75),
    (BAR,[.179,.188,.174],.73), (REVEAL,[.518,.384,.229],.9), (GLASS,[.531,.586,.573],.34)
]}
WIDTH = 3.04
HEIGHT = 2.55
CENTRES = [-.454,0,.454]
SIDE = .211

def texture():
    path = Path(__file__).with_name('ochre-mineral-render.png')
    if not path.exists():
        rng = np.random.default_rng(811)
        speckle = rng.normal(0,2.6,(480,640,1))
        colours = np.array([207,149,104])+speckle
        Image.fromarray(colours.clip(0,255).astype('uint8')).quantize(72).save(path)
    PALETTE[RENDER]['texture'] = str(path)

def add_building(b, far=False):
    texture()
    def face(shape, inner, outer, mat, name):
        b.prism(shape,inner,outer,lambda x,z,d:(x,-d,z),mat,name)
    def block(left,right,bottom,top,inner,outer,mat,name):
        face(box(left,bottom,right,top),inner,outer,mat,name)
    opening = box(-.71,.505,.71,2.028)
    wall = box(-WIDTH/2,0,WIDTH/2,2.323).difference(opening)
    face(wall,-.21,0,RENDER,'Bay of ochre render with a through window opening')
    for x in [-1.34,1.34]:
        block(x-.149,x+.149,0,2.214,-.074,.026,BED,'Recessed beds between pilaster courses')
        for j in range(8):
            bot = j*.274+.005
            block(x-.154,x+.154,bot,bot+.256,-.046,.081,STONE,'Individually modelled rusticated course')
            if not far:
                block(x-.145,x+.145,bot+.006,bot+.249,.080,.088,STONE,'Dressed face and narrow arris of course')
        for bottom,top,half,depth in [(2.154,2.183,.162,.102),(2.183,2.216,.178,.124),(2.216,2.245,.195,.151)]:
            block(x-half,x+half,bottom,top,-.05,depth,DRIP,'Stepped capital of banded pilaster')
    for l,r,bottom,top in [(-.766,-.710,.487,2.089),(.710,.766,.487,2.089),(-.71,.71,2.028,2.089)]:
        block(l,r,bottom,top,-.047,.035,STONE,'Pale narrow dressed surround')
    face(opening.difference(box(-.684,.526,.684,2.006)),-.163,.002,REVEAL,'Inner faces of window reveal')
    block(-.797,.797,.454,.519,-.073,.128,DRIP,'Projecting stone sill below lower lights')
    block(-.746,.746,.433,.454,-.03,.081,STONE,'Recess below sill drip')
    block(-.684,.684,.512,2.014,-.156,-.127,GLASS,'Window pane field behind three casements')
    for l,r in [(-.689,-.658),(.658,.689),(-.249,-.205),(.205,.249)]:
        block(l,r,.509,2.018,-.134,-.071,STEEL,'Continuous jamb or dividing stile for the three casements')
    for z,t in [(.510,.541),(1.570,1.629),(1.981,2.018)]:
        block(-.681,.681,z,t,-.134,-.071,STEEL,'Main frame rail or wide transom')
    for x in CENTRES:
        block(x-.011,x+.011,.538,1.987,-.13,-.096,BAR,'Slender upright dividing one sash into two columns')
        for z in [.866,1.220,1.790]:
            block(x-SIDE,x+SIDE,z,z+.019,-.131,-.097,BAR,'Thin crossbar, two lights across each leaf')
    for z,t,depth,mat in [(2.247,2.276,.128,STONE),(2.276,2.305,.154,DRIP),(2.380,2.423,.205,STONE),(2.423,2.474,.229,DRIP),(2.474,2.55,.210,STONE)]:
        block(-WIDTH/2,WIDTH/2,z,t,-.21,depth,mat,'Horizontal ledges of cornice')
    for i in range(19):
        x=(i-9)*.158
        block(x-.038,x+.038,2.305,2.386,.018,.179,DENTIL,'Individual square dentil under the projecting cornice')
    for part in b.parts:
        if part['material']==RENDER:
            part['texcoords']=[[(x+WIDTH/2)/WIDTH,z/HEIGHT] for x,y,z in part['vertices']]
