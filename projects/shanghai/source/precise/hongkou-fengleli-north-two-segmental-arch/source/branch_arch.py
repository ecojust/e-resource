"""Fengleli North Two passage, depicted in Xiangzi G's 2016 account of the lanes."""
from pathlib import Path
from math import pi, sin, cos
import numpy as np
from shapely.geometry import Polygon,box
from PIL import Image,ImageDraw
ID='hongkou-fengleli-north-two-segmental-arch'
GREY='Blue-grey brick with pale mortar'; RED='Orange-red fired brick'; BURNT='Dark fired red brick'; LIP='Projecting dark red brick edge'
STONE='Pale cement key border'; INSET='Pale grey recessed key panel'; BAND='Horizontal terracotta course'; MORTAR='Recessed warm mortar'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(GREY,[1,1,1],.92),(RED,[.616,.299,.196],.91),(BURNT,[.517,.229,.147],.89),(LIP,[.462,.184,.134],.89),(STONE,[.775,.773,.739],.97),(INSET,[.604,.624,.632],.96),(BAND,[.578,.272,.167],.92),(MORTAR,[.532,.349,.271],.96)]}
SPRING=.76
def texture():
    f=Path(__file__).with_name('blue-grey-brick.png')
    if not f.exists():
        rng=np.random.default_rng(663);im=Image.new('RGB',(600,300),(153,155,152));d=ImageDraw.Draw(im)
        for row in range(25):
            for i in range(-1,17):
                x=i*39+(row%2)*19;z=row*12
                col=np.array([88,94,98])+rng.integers(-10,10)+rng.integers(-3,4,3)
                d.rectangle([x+1,z+1,x+37,z+10],fill=tuple(col.tolist()))
        a=np.array(im,dtype='float')+rng.normal(0,3,(300,600,1));Image.fromarray(a.clip(0,255).astype('uint8')).save(f)
    PALETTE[GREY]['texture']=str(f)
def arc(radius,rise,n):
    return [(radius*cos(a),SPRING+rise*sin(a)) for a in np.linspace(0,pi,n+1)]
def inner(radius,rise,n):
    return Polygon([(-radius,-.1),(radius,-.1)]+arc(radius,rise,n))
def sector(ri,hi,ro,ho,a,b,n):
    return Polygon([(r*cos(t),SPRING+h*sin(t))for r,h,aa,bb in [(ri,hi,a,b),(ro,ho,b,a)] for t in np.linspace(aa,bb,n)])
def add_building(b,far=False):
    texture();n=28 if far else 68
    def form(p,d,e,m,k):b.prism(p,d,e,lambda x,z,y:(x,-y,z),m,k)
    def rect(l,r,a,c,d,e,m,k):form(box(l,a,r,c),d,e,m,k)
    passage=inner(1.55,.71,n);outer=inner(2.04,1.25,n)
    form(box(-2.41,0,2.41,2.12).difference(passage),-.55,-.085,GREY,'Original through-passage, leaving the interior fully open')
    form(box(-2.41,0,2.41,2.12).difference(outer),-.09,0,GREY,'Grey header and side-wall faces')
    for side in (-1,1):
        l,r=sorted([1.55*side,2.04*side])
        rect(l,r,0,SPRING,-.09,0,GREY,'Brick jamb returning into passage')
        for bottom,high in ((.13,.20),(.21,.26),(.62,.68),(.685,.752)):
            a,c=sorted((side*1.55,side*2.41))
            rect(a,c,bottom,high,-.015,.014,BAND,'Continuation of the red horizontal bands in grey brickwork')
    form(sector(1.55,.71,2.04,1.25,0,pi,n),-.54,.008,MORTAR,'Full-depth bed behind individual red arch bricks')
    count=27 if far else 51
    for i in range(count):
        a=pi*i/count+.0019;c=pi*(i+1)/count-.0019
        for lo,lh,hi,hh,d,m in [(1.55,.71,1.78,.953,.032,RED),(1.791,.961,2.04,1.25,.047,BURNT if i%6==0 else RED)]:
            form(sector(lo,lh,hi,hh,a,c,3 if far else 4),-.545,d,m,'Radial arch brick across the curved soffit')
    form(sector(2.012,1.231,2.071,1.280,0,pi,n),.015,.093,LIP,'Projecting outer brick edging')
    key=Polygon([(-.176,1.520),(.171,1.520),(.202,2.087),(-.204,2.087)])
    inset=box(-.139,1.600,.137,2.032)
    form(key.difference(inset),-.09,.128,STONE,'Pale raised frame at the crown')
    form(inset,-.080,.103,INSET,'Recessed panel in keystone')
    for part in b.parts:
        if part['material']==GREY:part['texcoords']=[[(x+2.41)/4.82,z/2.12] for x,y,z in part['vertices']]
