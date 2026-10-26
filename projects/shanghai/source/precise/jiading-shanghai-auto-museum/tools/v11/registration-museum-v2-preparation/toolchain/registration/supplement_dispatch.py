"""Explicit per-model supplementary evidence selection; Library code unchanged."""
from geometry_supplements import (
    validate_raw_supplements as library_raw,
    validate_decoded_supplement_transfer as library_transfer)
from museum_supplements import validate_raw_supplements as museum_raw
from museum_supplements import validate_decoded_supplement_transfer as museum_transfer

def validate_raw_supplements(request,target,package,structure,inputs):
    if target['id']=='jiading-shanghai-auto-museum':
        return museum_raw(request,target,package,structure,inputs)
    return library_raw(request,target,package,structure,inputs)

def validate_decoded_supplement_transfer(validated,decoded,request,target,package,structure,inputs):
    if target['id']=='jiading-shanghai-auto-museum':
        return museum_transfer(validated,decoded,request,target,package,structure,inputs)
    return library_transfer(validated,decoded,request,target,package,structure,inputs)
