"""Ground arcade and the projecting grille on no. 3, from the dated front photograph."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE.parent/'measurements/ground-arcade-source.json').read_text())
RED=['Ground arcade | %s'%n for n in ('orange brick','burnt red brick','warm red brick','salmon brick')]
GREY=['Arcade pier | %s'%n for n in ('slate brick','smoke grey brick','brown grey brick')]
BED='Ground arcade | warm red pointing'
GREY_BED='Arcade pier | grey pointing'
LIMESTONE='Arcade pier | pale base'
CAP='Arcade pier | terracotta cap'
LIP='Ground arcade | light terracotta lip'
APRON='Left enclosure | grey rendered sill wall'
IRON='Left grille | warm grey painted steel'
WOOD='Left enclosure | chalk painted wood'
GLASS='Left enclosure | shaded glazing'
HOOD='Left steel awning | weathered blue'
RIDGE='Left steel awning | blue crests'

def finish(rgb,rough=.86,metal=0):
    s=np.array(rgb)/255.
    return dict(color=np.where(s<=.04045,s/12.92,((s+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={k:finish(v) for k,v in zip(RED+GREY,[(167,80,50),(153,68,44),(176,87,55),(182,94,61),(85,87,83),(95,96,87),(98,92,82)])}
PALETTE.update({BED:finish((179,131,98)),GREY_BED:finish((161,155,140)),LIMESTONE:finish((192,181,159)),CAP:finish((169,83,52)),LIP:finish((193,116,75)),APRON:finish((162,154,135)),IRON:finish((169,165,143),.67,.25),WOOD:finish((205,196,167),.78),GLASS:finish((50,62,61),.35,.14),HOOD:finish((71,102,137),.68,.17),RIDGE:finish((94,129,154),.67,.18)})

DEFAULT_LAYOUT=json.loads((HERE.parent/'measurements/ground-arcade-camera.json').read_text())

def _point(u,v,y,layout):
    layout=layout or DEFAULT_LAYOUT
    if layout and 'ground_photo_xyz' in layout:
        return np.asarray(layout['ground_photo_xyz'](float(u),float(v),float(y)),float)
    # A project may supply one plane or a perspective camera with finite depth.
    if layout and 'ground_camera_P' in layout:
        p=np.asarray(layout['ground_camera_P'],float)
        q=np.linalg.solve(p[:,[0,2,3]]+np.outer(p[:,1],[0,0,y]),[u,v,1.])
        return np.array((q[0]/q[2],y,q[1]/q[2]))
    raise ValueError('Ground arcade requires the common ground_camera_P or ground_photo_xyz')

def _arc(row,fraction,theta):
    rx,rz=np.array(row['intrados'])+fraction*(np.array(row['outer'])-row['intrados'])
    u,v=row['spring']
    return np.column_stack((u+rx*np.cos(theta)+row['crest_shift']*np.sin(theta),v-rz*np.sin(theta)))

def _field(poly,y,layout):
    points=[_point(u,v,y,layout)[[0,2]] for u,v in poly.exterior.coords]
    return Polygon(points,[[tuple(_point(u,v,y,layout)[[0,2]])for u,v in ring.coords]for ring in poly.interiors])

def _prism(b,label,poly,front,back,mat,layout):
    if poly.is_empty or poly.area<.03:return
    b.prism(_field(poly,front,layout),-back,-front,lambda x,z,d:(x,-d,z),mat,label)

def _uvbox(b,label,ub,vb,front,back,mat,layout):
    _prism(b,label,box(min(ub),min(vb),max(ub),max(vb)),front,back,mat,layout)

def _sector(row,inner,outer,start,stop,steps):
    a=np.linspace(start,stop,steps+1)
    return Polygon(np.vstack((_arc(row,outer,a),_arc(row,inner,a[::-1]))))

def openings(layout=None,outer=False):
    """Three X/Z through-cuts. Outer=True follows the outside of the brick rings."""
    result=[]
    for i,row in enumerate(DATA['arches']):
        arch=_arc(row,float(outer),np.linspace(np.pi,0,65))
        feet=[(arch[-1,0],1128),(arch[0,0],1128)]
        uv=Polygon([*arch,*feet])
        if outer:
            uv=uv.intersection(box(DATA['piers'][i]['axis'],790,DATA['piers'][i+1]['axis'],1130))
        result.append(_field(uv,0,layout))
    return result

def _joints(band):
    measured=DATA['joint_samples']['middle_'+band+'_degrees']
    nominal=float(np.median(np.diff(measured)))
    west=np.linspace(0,measured[0],round(measured[0]/nominal)+1)[:-1]
    east=np.linspace(measured[-1],180,round((180-measured[-1])/nominal)+1)[1:]
    return np.deg2rad(np.r_[west,measured,east])

def _rings(b,layout,lod):
    for i,row in enumerate(DATA['arches']):
        name='Arcade '+row['label']; mask=box(DATA['piers'][i]['axis'],788,DATA['piers'][i+1]['axis'],925)
        collar=_sector(row,0,1.,0,np.pi,80).intersection(mask)
        _prism(b,name+' mortar and intrados',collar,-.032,.35,BED,layout)
        _prism(b,name+' outer course pointing',_sector(row,.71,1.,0,np.pi,76).intersection(mask),-.045,-.028,BED,layout)
        for band,lo,hi,face in [('inner',.012,.71,-.042),('outer',.727,.975,-.054)]:
            limits=_joints(band)
            for j,(a,z) in enumerate(zip(limits,limits[1:])):
                # Short stretchers and full radial bricks alternate in the inner course.
                pieces=[(lo,hi)]
                if band=='inner' and j%2==1:pieces=[(lo,.332),(.348,hi)]
                for part,(r,s) in enumerate(pieces):
                    piece=_sector(row,r,s,a+.0036,z-.0036,1 if lod else 2).intersection(mask)
                    if piece.is_empty or piece.geom_type!='Polygon' or piece.area<.25:continue
                    material=RED[(j*7+i*3+part+j//9)%len(RED)]
                    _prism(b,f'{name} {band} {j+1:02d}.{part+1}',piece,face,-.014,material,layout)
        # The narrow bright outside roll is visible across the crown of each arch.
        _prism(b,name+' outer lip',_sector(row,.973,1,0,np.pi,46).intersection(mask),-.064,-.040,LIP,layout)

def _piers(b,layout,lod):
    for i,row in enumerate(DATA['piers']):
        u=row['axis']; width=row['width']; peak=row['head_width']; tag=f'Arcade pier {i+1}'
        def front(label,w,top,base,front,depth,mat):
            _uvbox(b,tag+' '+label,[u-w/2,u+w/2],[top,base],front,depth,mat,layout)
        front('stone foot',width+6,1096.5,1127,-.039,.39,LIMESTONE)
        front('mortar shaft',width,958.5,1097,0,.355,GREY_BED)
        # The directly readable second pier has 28 courses from base to neck;
        # two warm courses form the stripe below midheight.
        n=28; heights=np.linspace(959,1097,n+1)
        unit=21.0
        for c,(v0,v1) in enumerate(zip(heights,heights[1:])):
            left=u-width/2;right=u+width/2
            joints=np.arange(left-(.5 if c%2 else 0)*unit,right+unit,unit)
            for j,(a,z) in enumerate(zip(joints,joints[1:])):
                a=max(left,a+.42);z=min(right,z-.42)
                if z-a<.75:continue
                colors=RED if 1029<(v0+v1)/2<1041 else GREY
                mat=colors[(i+c+j)%len(colors)]
                _uvbox(b,f'{tag} brick {c+1:02d}.{j+1}',(a,z),(v0+.36,v1-.38),-.012,.014,mat,layout)
            # The right return is visible alongside the front face of each central pier.
            # Continue those same bed joints onto the side with alternate half bricks.
            side_u=u+width/2
            a=_point(side_u,v0+.36,0,layout);z=_point(side_u,v1-.38,0,layout)
            low,high=sorted((a[2],z[2]))
            seams=[.006,.197,.349] if c%2 else [.006,.103,.302,.349]
            for k,(near,far) in enumerate(zip(seams,seams[1:])):
                length=far-near-.006
                if length<=0:continue
                mat=(RED if 1029<(v0+v1)/2<1041 else GREY)[(c+i+k)%3]
                b.box((a[0]+.002,(near+far)/2,(low+high)/2),(.018,length,high-low),mat,
                      label=f'{tag} return {c+1:02d}.{k+1}')
        for part,(top,base,wide,depth) in enumerate([(922,925,1,-.095),(925,929,.94,-.076),(929,933,.86,-.068),(933,937,.80,-.052),(937,946,.76,-.043),(946,952,.73,-.036),(952,956,.78,-.052),(956,959,.73,-.039)]):
            front(f'cap step {part+1}',peak*wide,top,base,depth,.355,CAP if part%2 else RED[2])
        for j in range(7):
            left=u-peak*.39+(j+.18)*peak*.78/7
            _uvbox(b,f'{tag} dentil {j+1}',(left,left+peak*.057),(930.0,934.5),-.089,-.051,RED[1],layout)

def _grille(b,layout,lod):
    g=DATA['grille']; yf=-.30
    def tube(label,uv,r=.014,y=yf,material=IRON):
        b.tube([_point(u,v,y,layout) for u,v in uv],r,material,5 if lod else 8,label)
    for name,r in [('inner',g['inner_radii']),('outer',g['radii'])]:
        a=np.linspace(0,np.pi,26 if lod else 44)
        points=np.array(g['hub'])+np.c_[r[0]*np.cos(a),-r[1]*np.sin(a)]
        tube('Grille fan '+name+' round',points,.013)
    hub=np.array(g['hub']);rad=np.array(g['inner_radii'])
    for j,pt in enumerate(g['spoke_tip_uv']):
        d=np.array(pt)-hub;start=hub+d/max(1.,np.linalg.norm(d/rad))
        tube(f'Grille fan spoke {j+1}',[start,pt],.0125)
    top=np.array(g['hood_front'])
    for i,u in enumerate(g['bars_u']):
        v=float(np.interp(u,top[:,0],top[:,1]))
        # No through-bar crosses the small fan: this zone is articulated by spokes.
        upper=879 if 325<=u<=418.9 else v+1.
        tube(f'Grille front upright {i+1}',[(u,upper),(u,g['lower_v'])],.011 if i not in (0,15) else .017)
    for j,v in enumerate(g['rails_v']):
        tube(f'Grille horizontal rail {j+1}',[(301,v),(476.1,v)],.0125)
    for side,(u,v,ub,vb) in enumerate([(300.8,846.8,309.2,843.8),(476.1,880.7,487.2,876.7)]):
        for k,z in enumerate([v,926,976,g['lower_v']]):
            pts=[_point(u,z,yf,layout),_point(ub,z+vb-v,-.015,layout)]
            b.tube(pts,.014,IRON,5 if lod else 8,f'Grille return {side+1} rail {k+1}')
        for j in range(1,4):
            t=j/3;pt=[]
            for z in [v,g['lower_v']]:
                pt.append((1-t)*_point(u,z,yf,layout)+t*_point(ub,z+vb-v,-.015,layout))
            b.tube(pt,.012,IRON,5 if lod else 8,f'Grille return {side+1} upright {j}')
    # One continuous folded sheet, with strips running parallel to its fall on each break.
    fore=np.array(g['hood_front']);back=np.array(g['hood_back'])
    for j in range(3):
        rails=[]
        for t in np.linspace(0,1,max(3,round(np.linalg.norm(fore[j+1]-fore[j])/(7 if lod else 4)))):
            uv=(1-t)*fore[j]+t*fore[j+1]; buv=(1-t)*back[j]+t*back[j+1]
            p=_point(*uv,yf-.025,layout);q=_point(*buv,-.011,layout)
            rails.append((p,q))
        for k,(r,s) in enumerate(zip(rails,rails[1:])):
            face=np.array([r[0],s[0],s[1],r[1]]);normal=np.cross(face[1]-face[0],face[2]-face[0]);normal/=np.linalg.norm(normal)
            if normal[2]<0:face=face[::-1];normal=-normal
            vertices=np.vstack((face,face-normal*.012))
            b.add(vertices,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],HOOD,f'Blue steel hood plane {j+1}.{k+1}')
            if not lod or k%2==0:b.tube(r,.012,RIDGE,6,f'Blue hood folded seam {j+1}.{k+1}')
    w=g['secondary_window'];x0,x1,top_v,bottom=w['bounds'];spring=w['spring_v'];c=(x0+x1)/2
    a=np.linspace(0,np.pi,40);arch=np.c_[c+(x1-x0)/2*np.cos(a),spring-(spring-top_v)*np.sin(a)]
    field=Polygon([*arch,(x0,bottom),(x1,bottom)])
    _uvbox(b,'Enclosure rendered apron',(x0,x1),(bottom,1126.8),.145,.34,APRON,layout)
    _uvbox(b,'Enclosure lower sill',(x0-1,x1+1),(bottom-1,bottom+3),.086,.20,WOOD,layout)
    _prism(b,'Grille window shaded glazing',field,.15,.17,GLASS,layout)
    _prism(b,'Grille window pale arched outer frame',field.difference(field.buffer(-4.3)),.105,.149,WOOD,layout)
    for i,u in enumerate(w['visible_mullions_u']):
        v=spring-(spring-top_v)*np.sqrt(1-((u-c)/((x1-x0)/2))**2)
        _uvbox(b,f'Grille window stile {i+1}',(u-2.4,u+2.4),(v+1,bottom-1),.10,.151,WOOD,layout)
    for i,v in enumerate(w['crossrails_v']):
        _uvbox(b,f'Grille window horizontal {i+1}',(x0+2,x1-2),(v-1.8,v+1.8),.095,.153,WOOD,layout)

def add_ground_arcade(b,lod=False,layout=None):
    """Build the three ring arches, piers, and the enclosed left opening."""
    simple=lod is True or lod=='lod'
    first=len(b.parts)
    _rings(b,layout,simple)
    _piers(b,layout,simple)
    _grille(b,layout,simple)

    if simple:
        # Preserve through-joints in the distant mesh and group like bricks by bay.
        group={}
        keep=[]
        for item in b.parts[first:]:
            name=item['label']
            if (' brick ' in name or ' return ' in name or ' inner ' in name or ' outer ' in name) and item['material'] in RED+GREY:
                prefix=' '.join(name.split()[:3]) if name.startswith('Arcade pier') else ' '.join(name.split()[:2])
                key=(prefix,item['material'])
                vertices,faces=group.setdefault(key,([],[]))
                offset=len(vertices);vertices.extend(item['vertices'])
                faces.extend([a+offset,b0+offset,c+offset]for a,b0,c in item['triangles'])
            else:keep.append(item)
        b.parts[first:]=keep
        for (prefix,material),(vertices,faces) in group.items():
            b.parts.append(dict(label=prefix+' | '+material.split(' | ')[1],material=material,vertices=vertices,triangles=faces))
