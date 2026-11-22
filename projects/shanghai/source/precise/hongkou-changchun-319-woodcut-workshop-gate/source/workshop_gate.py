"""Reconstruct the street gate of No. 319 from the September 2021 and March 2023 views."""
from pathlib import Path
import json
import numpy as np

HOME=Path(__file__).resolve().parent
FIT=json.loads((HOME.parent/'measurements/gate-camera-fit.json').read_text())
LETTERS=json.loads((HOME/'sign-contours.json').read_text())
D=FIT['dimensions']
P=np.asarray(FIT['views'][0]['P'])
SAND='Piers | limestone-coloured cap'
BASE='Piers | warm pale plinth'
MORTAR='Piers | light mortar'
BRICKS=['Piers | fired brick '+str(i+1) for i in range(4)]
GATE='Leaves | reddish brown painted finish'
EDGES='Leaves | dark frame edges'
SIDE='Leaves | darker angled faces'
WHITE='Left plaque | pale enamel'
COPPER='Right plaque | brown stone'
BLACK='Lettering | dark finish'
GOLD='Right plaque | pale engraved lettering'
PALETTE={name:{'color':color,'roughness':r} for name,color,r in [
 (SAND,[.72,.69,.62],.91),(BASE,[.58,.53,.47],.9),(MORTAR,[.52,.43,.35],.92),
 *[(n,col,.91) for n,col in zip(BRICKS,[[.280,.101,.069],[.236,.080,.050],[.327,.128,.083],[.254,.092,.067]])],
 (GATE,[.195,.055,.033],.65),(EDGES,[.111,.035,.023],.61),(SIDE,[.134,.041,.028],.65),
 (WHITE,[.68,.72,.70],.48),(COPPER,[.166,.083,.058],.56),(BLACK,[.038,.030,.023],.58),(GOLD,[.68,.57,.40],.59)]}
BOX=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]

def xz(u,v,y):
    hom=P[:,[0,2,3]].copy();hom[:,2]+=y*P[:,1]
    h=np.linalg.solve(hom,[u,v,1]);return h[0]/h[2],h[1]/h[2]

def rectangular_loop(x0,x1,y0,y1,z):
    return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]

