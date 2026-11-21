"""Photograph-based exterior of the museum's French vertical recording barometer, ca. 1850.

The cabinet height is one model unit. Change the object's scene scale as a
whole if a catalogue measurement becomes available. Coordinates are X right,
Y toward the back of the cabinet, Z up. All finishes and the chart are original.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon

SOURCE=Path(__file__).resolve().parent
GRAPH='Ivory recording paper'
WOOD='Polished reddish case wood'
TRIM='Beaded wood edges'
DARK='Recessed cabinet back'
SILVER='Silvered corrugated face'
BRASS='Aged yellow metal'
EDGE='Polished brass edges'
IRON='Blackened fittings'
GLASS='Cabinet glass'
WIDTH=.56
DEPTH=.236

def material(rgb,roughness,metal=0.,**kwargs):
    c=np.array(rgb)/255.
    linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    return dict(color=linear.tolist(),roughness=roughness,metallic=metal,**kwargs)

def chart_image(path):
    width,height=384,896
    # Original grid derived from the visible grid pitch; the pressure trace is illegible.
    rng=np.random.default_rng(396)
    tone=rng.normal(0,1.05,(height,width,1))
    pixels=np.uint8(np.clip(np.array([239,228,194])+tone,0,255))
    img=Image.fromarray(pixels,'RGB')
    draw=ImageDraw.Draw(img)
    for x in range(9,width,18):
        draw.line(((x,0),(x,height)),fill=(216,204,178),width=1)
    for y in range(6,height,21):
        draw.line(((0,y),(width,y)),fill=(216,201,171),width=1)
    img.save(path,optimize=True)

def palette(image):
    return {WOOD:material((106,51,31),.40),TRIM:material((145,76,43),.39),
            DARK:material((61,38,29),.64),SILVER:material((185,180,157),.34,.65),
            BRASS:material((157,113,54),.39,.68),EDGE:material((189,150,75),.31,.74),
            IRON:material((73,61,47),.42,.60),GLASS:material((185,202,191),.22,.05,alpha=.060),
            GRAPH:dict(color=[1,1,1],texture=str(image),roughness=.88)}

def add_barometer(b,lod=False):
    def box(x,y,z,w,d,h,mat,label):
        b.box((x,y,z),(w,d,h),mat,label=label)
    def tube(points,r,mat,label,sides=10):
        b.tube(points,r,mat,sides if not lod else min(7,sides),label)
    def ring_box(y,z,width,height,edge,depth,mat,tag):
        for sign in (-1,1):
            box(sign*(width-edge)/2,y,z,edge,depth,height,mat,tag+' upright')
            box(0,y,z+sign*(height-edge)/2,width-2*edge,depth,edge,mat,tag+' rail')
    def xz_plate(points,y0,y1,mat,label):
        b.prism(Polygon(points),-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)
    def rod_x(xmin,xmax,y,z,r,mat,label):
        n=18 if not lod else 10
        vertices=[(x,y+r*math.cos(i*math.tau/n),z+r*math.sin(i*math.tau/n))for x in (xmin,xmax)for i in range(n)]
        faces=[(i,(i+1)%n,n+(i+1)%n,n+i)for i in range(n)]
        faces.extend([tuple(reversed(range(n))),tuple(range(n,2*n))]);b.add(vertices,faces,mat,label)

    # A dark side panel, stepped door and a clear glass sheet enclose the mechanism.
    box(0,DEPTH/2,.024,WIDTH,DEPTH,.048,WOOD,'Case / base')
    box(0,DEPTH/2,.983,WIDTH,DEPTH,.034,WOOD,'Case / cap')
    box(0,DEPTH-.009,.504,WIDTH-.017,.018,.93,DARK,'Case / recessed lining')
    for side in (-1,1):
        box(side*(WIDTH-.017)/2,.118,.505,.017,.222,.922,WOOD,'Case / side boards')
    ring_box(.004,.501,WIDTH,.974,.030,.023,WOOD,'Case / face frame')
    ring_box(-.008,.505,WIDTH-.048,.918,.014,.014,TRIM,'Door / raised bead')
    ring_box(-.003,.505,WIDTH-.074,.893,.012,.008,DARK,'Door / inside rebate')
    box(0,.009,.508,WIDTH-.087,.002,.870,GLASS,'Door / front glass')
    box(0,.018,.090,WIDTH-.084,.049,.046,TRIM,'Door / raised sill')
    # Bail and hinged brass fittings on the cabinet top.
    for x in (-.075,.075):
        box(x,.120,1.004,.031,.042,.008,BRASS,'Cap / handle shoes')
    points=[(.075*math.cos(t),.120,1.013+.036*math.sin(t)) for t in np.linspace(0,math.pi,13 if lod else 25)]
    tube(points,.0055,IRON,'Cap / arched carrying handle')
    for x in (-.185,.185):
        box(x,.178,1.005,.036,.025,.009,BRASS,'Cap / keeper plates')
        tube([(x-.009,.170,1.009),(x-.005,.170,1.016),(x+.006,.170,1.016),(x+.012,.170,1.009)],.002,IRON,'Cap / keeper loops')
    box(0,.043,1.002,.092,.027,.004,BRASS,'Cap / inset tablet')

    # Concentric corrugations form one turned surface. The central upright remains in front.
    cx,cz=.041,.767
    n=54 if lod else 108
    def turned(profile,mat,label):
        vertices=[(cx+r*math.cos(t*math.tau/n),y,cz+r*math.sin(t*math.tau/n)) for r,y in profile for t in range(n)]
        faces=[(i*n+j,(i+1)*n+j,(i+1)*n+(j+1)%n,i*n+(j+1)%n) for i in range(len(profile)-1) for j in range(n)]
        b.add(vertices,faces,mat,label)
    turned([(.001,.144),(.040,.141),(.051,.143)],SILVER,'Instrument / central mounting face')
    profile=[(.051,.143)]
    for k in range(6):
        r=.052+k*.0132
        profile.extend([(r,.142),(r+.004,.134),(r+.008,.138),(r+.012,.145)])
    turned(profile,SILVER,'Instrument / six traced corrugations')
    turned([(profile[-1][0],profile[-1][1]),(.135,.148),(.139,.148),(.140,.151)],
           SILVER,'Instrument / terminal rim')
    box(cx,.135,.771,.022,.022,.262,BRASS,'Instrument / vertical guide')
    support=[(cx-.026,.897),(cx+.016,.897),(cx+.021,.740),(cx+.032,.671),
             (cx+.044,.657),(cx+.065,.651),(cx+.066,.596),(cx-.066,.596),
             (cx-.066,.647),(cx-.045,.663),(cx-.037,.700)]
    xz_plate(support,.109,.125,BRASS,'Instrument / shouldered front support')
    for x in (cx-.055,cx+.054):
        tube([(x,.137,.619),(x,.094,.605),(x,.070,.594)],.0055,EDGE,'Instrument / tray braces')
    box(cx,.064,.594,.226,.016,.030,BRASS,'Instrument / rectangular maker tablet')
    box(cx,.054,.609,.225,.005,.003,EDGE,'Instrument / tablet lip')
    for x in (cx-.102,cx+.102):
        box(x,.054,.594,.004,.004,.004,IRON,'Instrument / tablet fasteners')

    # The visible profile winds over the upper roller and drops to a smaller lower return.
    left,right=-.092,.146
    rod_x(left-.012,right+.012,.116,.486,.055,IRON,'Recorder / upper drum')
    rod_x(left-.015,right+.013,.068,.156,.024,IRON,'Recorder / lower roller')
    rod_x(right+.010,right+.024,.116,.486,.073,BRASS,'Recorder / drum cheek')
    rod_x(right+.020,right+.034,.116,.486,.025,EDGE,'Recorder / spindle boss')
    rod_x(left-.015,left-.007,.068,.156,.029,EDGE,'Recorder / lower bearings')
    rod_x(right+.010,right+.019,.068,.156,.029,EDGE,'Recorder / lower bearings')
    for x in [left-.012,right+.014]:
        box(x,.140,.302,.010,.024,.286,BRASS,'Recorder / side standards')
    track=[(.116+.070*math.cos(t),.484+.070*math.sin(t))
           for t in np.linspace(math.pi*.52,math.pi*1.04,13 if lod else 31)]
    track+=[(.045,.345),(.052,.255),(.047,.169)]
    track+=[(.068+.023*math.cos(t),.156+.023*math.sin(t))
            for t in np.linspace(math.pi*.90,math.pi*1.48,7 if lod else 14)]
    length=[0.]
    for p,q in zip(track,track[1:]):length.append(length[-1]+math.dist(p,q))
    vs=[];uv=[];fs=[]
    for i,(y,z) in enumerate(track):
        vs.extend([(left,y,z),(right,y,z)]);uv.extend([(0.,1.-length[i]/length[-1]),(1.,1.-length[i]/length[-1])])
        if i:fs.append((2*i-2,2*i,2*i+1,2*i-1))
    b.add(vs,fs,GRAPH,'Recorder / continuous ruled paper strip')
    b.parts[-1]['texcoords']=uv
    tube([(left+.029,.085,.576),(left+.039,.067,.558),(left+.049,.075,.550)],.0026,IRON,'Recorder / visible stylus bracket')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--project',type=Path,default=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),Path.cwd()))
    opt=parser.parse_args()
    sys.path.insert(0,str(opt.project/'source/precise/hongkou-general-post-office/source/common'))
    from photo_architecture import Builder
    chart=opt.output.parent/'recording-paper.png'
    chart.parent.mkdir(exist_ok=True,parents=True)
    if not chart.exists():chart_image(chart)
    b=Builder(palette(chart));add_barometer(b,opt.lod)
    reference=SOURCE/'museum-reference.json'
    if not reference.is_file():reference=SOURCE.parent/'museum-reference.json'
    ref=json.loads(reference.read_bytes())
    b.save(opt.output,dict(id='xuhui-zikawei-museum-french-vertical-barometer',name='上海气象博物馆藏法国垂直气压计',
        museum=ref['museum'],object_date='约1850年',object_origin='法国',category='馆藏气象观测仪器',
        model_unit='展示比例；木柜正面高度定义为1，实物高度未获测量。',geometry_license='MIT',
        photo_embedded=False,copyright='Original exhibit geometry and chart texture, MIT. Historical reference photograph credited to 杨阳.',
        source_article=ref['article']['url'],source_photo=ref['photo']['img'],reference_sha256=ref['photo']['sha256']))
if __name__=='__main__':main()
