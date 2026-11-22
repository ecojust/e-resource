"""Twin photographed street dormers and the narrow lower window band at 9 Xiangshan Road."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import Polygon, box as rectangle
from scipy.optimize import minimize_scalar
from xiangshan_photo_plane import pixel

DATA=json.loads((Path(__file__).resolve().parents[1]/'measurements'/'xiangshan-dormer-sections.json').read_text())
PLASTER='Xiangshan dormers | warm white plaster'
REVEAL='Xiangshan dormers | shaded plaster reveal'
FRAME='Xiangshan dormers | aged dark casing'
SASH='Xiangshan dormers | dark green painted sash'
GLASS='Xiangshan dormers | grey blue glass'
BEAD='Xiangshan dormers | rubbed glazing bead'
DARK='Xiangshan dormers | deep shadow behind open sash'
EAVE='Xiangshan dormers | dark timber soffit'
FASCIA='Xiangshan dormers | muted red brown bargeboard'
ROD='Xiangshan dormers | painted steel drying rails'
RIDGE='Xiangshan dormers | weathered ridge cap'
TILES=['Xiangshan dormers | fired tile '+str(i+1) for i in range(4)]
def colour(rgb,rough,metallic=0):
    c=np.array(rgb)/255
    return dict(color=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metallic)
PALETTE={PLASTER:colour([211,208,192],.92),REVEAL:colour([164,162,150],.92),FRAME:colour([62,61,53],.85),SASH:colour([71,76,65],.78),GLASS:colour([100,114,114],.26,.23),BEAD:colour([87,88,73],.78),DARK:colour([42,43,39],.96),EAVE:colour([70,61,55],.9),FASCIA:colour([97,63,57],.87),ROD:colour([80,85,77],.70,.23),RIDGE:colour([139,117,104],.88)}
PALETTE.update({k:colour(rgb,.89)for k,rgb in zip(TILES,[[139,84,75],[126,76,69],[150,96,82],[131,82,73]])})

def roof_seats():
    """Front footprint and estimated closing cut of each visible roof fragment."""
    return [dict(name=k,x_limits=DATA[k]['x'],front_y=0.,cut_y=DATA[k]['far_y'],base_z=DATA[k]['base']) for k in ('eastern','western')]+[dict(name='link',x_limits=DATA['link']['x'],front_y=DATA['link']['front_y'],cut_y=DATA['link']['far_y'],base_z=DATA['link']['base'])]

def box(b,a,c,y,q,z,t,m,name):
    b.box([(a+c)/2,(y+q)/2,(z+t)/2],[c-a,q-y,t-z],m,label=name)

def slab(b,outline,y0,y1,mat,name):
    b.prism(outline,-y1,-y0,lambda x,z,d:(x,-d,z),mat,name)

def roof(b,row,k,low):
    left,right=row['x'];rx=row['ridge_x'];yr=row['far_y'];yf=-row['forward_overhang']
    for side,e,sign in [('east',left,-1),('west',right,1)]:
        end=e+sign*row['rake_overhang']
        slope=(row['ridge']-row['spring'])/abs(rx-e)
        eave=row['ridge']-abs(end-rx)*slope
        top=row['ridge']+row['roof_rise']
        outline=Polygon([(rx,top-.12),(rx,top),(end,eave+row['roof_rise']),(end,eave+row['roof_rise']-.12)])
        slab(b,outline,yf+.055,yr,EAVE,k+' | '+side+' roof soffit')
        # The painted board follows each rake; its visible face clears the plaster.
        slab(b,outline,yf-.015,yf+.055,FASCIA,k+' | '+side+' front rake board')
        courses=max(3,round(abs(end-rx)/.32));pitch=.215;ntiles=max(5,round((yr-yf)/pitch))
        for i in range(courses):
            inner=rx+(end-rx)*i/courses;outer=rx+(end-rx)*(i+1)/courses
            zi=top-abs(inner-rx)*slope;zo=top-abs(outer-rx)*slope
            for j in range(ntiles):
                ya=yf+(yr-yf)*j/ntiles;yb=yf+(yr-yf)*(j+1)/ntiles
                # The wave runs down the tile. Five cross-section samples preserve the rolled edge.
                samples=3 if low else 7
                yn=np.linspace(ya,yb,samples);heights=[.006+.024*(.5+.5*math.cos(2*math.pi*f))**2 for f in np.linspace(0,1,samples)]
                coords=[];faces=[]
                for x,z,lip in [(inner,zi,0.),(outer,zo,.018)]:
                    coords.extend([[x,y,z+h+lip]for y,h in zip(yn,heights)])
                    coords.extend([[x,y,z-.006+lip]for y in yn])
                for i0 in range(samples-1):
                    for a in [(0,2*samples),(3*samples,samples)]:
                        a0,a1=a;faces.append([a0+i0,a0+i0+1,a1+i0+1,a1+i0])
                    faces.extend([[i0,samples+i0,samples+i0+1,i0+1],[2*samples+i0,2*samples+i0+1,3*samples+i0+1,3*samples+i0]])
                for a in (0,samples-1):
                    faces.append([a,2*samples+a,3*samples+a,samples+a] if a==0 else [a,samples+a,3*samples+a,2*samples+a])
                vv=np.array(coords);tri=[(f[0],f[1],f[2]) for f in faces]+[(f[0],f[2],f[3])for f in faces]
                m=vv[tri];vol=np.einsum('ij,ij->i',m[:,0],np.cross(m[:,1],m[:,2])).sum()
                if vol<0: faces=[f[::-1]for f in faces]
                b.add(coords,faces,TILES[(j+2*i+(1 if sign>0 else 0))%4],f'{k} | {side} tile {i+1}.{j+1}')
    b.tube([[rx,yf-.023,row['ridge']+row['roof_rise']+.04],[rx,yr,row['ridge']+row['roof_rise']+.04]],.069,RIDGE,sides=8 if low else 14,label=k+' | capped ridge')

def sash(b,aperture,front,opening,k,low):
    x0,x1,z0,z1=aperture; y=front+.135; top=z1-.038; bot=z0+.03
    for a,c in ((x0,x0+.045),(x1-.045,x1)):box(b,a,c,y-.03,y+.045,z0,z1,FRAME,k+' | fixed jamb')
    for a,c in ((z0,bot),(top,z1)):box(b,x0+.045,x1-.045,y-.03,y+.045,a,c,FRAME,k+' | fixed horizontal casing')
    w=(x1-x0-.09)/2
    for index in range(2):
        hinge=x0+.045+index*w
        rot=0.
        if index==0 and opening:
            # The photographed free top sits to the left of the hinged edge in the western winter view.
            observed=np.asarray(pixel([720/62-11,0.,13.6-178/62],'roof-15-west'))
            def residual(angle):
                pos=[hinge+w*math.cos(angle),y-.03-w*math.sin(angle),top-.015]
                return np.linalg.norm(np.asarray(pixel(pos,'roof-15-west'))-observed)
            rot=minimize_scalar(residual,bounds=(.15,math.pi-.05),method='bounded').x
        d=np.array([math.cos(rot),-math.sin(rot),0.]);n=np.array([math.sin(rot),math.cos(rot),0.]);up=np.array([0,0,1.])
        o=np.array([hinge,y-.031,0.]);label=f'{k} | leaf {index+1} '
        def piece(a,c,lo,hi,ba,he,mat,desc):
            b.box(o+d*((a+c)/2)+n*((lo+hi)/2)+up*((ba+he)/2),(c-a,hi-lo,he-ba),mat,basis=[d,n,up],label=label+desc)
        for a,c in ((0,.028),(w-.028,w)):piece(a,c,-.018,.018,bot,top,SASH,'stile')
        for ba,he in ((bot,bot+.034),(top-.032,top)):piece(.028,w-.028,-.018,.018,ba,he,SASH,'rail')
        ba,he=bot+.034,top-.032
        for cell in range(3):
            za=ba+(he-ba)*cell/3;zb=ba+(he-ba)*(cell+1)/3
            mid=w/2
            for col,(a,c) in enumerate(((.028,mid-.007),(mid+.007,w-.028))):
                piece(a,c,.003,.008,za+.006,zb-.006,GLASS,f'pane {cell+1}.{col+1}')
                if not low:
                    for bead_l,bead_r in ((a,a+.006),(c-.006,c)):
                        piece(bead_l,bead_r,-.009,-.003,za+.006,zb-.006,BEAD,'putty bead')
            piece(mid-.007,mid+.007,-.012,.012,za+.006,zb-.006,SASH,'central upright glazing bar')
            if cell<2:piece(.028,w-.028,-.011,.012,zb-.007,zb+.007,SASH,'horizontal glazing bar')
    box(b,x0-.015,x1+.015,front+.52,front+.537,z0-.015,z1+.015,DARK,k+' | recess shade')
    box(b,x0-.052,x1+.052,front-.055,front+.14,z0-.038,z0,REVEAL,k+' | sill')

def add_dormers(builder,lod=False):
    b=builder;low=lod in (True,'lod'); front=0.
    for key in ('eastern','western'):
        row=DATA[key];left,right=row['x'];z=row['base'];spring=row['spring'];r=row['ridge'];rx=row['ridge_x']
        body=Polygon([(left,z),(right,z),(right,spring),(rx,r),(left,spring)])
        for op in row['openings']:
            a,c,ba,t=op;body=body.difference(rectangle(a,ba,c,t))
        slab(b,body,front,front+.125,PLASTER,key+' | plaster gable with photographed apertures')
        for a,c in ((left,left+.10),(right-.1,right)):box(b,a,c,front+.125,row['far_y'],z,spring,PLASTER,key+' | visible side return')
        for i,op in enumerate(row['openings']):sash(b,op,front,row['sashes'][i]['left_open'],key+' window '+str(i+1),low)
        if key=='western':
            for j,(a,c,ba,t) in enumerate(row['openings']):
                for x in (a-.08,c+.08):
                    b.tube([[x,.01,ba-.27],[x,-.28,ba-.11],[x,-.28,ba-.028]],.019,ROD,sides=6 if low else 10,label=f'western rack {j+1} | bracket')
                for y in (-.16,-.285):
                    b.tube([[a-.11,y,ba-.023],[c+.11,y,ba-.023]],.019,ROD,sides=6 if low else 10,label=f'western rack {j+1} | rail')
        roof(b,row,key,low)
    row=DATA['link'];left,right=row['x'];front=row['front_y']
    body=rectangle(left,row['base'],right,row['top'])
    for op in row['openings']:
        a,c,ba,t=op;body=body.difference(rectangle(a,ba,c,t))
    slab(b,body,front,front+.115,PLASTER,'link | lower connecting dormer face')
    for j,op in enumerate(row['openings']):sash(b,op,front,False,'link window '+str(j+1),low)
    box(b,left-.06,right+.06,front-.18,row['far_y'],row['top'],row['top']+.08,EAVE,'link | flat soffit and narrow eave')
    cap=Polygon([(front-.18,row['top']+.08),(row['far_y'],row['top']+.08+(row['far_y']-front+.18)*row['cap_slope']),(row['far_y'],row['top']+.13+(row['far_y']-front+.18)*row['cap_slope']),(front-.18,row['top']+.13)])
    b.prism(cap,left-.06,right+.06,lambda y,z,x:(x,y,z),TILES[2],'link | shallow sloped cap')
