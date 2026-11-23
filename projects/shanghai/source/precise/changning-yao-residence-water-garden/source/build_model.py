"""Build the photographically recorded corner of the water garden at Yao Residence."""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.geometry import box as rectangle

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder as ArchitectureBuilder
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
sys.path.insert(0,str(HERE))
from crown_builder import CrownBuilder
import garden_finishes

MEASUREMENTS = HERE.parent/'measurements'
HOUSE_ID = 'changning-yao-residence-water-garden'
EAVE, ROOF, WOOD = 'Yao | painted cream soffit','Yao | dark olive roof fascia','Yao | russet window frame'
GLASS, SCREEN, CURTAIN = 'Yao | garden glass','Yao | pale horizontal screen','Yao | pale drapery'
STONE, RECESS, WATER = 'Yao | terrace stone','Yao | shaded interior','Yao | shallow garden water'
AC, FAN = 'Yao | existing ivory unit','Yao | condenser grilles'
PALETTE = {EAVE:{'color':[.70,.65,.45],'roughness':.85},ROOF:{'color':[.14,.145,.093]},
           WOOD:{'color':[.24,.074,.033],'roughness':.49},GLASS:{'color':[.22,.32,.29],'alpha':.38,'roughness':.20,'metallic':.12},
           SCREEN:{'color':[.76,.74,.68],'roughness':.85},CURTAIN:{'color':[.59,.64,.59],'roughness':.96},
           STONE:{'color':[.36,.33,.26],'roughness':.85},RECESS:{'color':[.07,.075,.055],'roughness':.94},
           WATER:{'color':[.15,.19,.135],'roughness':.19,'metallic':.14},
           AC:{'color':[.67,.655,.58],'roughness':.64},FAN:{'color':[.23,.22,.16],'roughness':.66}}

PALETTE.update(garden_finishes.PALETTE)
ID=HOUSE_ID
META={'id':ID,'name':'淮阴路姚氏住宅水庭转角长窗与水平格栅','address':'上海市长宁区淮阴路200号西郊宾馆4号楼',
      'heritage_id':'sh-historic-b1-036','official_id':'1M001','geometry_license':'MIT','texture_license':'MIT',
      'viewer_page':'yao-residence-water-garden.html','photos_embedded':False,
      'camera_views':json.loads((HERE/'cameras.json').read_bytes()),
      'source':'https://wenhui.whb.cn/third/yidian/201907/11/276235.html',
      'photo_source':'https://news.sina.cn/2017-09-16/detail-ifykyfwq7849691.d.html?vt=4',
      'scope':'Photographic section of the two glazed garden walls, horizontal screens, joined eaves and stone pool. The inner room, unseen building wings, guest hotel and other buildings lie outside this study.'}

class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in garden_finishes.STEMS:
            garden_finishes.metric_uv(self.parts[-1])

    def save(self,path,metadata=None):
        ArchitectureBuilder.save(self,path,metadata)
        return garden_finishes.writer.embed_normals(path)


def flat(builder, polygon, bottom, top, material, label):
    builder.prism(polygon,bottom,top,lambda x,y,z:(x,y,z),material,label)


class WindowPlane:
    def __init__(self,builder,kind,xcorner,sill,head):
        self.b=builder; self.kind=kind; self.corner=xcorner;self.sill=sill;self.head=head
        self.existing_stiles=set()

    def solid(self,left,right,bottom,top,out,depth,material,name):
        mid=(left+right)/2;z=(bottom+top)/2
        if self.kind=='back':
            center=[mid,-out,z];size=[right-left,depth,top-bottom]
        else:
            center=[self.corner+out,mid,z];size=[depth,right-left,top-bottom]
        self.b.box(center,size,material,label=f'{self.kind} / {name}')

    def glazing(self,lo,hi,divisions,transom,name,curtain=False):
        zs,zh=self.sill,self.head
        self.solid(lo,hi,zs,zh,-.09,.025,GLASS,name+' glass')
        self.solid(lo,hi,zs,zh,-.45,.045,CURTAIN if curtain else RECESS,name+' inner shade')
        for label,h in [('sill',zs),('head',zh),('rail',transom)]:
            self.solid(lo,hi,h-.023,h+.023,.01,.092,WOOD,name+' '+label)
        for i,t in enumerate([0.,*divisions,1.]):
            x=lo+(hi-lo)*t
            axis=round(x,7)
            if axis in self.existing_stiles:continue
            self.existing_stiles.add(axis)
            self.solid(x-.021,x+.021,zs+.023,zh-.023,.01,.09,WOOD,name+f' stile {i+1}')
        if curtain:
            # Woven folds are behind the glass. Relief is independent of the photo colours.
            for i in range(1,14):
                x=lo+(hi-lo)*i/14
                self.solid(x-.009,x+.009,zs+.06,zh-.08,-.396,.045,CURTAIN,'pale curtain fold')

    def screen(self,left,right,profile,lod):
        for k,(bottom,top) in enumerate(profile):
            self.solid(left,right,bottom,top,.098,.21,SCREEN,f'open screen bar {k+1}')
        for p in (.04,.96):
            q=left+(right-left)*p
            self.solid(q-.032,q+.032,0,self.head,-.12,.09,WOOD,'upright behind screen')
        # In both photographs green and amber are visible in the gaps.
        self.solid(left,right,self.sill,self.head,-.265,.023,GLASS,'glazing visible through screen')

    def units(self,left,right,lod):
        width=right-left
        for index,(bottom,top) in enumerate(((.36,1.32),(1.43,2.37))):
            self.solid(left+.07,right-.015,bottom,top,.12,.28,AC,'existing stacked condenser '+str(index+1))
            for h in (bottom+.23,bottom+.68):
                u=(left+right)/2
                seg=12 if lod else 28
                ring=[(u+.17*math.cos(t*math.tau/seg),h+.17*math.sin(t*math.tau/seg))for t in range(seg)]
                self.b.prism(Polygon(ring),.260,.273,lambda x,z,d:(x,-d,z),FAN,'condenser fan disc')
                if not lod:
                    for j in range(-2,3):
                        offset=j*.047;dy=math.sqrt(.17**2-offset**2)
                        self.solid(u+offset-.007,u+offset+.007,h-dy,h+dy,.28,.009,AC,'fan grille rib')


