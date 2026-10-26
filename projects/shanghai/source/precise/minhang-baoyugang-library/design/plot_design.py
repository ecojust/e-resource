from pathlib import Path
import json,math
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import Polygon
P=Path(__file__).resolve().parents[1];c=json.loads((P/'calibration.json').read_text());g=json.loads((P/'geometry-input.json').read_text());e=c['estimated'];t=np.array(c['coordinate_frame']['u_eastward_ENU']);n=np.array(c['coordinate_frame']['v_northward_ENU']);q=np.array(g['polygon_local_east_north']);uv=np.column_stack([q@t,q@n]);profiles=e['level_profiles_uv_m'];colors=plt.cm.viridis(np.linspace(.07,.9,6));fig,axs=plt.subplots(2,2,figsize=(14,9));ax=axs[0,0]
ax.plot(*np.vstack([uv,uv[0]]).T,'k--',lw=2,label='Frozen owner outline')
for i,(poly,color) in enumerate(zip(profiles,colors)):
 ar=np.array(poly+[poly[0]]);ax.plot(*ar.T,color=color,lw=1.6,label=f'F{i+1} estimate')
ax.set_aspect('equal');ax.set(xlabel='u eastward metres',ylabel='v northward metres',title='Six independently estimated levels; south = negative v');ax.legend(fontsize=7,ncol=2);ax.grid(alpha=.2)
ax=axs[0,1]
for i,(poly,color) in enumerate(zip(profiles,colors)):
 ar=np.array(poly+[poly[0]]);v=e['level_base_z_m'][i];ax.plot(ar[:,0],ar[:,1]*.22+v,color=color);ax.plot(ar[:,0],ar[:,1]*.22+v+3.9,color=color,lw=.5)
ax.set(xlabel='u metres',ylabel='z + 0.22v (diagram only)',title='Depth-separated schematic: distinct setbacks');ax.grid(alpha=.2)
ax=axs[1,0]
for i,color in enumerate(colors):
 z=e['level_base_z_m'][i];lo=min(p[0] for p in profiles[i]);hi=max(p[0] for p in profiles[i]);ax.add_patch(Patch([[lo,z],[hi,z],[hi,z+3.9],[lo,z+3.9]],facecolor=color,alpha=.2,edgecolor=color))
 if i<3:
  ax.add_patch(Patch([[-5.3,z],[15.2,z],[15.2,z+3.9],[-5.3,z+3.9]],facecolor='white',edgecolor='none'))
 for u in np.arange(lo+1.4,hi-1,3.7):
  if i<3 and -5.3<u<15.2:continue
  ax.add_patch(Patch([[u,z+.85],[u+2.5,z+.85],[u+2.5,z+3.05],[u,z+3.05]],facecolor='#7eabb5',alpha=.4,edgecolor='#303638',lw=.4))
ax.add_patch(Patch([[18,24.85],[30,24.85],[30,26.29],[26,27.4],[22,27.4],[18,26.29]],facecolor='#933d32',alpha=.5,edgecolor='brown'))
for u in e['entry']['column_u_m']:ax.plot([u,u],[.45,12.75],color='#863e33',lw=3)
for u in np.linspace(-17,20.8,30):ax.plot([u,u],[23.85,24.15],color='black',lw=1)
ax.set(xlim=(-55,50),ylim=(0,30),xlabel='u metres',ylabel='z metres',title='South massing diagram; openings schematic, not counted from image');ax.grid(alpha=.2)
ax=axs[1,1]
for i,color in enumerate(colors):
 poly=Polygon(profiles[i]);b=poly.bounds;z=e['level_base_z_m'][i];ax.add_patch(Patch([[b[1],z],[b[3],z],[b[3],z+3.9],[b[1],z+3.9]],facecolor=color,alpha=.2,edgecolor=color))
ax.set(xlim=(-23,22),ylim=(0,30),xlabel='v northward metres',ylabel='z metres',title='West-side depth envelope only; no surveyed section');ax.grid(alpha=.2)
fig.suptitle('Pao Yue-Kong Library | 2021 appearance | metric reconstruction estimates v2',fontsize=13);fig.tight_layout();fig.savefig(P/'design/plan-elevation-v2.png',dpi=140)
checks={'schema':'library-design-polygon-check-v1','not_actual_mesh_acceptance':True,'profiles':[{'level':i+1,'valid':Polygon(poly).is_valid,'area_m2_estimate':Polygon(poly).area,'bounds_uv_m':Polygon(poly).bounds} for i,poly in enumerate(profiles)],'scope':'Only finite/valid authored 2D design outlines; no raw/native geometry generated.'};(P/'design/profile-check-v2.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks))
