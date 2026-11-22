"""Rebuild the timber porch and photographed yellow-brick gable at 561 Jiaozhou Road."""
from pathlib import Path
import argparse,os,sys
source=Path(__file__).resolve().parent;project=source.parents[3]
sys.path.insert(0,str(source));sys.path.insert(0,str(project/'tools'))
from package_architectural_model import build
from porch import MATERIALS as PALETTE,add_building
ID='jingan-electricity-department-residence-gabled-porch'
name='胶州路561号电力部住宅门廊与砖山墙'
scope='依据2015和2021冬季街影及2024年10月24日刊载的署址照片，制作独立木柱尖顶门廊及相邻带窄阁孔的砖山墙，包括两层分格木窗、花栏、双坡卷饰和浅台阶。'
META=dict(id=ID,name=name,viewer_page='electricity-department-residence-porch.html',status='photo-informed-exterior-study',scope=scope,model_scope_zh=scope,reference_height_m=8.98,estimated='高度、进深和窗格尺寸由摄影比例估算。树荫下的另一翼、后屋面、院墙和室内没有用于复原。',coordinate_convention='Metres, Z up. Local +X runs toward the narrow-vent gable at the viewer’s right. Positive Y is behind the brick facade.',source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,copyright='Original modeled surfaces. Source pictures are cited for observation and are not embedded.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