def ellipse(pool,factor,n):
    x,y=pool['center_xy'];a,b=pool['radii'];ang=pool['rotation_rad']
    curve=[]
    for i in range(n):
        t=math.tau*i/n;u=factor*a*math.cos(t);v=factor*b*math.sin(t)
        curve.append((x+u*math.cos(ang)-v*math.sin(ang),y+u*math.sin(ang)+v*math.cos(ang)))
    return curve


def add_building(b,lod=False):
    survey=json.loads((MEASUREMENTS/'garden-cameras.json').read_bytes())
    sections=json.loads((MEASUREMENTS/'garden-sections.json').read_bytes())
    a=survey['axes_m'];xc=survey['corner_x_m'];zs=survey['sill_m'];zh=survey['opening_head_m']
    eave=survey['eave_top_m'];lip=survey['eave_face_height_m'];projection=survey['eave_projection_m']
    xr=a['court-pier-right']+1.17;yf=a['return-glazing-outer']
    outer_screen=sections['outer_screen']
    back=WindowPlane(b,'back',xc,zs,zh);side=WindowPlane(b,'return',xc,zs,zh)
    back.glazing(xc,a['court-dark-left'],[],.61,'shadowed inside corner')
    back.glazing(a['court-dark-left'],0,[],.61,'narrow dark light')
    back.glazing(0,a['court-white-right'],[],.60,'wide interior curtain',True)
    back.glazing(a['court-white-right'],a['court-red-right'],[.29,.55,.79],.62,'red garden opening')
    back.glazing(a['court-red-right'],a['court-pier-left'],[],.61,'narrow pane behind units')
    back.units(a['court-red-right'],a['court-pier-left'],lod)
    back.screen(a['court-pier-left'],a['court-pier-right'],sections['back_bands_bottom_to_top'],lod)
    back.glazing(a['court-pier-right'],xr,[.48],.62,'part of next glazed opening')
    # Only the four ends clear of the foreground tree are photographically grounded.
    side.screen(outer_screen['observed_interval_y'][0],yf,outer_screen['bands'],lod)
    side.glazing(yf,a['return-pier-outer'],[.34,.67],.64,'three-part garden return')
    side.screen(a['return-pier-outer'],a['return-pier-inner'],sections['return_bands_bottom_to_top'],lod)
    side.glazing(a['return-pier-inner'],0,[.23,.47,.7,.87],.62,'corner return glazing')
    yf=outer_screen['observed_interval_y'][0]
    for wall,left,right in [(back,xc,xr),(side,yf,0)]:
        wall.solid(left,right,-.025,zs,-.04,.24,WOOD,'continuous red plinth')
        wall.solid(left,right,zh,eave-lip+.008,-.08,.19,EAVE,'cream lintel over glazed openings')
    # The two survey panels meet continuously at the real re-entrant corner.
    # Their inner boundary is a section cut, not a claim about the back of the house.
    roof=unary_union([rectangle(xc-.97,-projection,xr,1.0),rectangle(xc-.97,yf,xc+projection,1.0)])
    # Both published photographs constrain a very shallow rise along the back wing.
    # The external return meets the same corner profile and stays level past it.
    edges=sections['back_roof_edges']
    for lo,hi,mat,name in [('bottom','dark_soffit',EAVE,'continuous cream canopy and soffit'),
                           ('dark_soffit','top',ROOF,'dark top edge of garden eaves')]:
        def map_roof(x,y,d):
            location=max(x,xc+projection)
            def height(k):
                if k=='bottom':return eave-lip
                edge=edges[k]
                return edge['intercept']+edge['slope']*location
            return x,y,(1-d)*height(lo)+d*height(hi)
        # Split the polygons at the longitudinal bend so every face is planar.
        joint=xc+projection
        for zone in [rectangle(xc-1.05,yf-.1,joint,1.1),rectangle(joint,yf-.1,xr+.1,1.1)]:
            b.prism(roof.intersection(zone),0.,1.,map_roof,mat,name)
    terrace=unary_union([rectangle(xc-.65,-.72,xr,.60),rectangle(xc-.65,yf,xc+.72,.60)])
    flat(b,terrace,-.18,-.025,STONE,'narrow garden terrace at the glazed sill')
    pool=sections['pool'];n=48 if lod else 96
    outer=ellipse(pool,1.,n);inner=ellipse(pool,.960,n)
    flat(b,Polygon(outer,[inner]),pool['rim_z_m']-.16,pool['rim_z_m'],STONE,'oval garden pool raised stone rim')
    flat(b,Polygon(inner),pool['rim_z_m']-.15,pool['rim_z_m']-.115,WATER,'shallow water below the rim')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',required=True,type=Path);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args()
    builder=Builder(PALETTE);add_building(builder,args.lod)
    print(builder.save(args.output,META)['sha256'])
