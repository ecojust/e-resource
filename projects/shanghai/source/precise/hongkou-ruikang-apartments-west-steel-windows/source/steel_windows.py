"""Sichuan North Road elevation, on the apartment block across from the Shanghai General Post Office."""
from math import floor

COLOURS = {
    'red common brick': (157,83,66), 'burnt brick': (144,73,59),
    'light fired brick': (168,92,73), 'brick joint': (116,75,64),
    'painted render': (200,184,160), 'sill stone': (164,150,133),
    'painted steel': (69,65,60), 'heavy steel transom': (68,56,49),
    'grey blue glass': (88,110,118), 'pale reflected glass': (100,121,125),
}
def linear(c):
    c /= 255.
    return c / 12.92 if c < .04045 else ((c+.055)/1.055)**2.4
PALETTE={name:{'color':[linear(c) for c in col],
               'roughness': .36 if 'glass' in name else .91}
         for name,col in COLOURS.items()}
CENTRES=(-1.48,0.,1.48)
WIDTHS=(.76,1.20,.76)
HALF=2.26
SILL=1.02
HEAD=2.71
TOP=3.18
def box(b,name,mat,x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)
def pier(b,index,left,right,lod):
    name=f'Brick pier {index}'
    box(b,name+' body','brick joint',left,right,-.069,.26,0,TOP)
    levels=36
    rise=TOP/levels
    colours=('red common brick','burnt brick','red common brick','light fired brick')
    step=.234
    for row in range(levels):
        z0=row*rise+.004
        z1=(row+1)*rise-.004
        if lod:
            # The distant mesh keeps the raked bed joints and the alternating
            # reveals at the corners. The intermediate per-brick headers merge.
            box(b,f'{name} continuous course {row+1}',colours[(row//4+index)%4],
                left,right,-.083,-.067,z0,z1)
            continue
        cursor=left-step/2*(row%2)
        col=0
        while cursor<right:
            a=max(left,cursor+.0035); e=min(right,cursor+step-.0035)
            if e>a+.006:
                box(b,f'{name} course {row+1} stretcher {col+1}',
                    colours[(row*7+col*5+index)%4],a,e,-.083,-.067,z0,z1)
            cursor+=step;col+=1
    # The outer pilasters have a raised narrow band. The two inner brick piers
    # have plain faces in the street observations.
    if index in (0,3):
        bx=(left+right)/2
        for k in range(36 if not lod else 18):
            count=36 if not lod else 18
            box(b,f'{name} projecting brick band {k+1}','red common brick',
                bx-.055,bx+.055,-.112,-.079,k*TOP/count+.003,(k+1)*TOP/count-.003)
def window(b,idx,cx,width,lod):
    x0,x1=cx-width/2,cx+width/2;colcount=6 if idx==1 else 3
    name=f'Window {idx+1}'
    box(b,name+' rendered apron','painted render',x0,x1,-.009,.23,0,SILL-.039)
    box(b,name+' sill','sill stone',x0,x1,-.062,.20,SILL-.040,SILL+.018)
    box(b,name+' wall over opening','painted render',x0,x1,-.012,.23,HEAD,TOP)
    box(b,name+' brick soldier lintel core','brick joint',x0-.025,x1+.025,-.090,.25,HEAD,HEAD+.153)
    n=round((width+.05)/.061);step=(width+.05)/n
    for k in range(n):
        l=x0-.025+k*step
        box(b,f'{name} header soldier {k+1}','burnt brick' if k%5==2 else 'red common brick',
            l+.0028,l+step-.0028,-.107,-.089,HEAD+.008,HEAD+.146)
    box(b,name+' projecting lintel edge','burnt brick',x0-.038,x1+.038,-.126,.08,HEAD+.148,HEAD+.18)
    for a in (x0,x1-.032):
        box(b,name+' steel jamb','painted steel',a,a+.032,.067,.160,SILL+.018,HEAD)
    for z in (SILL+.018,HEAD-.032):
        box(b,name+' perimeter horizontal','painted steel',x0,x1,.067,.16,z,z+.032)
    xa=x0+.032;xb=x1-.032;za=SILL+.05;zb=HEAD-.032
    for k in range(colcount):
        a=xa+(xb-xa)*k/colcount;e=xa+(xb-xa)*(k+1)/colcount
        for j in range(6):
            z=za+(zb-za)*j/6;h=za+(zb-za)*(j+1)/6
            box(b,f'{name} pane {k+1}/{j+1}', 'pale reflected glass' if (2*k+j+idx)%6==0 else 'grey blue glass',
                a,e,.150,.160,z,h)
            if not lod:
                box(b,f'{name} steel glazing bead {k+1}/{j+1}','painted steel',a+.004,a+.011,.119,.146,z+.012,h-.012)
    for k in range(1,colcount):
        a=xa+(xb-xa)*k/colcount
        box(b,name+' vertical glazing bar '+str(k),'painted steel',a-.009,a+.009,.089,.15,za,zb)
    for j in range(1,6):
        z=za+(zb-za)*j/6
        strong=j==4;half=.026 if strong else .008
        box(b,name+' horizontal glazing bar '+str(j),'heavy steel transom'if strong else 'painted steel',
            xa,xb,.074 if strong else .100,.150,z-half,z+half)
def add_building(b,lod=False):
    left=-HALF
    for i,(cx,wi)in enumerate(zip(CENTRES,WIDTHS)):
        pier(b,i,left,cx-wi/2,lod);window(b,i,cx,wi,lod);left=cx+wi/2
    pier(b,3,left,HALF,lod)
