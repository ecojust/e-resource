"""Draw the original campus comparison from independent plan coordinates and frozen source shapes."""
from pathlib import Path
import json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np

HERE=Path(__file__).resolve().parent
review=json.loads((HERE.parents[2]/'source/precise/huangpu-ruijin-guesthouse-01/footprint-review.json').read_bytes())
frame=review['author_frame'];h=math.radians(frame['runtime_heading_deg']);c,s=math.cos(h),math.sin(h)
lon,lat=frame['anchor']['lng'],frame['anchor']['lat'];k=frame['earth_radius_m']*math.cos(math.radians(lat))
def from_wgs(points):
    pts=np.asarray(points);e=np.radians(pts[:,0]-lon)*k;n=(np.arcsinh(np.tan(np.radians(pts[:,1])))-math.asinh(math.tan(math.radians(lat))))*k
    return np.column_stack((e*c-n*s,e*s+n*c))
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
fig,ax=plt.subplots(figsize=(8.2,6.5));ax.set_facecolor('#f5f3e9')
names={'historical main block':('1号楼主宅','#b77d66'),'west linked arm':('栋间廊','#ced2c4'),
       'separate 2':('2号楼','#ccc6b9'),'separate central hotel':('后建酒店主体','#d7d4cb'),
       'southwest extension':('附属体','#ded9cd')}
for key,(name,color) in names.items():
    pts=from_wgs(review['survey_alignment']['street_block_plan'][key]['wgs'])+np.array([1.1,-4.0])
    ax.fill(pts[:,0],pts[:,1],facecolor=color,edgecolor='#645844',lw=1.15)
    centroid=pts.mean(axis=0)
    if key=='historical main block':centroid+=(0,5)
    if key=='separate central hotel':centroid=np.array([41.,-35.8])
    ax.text(*centroid,name,fontproperties=font,fontsize=11,ha='center',va='center',color='#32291f')
for row in review['owners']:
    i=row['local_id']
    if i not in [1250,2335,799,3003]:continue
    pts=np.asarray(row['geometry_model_xy_m'])
    linecolor='#812d27'if i in [1250,2335]else'#567767'
    ax.plot(pts[:,0],pts[:,1],color=linecolor,linestyle='--',lw=1.6)
    u,v=pts.mean(axis=0)
    if i==2335:ax.annotate(str(i),xy=(u,v),xytext=(u-7,v-3.3),fontsize=9,arrowprops=dict(arrowstyle='-',color=linecolor),color=linecolor)
    else:ax.text(u,v,str(i),color=linecolor,fontsize=8,ha='center')
ax.text(1,-18,'北侧庭院',fontproperties=font,fontsize=12,ha='center',color='#60674c')
ax.annotate('N',xy=(-21,-28),xytext=(-17,-18),ha='center',arrowprops={'arrowstyle':'-|>','lw':1.4,'color':'#4d574c'})
ax.plot([28,38],[21,21],lw=2,c='#4d574c');ax.text(33,20.3,'10 m',ha='center',va='bottom',fontsize=9)
ax.set_xlim(-26,53);ax.set_ylim(27,-42);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
ax.set_title('瑞金宾馆1号楼与庭院周边',fontproperties=font,fontsize=17,pad=12)
fig.text(.5,.021,'实色为归属总平面轮廓，虚线为城市已有轮廓。坐标取近似配准。',fontproperties=font,fontsize=9,ha='center')
fig.savefig(HERE/'site-plan.png',dpi=155,bbox_inches='tight')
