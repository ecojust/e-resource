"""Garden elevation adjoining the central five-bay portico.

Design units here match the central portico before uniform placement scaling.
Garden faces point toward -Y. The two end porticoes have three openings each.
Virtual Shanghai 1438 and 15128 show the five arched bays between each pair
of porticoes. Heights, profiles, inset depth and hidden returns are estimates.
"""

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import opening


INNER = 12.5
END_START = 40.15
OUTER = 55.07
INSET = 4.4
BACK = 6.8


def mapped(x, z, distance):
    return x, -distance, z


def face(builder, shape, y, depth, material, label):
    builder.prism(shape, -(y + depth), -y, mapped, material, label)


def sill(builder, x, y, z, width, depth, height, mat, name):
    builder.box((x, y, z), (width, depth, height), mat, label=name)


def gable(x, width, base, rise):
    return Polygon([(x - width/2, base), (x + width/2, base), (x, base + rise)])


def raking_moulding(builder, x, width, base, rise, y, thickness, depth, mat, label):
    """Project a continuous sloped cornice with a mitred ridge above the tympanum."""
    ridge = LineString([(x-width/2, base), (x, base+rise), (x+width/2, base)])
    face(builder, ridge.buffer(thickness/2, cap_style='flat', join_style='mitre'),
         y, depth, mat, label)


def portico_end(builder, x, lod, name):
    width = OUTER - END_START
    pitch = (width - 1.10) / 3
    piers = [x + (i-1.5)*pitch for i in range(4)]
    bays = [x + i*pitch for i in (-1, 0, 1)]
    n = 8 if lod else 20
    arches = [opening(b, .24, 2.48, 4.10, 1.22, n) for b in bays]
    face(builder, box(x-width/2, .12, x+width/2, 5.9).difference(unary_union(arches)),
         .14, .80, 'cream render', name+'.ground arches')
    for arch, b in zip(arches, bays):
        face(builder, arch, .86, .075, 'window glass', name+'.recessed roundhead sash')
        if not lod:
            for z in (1.47, 3.10):
                sill(builder, b, .82, z, 2.48, .07, .09, 'sash', name+'.transom')
            sill(builder, b, .82, 2.23, .08, .07, 3.91, 'sash', name+'.arch mullion')
    for p in piers:
        if not lod:
            for offset in (-.32, .32):
                builder.lathe((p + offset, .04),
                              [(.13, .25), (.34, .25), (.42, .19),
                               (4.92, .18), (5.04, .26), (5.18, .26)],
                              'ivory stone', 10, name+'.paired lower shafts')
        sill(builder, p, .22, 7.54, 1.07, .83, 3.19,
             'buff moulding', name+'.solid gallery plinth')
        sill(builder, p, .31, 13.99, .95, 1.0, 8.46, 'ivory stone', name+'.two-storey pier')
        sill(builder, p, .28, 18.03, 1.19, 1.12, .36, 'ivory stone', name+'.capital')
        sill(builder, p, .29, 20.1, 1.00, .93, 3.02, 'cream render', name+'.attic pier')
        if not lod:
            builder.lathe((p, -.14), [(8.65,.30),(8.83,.33),(8.98,.24),
                          (9.18,.38),(9.59,.57),(9.76,.53),(9.94,.34)],
                          'ivory stone', 12, name+'.balcony urn')
    # The square sconces of the end loggias sit in front of a shadowed gallery.
    # The octagonal openings are specific to the central block.
    for z, h in [(6.04, .48), (9.63, .34), (13.66, .25), (18.26, .49),
                 (21.76, .43)]:
        sill(builder, x, 1.51, z, width+.17, 3.49, h,
             'ivory stone', name+'.projected floor edge')
    back_windows = [(b, lo, hi) for b in bays for lo,hi in
                    [(6.40,9.19),(9.94,13.29),(13.96,17.86),(18.61,21.32)]]
    apertures = [box(b-1.05,lo,b+1.05,hi) for b,lo,hi in back_windows]
    face(builder, box(x-width/2,.12,x+width/2,22.12).difference(unary_union(apertures)),
         2.85,.30,'cream render',name+'.inner gallery wall')
    for a in apertures:
        face(builder,a,3.17,.07,'window glass',name+'.inner glazing')
    for z in [9.77, 13.81, 18.54]:
        for b in bays:
            span = pitch - .74
            if z > 18:
                material, h = 'ivory stone', .79
            else:
                material, h = 'balcony iron', .73
            sill(builder, b, .16, z+h, span, .14, .095, material, name+'.guard rail')
            for j in range(1, 5 if lod else 10):
                stride = 5 if lod else 10
                bar = .125 if z > 18 else .053
                sill(builder,b-span/2+j*span/stride,.16,z+h/2,bar,.12,h,
                     material,name+'.balcony baluster')
    # Solid raised attic behind the gable, visible above its shoulders in 15128.
    sill(builder,x,2.25,22.62,width-.74,1.58,1.20,'cream render',name+'.attic upstand')
    triangle = gable(x, width+.24, 21.83, 2.64)
    face(builder, triangle, -.17, 2.71, 'ivory stone', name+'.triangular pediment')
    face(builder, gable(x,width-1.36,22.13,2.02),-.20,.030,
         'cream render',name+'.tympanum')
    raking_moulding(builder,x,width+.32,21.82,2.70,-.44,.27,.31,
                    'buff moulding',name+'.raking cornice bed')
    raking_moulding(builder,x,width+.49,21.95,2.72,-.57,.12,.28,
                    'ivory stone',name+'.raking cornice lip')
    sill(builder,x,-.30,21.83,width+.49,.63,.23,'ivory stone',name+'.pediment sill')
    for side in (-1, 1):
        sill(builder,x+side*(width/2-.13),4.90,10.99,.26,3.80,21.74,
             'section',name+'.cut return')
    sill(builder,x,4.93,21.78,width,3.74,.32,'section',name+'.cut top')


