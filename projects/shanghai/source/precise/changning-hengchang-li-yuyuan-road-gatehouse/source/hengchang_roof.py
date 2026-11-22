"""South gateway roof and the first Yuyuan Road frontage, metres.

X increases east along the street. Y increases north into the building.
The southern gateway cap, its narrow intermediate roof and its blue rear
cover are distinct in the 2025 aerial. The civic oblique shows the rear cover.
"""
from math import ceil, cos, pi, sqrt
from pathlib import Path

TILE = 'Hengchang | orange-brown clay tile'
LEAD = 'Hengchang | weathered zinc flashing'
EAVE = 'Hengchang | white painted eaves'
IRON = 'Hengchang | grey-blue sheet roofing'
CREST = 'Hengchang | solid red clay ridge'
WALL = 'Hengchang | ochre attic render'
SOFFIT = 'Hengchang | shaded roof underside'
FRAME = 'Hengchang | ivory sash frame'
DARK = 'Hengchang | brown metal casement'
GREEN = 'Hengchang | blue-green metal glazing frame'
GLASS = 'Hengchang | muted grey window glass'
LIGHT = 'Hengchang | light reflective window glass'

def _material(rgb, roughness):
    return {'color': [((v / 255 + .055) / 1.055) ** 2.4 for v in rgb],
            'roughness': roughness}

PALETTE = {
    TILE: dict(color=[1., 1., 1.], roughness=.88,
               texture=str(Path(__file__).with_name('hengchang-terracotta.png'))),
    CREST: _material((145, 78, 59), .91),
    LEAD: _material((164, 159, 149), .76),
    EAVE: _material((216, 205, 178), .83),
    IRON: _material((113, 137, 151), .77),
    WALL: _material((193, 167, 119), .92),
    SOFFIT: _material((111, 99, 81), .88),
    FRAME: _material((221, 213, 191), .73),
    DARK: _material((104, 74, 64), .77),
    GREEN: _material((72, 99, 98), .68),
    GLASS: _material((101, 109, 114), .32),
    LIGHT: _material((147, 151, 147), .37),
}

def make_tile_texture():
    """Original procedural glaze, six pantiles by four exposed courses."""
    from PIL import Image
    image = Image.new('RGB', (192, 192))
    pixels = image.load()
    for y in range(image.height):
        course, v = divmod(y, 48)
        for x in range(image.width):
            col, u = divmod(x, 32)
            hue = ((course * 3 + col * 7) % 13) - 6
            roll = 9 * cos(2 * pi * (u - 7) / 32) - 6 * cos(4 * pi * (u - 5) / 32)
            lip = -24 if v >= 44 else 7 if v >= 42 else 0
            tone = hue + roll + lip + 1.8*cos(2*pi*(x*9+y*13)/192)
            pixels[x, y] = tuple(round(base + amount*tone)
                                 for base, amount in ((156, 1), (84, .72), (62, .64)))
    image.save(Path(__file__).with_name('hengchang-terracotta.png'), optimize=True)

def _box(b, x0, x1, y0, y1, z0, z1, mat, label):
    if x1 <= x0 or y1 <= y0 or z1 <= z0:
        raise ValueError(f'Invalid roof member {label}: {(x0,x1,y0,y1,z0,z1)}')
    b.box(((x0+x1)/2, (y0+y1)/2, (z0+z1)/2),
          (x1-x0, y1-y0, z1-z0), mat, label=label)

def _sheet(b, x0, x1, y0, y1, z0, z1, thickness, mat, label):
    """A rectangular inclined sheet, with UVs following the slope in metres."""
    top=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1)]
    bottom=[(x,y,z-thickness) for x,y,z in top]
    rings=[top, list(reversed(bottom))]
    for i in range(4):
        j=(i+1)%4
        rings.append([top[j],top[i],bottom[i],bottom[j]])
    vertices,faces,coords=[],[],[]
    scale=sqrt(1+((z1-z0)/(y1-y0))**2)
    for i,r in enumerate(rings):
        k=len(vertices)
        vertices.extend(r);faces.append((k,k+1,k+2,k+3))
        if i<2:
            coords.extend([(x/1.20, y*scale/.96) for x,y,z in r])
        else:
            dx,dy,dz=[r[1][j]-r[0][j] for j in range(3)]
            width=sqrt(dx*dx+dy*dy+dz*dz)/1.20
            coords.extend([(0,0),(width,0),(width,thickness/.96),(0,thickness/.96)])
    b.add(vertices,faces,mat,label)
    if mat==TILE and not b.parts[-1].get('texcoords'):
        b.parts[-1]['texcoords']=coords

