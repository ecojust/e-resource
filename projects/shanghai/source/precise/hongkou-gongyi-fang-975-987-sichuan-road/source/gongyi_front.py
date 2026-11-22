"""Restored French doors, shop glazing, principal masonry and pierced street parapet."""
from math import radians, cos, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from gongyi_materials import BRICK, STONE, TRIM, SOFFIT, WOOD, DOOR_GLASS, STEEL, SHOP_GLASS, SHOP_SHADE, DARK_RECESS


def plane(s, z, d):
    return s, -d, z


def front(b, shape, inside, outside, material, name):
    if not shape.is_empty:
        b.prism(shape, inside, outside, plane, material, name)


def strip(b, x0, z0, x1, z1, low, high, material, name):
    front(b, box(x0, z0, x1, z1), low, high, material, name)


def glazed_frame(b, x0, z0, x1, z1, width, mullions, rails, depth, material, glass, label):
    opening = box(x0, z0, x1, z1)
    parts = [opening.difference(box(x0 + width, z0 + width, x1 - width, z1 - width))]
    parts += [box(x - width * .40, z0, x + width * .40, z1) for x in mullions]
    parts += [box(x0, z - width * .45, x1, z + width * .45) for z in rails]
    frame = unary_union(parts)
    front(b, frame, depth - .055, depth, material, label + ' frame')
    front(b, opening.difference(frame), depth - .074, depth - .058, glass, label + ' glass')


def documented_open_door(b, left, right, sill, transom, head, label):
    """One sash in the restored photograph is open inwards beside its closed mate."""
    mid=(left+right)/2
    jamb=box(left,sill,right,head).difference(box(left+.065,sill+.065,right-.065,head-.065))
    front(b,jamb,-.215,-.14,WOOD,label+' outer casing')
    glazed_frame(b,left+.055,transom,right-.055,head-.055,.049,
                 [left+(right-left)*v for v in (.25,.5,.75)],[(transom+head)/2],
                 -.155,WOOD,DOOR_GLASS,label+' upper lights')
    strip(b,left+.018,sill+.025,right-.018,transom-.025,-.94,-.91,DARK_RECESS,label+' shadowed interior')
    angle=radians(84)
    def open_plane(s,z,d):
        return (left+(s-left)*cos(angle)+d*sin(angle),.16+(s-left)*sin(angle)-d*cos(angle),z)
    def fixed_plane(s,z,d):
        return s,.16-d,z
    for a,c,mapper,name in [(left+.065,mid,open_plane,'open leaf'),(mid,right-.065,fixed_plane,'closed leaf')]:
        body=box(a,sill+.04,c,transom-.028)
        glass=box(a+.044,sill+.65,c-.044,transom-.072)
        x=(a+c)/2
        bars=[box(x-.015,sill+.64,x+.015,transom-.06)]
        for level in (1,2):
            z=sill+.65+(transom-.072-sill-.65)*level/3
            bars.append(box(a+.039,z-.016,c-.039,z+.016))
        cutouts=glass.difference(unary_union(bars))
        b.prism(body.difference(cutouts),-.047,.016,mapper,WOOD,label+' '+name+' timber')
        b.prism(cutouts,-.061,-.048,mapper,DOOR_GLASS,label+' '+name+' glass')


def balcony_door(b, left, right, sill, head, transom_height, lod, label, open_leaf=False):
    width = right - left
    center = (left + right) / 2
    transom = head - transom_height
    border = .18
    surround = box(left - border, sill - .035, right + border, head + .27)
    front(b, surround.difference(box(left, sill, right, head)), -.009, .067, TRIM, label + ' surround')
    if open_leaf:
        documented_open_door(b,left,right,sill,transom,head,label)
    else:
        kick = sill + .67
        glass_height = transom - kick
        rails = [kick, kick + glass_height / 3, kick + 2 * glass_height / 3, transom]
        glazed_frame(b, left, sill, right, head, .073, [center], rails, -.145, WOOD, DOOR_GLASS, label)
        # The independent high-resolution photograph shows four by two lights in
        # the transom and two columns of glass per door leaf above the timber kick.
        for frac in [.25, .75]:
            x = left + frac * width
            strip(b, x - .014, transom + .019, x + .014, head - .060, -.187, -.143, WOOD, label + ' transom bar')
            strip(b, x - .017, kick + .022, x + .017, transom - .025, -.187, -.143, WOOD, label + ' leaf bar')
        cross = (transom + head) / 2
        strip(b, left+.065, cross-.014, right-.065, cross+.014, -.186, -.143, WOOD, label + ' transom cross')
        for lo, hi in [(left+.055,center-.055),(center+.055,right-.055)]:
            strip(b, lo, sill+.073, hi, sill+.62, -.18, -.145, WOOD, label + ' kick panel')
    if not lod:
        for x in [left - .075, right + .075]:
            strip(b, x - .037, head + .07, x + .037, head + .195, .06, .078, STONE, label + ' lintel return')
        strip(b,left-.207,head+.226,right+.207,head+.275,.052,.095,TRIM,label+' lintel cap')


