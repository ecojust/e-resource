"""Keep the city's original checks and use a fresh process for each real device or camera sequence."""
from pathlib import Path
import subprocess
work=Path(__file__).parent
s=(work/'check-180.cjs').read_text()
s=s.replace("const desktopOnly = process.argv.includes('--after-mobile');","const section = process.env.CITY_SECTION;\nconst desktopOnly = section!=='phone';")
s=s.replace("desktopOnly,caseSha256","desktopOnly,section,caseSha256")
s=s.replace("'--enable-unsafe-swiftshader',","'--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disk-cache-size=6291456',")
s=s.replace("const image=await page.screenshot({path:path.join(out,name+'.png'),timeout:300000});","const capture=await page.context().newCDPSession(page);let image;try{image=Buffer.from((await capture.send('Page.captureScreenshot',{format:'png',fromSurface:true})).data,'base64');}finally{await capture.detach();}fs.writeFileSync(path.join(out,name+'.png'),image);")
start=s.index("      if(!desktopOnly){")
end=s.index("      result.ground=",start)
s=s[:start]+"""      if(section==='desktop'||section==='phone'){
        const mobile=section==='phone';
        await page.setViewportSize(mobile?{width:390,height:844}:{width:870,height:660});
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
        const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
        if(mobile) await card.tap(); else await card.click();
        await view(mobile?'map-mobile':'map-desktop','full',true);
      }
      if(section==='details'){
        await clickBeacon(ID,PRIOR,[contract.lng,contract.lat],result);
        await view('map-beacon-return','full',true);
        await closePanel();await jump(camera);await view('map-street-facade','full',true);
        await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});
        await view('map-roof','full',true);
"""+s[end:]
start=s.index("      await page.setViewportSize({width:600,height:460});")
end=s.index("      assert.equal(sha(bytes(catalogFile))",start)
s=s[:start]+"""      }
      if(section==='distant'){
        await page.setViewportSize({width:440,height:380});
        await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
        await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
        await jump({...camera,zoom:15.5,pitch:32,elevation:0});await view('map-distant','distant');
        for(const [role,item] of Object.entries(manifest.assets))
          await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),item,role==='lod');
      }
      if(section==='details')await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),manifest.assets.full.file),manifest.assets.full,true);
"""+s[end:]
s=s.replace("await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,true);","await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,control||section==='details'||(section==='distant'&&rec.repository_path.endsWith('/far.glb')));")
f=work/'check-180-separated.cjs';f.write_text(s)
subprocess.run(['node','--check',f],check=True)
