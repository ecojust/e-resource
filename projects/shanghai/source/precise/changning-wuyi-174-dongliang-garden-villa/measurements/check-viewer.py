"""Open the ordinary model page at desktop and phone widths and exercise every view and download."""
import argparse
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright

PROJECT=Path(__file__).resolve().parents[4]
ID='changning-wuyi-174-dongliang-garden-villa'
PAGE='wuyi-174-dongliang-garden-villa.html'


class Handler(SimpleHTTPRequestHandler):
    def log_message(self,format,*args):
        pass


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--chromium',default='/usr/bin/chromium');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((PROJECT/'assets/models/candidates'/ID/'manifest.json').read_bytes())
    poses=json.loads((Path(__file__).resolve().parents[1]/'source/cameras.json').read_bytes())
    report={}
    with ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(PROJECT))) as server,sync_playwright()as driver:
        threading.Thread(target=server.serve_forever,daemon=True).start()
        browser=driver.chromium.launch(executable_path=a.chromium,headless=True,
            args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-webgl','--no-sandbox','--disable-dev-shm-usage'])
        for mode,width,height in [('desktop',1100,760),('phone',390,760)]:
            out=a.output/mode;out.mkdir(exist_ok=True)
            context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,
                is_mobile=mode=='phone',has_touch=mode=='phone',accept_downloads=True)
            page=context.new_page();errors=[];resources=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('response',lambda response:resources.append({'path':response.url.split(str(server.server_port),1)[-1],'status':response.status}))
            page.goto('http://127.0.0.1:'+str(server.server_port)+'/'+PAGE,wait_until='networkidle',timeout=60000)
            page.wait_for_function("document.querySelector('#status')?.textContent.startsWith('近景')",timeout=60000)
            stage=page.locator('#model-view canvas')
            viewport=stage.bounding_box()
            assert viewport['width']>220 and viewport['height']>225
            assert page.evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth+1")
            gl=stage.evaluate("""el=>{let gl=el.getContext('webgl2');return {version:gl.getParameter(gl.VERSION),width:gl.drawingBufferWidth,height:gl.drawingBufferHeight}}""")
            shots=[]
            for pose in poses:
                key='oblique' if pose['name']=='overview' else pose['name']
                page.locator('[data-view="'+key+'"]').click()
                page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                dest=out/(key+'.jpg');stage.screenshot(path=str(dest),type='jpeg',quality=89)
                shots.append(dict(view=pose['label'],file=dest.name,sha256=sha(dest)))
            assert len({s['sha256']for s in shots})==len(poses)
            page.locator('#detail').select_option('lod')
            page.wait_for_function("document.querySelector('#status')?.textContent.startsWith('远景')",timeout=60000)
            lod=page.locator('#status').inner_text()
            page.locator('#detail').select_option('full')
            page.wait_for_function("document.querySelector('#status')?.textContent.startsWith('近景')",timeout=60000)
            saves={}
            for role,asset in manifest['assets'].items():
                with page.expect_download()as waiting:
                    page.locator('#downloads a[href$="'+asset['file']+'"]').click()
                d=waiting.value;dest=out/d.suggested_filename;d.save_as(dest)
                assert dest.stat().st_size==asset['bytes'] and sha(dest)==asset['sha256']
                saves[role]=dict(file=dest.name,bytes=asset['bytes'],sha256=asset['sha256'])
            assert not errors and not [row for row in resources if row['status']>=400]
            report[mode]=dict(css_viewport=[width,height],canvas=viewport,webgl=gl,views=shots,
                              near_status=page.locator('#status').inner_text(),far_status=lod,
                              downloads=saves,resource_responses=resources)
            context.close()
        browser.close()
    (a.output/'viewer-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')


if __name__=='__main__':main()
