"""The photographed four-light steel screen, twin red cornices and recessed return sash."""
import math
from shapely.geometry import box
from shapely.ops import unary_union

RED='Muted red cornice tile'
PALE='Pale inset in red band'
BROWN='Wine red shadow tile'
CREAM='Buff stone window surround'
SAND='Pale projecting ledge'
STEEL='Aged steel glazing bars'
BLACK='Dark reveal'
GLASS='Light behind pale glass'
GLASS2='Cream reflected glass'
SIDE='Side window in shadow'
EDGE='Grey return casement'

def double_cornice(face,left,right,top,band,records,side=False):
    name=face.label+' cornice'
    # The front carries two periodic red bands separated by a light projecting ledge.
    for i,(a,b) in enumerate([(top-band,top-band*.60),(top-band*.32,top)]):
        face.prism(box(left,a,right,b),-.025,.019,RED,'red course '+str(i+1))
        record=records[1-i]
        if side:
            pitch=record['median_period_m'];n=max(2,round((right-left)/pitch))
            centres=[left+(k+.5)*(right-left)/n for k in range(n)]
        else:centres=record['visible_pale_centres_m']
        for j,x in enumerate(centres):
            x0=max(left+.002,x-.019);x1=min(right-.002,x+.019)
            if x0<x1:
                face.prism(box(x0,a+.012,x1,b-.009),.020,.023,BROWN if side else PALE,'brick rhythm '+str(i+1))
    face.prism(box(left,top-.60*band,right,top-.32*band),-.025,.047,SAND,'pale separating belt')
    face.prism(box(left,top-.67*band,right,top-.57*band),-.025,.033,CREAM,'edge below belt')
    if not side:
        # Broad pale noses cast short independent shadows in the horizontal band.
        for j,f in enumerate([.032,.238,.626,.977]):
            x=left+(right-left)*f
            face.box(x,top-band*.51,.13,.054,.135,.042,SAND,'projecting belt stone')

def window_surround(face,bounds,sill=True):
    a,b,c,e=bounds;h=e-b;w=c-a
    face.prism(box(a-.082,b-.062,c+.086,e+.077).difference(box(a,b,c,e)),-.130,.032,CREAM,'pale rectangular frame')
    if sill:face.box((a+c)/2,b-.059,w+.226,.060,.150,.015,CREAM,'projecting stone sill')
    face.prism(box(a,b,c,e).difference(box(a+.029,b+.024,c-.022,e-.035)),-.133,-.049,BLACK,'inset dark rebate')

def steel_front(face,bounds,grid,lod):
    a,b,c,e=bounds;h=e-b;w=c-a
    window_surround(face,bounds)
    face.prism(box(a+.013,b+.012,c-.010,e-.016),-.143,-.131,BLACK,'back to steel opening')
    for j,r in enumerate(grid['columns']):
        left=a+w*r['left_frac'];right=a+w*r['right_frac']
        x0=left+.015;x1=right-.011
        if j==3:x1=min(x1,c-.021)
        if x1<=x0:continue
        face.prism(box(left-.009,b+.024,left+.010,e-.039),-.112,-.064,STEEL,'vertical steel '+str(j+1))
        if j==0:
            face.prism(box(a+.022,b+.024,left-.007,e-.025),-.115,-.091,BLACK,'deep left side of reveal')
        rails=sorted(e-h*v for v in r['rail_fractions_from_top'])
        for k,(low,high) in enumerate(zip([b+.024,*[z+.012 for z in rails]],[*[z-.012 for z in rails],e-.04])):
            face.prism(box(x0-.003,low-.003,x1+.003,high+.003),-.128,-.114,GLASS if (j+k)%3 else GLASS2,'pale pane '+str(j+1))
            if not lod:
                face.prism(box(x0+.013,low+.009,x0+.022,high-.007),-.114,-.112,'Reflected light','narrow vertical reflection')
        for z in rails:
            face.prism(box(x0-.014,z-.010,x1+.009,z+.010),-.111,-.065,STEEL,'staggered cross rail '+str(j+1))
    face.box((a+c)/2,e-.044,w-.046,.047,.052,-.079,BLACK,'deep lintel to window')

def return_sash(builder,face,bounds,lod):
    from photo_architecture import Facade
    a,b,c,e=bounds;mid=(a+c)/2;h=e-b
    # In the side window two narrow outward leaves reveal a dark interior.
    face.prism(box(a,b,c,e),-.173,-.157,SIDE,'shade behind side sash')
    window_surround(face,bounds,False)
    for j,(left,right,angle) in enumerate([(a+.041,mid-.012,.28),(mid+.012,c-.041,-.17)]):
        hinge=face.point(left if j==0 else right,0,-.072);width=right-left
        if j==0:
            start=hinge;end=hinge+face.t*width*math.cos(angle)+face.n*width*math.sin(angle)
        else:
            end=hinge;start=hinge-face.t*width*math.cos(angle)-face.n*width*math.sin(angle)
        pane=Facade(builder,start[:2],end[:2],face.label+' hinged sash '+str(j+1))
        w=pane.length;outer=box(-w/2,b+.028,w/2,e-.035);hole=outer.buffer(-.025,join_style=2)
        pane.prism(outer.difference(hole),-.013,.015,EDGE,'projecting perimeter frame')
        pane.prism(hole,-.018,-.013,'Dusty side glazing','side glass leaf')
        if not lod:pane.box(-w*.32,(b+e)/2,.012,h-.13,.010,-.009,'Muted glass reflection','vertical glint')