def _tiles(b, x0,x1,y0,y1,z0,z1,lod,name):
    count=max(1,ceil(abs(y1-y0)*sqrt(1+((z1-z0)/(y1-y0))**2)/(.94 if lod else .24)))
    for j in range(count):
        a,c=j/count,(j+1)/count
        ya,yc=y0+(y1-y0)*a,y0+(y1-y0)*c
        za,zc=z0+(z1-z0)*a,z0+(z1-z0)*c
        # Add the exposed lower lip to each course. The two low sides of
        # the pitched roof have opposite drainage directions.
        if z1>z0: za+=.012
        else: zc+=.012
        _sheet(b,x0,x1,ya,yc,za,zc,.065,TILE,name)

def _facade(b, direction, face, lo, hi, zb, zt, lights, label, projections=None):
    """Pier and spandrel plates meet each actual opening at its four edges."""
    def piece(a,c,d0,d1,z0,z1,mat,part):
        if direction=='south':
            ext=(a,c,face+d0,face+d1)
        elif direction=='west':
            ext=(face+d0,face+d1,a,c)
        else:
            ext=(face-d1,face-d0,a,c)
        _box(b,*ext,z0,z1,mat,label+' '+part)
    end=lo
    for i,(a,c,sill,head,n,fr) in enumerate(lights):
        if not (end<=a<c<=hi and zb<sill<head<zt):
            raise ValueError(f'Opening outside {label}: {(a,c,sill,head)}')
        key=str(i+1)
        projection=(projections or {}).get(i,0.)
        if a>end:piece(end,a,0,.18,zb,zt,WALL,'pier '+key)
        piece(a,c,0,.18,zb,sill,WALL,'apron '+key)
        piece(a,c,0,.18,head,zt,WALL,'head '+key)
        piece(a-.036,c+.036,-.061,.12,sill-.054,sill, EAVE,'sill '+key)
        def sash(left,right,front,back,bottom,top,material,member):
            piece(left,right,front-projection,back-projection,bottom,top,material,member)
        if projection:
            # Projecting glazed cheeks have separate top rails and caps. The
            # actual wall opening remains clear behind the front glazing.
            for side,edge in [('left',a),('right',c-.05)]:
                piece(edge,edge+.05,-projection,0,sill+.055,head-.055,
                      GLASS,'projected '+side+' cheek '+key)
                for z in (sill,head-.05):
                    piece(edge,edge+.05,-projection,.04,z,z+.05,fr,'projected side rail '+key)
            piece(a-.038,c+.038,-projection-.04,.05,head,head+.045,IRON,'projected metal hood '+key)
            piece(a-.03,c+.03,-projection-.03,.05,sill-.055,sill,fr,'projected base '+key)
        rim=.052;inner=(c-a-2*rim-(n-1)*.052)/n
        sash(a,c,.018,.09,sill,sill+rim,fr,'frame '+key)
        sash(a,c,.018,.09,head-rim,head,fr,'frame '+key)
        sash(a,a+rim,.018,.09,sill+rim,head-rim,fr,'frame '+key)
        sash(c-rim,c,.018,.09,sill+rim,head-rim,fr,'frame '+key)
        u=a+rim
        for j in range(n):
            sash(u,u+inner,.082,.105,sill+rim,head-rim,
                  LIGHT if (i+j)%3==0 else GLASS,'glass '+key+'-'+str(j+1))
            u+=inner
            if j+1<n:
                sash(u,u+.052,.018,.09,sill+rim,head-rim,fr,'mullion '+key)
                u+=.052
        end=c
    if end<hi:piece(end,hi,0,.18,zb,zt,WALL,'end pier')

