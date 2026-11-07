const {chromium}=require('playwright'); const fs=require('fs'); const {spawn}=require('child_process');
(async()=>{
 const mode=process.argv[2]||'test'; const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('file://'+__dirname+'/index.html'); await p.evaluate(e=>{ENV=e},JSON.parse(fs.readFileSync('env.json')));
 await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(500);
 if(mode==='test'){const ts=[0.6,1.6,3.6,5.9,7.6,8.9,10.2,12.2,14.0,15.8,18.0,20.6,23.6,28.0,31.4,34.6,36.7];
   for(const [i,t] of ts.entries()){await p.evaluate(t=>render(t),t); await p.screenshot({path:`t_${String(i).padStart(2,'0')}.png`});}
   await b.close(); return;}
 const D=36.96, FPS=30, N=Math.round(D*FPS);
 const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate','60','-i','-','-i','../vo.wav','-vf','tmix=frames=2,fps=30','-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','../Sumit_Intro_Reel.mp4']);
 ff.stderr.on('data',d=>process.stderr.write(d));
 for(let i=0;i<N*2;i++){await p.evaluate(t=>render(t),i/60); const buf=await p.screenshot({type:'jpeg',quality:92}); if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));}
 ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await b.close();
})();
