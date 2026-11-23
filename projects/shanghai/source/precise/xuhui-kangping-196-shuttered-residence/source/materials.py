"""Cool rendered walls, white relief and dark painted timber from the 2019 street photograph."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
WALL='Kangping 196 | green grey street render'
ASHLAR='Kangping 196 | ruled rear plaster'
BASE='Kangping 196 | slate grey plinth'
PALE='Kangping 196 | cream relief'
SHADE='Kangping 196 | relief shadow'
WOOD='Kangping 196 | dark shutter frames'
LOUVER='Kangping 196 | painted blind slats'
DEEP='Kangping 196 | deep recess'
GLASS='Kangping 196 | sash glazing'
TRIM='Kangping 196 | pale window surround'
ROOF='Kangping 196 | terra cotta roof tile'
RIDGE='Kangping 196 | ridge clay'
EAVE='Kangping 196 | dark eaves'
PAVE='Kangping 196 | grey stone steps'
IRON='Kangping 196 | ironwork'
def paint(values,rough=.84):
    return {'color':[((v/255+.055)/1.055)**2.4 if v>10.315 else v/3294.6 for v in values],'roughness':rough}
def finish(name):
    return {'texture':str(HERE/name),'color':[1,1,1],'roughness':.95}
PALETTE={WALL:finish('street-grey-plaster.png'),ASHLAR:finish('rear-ruled-plaster.png'),BASE:paint((84,91,87)),PALE:paint((232,229,205)),SHADE:paint((178,176,154)),
 WOOD:paint((52,55,45)),LOUVER:paint((126,131,114)),DEEP:paint((44,46,39)),GLASS:paint((81,90,86),.29),TRIM:paint((211,208,186)),ROOF:paint((134,74,53)),RIDGE:paint((125,74,55)),EAVE:paint((69,71,61)),PAVE:paint((141,139,126)),IRON:paint((63,65,58),.51)}
