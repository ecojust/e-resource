"""Openwork parapet of the White Hall in Ye Garden, interpreted from the 2015 front photograph."""
from shapely.geometry import box
from shapely.ops import unary_union

def material(rgb, roughness):
    def linear(c):
        s=c/255.0
        return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
    return {'color':[linear(c) for c in rgb],'roughness':roughness}
PALETTE={
    'painted parapet':material((214,213,202),.84),
    'cap weathering':material((191,188,174),.88),
    'light edge':material((225,223,209),.78),
    'recessed tablet':material((201,200,188),.87),
    'stone footing':material((164,159,145),.91),
}
PIERS=(-1.63,1.63)
REPEAT=.435
CENTRES=[REPEAT*(i-2.5) for i in range(6)]

def add_building(b,lod=False):
    def cube(label,x0,x1,y0,y1,z0,z1,mat):
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
    def stock(label,x0,x1,levels,mat):
        """Give both front and rear of a horizontal moulding its stepped profile."""
        vs=[]
        for z,d in levels:
            vs.extend([(x0,-d,z),(x1,-d,z),(x1,d,z),(x0,d,z)])
        fs=[(3,2,1,0)]
        for i in range(len(levels)-1):
            for j in range(4):
                k=(j+1)%4
                fs.append((4*i+j,4*i+k,4*i+4+k,4*i+4+j))
        n=len(vs);fs.append((n-4,n-3,n-2,n-1));b.add(vs,fs,mat,label)
    cube('continuous terrace footing',-1.93,1.93,-.207,.207,0,.065,'stone footing')
    stock('low sill',-1.91,1.91,[(.065,.184),(.104,.184),(.123,.168)] if not lod else [(.065,.184),(.123,.167)],'light edge')
    cube('lower panel plinth',-1.39,1.39,-.105,.105,.123,.247,'painted parapet')
    # Adjacent repeats alternate high and low connecting bridges and leave through-openings.
    for j,x in enumerate(CENTRES):
        left=x-REPEAT/2;right=x+REPEAT/2
        width=.065
        parts=[box(left,.245,left+width,.905),box(x-width/2,.245,x+width/2,.905),
               box(left+width,.68,x-width/2,.744),box(x+width/2,.395,right,.457)]
        b.prism(unary_union(parts),-.091,.091,lambda u,z,d:(u,-d,z),'painted parapet','openwork repeat '+str(j+1))
    for i,sign in enumerate([-1,1]):
        a,c=sorted([sign*1.389,sign*(3*REPEAT)])
        cube('end return web '+str(i+1),a,c,-.091,.091,.245,.905,'painted parapet')
    stock('continuous soffit and crown',-1.93,1.93,[(.898,.124),(.931,.124),(.945,.151),(.967,.159),(.988,.164),(1.012,.17)] if not lod else [(.898,.124),(.935,.124),(1.012,.17)],'light edge')
    stock('weathered top ledge',-1.93,1.93,[(1.012,.171),(1.052,.171),(1.064,.155)] if not lod else [(1.012,.171),(1.064,.159)],'cap weathering')
    # The front rectangles inside each square end pier are relieved in the plaster.
    for j,x in enumerate(PIERS):
        name='left' if j==0 else 'right'
        stock(name+' pier foot',x-.282,x+.282,[(.066,.205),(.185,.205),(.207,.185)] if not lod else [(.066,.205),(.207,.185)],'painted parapet')
        cube(name+' pier shaft',x-.24,x+.24,-.154,.154,.201,.899,'painted parapet')
        for side in (-1,1):
            label=name+(' front' if side==-1 else ' rear')
            rings=[(.187,.303,.619,.154),(.186,.304,.618,.174),(.163,.328,.595,.189),(.152,.342,.581,.180)]
            if lod:rings=[rings[0],rings[-1]]
            vs=[]
            for half,low,high,depth in rings:
                vs.extend([(x-half,side*depth,low),(x+half,side*depth,low),(x+half,side*depth,high),(x-half,side*depth,high)])
            fs=[]
            for q in range(len(rings)-1):
                for k in range(4):
                    l=(k+1)%4;f=(4*q+k,4*q+l,4*q+4+l,4*q+4+k);fs.append(f if side<0 else f[::-1])
            b.add(vs,fs,'light edge',label+' bevelled tablet frame')
            a,c=sorted([side*.154,side*.161]);cube(label+' inset panel',x-.149,x+.149,a,c,.344,.579,'recessed tablet')
        stock(name+' small overhanging capital',x-.264,x+.264,[(.839,.169),(.853,.177),(.861,.187),(.884,.193),(.91,.198)] if not lod else [(.839,.169),(.91,.198)],'light edge')

