"""Original geometry for the Central Trust Company's restored glazed ceiling.

The 2015 conservation photographs establish the coloured underside. The view
from the open lightwell shows a separate, lightly pitched weather cover.
Coordinates are metres. The caller supplies the four plan corners (southwest,
southeast, northeast, northwest) and the wall bearing level at the soffit.
"""
from collections import defaultdict
from math import cos, hypot, pi, sin

GLASS_MATERIALS = {
    'Trust skylight antique lead': {'color': [.048, .042, .038], 'roughness': .52, 'metallic': .35},
    'Trust skylight reeded brass': {'color': [.475, .347, .144], 'roughness': .4, 'metallic': .25},
    'Trust skylight antique ivory': {'color': [.833, .796, .617], 'roughness': .35},
    'Trust skylight pale sage': {'color': [.600, .686, .431], 'roughness': .32},
    'Trust skylight emerald': {'color': [.045, .116, .060], 'roughness': .31},
    'Trust skylight leaf green': {'color': [.323, .491, .202], 'roughness': .31},
    'Trust skylight charcoal blue': {'color': [.077, .120, .143], 'roughness': .39},
    'Trust skylight wine': {'color': [.360, .093, .094], 'roughness': .36},
    'Trust skylight grey weather glass': {'color': [.56, .61, .62], 'roughness': .33, 'alpha': .27},
    'Trust skylight zinc bars': {'color': [.43, .45, .44], 'roughness': .61, 'metallic': .27},
}
LEAD, BRASS, IVORY, SAGE, EMERALD, LEAF, BLUE, RED, COVER, ZINC = GLASS_MATERIALS