def add_gate(b,lod,layout=None):
    """Positive X is right in the street portrait, positive Y enters the courtyard."""
    layout=layout or {};scale=float(layout.get('course_height',.064))/.064
    offset=np.asarray(layout.get('gate_origin',(0.,0.,0.)),float)
    far=lod is True or lod=='lod';b.palette.update(PALETTE)
    def add(xyz,tri,material,label):
        verts=np.array(xyz,dtype=float)
        if 'leaf_angles_degrees' in layout and (label.startswith(('280 |','left leaf')) or label.startswith(('441 |','right leaf'))):
            left=label.startswith(('280 |','left leaf'));pivot_uv=281 if left else 525
            pivot=np.array([xz(pivot_uv,320,.36)[0],.36])
            angle=np.deg2rad(layout['leaf_angles_degrees'][0 if left else 1])*(1 if left else -1)
            rot=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
            verts[:,:2]=(verts[:,:2]-pivot)@rot.T+pivot
        b.add((verts*scale+offset).tolist(),tri,material,label=label)
    def cube(x0,x1,y0,y1,z0,z1,material,label):
        add(rectangular_loop(x0,x1,y0,y1,z0)+rectangular_loop(x0,x1,y0,y1,z1),BOX,material,label)
    gap,depth,base,over=(D[k]for k in ('clear_width','depth','plinth_top','cap_overhang'))
    head=base+28*.064;crest=head+D['cap_height']
    for post,x0,x1 in [('left',-gap/2-D['left_width'],-gap/2),('right',gap/2,gap/2+D['right_width'])]:
        cube(x0-.012,x1+.012,-.008,depth+.008,0,base,BASE,post+' | plinth')
        cube(x0+.007,x1-.007,.008,depth-.008,base-.002,head+.002,MORTAR,post+' | mortar core')
        # Stretchers and half-bond returns have separate front and side faces on each course.
        batches={m:([],[]) for m in BRICKS}
        for n in range(28):
            z0=base+n*.064+.003;z1=z0+.0564
            for side,length in enumerate((x1-x0,depth,x1-x0,depth)):
                bond=.239;start=-bond/2 if (n+side)%2 else 0
                j=0
                while start+j*bond<length:
                    left=max(0,start+j*bond);right=min(length,start+(j+1)*bond);j+=1
                    if right-left<.012:continue
                    a,bx=left+.0035,right-.0035
                    if side==0:rect=(x0+a,x0+bx,-.004,.007)
                    elif side==1:rect=(x1-.006,x1+.004,a,bx)
                    elif side==2:rect=(x1-bx,x1-a,depth-.007,depth+.004)
                    else:rect=(x0-.004,x0+.006,depth-bx,depth-a)
                    mat=BRICKS[(17*n+5*j+side*3+n*j)%4 if not far else (n+side)%2]
                    verts,faces=batches[mat];i=len(verts)
                    verts.extend(rectangular_loop(*rect,z0)+rectangular_loop(*rect,z1));faces.extend([[i+k for k in f]for f in BOX])
        for mat,(v,t)in batches.items():
            if v:add(v,t,mat,post+' | running bond '+mat[-1])
        # Stepped, bevelled course and upper projecting slab are continuous on the visible returns.
        profile=[(head,.027),(head+.045,.027),(head+.050,.012),
                 (head+.242,.012),(head+.253,.031),(head+.276,.043),(head+.290,.043),
                 (head+.306,.062),(head+.327,.066),(head+.351,.072),(head+.362,.090),
                 (head+.397,.090),(head+.419,over),(crest-.030,over),(crest,over-.007)]
        if far:profile=[profile[i]for i in (0,1,3,5,8,10,11,12,13,14)]
        verts=[];faces=[[0,2,1],[0,3,2]]
        for k,(height,e) in enumerate(profile):
            verts+=rectangular_loop(x0-e,x1+e,-e,depth+e,height)
            if k:
                for j in range(4):
                    a=(k-1)*4+j;c=(k-1)*4+(j+1)%4;faces.extend([[a,c,c+4],[a,c+4,a+4]])
        n=len(verts)-4;faces.extend([[n,n+1,n+2],[n,n+2,n+3]])
        add(verts,faces,SAND,post+' | stepped stone-coloured cap')
    # The two leaves meet off-centre. Four independent folded fins leave three visible slots.
    leaf_y=.36
    def face_box(u0,u1,vtop,vbottom,y0,y1,mat,label):
        x0,z1=xz(u0,vtop,y0);x1,z0=xz(u1,vbottom,y0)
        if vbottom>=484:z0=max(.002,z0)
        cube(x0,x1,y0,y1,z0,z1,mat,label)
    for a,c in ((280,440),(441,527)):
        for lo,hi,vt,vb,lab in [(a,a+4,149,491,'left stile'),(c-4,c,149,491,'right stile'),(a+4,c-4,149,155,'top bar'),(a+4,c-4,484,491,'bottom bar')]:
            face_box(lo,hi,vt,vb,leaf_y,leaf_y+.045,EDGES,str(a)+' | '+lab)
    for j,(u0,u1) in enumerate([(290,321),(327,359),(363,393),(399,431)]):
        x0,z1=xz(u0,154,leaf_y+.019);x1,z0=xz(u1,483,leaf_y+.019)
        verts=[];faces=[]
        # Flat lip and angled folded panel follow the alternating light and dark vertical faces.
        loop=[(x0,leaf_y+.075),(x0+.014,leaf_y+.076),(x1,leaf_y+.020),(x1,leaf_y+.004),(x0+.017,leaf_y+.057),(x0,leaf_y+.057)]
        for z in (z0,z1):verts += [(x,y,z)for x,y in loop]
        n=len(loop)
        # Each folded sheet is composed of its two closed convex bends.
        for poly,mat in [([0,1,4,5],SIDE),([1,2,3,4],GATE)]:
            vs=[verts[i]for i in poly]+[verts[i+n]for i in poly]
            add(vs,BOX if np.cross(np.array(vs[1])-vs[0],np.array(vs[3])-vs[0])[2]>0 else [t[::-1]for t in BOX],mat,'left leaf | folded fin '+str(j+1))
    face_box(447,522,155,483,leaf_y+.022,leaf_y+.052,GATE,'right leaf | full panel')
    for q,mat,tag in [((141,254,169,263,-.024,-.004),WHITE,'left | civic plaque'),((548,670,166,252,-.036,-.003),COPPER,'right | memorial plaque')]:
        face_box(*q,mat,tag)
    def letter(ch,left,right,top,bottom,y,mat,label):
        x0,z1=xz(left,top,y);x1,z0=xz(right,bottom,y);g=LETTERS[ch]
        uv=np.array(g['v']);t=np.array(g['f']);n=len(uv)
        front=np.column_stack([x0+(x1-x0)*uv[:,0],np.full(n,y),z0+(z1-z0)*uv[:,1]]);back=front.copy();back[:,1]+=.00125
        v=np.vstack([front,back]);faces=t.tolist()+(t[:,::-1]+n).tolist();edges={}
        for tri in t:
            for a,c in zip(tri,np.roll(tri,-1)):
                key=tuple(sorted((a,c)));edges[key]=None if key in edges else (a,c)
        for edge in edges.values():
            if edge:
                a,c=edge;faces.extend([[a,a+n,c+n],[a,c+n,c]])
        add(v,faces,mat,label)
    for i,ch in enumerate('木刻講習會'):
        u,v=[(487,236),(486,278),(486,322),(486,365),(486,409)][i]
        letter(ch,u-14,u+14,v-13,v+13,leaf_y+.0208,BLACK,'right leaf | '+ch)
    def text(line,l,r,top,bottom,y,mat,prefix):
        step=(r-l)/len(line)
        for j,ch in enumerate(line):
            if ch!=' ':letter(ch,l+j*step,l+(j+.82)*step,top,bottom,y,mat,prefix+ch)
    text('优秀历史建筑',160,235,182,190,-.0252,BLACK,'left | heading ')
    if not far:text('HERITAGE ARCHITECTURE',160,236,192,197,-.0252,BLACK,'left | English ')
    text('木刻讲习所旧址',580,648,188,196,-.0372,GOLD,'right | heading ')
    # The dated photograph resolves a pale square. No present-day scannable code is reconstructed.
    face_box(651,666,228,244,-.0376,-.0362,GOLD,'right | square marker')
