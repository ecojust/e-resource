"""Original roughcast, washed-gravel plinth, steel and cement finishes."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
PLASTER='Xiangyang | warm roughcast'
BASE='Xiangyang | washed aggregate toe'
CEMENT='Xiangyang | warm grey moulding'
SHADOW='Xiangyang | inner reveals'
GLASS='Xiangyang | blue grey casement glass'
FRAME='Xiangyang | dark metal window frames'
DARK='Xiangyang | dark apron recess'
DENTIL='Xiangyang | pale cornice teeth'
IRON='Xiangyang | painted iron'
ROOF='Xiangyang | grey roof and coping'
GRILLE='Xiangyang | relief and ornament'
WOOD='Xiangyang | dark timber'
PAVE='Xiangyang | pavement'
def rgb(values,rough=.85):
    return {'color':[((v/255+.055)/1.055)**2.4 if v>10.315 else v/3294.6 for v in values],'roughness':rough}
def finish(name):return {'texture':str(HERE/name),'color':[1,1,1],'roughness':.94}
PALETTE={PLASTER:finish('street-plaster.png'),BASE:finish('granite-chips.png'),CEMENT:rgb((173,160,138)),SHADOW:rgb((75,72,62)),
 GLASS:rgb((113,130,136),.31),FRAME:rgb((61,62,58),.50),DARK:rgb((84,78,65)),DENTIL:rgb((200,188,166)),IRON:rgb((58,59,55),.55),
 ROOF:rgb((119,115,105)),GRILLE:rgb((139,128,103)),WOOD:rgb((89,62,47)),PAVE:rgb((141,138,126))}
