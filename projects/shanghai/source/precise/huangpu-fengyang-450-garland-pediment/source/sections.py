"""Independently intersect the delivered pediment and its shoulder returns."""
import numpy as np
from garland_pediment import *
def test(tri,materials,hit):
 rays=[]
 def at(x,y,expected,label):
  pos=np.array(local(x,y,2));r=hit(tri,materials,pos,np.array([0,1,0]));assert r and r[0]==expected,(x,y,r,expected)
  rays.append(dict(label=label,material=expected,point=r[1]))
 # Keep control points below the two suspended swags, inside the uncarved field.
 for x in (202,207,214,221,229,247,256,268,274,280):
  for y in (182,185,189):at(x,y,FIELD,'Lower field between hanging ornament and basal ledge')
 # Some narrow leaf ribbing sits in front of the garland, and differs between the two meshes.
 for x,y in ((236,138),(236,165)):
  r=hit(tri,materials,np.array(local(x,y,2)),np.array([0,1,0]));assert r and r[0] in (RIB,RELIEF)
  rays.append(dict(label='Raised ornament at the crossing of leaf rib and suspended garland',material='Carved festoon assembly',physical_material=r[0],point=r[1]))
 for x,y in ((233,138),(242,138),(233,165),(242,165)):at(x,y,RELIEF,'Body of upper and lower hanging garlands')
 for x in (170,185,197,225,256,278,299,306):
  for y in (74,80,194,201):
   at(x,y,RIM,'Four straight moulding levels')
 for y in (43,46,50,53,55,58,61):
  for x in (244,246,249,251):at(x,y,RELIEF,'Oval boss')
 for side in (-1,1):
  for y in (127,142,159,171,185):
   at(238+side*63,y,RIB,'Pier between beads')
  for x in (131,145,151):
   at(238+side*x,186,FIELD,'Sloping side wing')
 return rays