def connecting_bays(builder, x, lod, name):
    width = END_START - INNER
    pitch = width/5
    bays = [x+i*pitch for i in (-2,-1,0,1,2)]
    count = 8 if lod else 20
    arches = [opening(b,.14,pitch-.61,4.73,1.98,count) for b in bays]
    rows = [(5.76,8.97), (10.40,12.78), (14.31,16.65), (18.66,20.47)]
    panes = [box(b-1.30,lo,b+1.30,hi) for b in bays for lo,hi in rows]
    cut = box(x-width/2,.1,x+width/2,21.70).difference(unary_union(arches+panes))
    face(builder,cut,INSET,.49,'cream render',name+'.arcade and window wall')
    for a in arches:
        # Blank recess represents the shadow beyond the arcade, not an entrance.
        face(builder,a,BACK-.14,.12,'reveal',name+'.arcade back at cut')
        if not lod:
            face(builder,a.buffer(.11,join_style='mitre').difference(a).intersection(
                 box(x-width/2,.14,x+width/2,5.3)),INSET-.13,.11,
                 'buff moulding',name+'.arch surround')
    for a in panes:
        face(builder,a,INSET+.50,.10,'window glass',name+'.recessed glazing')
        left,lo,right,hi = a.bounds
        b = (left+right)/2
        if not lod:
            sill(builder,b,INSET+.47,(lo+hi)/2,.085,.09,hi-lo,'sash',name+'.sash mullion')
            sill(builder,b,INSET+.47,lo+.58*(hi-lo),right-left,.09,.08,'sash',name+'.sash transom')
            sill(builder,b,INSET-.07,lo-.07,right-left+.22,.24,.14,
                 'buff moulding',name+'.window sill')
    for b in bays:
        face(builder,gable(b,3.26,9.13,.87),INSET-.27,.30,
             'ivory stone',name+'.first floor hood')
        if not lod:
            face(builder,gable(b,2.34,9.27,.49),INSET-.294,.027,
                 'cream render',name+'.hood relief')
        raking_moulding(builder,b,3.39,9.15,.89,INSET-.48,.18,.24,
                        'buff moulding',name+'.projecting window hood')
        if not lod:
            raking_moulding(builder,b,3.44,9.23,.89,INSET-.55,.08,.17,
                            'ivory stone',name+'.window hood lip')
    for z,projection in [(5.10,.15),(17.78,.41),(21.28,.38),(22.74,.24)]:
        sill(builder,x,INSET-.12,z,width,projection+.2,.25,
             'ivory stone',name+'.string course')
    sill(builder,x,INSET+.77,21.57,width,1.77,.30,'section',name+'.flat roof cut')
    for b in bays:
        sill(builder,b-pitch/2+.2,INSET+.02,22.09,.42,.42,1.03,
             'cream render',name+'.parapet pier')
        for j in range(1,5 if lod else 10):
            stride = 5 if lod else 10
            sill(builder,b-pitch/2+j*pitch/stride,INSET+.02,22.07,
                 .13,.23,.99,'ivory stone',name+'.roof baluster')
    # Close just the exposed plain cut immediately behind the frontage.
    sill(builder,x,BACK-.06,10.85,width,.12,21.50,'section',name+'.rear cut')
    sill(builder,x,(BACK+INSET)/2,21.63,width,BACK-INSET,.14,'section',name+'.rear cut top')


def add_wings(builder, lod):
    """Append two five-bay infills and two three-bay end loggias."""
    for side, direction in [(-1,'west'),(1,'east')]:
        connecting_bays(builder,side*(INNER+END_START)/2,lod,direction+'.infill')
        portico_end(builder,side*(END_START+OUTER)/2,lod,direction+'.end loggia')
        sill(builder,side*(INNER-.16),4.90,10.92,.35,3.8,21.61,
             'section',direction+'.central step return')
