"""Read a single authentic site into sealed descriptors inherited only by its verifying Node process."""
import fcntl,hashlib,os
from urllib.request import urlopen
from pathlib import Path

def signed_inputs(order,origin,snapshot,identifier):
    paths=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
    if order==212:paths.append('assets/models/candidates/'+identifier+'/manifest.json')
    descriptors={};details={}
    try:
        for path in paths:
            fd=os.memfd_create('city-212-'+str(order),os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
            descriptors[path]=fd;total=0;digest=hashlib.sha256()
            with urlopen(origin+path,timeout=70)as response,os.fdopen(os.dup(fd),'wb') as out:
                assert response.status==200
                while chunk:=response.read(98304):
                    out.write(chunk);digest.update(chunk);total+=len(chunk)
            assert digest.hexdigest()==snapshot['files'][path],path
            # Linux UAPI F_ADD_SEALS and F_GET_SEALS; Python may omit these names.
            fcntl.fcntl(fd,getattr(fcntl,"F_ADD_SEALS",1033),15)
            assert fcntl.fcntl(fd,getattr(fcntl,"F_GET_SEALS",1034)) & 15 == 15
            assert os.fstat(fd).st_size==total;details[path]=dict(sha256=digest.hexdigest(),bytes=total)
        return descriptors,details
    except BaseException:
        for fd in descriptors.values():os.close(fd)
        raise