def parapet(b, edges, height, lod):
    # The repaired street elevation has an open stone crest above its broad cornice.
    for i, (z0, z1, depth, material) in enumerate([
        (-.35,-.24,.15,STONE),(-.24,-.16,.22,TRIM),(-.16,-.072,.31,SOFFIT),
        (-.072,.02,.38,TRIM),(.02,.115,.31,TRIM)]):
        strip(b,edges[0]-.10,height+z0,edges[-1]+.10,height+z1,-.16,depth,material,'Cornice course '+str(i+1))
    for index,(lo,hi) in enumerate(zip(edges,edges[1:]),1):
        left, right = lo+.15, hi-.15
        panel = box(left,height+.11,right,height+.50)
        holes=[]
        count=14
        for k in range(count):
            x=left+(right-left)*(k+.5)/count
            w=(right-left)/count*.37
            holes.append(Polygon([(x-w*.77,height+.17),(x+w*.77,height+.17),
                                  (x+w,height+.32),(x+w*.73,height+.39),
                                  (x-w*.73,height+.39),(x-w,height+.32)]))
        front(b,panel.difference(unary_union(holes)),-.155,.045,TRIM,'Parapet pierced bay '+str(index))
        strip(b,left-.025,height+.49,right+.025,height+.561,-.185,.079,TRIM,'Parapet rail '+str(index))
    for i,x in enumerate(edges):
        for z0,z1,half,d in [(.10,.49,.18,.086),(.49,.60,.213,.108),(.60,.655,.235,.12)]:
            strip(b,x-half,height+z0,x+half,height+z1,-.193,d,TRIM,'Parapet pier '+str(i+1))


def add_front(b,lod,layout):
    edges=layout['bay_edges'];floors=layout['balcony_z'];height=layout['street_cornice_z']
    openings=[];entries=[]
    for i,(lo,hi) in enumerate(zip(edges,edges[1:]),1):
        span=hi-lo
        # The ground datum changes after restoration. Current doors and continuous
        # transom follow the repaired shopfront photograph, not the 2018 boarding.
        a,c,sill,head,transom,division,meeting=layout['shops_relative_to_bay'][str(i)]
        shop=(lo+span*a,span*sill,lo+span*c,span*head)
        openings.append(box(*shop))
        entries.append(('shop',shop,'Shop '+str(i),(span*transom,division,meeting)))
        for floor in (2,3):
            for side in (1,2):
                key=f'L{floor}-{i}-{side}'
                a,c,sill,head,transom=layout['doors_relative_to_bay'][key]
                params=(lo+span*a,span*sill,lo+span*c,span*head)
                openings.append(box(*params))
                entries.append(('door',params,f'Floor {floor} bay {i} leaf {side}',span*transom))
    holes=unary_union(openings)
    lower=box(edges[0],0,edges[-1],floors[0]-.13)
    upper=box(edges[0],floors[0]-.13,edges[-1],height)
    front(b,lower.difference(holes),-.38,0,STONE,'Street | shopfront masonry')
    front(b,upper.difference(holes),-.38,0,BRICK,'Street | perforated upper brick')
    for kind,(left,bottom,right,top),label,fit in entries:
        if kind=='door':
            balcony_door(b,left,right,bottom,top,fit,lod,label,open_leaf=label==layout['observed_open_door'])
        else:
            center=(left+right)/2;span=right-left
            # In the northernmost photographed shop the double door swings in the
            # other half. Only the fixed light/door division continues through the transom.
            transom_height,division,door_meeting=fit
            main = left + span * division
            meeting = left + span * door_meeting
            rail = top - transom_height
            glazed_frame(b,left,bottom,right,top,.075,[main],[rail],-.195,STEEL,SHOP_GLASS,label)
            strip(b,meeting-.025,bottom+.015,meeting+.025,rail-.022,-.240,-.192,STEEL,label+' door meeting')
            strip(b,left,top,right,floors[0]-.21,-.016,.015,SHOP_SHADE,label+' fascia')
            strip(b,left-.017,top-.015,right+.017,top+.052,-.04,.06,STEEL,label+' top rail')
    for i,x in enumerate(edges):
        lo=max(edges[0],x-.31);hi=min(edges[-1],x+.31)
        strip(b,lo,.025,hi,floors[0]-.12,-.023,.075,STONE,'Shopfront pier '+str(i+1))
        if not lod:
            strip(b,lo-.018,floors[0]-.48,hi+.018,floors[0]-.28,-.018,.099,TRIM,'Shopfront capital '+str(i+1))
    parapet(b,edges,height,lod)