def roof_dimensions(layout):
    """Edition-specific roof values can be supplied under layout['roof'].""" 
    r=dict(layout.get('roof',{}))
    g=float(r.get('gate_width',layout.get('portal',{}).get('width',6.34)))
    far=float(r.get('frontage_east_x',layout.get('east_end',35.8)))
    k=g/6.34
    def value(name, default):return float(r.get(name,default*k))
    return dict(gate_width=g,frontage_east_x=far,scale=k,
                street_face=float(r.get('street_face',layout.get('front_y',{}).get('east',.55))), low_eave_z=value('low_eave_z',10.715),
                shoulder_y=value('shoulder_y',2.05), shoulder_z=value('shoulder_z',12.174),
                upper_eave_z=value('upper_eave_z',13.805), ridge_y=value('ridge_y',5.85),
                ridge_z=value('ridge_z',14.95), rear_y=float(r.get('rear_y',layout.get('wing_depth',10.7)+layout.get('front_y',{}).get('east',.55))),
                rear_eave_z=value('rear_eave_z',10.71), cap_front_y=value('cap_front_y',.08),
                cap_back_y=value('cap_back_y',2.86), cap_sill_z=value('cap_sill_z',13.49),
                cap_head_z=value('cap_head_z',15.19), cap_top_z=value('cap_top_z',15.69),
                cap_base_z=value('cap_base_z',11.87), rear_cover_z=value('rear_cover_z',10.30),
                rear_cover_y0=value('rear_cover_y0',11.02),rear_cover_y1=float(r.get('rear_cover_y1',layout.get('tower_depth',16.2))))