def add_skylight(builder, lod, box):
    """Add the original-colour pattern and transparent cover. Return measured roles.

    box={'corners': [(x,y), ...], 'soffit_z': metres}. X increases across the
    short dimension and Y runs to the opposite end. Optional 'cover_rise'
    changes only the estimated ridge elevation above the cover eaves.
    """
    corners = box['corners']
    z = float(box['soffit_z'])
    if len(corners) != 4 or any(len(p) != 2 for p in corners):
        raise ValueError('The glazed ceiling requires four XY corners')
    width = sum(hypot(corners[j][0]-corners[i][0], corners[j][1]-corners[i][1]) for i,j in [(0,1),(3,2)]) / 2
    length = sum(hypot(corners[j][0]-corners[i][0], corners[j][1]-corners[i][1]) for i,j in [(0,3),(1,2)]) / 2
    if not 0 < width < length:
        raise ValueError('Supply the front and rear edges of a longitudinal skylight')
    for name, spec in GLASS_MATERIALS.items():
        builder.palette.setdefault(name, dict(spec))
    parts = defaultdict(lambda: [[], []])
    rise = box.get('cover_rise', width * .095)
    shoulder = width * .035

    def xyz(x, y, offset, cover=False):
        u, v = x / width, y / length
        weights = ((1-u)*(1-v), u*(1-v), u*v, (1-u)*v)
        east, north = (sum(w*p[k] for w,p in zip(weights, corners)) for k in (0,1))
        # The four green margins turn down from the flat rectangular centre.
        if cover:
            h = z + shoulder + .18 + rise * (1 - abs(2*u-1))
        else:
            h = z + shoulder * max(0., min(1., min(u,1-u)/.255, min(y,length-y)/pad))
        return (east,north,h+offset)

    def patch(points, mat, label, offset=0., cover=False, both=False):
        verts, faces = parts[(label,mat)]
        start = len(verts)
        verts.extend(xyz(x,y,offset,cover) for x,y in points)
        ids = list(range(start,start+len(points)))
        # The coloured face is seen from below. A single solid base has a
        # second skin above. Surface ornament stays on the indoor face.
        faces.append(tuple(reversed(ids)))
        if both:
            faces.append(tuple(ids))

    def rect(x0,y0,x1,y1,mat,label,offset=0.,cover=False,both=False):
        patch([(x0,y0),(x1,y0),(x1,y1),(x0,y1)], mat,label,offset,cover,both)

    def line(x0,y0,x1,y1,thick,mat,label,offset=-.015,cover=False,both=False):
        dx, dy = x1-x0, y1-y0
        scale = thick*.5/hypot(dx,dy)
        a,b = -dy*scale, dx*scale
        patch([(x0-a,y0-b),(x1-a,y1-b),(x1+a,y1+b),(x0+a,y0+b)],
              mat,label,offset,cover,both)

    def oval(cx,cy,rx,ry,mat,label,offset):
        n = 16 if lod else 32
        for i in range(n):
            a,b = (2*pi*j/n for j in (i,i+1))
            patch([(cx,cy),(cx+rx*cos(a),cy+ry*sin(a)),(cx+rx*cos(b),cy+ry*sin(b))], mat,label,offset)

    # A shallow green turned border is visible at both short ends.
    pad = width*.185
    x0,x1 = width*.269,width*.731
    y0,y1 = pad,length-pad
    for left,right in [(0,width*.255),(width*.255,width*.745),(width*.745,width)]:
        for bottom,top in [(0,pad),(pad,length-pad),(length-pad,length)]:
            rect(left,bottom,right,top,EMERALD,'Green canopy fields',both=True)
    rect(x0,y0,x1,y1,IVORY,'Milk glass centre',-.004,both=True)
    bay = (y1-y0)/6
    pane_left,pane_right = width*.307,width*.693
    for index in range(6):
        a,b = y0+index*bay,y0+(index+1)*bay
        inner_a,inner_b = a+.055,b-.055
        rect(pane_left,inner_a,pane_right,inner_b,SAGE if index in (0,5) else IVORY,
             'Light gridded panels',-.008)
        cols,rows = (4,4) if lod else (8,10)
        dx,dy = (pane_right-pane_left)/cols,(inner_b-inner_a)/rows
        for c in range(cols+1):
            x = pane_left+c*dx
            line(x,inner_a,x,inner_b,.019,EMERALD,'Green glazing grid')
        for r in range(rows+1):
            y = inner_a+r*dy
            line(pane_left,y,pane_right,y,.018,LEAF,'Green glazing grid')
        if not lod:
            for c in range(cols):
                for r in range(rows):
                    x, y = pane_left+c*dx,inner_a+r*dy
                    line(x,y,x+dx,y+dy,.007,BRASS,'Diagonal filaments',-.018)
                    line(x+dx,y,x,y+dy,.007,BRASS,'Diagonal filaments',-.018)
        # Four circular bosses can be counted in the complete conservation view.
        if 1 <= index <= 4:
            cx,cy = width*.5,(a+b)*.5
            radius = min(width*.103,bay*.22)
            rect(cx-radius*1.04,cy-radius*1.04,cx+radius*1.04,cy+radius*1.04,LEAD,'Medallion corner grounds',-.021)
            oval(cx,cy,radius,radius,BRASS,'Four brass roundels',-.024)
            oval(cx,cy,radius*.87,radius*.87,LEAD,'Roundel inner leads',-.028)
            oval(cx,cy,radius*.71,radius*.71,IVORY,'Opal centres',-.032)
            line(cx,cy-radius*.69,cx,cy+radius*.69,.036,LEAD,'Roundel centre ribs',-.036)
            if not lod:
                for sx,sy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    u,v=cx+sx*radius*.82,cy+sy*radius*.82
                    oval(u,v,radius*.085,radius*.045,BRASS,'Roundel corner florets',-.026)
        for v in [a,b]:
            rect(x0,v-.026,x1,v+.026,LEAD,'Cross bay transoms',-.042)
        for v,w in [(a+.045,.021),(b-.045,.021)]:
            rect(x0,v-w,x1,v+w,BRASS,'Cross bay brass beads',-.034)
        if index < 5:
            rect(x0,b-.046,x1,b-.022,BLUE,'Blue transverse enamel',-.045)
            for pos in (.36,.50,.64):
                rect(width*pos-.045,b-.061,width*pos+.045,b+.061,RED,'Ruby joint insets',-.046)
    line(width*.5,y0,width*.5,y1,.036,LEAD,'Glazier longitudinal spine',-.0365)
    for side in (-1,1):
        flip = lambda x: x if side < 0 else width-x
        # Geometric key fret along the light central rectangle.
        f0,f1 = width*.273,width*.303
        for x in (f0,f1):
            line(flip(x),y0,flip(x),y1,.029,LEAD,'Fret borders',-.028)
        repeat = 28 if lod else 48
        step=(y1-y0)/repeat
        for n in range(repeat):
            v=y0+n*step
            path=[(f0,v),(f1,v),(f1,v+.77*step),(f0+.27*(f1-f0),v+.77*step),
                  (f0+.27*(f1-f0),v+.32*step),(f0+.68*(f1-f0),v+.32*step)]
            for p,q in zip(path,path[1:]):
                line(flip(p[0]),p[1],flip(q[0]),q[1],.016 if lod else .013,LEAD,'Square meander',-.031)
        lo,hi = width*.043,width*.238
        for x in (lo,hi):
            line(flip(x),pad*.85,flip(x),length-pad*.85,.050,IVORY,'Lateral ivory bands',-.012)
        ncol,nrow=(2,25) if lod else (3,45)
        dx,dy=(hi-lo-.09)/ncol,(length-2*pad)/nrow
        for j in range(nrow):
            v=pad+j*dy
            for c in range(ncol):
                u=lo+.045+(c+.5)*dx
                # Nested pointed scales from the restored green side fields.
                # Each scale is triangulated directly, including its turned tip.
                # Individual darker tesserae sit under the bright curved leaves.
                patch([(flip(u-dx*.46),v+dy*.14),(flip(u),v+dy*.07),
                       (flip(u+dx*.27),v+dy*.41),(flip(u),v+dy*.55)]
                      [::1 if side<0 else -1],BLUE,'Dark green and blue tesserae',-.012)
                steps=4 if lod else 7
                for t in range(steps):
                    a,b=pi*t/steps,pi*(t+1)/steps
                    def xy(theta,inner):
                        return (flip(u+(.46*dx if not inner else .36*dx)*cos(theta)),
                                v+(.86*dy if not inner else .64*dy)*sin(theta))
                    ring=[xy(a,False),xy(b,False),xy(b,True),xy(a,True)]
                    patch(ring if side<0 else ring[::-1],LEAF,'Green overlapping scales',-.019)
        for k in range(7):
            v=pad+k*bay
            line(flip(width*.015),v,flip(width*.254),v,.062,LEAD,'Lateral transoms',-.032)
        line(flip(width*.014),0,flip(width*.014),length,.074,LEAD,'Perimeter lead',-.052)
    # At the short returns the leaf pattern turns ninety degrees and follows
    # the mitred four-corner border, visible in the complete pre-repair view.
    for sign in (-1,1):
        ybase = pad*.5 if sign < 0 else length-pad*.5
        for i in range(10 if not lod else 6):
            n = 10 if not lod else 6
            span = (width-width*.3)/n
            centre = width*.15 + (i+.5)*span
            for j in range(6):
                a,b = pi*j/6,pi*(j+1)/6
                points=[(centre+span*.44*cos(a),ybase+sign*pad*.29*sin(a)),
                        (centre+span*.44*cos(b),ybase+sign*pad*.29*sin(b)),
                        (centre+span*.34*cos(b),ybase+sign*pad*.20*sin(b)),
                        (centre+span*.34*cos(a),ybase+sign*pad*.20*sin(a))]
                patch(points if sign>0 else points[::-1],LEAF,'Turned end borders',-.023)
    for v in (0,length):
        line(0,v,width,v,.086,LEAD,'Perimeter lead',-.052)
    # The upper lightwell photograph shows an independent pitched grey cover
    # and a longitudinal ridge. Its glazing is translucent on the web model.
    for lo,hi in [(0,width*.5),(width*.5,width)]:
        rect(lo,0,hi,length,COVER,'Weather glazing two slopes',0,True,True)
    for u in (0,width*.25,width*.5,width*.75,width):
        line(u,0,u,length,.045,ZINC,'Longitudinal weather bars',.014,True,True)
    for j in range(13):
        v=length*j/12
        for lo,hi in [(0,width*.5),(width*.5,width)]:
            line(lo,v,hi,v,.041,ZINC,'Weather glazing joints',.014,True,True)
    for (label,mat),(v,f) in parts.items():
        builder.add(v,f,mat,label)
    return {'width_m':width,'length_m':length,'roundels':4,'panel_bays':6,
            'soffit_z':z,'ridge_z':z+shoulder+.18+rise}
