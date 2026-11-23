"""The lower continuation of the street eave behind the northeast glazed gable.

2015 and 2020 street views show the roof edge drop at the end of the raised bay.
The pitch behind this edge is estimated between the visible eave and the
longitudinal ridge in the 2021 aerial image. Retain the cutoff on the west.
"""
from shapely.geometry import Polygon,box
from residence_materials import CLAY,LEAD,IVORY_RENDER,SILL

START=3.40
END=8.84
NORTH_EAVE=.30
INNER_EAVE=-2.91
RIDGE=-1.35
EAVE_Z=6.11
RIDGE_Z=6.83


def height(x):
    t=(x-INNER_EAVE)/(RIDGE-INNER_EAVE) if x<=RIDGE else (NORTH_EAVE-x)/(NORTH_EAVE-RIDGE)
    return EAVE_Z+(RIDGE_Z-EAVE_Z)*t


def add_north_roof(b,lod=False):
    for west,east in [(INNER_EAVE,RIDGE),(RIDGE,NORTH_EAVE)]:
        section=box(west,START,east,END)
        b.prism(section,-.087,-.019,lambda x,y,t:(x,y,height(x)+t),
                IVORY_RENDER,'Northern roof | pale projecting soffit')
        b.prism(section,-.018,.019,lambda x,y,t:(x,y,height(x)+t),
                CLAY,'Northern roof | shallow hipped-wing tile bed')
        # The rows and rounded covers run downhill. Stops leave an individual lip
        # over the eave, also visible in the aerial and oblique ground views.
        n=round((END-START)/(.39 if lod else .20))
        for j in range(n):
            y=START+(j+.5)*(END-START)/n
            b.tube([(west,y,height(west)+.023),(east,y,height(east)+.023)],.029,
                   CLAY,6 if lod else 10,'Northern roof | tile cover rolls')
        courses=max(2,round((east-west)/(.47 if lod else .32)))
        for j in range(1,courses):
            x=west+j*(east-west)/courses
            b.prism(box(x-.025,START,x+.009,END),.016,.033,
                    lambda u,y,t:(u,y,height(u)+t),CLAY,'Northern roof | course joint')
        b.prism(box(west,END-.038,east,END+.012),-.10,.025,
                lambda x,y,t:(x,y,height(x)+t),LEAD,'Northern roof | western verge')
    b.tube([(RIDGE,START-.018,RIDGE_Z+.03),(RIDGE,END+.027,RIDGE_Z+.03)],
           .053,CLAY,8 if lod else 14,'Northern roof | capped longitudinal ridge')
    b.box((NORTH_EAVE-.007,(START+END)/2,EAVE_Z-.025),(.065,END-START,.128),
          LEAD,label='Northern roof | dark fascia')
    b.box((NORTH_EAVE-.031,(START+END)/2,EAVE_Z-.084),(.06,END-START,.021),
          SILL,label='Northern roof | lower fascia return')
    # At the feathered end only the plain section behind the tile bed is inferred.
    section=Polygon([(INNER_EAVE,6.00),(NORTH_EAVE,6.00),(NORTH_EAVE,EAVE_Z-.091),
                     (RIDGE,RIDGE_Z-.091),(INNER_EAVE,EAVE_Z-.091)])
    b.prism(section,-END,-END+.09,lambda u,z,d:(u,-d,z),SILL,'Northern roof | western section')
