"""Mineral finishes and steel garden casements on the former Jianguo Road residence."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
RENDER='Jianguo 629 | ivory stucco'
BRICK='Jianguo 629 | red stretcher bond'
SILL='Jianguo 629 | warm stone'
TRIM='Jianguo 629 | pale rendered band'
DARK='Jianguo 629 | recessed shadow'
FRAME='Jianguo 629 | painted steel'
GLASS='Jianguo 629 | garden-facing glass'
MID_GLASS='Jianguo 629 | reflected glass'
BLOCK='Jianguo 629 | translucent glass brick'
MORTAR='Jianguo 629 | cream joints'
ROOF='Jianguo 629 | roof weathering'
BASE='Jianguo 629 | concrete plinth'
IRON='Jianguo 629 | dark metal'
WOOD='Jianguo 629 | dark wood'
def paint(rgb,roughness=.82):
    return {'color':[((v/255+.055)/1.055)**2.4 if v>10.315 else v/3294.6 for v in rgb],'roughness':roughness}
def texture(name):
    return {'texture':str(HERE/name),'color':[1,1,1],'roughness':.94}
PALETTE={RENDER:texture('garden-stucco.png'),BRICK:texture('garden-red-brick.png'),SILL:paint((191,180,161)),
 TRIM:paint((222,212,190)),DARK:paint((62,57,47)),FRAME:paint((69,64,55),.49),GLASS:paint((76,89,88),.23),
 MID_GLASS:paint((111,126,125),.29),BLOCK:paint((130,151,144),.33),MORTAR:paint((194,186,166)),
 ROOF:paint((119,118,110)),BASE:paint((159,145,126)),IRON:paint((63,59,55),.44),WOOD:paint((85,67,53))}
