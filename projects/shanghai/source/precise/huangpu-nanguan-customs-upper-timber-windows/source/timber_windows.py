"""Street-facing pair at the former Jianghainan Customs Office, 348 Waima Road.

The June 2016 photograph records a green transom on the right and an oxblood
one on the left. Heights and depths estimate the proportions of this photograph.
"""
def paint(r,g,b,roughness=.75):
    def lin(v):
        x=v/255
        return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
    return dict(color=[lin(v) for v in (r,g,b)],roughness=roughness,metallic=0)
PALETTE={k:paint(*rgb) for k,rgb in {
    'limewash':(187,193,193),'dark red jamb':(75,43,34),'oxblood sash':(104,51,42),
    'lighter timber arris':(122,64,50),'green transom':(42,76,65),'green arris':(60,90,75),
    'aged putty':(90,66,54),'left dark glass':(55,62,62),'muted glass':(67,72,68),
    'smoky green glass':(61,75,71),'glass reflected sky':(83,91,92),
    'sill top':(180,178,165),'shaded sill fascia':(145,146,138),
    'sub-sill shadow':(124,126,118),'lintel fillet':(154,160,156)}.items()}
def extrusion(b,name,x1,x2,profile,material):
    n=len(profile);v=[(x,y,z)for x in (x1,x2)for y,z in profile]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    f.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
    b.add(v,f,material,name)
def block(b,name,x1,x2,y1,y2,z1,z2,m):
    extrusion(b,name,x1,x2,[(y1,z1),(y2,z1),(y2,z2),(y1,z2)],m)
def add_building(b,lod=False):
    spans=[(-1.42,-.47),(.47,1.42)];bottom=.31;top=2.32
    for i,(x1,x2,z1,z2)in enumerate([(-1.68,1.68,0,bottom),(-1.68,1.68,top,2.54),(-1.68,-1.42,bottom,top),(-.47,.47,bottom,top),(1.42,1.68,bottom,top)]):
        block(b,'plaster wall '+str(i),x1,x2,0,.20,z1,z2,'limewash')
    for a,z,depth in [(0,2.456,.018),(1,2.497,.030)]:
        block(b,'fillet below eaves '+str(a),-1.68,1.68,-depth,.002,z,z+.015,'lintel fillet')
    for wi,(lo,hi) in enumerate(spans):
        label=('left' if wi==0 else 'right');mid=(lo+hi)/2;split=1.59
        for i,(a,c)in enumerate([(lo,lo+.052),(hi-.052,hi),(mid-.024,mid+.024)]):
            block(b,label+' outer jamb '+str(i),a,c,.018,.158,bottom,top,'dark red jamb')
        for i,(z,t)in enumerate([(bottom,.052),(split-.03,.06),(top-.05,.05)]):
            block(b,label+' outer rail '+str(i),lo,hi,.016,.142,z,z+t,'dark red jamb')
        for upper,(z0,z1)in enumerate([(bottom+.046,split-.025),(split+.027,top-.046)]):
            for side,(x0,x1)in enumerate([(lo+.045,mid-.020),(mid+.020,hi-.045)]):
                n=f'{label} section {upper}-{side}';m='green transom' if wi and upper else 'oxblood sash'
                for x in (x0,x1-.036):block(b,n+' stile',x,x+.036,.039,.101,z0,z1,m)
                for z in (z0,z1-.037):block(b,n+' rail',x0,x1,.039,.102,z,z+.037,m)
                if not lod:
                    for x in (x0+.028,x1-.036):block(b,n+' profiled edge',x,x+.008,.033,.042,z0+.035,z1-.034,'green arris' if m=='green transom' else 'lighter timber arris')
                a=x0+.037;c=x1-.037;bot=z0+.038;t=z1-.038
                sx=(a+c)/2;sz=(bot+t)/2
                block(b,n+' slender vertical bar',sx-.008,sx+.008,.065,.111,bot,t,m)
                if not upper:block(b,n+' lower horizontal bar',a,c,.064,.111,sz-.010,sz+.010,m)
                for col,(x,y)in enumerate([(a,sx),(sx,c)]):
                    for j,(z,v)in enumerate([(bot,sz),(sz,t)]if not upper else [(bot,t)]):
                        glass=('left dark glass','smoky green glass','muted glass','glass reflected sky')[(wi*2+upper+side+col+j)%4]
                        block(b,n+f' pane {col}-{j}',x,y,.110,.121,z,v,glass)
                        if not lod: block(b,n+' lower putty lip',x,y,.095,.112,z,z+.007,'aged putty')
        extrusion(b,label+' sloped stone sill',lo-.060,hi+.060,[(-.103,.253),(.079,.258),(.079,.321),(-.103,.292)],'sill top')
        block(b,label+' outer sill bevel',lo-.056,hi+.056,-.096,-.031,.231,.260,'shaded sill fascia')
        block(b,label+' sill underside',lo-.046,hi+.046,-.071,.009,.223,.243,'sub-sill shadow')
