from pathlib import Path
HERE=Path(__file__).resolve().parent
MATERIAL='Residence | grey facing brick'
TEXTURE=HERE/'changde-grey-brick.png'
GRANITE=HERE/'changde-porch-granite.png'
TEXTURES={MATERIAL:TEXTURE,**{'Entrance porch | '+name:GRANITE for name in ('grey granite','cut granite moulding','carved stone')}}
