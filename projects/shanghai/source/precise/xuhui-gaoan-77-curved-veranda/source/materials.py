"""Programmatic mineral render, red Roman clay, lime trim, timber and painted steel."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
PLASTER='Gaoan 77 | cream plaster'
DARK='Gaoan 77 | exposed dark timber'
ROOF='Gaoan 77 | red clay roof'
RIDGE='Gaoan 77 | tile crests'
STONE='Gaoan 77 | pale stone'
IRON='Gaoan 77 | wrought iron'
BRICK='Gaoan 77 | russet brickwork'
JOINT='Gaoan 77 | lime mortar'
FRAME='Gaoan 77 | ochre casement'
GLASS='Gaoan 77 | dark glazing'
RECESS='Gaoan 77 | shaded opening'
BASE='Gaoan 77 | plinth and cut face'
def surface(rgb,rough=.85):
    return {'color':[((x/255+.055)/1.055)**2.4 if x>10.315 else x/3294.6 for x in rgb],'roughness':rough}
PALETTE={PLASTER:surface((213,207,181)),DARK:surface((67,59,47)),ROOF:surface((151,90,63)),RIDGE:surface((133,82,59)),STONE:surface((202,198,178)),
         IRON:surface((72,74,65),.55),BRICK:surface((167,109,78)),JOINT:surface((182,160,133)),FRAME:surface((127,99,65)),GLASS:surface((73,81,79),.25),RECESS:surface((46,44,39)),BASE:surface((143,136,117))}
PALETTE[PLASTER].update(texture=str(HERE/'cream-lime.png'),color=[1,1,1])
PALETTE[BRICK].update(texture=str(HERE/'warm-russet-brick.png'),color=[1,1,1])
