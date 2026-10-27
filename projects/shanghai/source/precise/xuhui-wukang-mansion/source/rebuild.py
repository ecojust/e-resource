#!/usr/bin/env python3
"""Portable public wrapper; source/ and sibling materials/ stay together."""
from pathlib import Path
import build_detailed_v1 as build
if __name__=='__main__':
 material=Path(__file__).resolve().parent.parent/'materials/wukang-brick-v1'
 if material.exists():
  build.MATERIAL=material
  spec=build.PALETTE['brick']
  for key,name in [('texture','brick-basecolor.png'),('normal_texture','brick-normal.png'),('orm_texture','brick-orm.png')]:spec[key]=str(material/'maps'/name)
 build.main()
