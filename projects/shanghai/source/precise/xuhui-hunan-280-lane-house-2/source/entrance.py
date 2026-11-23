"""The green number 2 plate and paired dark painted entrance on the southwest corner."""
import json
from pathlib import Path

from shapely.affinity import affine_transform
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union


CASING = 'Hunan Lane 280 | deep teal entrance frame'
BLADES = 'Hunan Lane 280 | painted door blades'
DARK = 'Hunan Lane 280 | shaded door inset'
PALE = 'Hunan Lane 280 | pale upper right insert'
HARDWARE = 'Hunan Lane 280 | worn entry fittings'
REVEAL = 'Hunan Lane 280 | ochre entrance reveal'
SILL = 'Hunan Lane 280 | worn stone threshold'
GREEN = 'Hunan Lane 280 | green number plate'
EDGE = 'Hunan Lane 280 | pressed green plate edge'
INK = 'Hunan Lane 280 | ivory address lettering'
PALETTE = {
    CASING: {'color': [.060, .113, .115], 'roughness': .62, 'metallic': .28},
    BLADES: {'color': [.088, .156, .154], 'roughness': .67, 'metallic': .20},
    DARK: {'color': [.027, .046, .045], 'roughness': .83},
    PALE: {'color': [.355, .325, .273], 'roughness': .92},
    HARDWARE: {'color': [.425, .457, .42], 'roughness': .59, 'metallic': .49},
    REVEAL: {'color': [.50, .443, .316], 'roughness': .97},
    SILL: {'color': [.356, .343, .301], 'roughness': .94},
    GREEN: {'color': [.062, .391, .357], 'roughness': .46, 'metallic': .15},
    EDGE: {'color': [.105, .331, .316], 'roughness': .51},
    INK: {'color': [.879, .865, .709], 'roughness': .64},
}
MEASURE = Path(__file__).resolve().parents[1] / 'measurements'
PREFIX = 'Southwest entrance / '


def _glyph(strokes):
    lines = [LineString([(u, 1-v) for u,v in group]) for group in strokes]
    return unary_union(lines).buffer(.048, cap_style='square', join_style='round', quad_segs=2)


def _inscription():
    """Small original line-drawn characters arranged as 湖南路二八〇弄."""
    water = [[(.05,.13),(.18,.23)],[(.03,.39),(.16,.47)],[(.06,.90),(.21,.59)]]
    hu = water + [[(.26,.32),(.58,.32)],[(.42,.07),(.42,.53)],
                  [(.28,.53),(.57,.53),(.57,.81),(.28,.81),(.28,.53)],
                  [(.60,.91),(.67,.60),(.67,.13),(.94,.13),(.94,.91),(.86,.86)],
                  [(.68,.37),(.93,.37)],[(.68,.60),(.93,.60)]]
    nan = [[(.08,.18),(.93,.18)],[(.50,.05),(.50,.32)],
           [(.17,.94),(.17,.33),(.85,.33),(.85,.93),(.75,.89)],
           [(.34,.43),(.40,.54)],[(.67,.43),(.58,.54)],[(.27,.56),(.75,.56)],
           [(.28,.71),(.73,.71)],[(.50,.57),(.50,.88)]]
    lu = [[(.08,.12),(.37,.12),(.37,.40),(.08,.40),(.08,.12)],
          [(.21,.40),(.21,.83)],[(.22,.59),(.39,.59)],[(.08,.58),(.08,.85)],
          [(.03,.88),(.42,.78)],[(.60,.10),(.47,.34)],[(.57,.18),(.88,.18),(.76,.41),(.45,.60)],
          [(.55,.33),(.75,.52),(.96,.59)],[(.51,.62),(.87,.62),(.87,.90),(.51,.90),(.51,.62)]]
    er = [[(.18,.24),(.81,.24)],[(.06,.77),(.94,.77)]]
    ba = [[(.38,.19),(.29,.58),(.06,.88)],[(.58,.16),(.68,.57),(.93,.87)]]
    zero = Point(.50,.52).buffer(.391,quad_segs=10).boundary.buffer(.046,quad_segs=2)
    nong = [[(.18,.11),(.83,.11)],[(.24,.29),(.77,.29)],[(.10,.48),(.89,.48)],
            [(.50,.12),(.50,.47)],[(.06,.67),(.94,.67)],[(.37,.54),(.37,.73),(.21,.93)],
            [(.68,.53),(.68,.94)]]
    letters = [_glyph(v) for v in (hu,nan,lu,er,ba)]+[zero,_glyph(nong)]
    return unary_union([affine_transform(v,[.108,0,0,.158,.066+i*.125,.071]) for i,v in enumerate(letters)])


