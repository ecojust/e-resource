#!/usr/bin/env python3
"""Render the original placement diagram; uses no reference imagery pixels.
Needs matplotlib + shapely and Noto Sans CJK available in the build environment.
"""
from pathlib import Path
import json,math,hashlib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Polygon as Patch
from shapely.geometry import shape,Polygon
from shapely.ops import transform
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'projects/shanghai';R=P/'data/audit/global-model-integration-v1';j=json.load(open(P/'data/global-models/chongming-placement.json'));a=json.load(open(R/'chongming-placement.json'));lon,lat=j['coordinate_frame']['anchor_wgs84'];co=math.cos(math.radians(lat));rad=6378137;ft=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
def en(lon1,lat1):return [(lon1-lon)*math.pi/180*rad*co,(lat1-lat)*math.pi/180*rad]
def patches(ax,g,**kw):
 for p in [g] if isinstance(g,Polygon) else g.geoms:
  ax.add_patch(Patch(list(p.exterior.coords),**kw))
fig,ax=plt.subplots(figsize=(12,10));patches(ax,transform(en,shape(a['source_feature']['geometry'])),facecolor='#c7c7c7',edgecolor='#555555',linewidth=1.2);patches(ax,transform(en,shape(a['clearance']['geometry'])),facecolor='#f4ead2',edgecolor='#ab7423',linewidth=1.2)
labels=[]
for i,r in enumerate(j['records'],1):
 g=transform(en,shape(r['collision_geometry']));patches(ax,g,facecolor='#7eafba',edgecolor='#22566b',linewidth=.7);x,y=en(r['lng'],r['lat']);ax.text(x,y,str(i),fontsize=8,ha='center',va='center',color='#102e3e');labels.append(f"{i:02d} {r['id'].removeprefix('chongming-')}")
ax.text(-48,53,'N ↑',fontsize=13);ax.text(44,35,'保留：东北合院等\n基线余体示意',fontproperties=ft,ha='center',fontsize=10);ax.text(-36,21,'保留：\n西轴余体',fontproperties=ft,ha='center',fontsize=10)
ax.plot([-40,-20],[-91,-91],color='black',lw=2);ax.text(-30,-95,'20 m',ha='center');ax.set_aspect('equal');ax.set_xlim(-55,70);ax.set_ylim(-101,67);ax.set_xlabel('East (m)');ax.set_ylabel('North (m)');ax.set_title('崇明学宫：20件全局模型近似布局与有界源遮挡',fontproperties=ft,fontsize=15);ax.grid(alpha=.14)
fig.text(.715,.80,'蓝色：候选保守外包\n米色：主轴／东轴清除区\n灰色：保留的原源余体\n\n位置与旋转为估计，非测绘。\n只开放全局俯瞰直达。\n无院内漫游验收。',fontproperties=ft,fontsize=11,va='top');fig.text(.715,.56,'\n'.join(labels),fontsize=8.8,va='top');fig.text(.12,.02,'地图轮廓：© OpenStreetMap contributors · ODbL-1.0；模型外包与近似位置由本项目编制',fontproperties=ft,fontsize=8);fig.subplots_adjust(right=.7,top=.93,bottom=.09);fig.savefig(R/'chongming-layout.png',dpi=135);plt.close(fig)
