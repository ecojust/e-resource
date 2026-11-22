"""Four red-brown sashes and interlocking tile courses from the Yuyuan Road roof."""
from math import sin, pi

def material(rgb, roughness=.82, metalness=0):
    def linear(n):
        return n / 3294.6 if n <= 10 else ((n/255+.055)/1.055)**2.4
    return dict(color=[linear(n) for n in rgb],roughness=roughness,metallic=metalness)

PALETTE={
    'clay russet':material((149,92,72)), 'clay red':material((163,100,75)),
    'clay dark':material((123,83,69)), 'clay sun':material((173,117,86)),
    'clay inset':material((108,77,65)), 'creamy reveal':material((214,205,185)),
    'painted frame':material((117,71,61)), 'sash brown':material((137,80,67)),
    'steel glazing bar':material((98,72,64),.6,.15),
    'blue grey glass':material((149,174,176),.35,.12),
    'warm grey glass':material((162,174,170),.35,.12),
    'weathered eave':material((85,69,63)), 'pale sill':material((188,180,161))}
TILES=('clay russet','clay red','clay russet','clay dark','clay sun','clay red')

def prism(b,front,back,mat,label):
    length=len(front)
    faces=[tuple(range(length-1,-1,-1)),tuple(range(length,length*2))]
    faces.extend((i,(i+1)%length,(i+1)%length+length,i+length) for i in range(length))
    b.add(front+back,faces,mat,label)

def box(b,x0,x1,y0,y1,z0,z1,mat,label):
    face=[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)]
    prism(b,face,[(x,y1,z)for x,y,z in face],mat,label)

def slope(z):
    return .08+z*.43

def field_segment(b,x0,x1,z0,z1,d0,d1,mat,label):
    surface=[(x0,slope(z0)+d0,z0),(x1,slope(z0)+d0,z0),(x1,slope(z1)+d0,z1),(x0,slope(z1)+d0,z1)]
    prism(b,surface,[(x,y+d1-d0,z)for x,y,z in surface],mat,label)

def tile(b,x0,x1,z0,z1,c,r,lod):
    if x1-x0<.035:return
    samples=5 if lod else 10
    front=[];back=[];faces=[]
    for line,z in enumerate((z0,z0+.022,z1)):
        for i in range(samples+1):
            t=i/samples
            depth=slope(z)-.021*sin(pi*t)**2-.028*(1-t)**5+(.013 if line==0 else 0)
            front.append((x0+(x1-x0)*t,depth,z));back.append((x0+(x1-x0)*t,depth+.035,z))
    cols=samples+1;n=len(front)
    for j in range(2):
        for i in range(samples):
            k=j*cols+i
            faces.extend([(k,k+1,k+1+cols,k+cols),(k+n+cols,k+n+1+cols,k+n+1,k+n)])
    outline=list(range(cols))+[2*cols-1]+list(range(3*cols-1,2*cols-1,-1))+[cols]
    for k,i in enumerate(outline):
        nxt=outline[(k+1)%len(outline)]
        faces.append((i,nxt,n+nxt,n+i))
    b.add(front+back,faces,TILES[(c*13+r*3+c*r)%len(TILES)],f'roof course {r+1:02} clay pan {c+2:02}')

def add_building(b,lod=False):
    for c,(lo,hi,zb,zt) in enumerate([(-2.16,-1.52,0,1.98),(1.52,2.16,0,1.98),(-1.52,1.52,0,.41),(-1.52,1.52,1.63,1.98)]):
        field_segment(b,lo,hi,zb,zt,.045,.092,'clay inset',f'cut tiled slope section {c+1}')
    pitch=.232;rise=.188
    for r in range(11):
        low=r*rise;high=min(1.98,low+rise+.018)
        if high<=low:continue
        for c in range(-1,20):
            left=max(-2.16,-2.16+(c+.19*(r%2))*pitch);right=min(2.16,-2.16+(c+1+.19*(r%2))*pitch-.005)
            if right-left<.03:continue
            for start,end in [(low,min(high,.405)),(max(low,1.637),high)]:
                if end-start>.027:tile(b,left,right,start,end,c,r,lod)
            start=max(.405,low);end=min(1.637,high)
            if end-start>.027:
                for x0,x1 in [(left,min(-1.52,right)),(max(1.52,left),right)]:
                    if x1-x0>.035:tile(b,x0,x1,start,end,c,r,lod)
    for side,x in [('left',-1.52),('right',1.32)]:
        face=[(x,.108,.394),(x,.108,1.66),(x,slope(1.66)+.06,1.66),(x,slope(.394)+.06,.394)]
        prism(b,face,[(px+.20,y,z)for px,y,z in face],'creamy reveal',side+' deep dormer reveal')
    box(b,-1.52,1.52,.065,.38,.39,.455,'pale sill','projecting pale sill')
    box(b,-1.52,1.52,.084,.86,1.574,1.652,'weathered eave','shadow lip beneath dormer head')
    for name,z0,z1 in [('bottom',.452,.526),('top',1.509,1.574)]:
        box(b,-1.32,1.32,.128,.227,z0,z1,'painted frame',name+' continuous timber rail')
    for j in range(5):
        x=-1.284+j*.642
        box(b,x-.036,x+.036,.128,.225,.452,1.574,'painted frame',f'painted structural jamb {j+1}')
    for c in range(4):
        left=-1.248+c*.642;right=left+.570;middle=(left+right)/2
        for label,a,z,x0,x1 in [('sill',.526,.546,left,right),('head',1.488,1.509,left,right),('left',.546,1.488,left,left+.019),('right',.546,1.488,right-.019,right)]:
            box(b,x0,x1,.147,.208,a,z,'sash brown',f'sash {c+1} {label}')
        box(b,middle-.01,middle+.01,.161,.205,.546,1.488,'steel glazing bar',f'sash {c+1} central narrow glazing bar')
        for row,z in enumerate((.860,1.172)):
            box(b,left+.019,right-.019,.159,.207,z-.01,z+.01,'steel glazing bar',f'sash {c+1} horizontal glazing bar {row+1}')
        for row,(zb,zt) in enumerate([(.546,.850),(.870,1.162),(1.182,1.488)]):
            for half,(a,end) in enumerate([(left+.019,middle-.01),(middle+.01,right-.019)]):
                mat='warm grey glass' if (row+2*c+half)%4==0 else 'blue grey glass'
                box(b,a,end,.2,.214,zb,zt,mat,f'sash {c+1} glazing light {row+1}-{half+1}')
    box(b,-2.17,2.17,.028,.23,-.09,0,'weathered eave','lower eave and gutter edge')
