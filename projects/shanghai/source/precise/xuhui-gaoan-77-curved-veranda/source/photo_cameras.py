"""Convert the measured dimensionless camera frame to the local metre model."""
import numpy as np
from house_layout import CENTRE_X,DECK_Z,FIT,POST_SPAN
def projection(name):
    to_units=np.eye(4);to_units[:3,:3]/=POST_SPAN;to_units[:3,3]=-np.array([CENTRE_X,0.,DECK_Z])/POST_SPAN
    return np.asarray(FIT['cameras'][name]['projection'])@to_units
