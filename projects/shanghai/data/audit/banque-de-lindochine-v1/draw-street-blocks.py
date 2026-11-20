"""Draw the actual parcels and road centerlines in a north-up working plan."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
records = json.loads((PROJECT/'source/precise/huangpu-banque-de-lindochine/footprint-review.json').read_bytes())
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
fig,ax=plt.subplots(figsize=(8,8))
ax.set_facecolor('#f9f6ed')
for road in records['map_crosscheck']['roads'].values():
    pts=road['geometry_local_m']
    ax.plot([-p[1]for p in pts],[p[0]for p in pts],color='#ecddc1',linewidth=3,solid_capstyle='round')
for q in records['owners']:
    points=q['geometry_model_xy_m']
    i=q['local_id'];xs=[-p[1]for p in points];ys=[p[0]for p in points]
    fill={2037:'#bd9981',1332:'#a4b8b1',833:'#b4b1aa'}.get(i,'#e0ddd4')
    ax.fill(xs,ys,facecolor=fill,edgecolor='#827b71',lw=.8)
ax.plot([0,0],[-10.965,10.965],lw=3.5,color='#8b3427')
for x,y,s in [(-32,0,'29号  东方汇理银行'),(-33,-24,'格林邮船大楼'),(-32,-39,'北京东路'),(-29,-64,'27号  怡和洋行'),(15,4,'中\n山\n东\n一\n路'),(28,-16,'临江立面')]:
    ax.text(x,y,s,ha='center',va='center',fontproperties=font,fontsize=11,color='#302e29')
ax.annotate('',xy=(.2,0),xytext=(26,-14),arrowprops={'arrowstyle':'->','color':'#8b3427','lw':1.6})
ax.plot([-64,-44],[-84,-84],lw=2,color='#30352e')
ax.text(-54,-81,'20 m',ha='center',fontsize=9)
ax.annotate('N',xy=(27,29),xytext=(27,19),ha='center',arrowprops={'arrowstyle':'-|>','color':'#30352e'})
ax.set_xlim(-74,39);ax.set_ylim(-92,36);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
ax.set_title('外滩29号及其南侧街坊',fontproperties=font,fontsize=17,pad=12)
fig.text(.5,.028,'© OpenStreetMap contributors · Overture Maps Foundation',ha='center',color='#56594e',fontsize=9)
fig.savefig(HERE/'street-blocks.png',dpi=155,bbox_inches='tight')