def _number_plate(prism, data, lod):
    px,pz = data['centre_local_m']
    width,height = data['size_m']
    def finish(poly,z1,z2,mat,name):
        shape = affine_transform(poly,[width,0,0,height,px-width/2,pz-height/2])
        prism(shape,z1,z2,mat,name)
    skin = box(.025,.034,.975,.966).buffer(.025,quad_segs=3)
    front = .011
    finish(skin,.003,front,GREEN,'enameled house number plaque')
    inner = box(.041,.04,.958,.955).buffer(.015,quad_segs=2)
    finish(inner.difference(inner.buffer(-.012)),front,front+.0018,EDGE,'low pressed border')
    digit = Polygon([(.426,.697),(.434,.732),(.456,.773),(.490,.797),(.530,.799),(.561,.789),
                     (.581,.765),(.592,.729),(.593,.690),(.583,.650),(.549,.594),(.478,.480),
                     (.472,.473),(.597,.473),(.597,.418),(.414,.418),(.415,.466),(.488,.582),
                     (.531,.647),(.544,.687),(.543,.718),(.532,.738),(.512,.747),(.490,.740),
                     (.479,.726),(.471,.696)])
    finish(digit,front,front+.002,INK,'number 2')
    finish(_inscription(),front,front+.0017,INK,'Hunan Road Lane 280 below the number')
    if not lod:
        for u,z in ((.036,.947),(.962,.942),(.035,.050),(.965,.053)):
            shape=Point(px+(u-.5)*width,pz+(z-.5)*height).buffer(.0018,quad_segs=3)
            prism(shape,front,front+.0022,HARDWARE,'small corner fastening mark')


def add_entrance(b,lod=False,placement=None):
    """Mount the measured entry in the host opening; +u is right as seen from outdoors."""
    if placement is None:
        placement=json.loads((MEASURE/'entrance-placement.json').read_text())
    origin=placement['left_sill_enu_m']
    ux,uy=placement['across_unit_enu']
    width,height=placement['opening_size_m']
    def point(u,z,out):
        return (origin[0]+ux*u+uy*out,origin[1]+uy*u-ux*out,origin[2]+z)
    def solid(shape,back,front,mat,name):
        b.prism(shape,back,front,point,mat,PREFIX+name)
    def region(u0,u1,z0,z1,back,front,mat,name):
        solid(box(u0*width,z0*height,u1*width,z1*height),back,front,mat,name)
    for key,material in PALETTE.items():
        b.palette.setdefault(key,material)
    # Narrow visible wall returns precede the dark jambs. The heavy overhang is in the host.
    frame=box(0,0,width,height)
    reveal=frame.difference(box(.012*width,-.03,.988*width,.984*height))
    solid(reveal,-.16,.002,REVEAL,'shallow head and jamb returns')
    region(0,1,-.036,0,-.18,.077,SILL,'single projecting threshold')
    solid(box(.012*width,0,.988*width,.984*height).difference(
          box(.038*width,.015*height,.962*width,.947*height)),-.065,.068,CASING,'dark outside frame')
    for name,x0,x1 in [('left',.037,.494),('right',.500,.963)]:
        region(x0,x1,.014,.947,-.041,.014,DARK,name+' shaded inset')
        border=box(x0*width,.015*height,x1*width,.948*height)
        glass=box((x0+.020)*width,.602*height,(x1-.019)*width,.926*height)
        grille=box((x0+.020)*width,.037*height,(x1-.019)*width,.575*height)
        solid(border.difference(unary_union([glass,grille])),.016,.060,CASING,name+' leaf rails and stiles')
        # Eight uninterrupted blades above the centre line alternate with slits.
        # At the dated overprint the repeated pitch is interpolated from the visible rows.
        for i in range(21):
            z=(.040+i*.0262)*height
            if z+.018*height>.575*height:break
            region(x0+.019,x1-.018,z/height,z/height+.018,.017,.043,BLADES,name+' horizontal blade '+str(i+1))
    u0,u1,z0,z1,face = placement.get('pale_insert_fit',{}).get('placement',[.523,.904,.639,.895,.03])
    region(u0,u1,z0,z1,face-.007,face,PALE,'pale upper-right rectangular insert')
    u0,u1,z0,z1 = placement.get('central_cover_fit',{}).get('placement',[.210,.482,.419,.578])
    region(u0,u1,z0,z1,.045,.071,BLADES,'rectangular centre cover')
    region(u1-.012,u1+.001,z0+.008,z1-.007,.071,.082,HARDWARE,'slender bright central fitting')
    for u in [.292,.320]:
        region(u,u+.009,.622,.715,.019,.031,HARDWARE,'vertical light on the upper-left panel')
    _number_plate(solid,placement['house_plaque'],lod)
