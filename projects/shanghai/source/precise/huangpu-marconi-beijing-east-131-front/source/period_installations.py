"""Street fittings, shopfront and two supported condensers visible in both dated photographs."""
import numpy as np
from marconi_street_fabric import block,WOOD,METAL,GREY,STONE,TILE,IRON,ROOF
from broad_office_sashes import layout
def evidence(b,lod):
 # White horizontal shutters, dark tiled plinth and the timber wicket of the corner shop.
 for a,c in [(-15.8,-13.7),(-12.35,-10.32),(-7.73,-6.34),(-4.64,-2.81)]:
  block(b,a,c,.105,.141,.12,1.22,STONE,'Shop front | dark cladding below pale courses')
 for x in np.arange(-15.6,-2.8,.22):
  for lo,hi in [(1.26,2.18),(2.47,3.37)]:
   if not (-6.36<x<-4.7):block(b,x-.005,x+.005,.15,.157,lo,hi,GREY,'Shop front | narrow facing joints')
 for a,c in [(-13.2,-11.93),(-9.6,-8.6),(-4.67,-2.81)]:
  block(b,a,c,.143,.155,2.04,2.23,WOOD,'Shop front | strip of dark red tile')
 for z in np.linspace(.22,3.18,26):block(b,-11.90,-8.68,.130,.145,z,z+.013,GREY,'Shop front | fine slats')
 lo,hi=1.59,2.82;left,right=-5.96,-5.30
 block(b,left,right,.039,.064,lo,hi,WOOD,'Shop door | recessed inset')
 for i in range(6): 
  xx=left+(right-left)*(i+.4)/6;block(b,xx-.010,xx+.010,.027,.050,lo,hi,GREY,'Shop door | light grille stiles')
 for z in np.linspace(lo+.04,hi-.04,11):block(b,left,right,.024,.048,z-.008,z+.008,GREY,'Shop door | cross bars')
 # The narrow frames just beyond each dormer are attached at the window sill elevation.
 # Metal cages and support angles are separately drawn. Air-conditioning cabinets are visible in 2015 and 2017.
 for j,(x,z,w,h,depth,cage)in enumerate([(-12.78,19.07,.88,.65,.43,2.34),(-10.19,19.18,.81,.64,.42,2.03)]):
  label='Roof-level condenser '+str(j+1)
  base_y=.34
  block(b,x-w/2,x+w/2,base_y-depth,base_y,z,z+h,METAL,label+' | metal cabinet')
  for q in np.linspace(-.32,.32,14 if lod else 27):
   block(b,x+q-.006,x+q+.006,base_y-depth-.018,base_y-depth-.003,z+.085,z+h-.08,IRON,label+' | ventilation grille')
  b.tube([(x+.223*np.cos(t),base_y-depth-.018,z+h*.51+.223*np.sin(t)) for t in np.linspace(0,2*np.pi,23)],.009,IRON,5 if lod else 7,label+' | circular fan rim')
  for dx in (-w*.40,w*.40):
   b.tube([[x+dx,1.02,z-.31],[x+dx,base_y-depth,z-.035],[x+dx,1.02,z-.035]],.027,IRON,6,label+' | triangular bracket')
  west=x-.18 if j==0 else x+cage/2
  for xx in (west-cage/2,west+cage/2):
   b.tube([[xx,.94,18.62],[xx,-.13,18.62],[xx,-.13,19.55],[xx,.94,19.55]],.019,IRON,6,'Roof window | projecting cage')
  for zz in (18.66,19.04,19.53):b.tube([[west-cage/2,-.13,zz],[west+cage/2,-.13,zz]],.014,IRON,6,'Roof window | front cage rail')
 # The parallel boards beneath the eaves can be counted on the paired dormers.
 for j,(xa,xc,xb,zb,zt)in enumerate([(-15.80,-14.00,-12.14,21.58,22.12),(-10.46,-8.44,-6.24,21.54,22.17)]):
  for r in range(4):
   dz=.055+.055*r
   for a,z0,c,z1 in [(xa,zb,xc,zt),(xc,zt,xb,zb)]:
    b.tube([[a,.925,z0-dz],[c,.925,z1-dz]],.013,ROOF,6,'Dormer eaves | parallel fascia lines')
