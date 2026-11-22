"""The top two repeated rectangular patterns of three courtyard screens in the 2015 Qingxi photograph."""
from math import sin, pi
from random import Random

COLOURS = {
    'varnished wood': (.130, .053, .023), 'shadowed wood': (.087, .032, .018),
    'timber glint': (.174, .075, .028), 'amber glass': (.455, .287, .101),
    'honey glass': (.573, .402, .162), 'slate glass': (.145, .183, .188),
    'bluish glass': (.164, .224, .247), 'smoked glass': (.171, .163, .140),
    'reflected amber': (.291, .242, .145), 'mullion sides': (.103, .038, .020)
}
PALETTE = {name: {'color': list(rgb), 'roughness': .38 if 'glass' in name or 'amber' in name else .61}
           for name, rgb in COLOURS.items()}
CLEAR = .445
PITCH = .555
HEIGHT = .89
RAIL = .016
W = .008

def cut_wood(builder, label, x0, x1, z0, z1, front, back, material):
    vertices = [(x0,front,z0),(x1,front,z0),(x1,back,z0),(x0,back,z0),
                (x0,front,z1),(x1,front,z1),(x1,back,z1),(x0,back,z1)]
    faces = [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
             (3,7,6),(3,6,2),(0,4,7),(0,7,3),(1,2,6),(1,6,5)]
    builder.add(vertices,faces,material,label)

def rolled_glass(builder, label, x0, x1, z0, z1, material, lod, seed):
    # Small irregular relief is an approximate representation of the visibly mottled rolled glass.
    rng = Random(seed)
    nx = max(3, round((x1-x0) / (.042 if lod else .014)))
    nz = max(3, round((z1-z0) / (.042 if lod else .014)))
    vertices=[]; faces=[]
    def idx(i,j): return j*(nx+1)+i
    for j in range(nz+1):
        for i in range(nx+1):
            inner = 0<i<nx and 0<j<nz
            x = x0+(x1-x0)*(i+(rng.uniform(-.22,.22) if inner else 0))/nx
            z = z0+(z1-z0)*(j+(rng.uniform(-.22,.22) if inner else 0))/nz
            relief = rng.uniform(.0002,.0029) if inner else 0
            vertices.append((x,.036-relief,z))
    for j in range(nz):
        for i in range(nx):
            a,b,c,d=idx(i,j),idx(i+1,j),idx(i+1,j+1),idx(i,j+1)
            faces.extend([(a,b,c),(a,c,d)] if rng.random()>.5 else [(a,b,d),(b,c,d)])
    boundary=([idx(i,0) for i in range(nx)]+[idx(nx,j) for j in range(nz)]
              +[idx(i,nz) for i in range(nx,0,-1)]+[idx(0,j) for j in range(nz,0,-1)])
    back=[]
    for point in boundary:
        x,_,z=vertices[point];back.append(len(vertices)); vertices.append((x,.043,z))
    centre=len(vertices);vertices.append(((x0+x1)/2,.043,(z0+z1)/2))
    for k,c in enumerate(boundary):
        following=(k+1)%len(boundary);d=boundary[following];a=back[k];b=back[following]
        faces.extend([(c,a,b),(c,b,d),(centre,b,a)])
    builder.add(vertices,faces,material,label)

def add_building(builder,lod):
    glass_colours=[('amber glass','honey glass','reflected amber'),
                   ('smoked glass','slate glass','reflected amber'),
                   ('bluish glass','slate glass','smoked glass')]
    for screen in range(3):
        x0=(screen-1)*PITCH-CLEAR/2
        def wood(label,a,b,c,d,front=.004,mat='varnished wood'):
            cut_wood(builder,f's{screen+1} {label}',x0+a,x0+b,c,d,front,.057,mat)
        for x,label in [(-.038,'left'),(CLEAR,'right')]:
            wood(label+' jamb',x,x+.038,-.035,HEIGHT+.035,-.014,'shadowed wood')
        wood('frame head',0,CLEAR,HEIGHT,HEIGHT+.035,-.010)
        wood('frame sill',0,CLEAR,-.035,0,-.010)
        levels=(0,.097,.401,.502,.798,HEIGHT)
        for k in range(1,len(levels)-1):
            z=levels[k];wood(f'cross rail {k}',0,CLEAR,z-RAIL/2,z+RAIL/2,-.002)
        parts=0
        def pane(label,a,b,c,d):
            nonlocal parts
            colour=glass_colours[screen][(0,1,0,2,1,0,2,1,0,0,1,2,0,1,0,2)[parts%16]]
            rolled_glass(builder,f's{screen+1} pane {label}',x0+a,x0+b,c,d,colour,lod,screen*37+parts)
            parts+=1
        for band,(low,high) in enumerate(zip(levels,levels[1:])):
            lo=low+(RAIL/2 if band else 0);hi=high-(RAIL/2 if band<4 else 0)
            if band in (0,2,4):
                mid=CLEAR*(.51 if band==2 else .53)
                wood(f'band {band} short upright',mid-W,mid+W,lo,hi)
                pane(f'{band}.1',0,mid-W,lo,hi);pane(f'{band}.2',mid+W,CLEAR,lo,hi)
            else:
                a,b=CLEAR*.272,CLEAR*.718
                for x,k in [(a,1),(b,2)]:wood(f'band {band} upright {k}',x-W,x+W,lo,hi)
                mid=lo+(hi-lo)*.51
                wood(f'band {band} left tie',0,a-W,mid-W,mid+W,.006)
                wood(f'band {band} right tie',b+W,CLEAR,mid-W,mid+W,.006)
                pane(f'{band}.centre',a+W,b-W,lo,hi)
                for j,(left,right)in enumerate([(0,a-W),(b+W,CLEAR)],1):
                    pane(f'{band}.{j} low',left,right,lo,mid-W)
                    pane(f'{band}.{j} high',left,right,mid+W,hi)
        assert parts==16
    for j,xc in enumerate([-.2775,.2775],1):
        gap=(PITCH-CLEAR)/2-.038
        cut_wood(builder,f'intermediate timber {j}',xc-gap,xc+gap,-.035,HEIGHT+.035,.003,.09,'mullion sides')
