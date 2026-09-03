const { chromium } = require('playwright-core'); const path=require('path'); const fs=require('fs');
(async()=>{
  const out=path.resolve(__dirname,'out'); fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium',args:['--font-render-hinting=none','--disable-lcd-text']});
  const jobs=[];
  for(const lang of ['en','de']){
    for(let i=1;i<=7;i++) jobs.push({lang,slide:String(i),w:1080,h:1080,name:`carousel_${lang}_0${i}.png`});
    jobs.push({lang,slide:'story',w:1080,h:1920,name:`story_${lang}.png`});
    jobs.push({lang,slide:'story',guide:1,w:1080,h:1920,name:`story_${lang}_guide.png`});
  }
  const only=process.argv[2];
  for(const j of jobs){
    if(only && !j.name.includes(only)) continue;
    const p=await b.newPage({viewport:{width:j.w,height:j.h},deviceScaleFactor:1});
    await p.goto('file://'+path.resolve(__dirname,'post.html')+`?lang=${j.lang}&slide=${j.slide}${j.guide?'&guide=1':''}`);
    await p.waitForTimeout(500);
    await p.screenshot({path:path.join(out,j.name)}); await p.close(); process.stdout.write(j.name+' ');
  }
  await b.close(); console.log('\ndone');
})();
