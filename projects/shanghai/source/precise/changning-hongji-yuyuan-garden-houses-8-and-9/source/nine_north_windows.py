"""Visible openings in the two north projections of the numbered house 9."""
from math import hypot

from shapely.geometry import box

from house_nine_sashes import BEAD, EDGE, GLASS, MOUNT, PALETTE, PLASTER, WOOD


def openings(layout):
    """Return the seven apertures in outward-facing order in the axes of house 9."""
    sections = [
        ("east gable upper", (13.40, 6.41), (13.40, 7.43), 3.25, 4.56),
        ("east rear return upper", (10.37, 10.43), (9.68, 10.43), 3.34, 4.63),
        ("west gable upper", (13.15, 16.577), (13.15, 17.423), 3.436, 4.932),
        ("west gable lower", (13.15, 16.377), (13.15, 17.705), .63, 1.770),
        ("west east return upper", (11.78, 14.96), (12.68, 14.96), 3.39, 4.98),
        ("west recessed upper", (11.58, 20.075), (11.58, 20.915), 3.47, 4.89),
        ("west recessed lower", (11.58, 19.84), (11.58, 20.98), .64, 1.87),
    ]
    return [dict(id=label, a=a, c=c, low=low, high=high) for label,a,c,low,high in sections]


def add_windows(b, lod, layout):
    for material, description in PALETTE.items():
        b.palette.setdefault(material, description)
    for row in openings(layout):
        x,y=row['a']
        dx,dy=row['c'][0]-x,row['c'][1]-y
        width=hypot(dx,dy)
        ux,uy=dx/width,dy/width
        low,high=row['low'],row['high']
        upper=row['id'].endswith('upper')
        label='9 | N '+row['id']+' | '
        def plane(u,z,d):
            return (x+ux*u+uy*d, y+uy*u-ux*d, z)
        def part(outline,near,far,material,name):
            b.prism(outline,far,near,plane,material,label+name)

        surround=box(0,low,width,high)
        jamb=.049 if upper else .053
        light=box(jamb,low+jamb,width-jamb,high-jamb)
        part(surround.difference(light),-.061,-.153,WOOD,'fixed frame')
        if not lod:
            bead=light.difference(light.buffer(-.013,join_style=2))
            part(bead,-.077,-.146,BEAD,'inner bead')
        centre=width/2
        part(box(centre-.022,low+jamb,centre+.022,high-jamb),
             -.070,-.147,WOOD,'meeting stile')
        # The broad central sash has two leaves. Its lower pane has a lighter,
        # thinner glazing bar below the meeting rail in both 2023 views.
        # Ground-floor heads and two lights are exposed above the shrubs.
        steps=[(low+jamb,0.,'bottom')]
        if upper:
            steps.extend([(low+.297*(high-low),.011,'glazing bar'),
                          (low+.529*(high-low),.026,'meeting rail')])
        steps.append((high-jamb,0.,'top'))
        for col,(l,r) in enumerate([(jamb,centre-.022),(centre+.022,width-jamb)]):
            for j,((a,h,_),(c,k,bar)) in enumerate(zip(steps,steps[1:])):
                part(box(l,a+h,r,c-k),-.148,-.162,GLASS[(col+j)%3],
                     f'leaf {col+1} pane {j+1}')
                if k:
                    part(box(l,c-k,r,c+k),-.081 if k>.02 else -.099,-.148,
                         WOOD if k>.02 else BEAD,f'leaf {col+1} {bar}')
        part(box(-.066,high+.002,width+.066,high+.103),
             .101,-.016,PLASTER,'projecting head')
        part(box(-.102,high+.103,width+.102,high+.148),
             .146,-.014,EDGE,'upper head lip')
        if upper:
            part(box(-.040,low-.111,width+.040,low-.042),
                 .060,-.012,PLASTER,'sill apron')
            part(box(-.078,low-.042,width+.078,low-.002),
                 .136,-.016,EDGE,'sill nose')
        if row['id'] in ('west gable upper','west gable lower','west recessed lower'):
            offsets=[centre] if upper else [.025,width-.025]
            for i,u in enumerate(offsets):
                part(box(u-.039,high+.147,u+.039,high+.222),
                     .059,.005,MOUNT,f'head fixing {i+1}')