def add_roof(b,lod=False,layout=None):
    for key,material in PALETTE.items():b.palette.setdefault(key,material)
    d=roof_dimensions(layout or {});g=d['gate_width'];k=d['scale'];x1=d['frontage_east_x']
    front=d['cap_front_y'];back=d['cap_back_y'];sill=d['cap_sill_z'];head=d['cap_head_z'];top=d['cap_top_z'];base=d['cap_base_z']
    result_start=len(b.parts)
    _box(b,.09*k,g-.09*k,front,back,base-.025*k,base+.065*k,SOFFIT,'Gate cap floor')
    # The paired end returns accompany the single four-light street band.
    _facade(b,'south',front,.09*k,g-.09*k,base,top,
            [(.265*k,g-.76*k,sill,head,4,FRAME)],'Gate roof front')
    for f,face in [('west',.09*k),('east',g-.09*k)]:
        _facade(b,f,face,front+.18,back,base,top,
                [(front+.27*k,back-.26*k,sill+.015*k,head-.035*k,2,FRAME)],'Gate roof '+f)
    _box(b,.09*k,g-.09*k,back-.17,back,base,top,WALL,'Gate cap rear closure')
    _box(b,-.16*k,g+.16*k,front-.20*k,back+.20*k,top-.080*k,top,EAVE,'Gate overhanging rim')
    _sheet(b,-.16*k,g+.16*k,front-.20*k,back+.20*k,top+.035*k,top+.080*k,.045*k,IRON,'Gate top blue grey sheet')
    # The lower stone water table is built by the controlling wall module.
    # Two visibly marked ends of that cornice rise 0.26 m on registration.
    for part in b.parts[result_start:]:
        for i,(x,y,z) in enumerate(part['vertices']):
            part['vertices'][i]=(x,y,z+.0410*x)
    # Plain rear canopy belongs to the block, independently visible in the public oblique.
    _sheet(b,-.08*k,g+.05*k,d['rear_cover_y0'],d['rear_cover_y1'],
           d['rear_cover_z'],d['rear_cover_z']+.10*k,.10*k,IRON,'Lane rear separate blue cover')

    low=d['low_eave_z'];hy=d['shoulder_y'];hz=d['shoulder_z'];ey=d['street_face']-.19*k
    upper=d['upper_eave_z'];ry=d['ridge_y'];rz=d['ridge_z'];end=d['rear_y'];ez=d['rear_eave_z']
    def station(t):return g+(x1-g)*t
    _tiles(b,g,x1,ey,hy,low,hz,lod,'Street lower pantile courses')
    _box(b,g,x1,ey-.05*k,ey+.10*k,low-.135*k,low-.06*k,SOFFIT,'Street eave shaded fascia')
    _box(b,g,x1,ey-.085*k,ey+.065*k,low-.09*k,low+.015*k,EAVE,'Street eave gutter')
    for t in [.055,.316,.536,.812,.951]:
        x=station(t)
        _sheet(b,x-.038*k,x+.038*k,ey,hy,low+.034*k,hz+.032*k,.018*k,LEAD,'Street shoulder flashing')
    # Axis intervals are the observable 2018 openings mapped onto the first
    # contiguous red roof. Tree-covered edges and the adjacent high gable are excluded.
    lights=[]
    # These coordinates are intersections of the measured image corners with
    # the attic face. The two projecting glazed lights use their own return.
    surveyed=[(6.74,7.38,12.55,13.69,1,DARK),(8.33,8.90,12.43,13.60,1,FRAME),
              (9.01,11.93,12.29,13.59,3,FRAME),(13.22,15.90,12.67,13.49,3,DARK),
              (17.77,19.28,12.55,13.68,2,DARK),(21.20,22.17,12.55,13.67,2,DARK),
              (23.61,25.82,12.75,13.68,2,FRAME),(27.50,32.73,12.73,13.62,3,GREEN),
              (34.86,35.72,12.51,13.50,1,DARK)]
    for l,r,s,h,n,fr in surveyed:
        zz=lambda a:hz+(upper-hz)*(a-12.174)/(13.805-12.174)
        lights.append((station((l-6.34)/29.46),station((r-6.34)/29.46),zz(s),zz(h),n,fr))
    _facade(b,'south',hy,g,x1,hz-.085*k,upper,lights,'Roof storey',{2:.63*k,7:.65*k})
    def west_rise(x):
        return .22*k*max(0.,min(1.,(station(.24)-x)/(station(.24)-station(.16))))
    for x0,x2 in zip([g,station(.16),station(.24)],[station(.16),station(.24),x1]):
        start=len(b.parts)
        _box(b,x0,x2,hy-.17*k,hy+.10*k,upper-.080*k,upper+.025*k,EAVE,'Roof storey shallow gutter')
        _tiles(b,x0,x2,hy-.11*k,ry,upper+.07*k,rz,lod,'Main south pantile slope')
        for part in b.parts[start:]:
            for i,(x,y,z) in enumerate(part['vertices']):
                part['vertices'][i]=(x,y,z+west_rise(x)*max(0.,min(1.,(ry-y)/(ry-hy))))
    # Close the narrow step above the western attic wall.
    _box(b,g,station(.16),hy,hy+.17,upper,upper+.22*k,WALL,'West raised attic head')
    _sheet(b,station(.16),station(.24),hy,hy+.17,upper+.22*k,upper+.22*k,.22*k,WALL,'West attic head transition')
    last=b.parts[-1]
    for i,(x,y,z) in enumerate(last['vertices']):
        blend=(station(.24)-x)/(station(.24)-station(.16))
        last['vertices'][i]=(x,y,upper+(z-upper)*(.02+.98*blend))
    _tiles(b,g,x1,ry,end,rz,ez,lod,'Main north pantile slope')
    _box(b,g-.035*k,x1+.035*k,ry-.085*k,ry+.085*k,rz-.035*k,rz+.078*k,CREST,'Main red crest')
    # The aerial bounds the intervening reddish cover but gives no room plan.
    _tiles(b,.09*k,g,back,ry,upper+.04*k,rz,lod,'Gate intermediate south roof')
    _tiles(b,.09*k,g,ry,d['rear_cover_y0'],rz,d['rear_cover_z']+.04*k,lod,'Gate intermediate north roof')

if __name__=='__main__':
    make_tile_texture()
