import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Html5Audio,Img,continueRender,delayRender,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
export type Scene={start:number;end:number;image?:string;lines:string[];motion?:string};
export type Props={duration:number;scenes:Scene[];audio?:string;font?:string};
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
export const DoodleReel:React.FC<Props>=({scenes,audio,font})=>{
 const frame=useCurrentFrame();const {fps}=useVideoConfig();const time=frame/fps;
 const [fontHandle]=useState(()=>delayRender('Local serif font'));
 useEffect(()=>{
  if(!font){continueRender(fontHandle);return;}
  const face=new FontFace('DoodleSerif',`url(${staticFile(font)})`);
  face.load().then(f=>{document.fonts.add(f);continueRender(fontHandle);}).catch(()=>continueRender(fontHandle));
 },[font,fontHandle]);
 const index=Math.max(0,scenes.findLastIndex(s=>s.start<=time));
 const scene=scenes[index];const age=(time-scene.start)*fps;
 const left=(scene.end-time)*fps;const incoming=scene.motion??'none';
 const outgoing=scenes[index+1]?.motion??'none';
 const entering=age<20&&index>0;const exiting=left<9&&index<scenes.length-1;
 let yaw=0,rotate=0,scale=1;
 if(incoming==='hinge'&&entering){yaw=interpolate(age,[0,9,20],[-87,16,0],clamp);scale=interpolate(age,[0,9,20],[.4,1.08,1],clamp);}
 if(outgoing==='hinge'&&exiting){yaw=interpolate(left,[0,9],[87,0],clamp);scale=interpolate(left,[0,9],[.45,1],clamp);}
 if(incoming==='spin'&&entering){rotate=interpolate(age,[0,20],[-90,0],clamp);scale=interpolate(age,[0,20],[.9,1],clamp);}
 if(outgoing==='spin'&&exiting){rotate=interpolate(left,[0,9],[90,0],clamp);}
 if(incoming==='zoom'&&entering){scale=interpolate(age,[0,6,20],[1.8,1.12,1],clamp);}
 const pulse=age%(fps*3)<fps?Math.floor(age/(fps*.25))%4:0;
 const inks=['#171717','#252b80','#99386e','#168aa4'];
 const tilt=Math.sin(age/fps*2*Math.PI)*.35;
 const vignette=.14*(.5+.5*Math.sin(frame/fps*Math.PI*3));
 return <AbsoluteFill style={{backgroundColor:(Math.abs(yaw)>1)?'black':'white',perspective:1800,overflow:'hidden'}}>
  {audio?<Html5Audio src={staticFile(audio)}/>:null}
  <AbsoluteFill style={{backgroundColor:'white',transform:`rotateY(${yaw}deg) rotateZ(${rotate}deg) scale(${scale})`,backfaceVisibility:'hidden',transformOrigin:'50% 50%'}}>
   <div style={{position:'absolute',left:80,top:535,width:820,textAlign:'center',color:'#9B843E',fontFamily:font?'DoodleSerif':'Georgia',fontSize:69,fontStyle:'italic',lineHeight:1.12,opacity:interpolate(age,[0,5],[0,1],clamp)}}>
    {scene.lines.map((line,i)=><div key={i}>{line}</div>)}
   </div>
   <div style={{position:'absolute',left:85,top:800,width:810,height:660,transform:`translateY(${Math.sin(age/fps*2*Math.PI)*5}px) rotate(${tilt}deg) scale(${1+.012*Math.sin(age/fps*2*Math.PI)})`}}>
    {scene.image?<><svg width="0" height="0"><defs><filter id="ink"><feFlood floodColor={inks[pulse]}/><feComposite in2="SourceAlpha" operator="in"/></filter></defs></svg><Img src={staticFile(scene.image)} style={{width:'100%',height:'100%',objectFit:'contain',filter:'url(#ink)'}}/></>:<svg viewBox="0 0 810 660" width="810" height="660"><path d="M300 570 Q260 480 280 320 Q290 190 400 180 Q520 190 525 340 L530 570 Q430 630 300 570" fill="none" stroke={inks[pulse]} strokeWidth="5"/><circle cx="360" cy="300" r="7"/><circle cx="440" cy="300" r="7"/><path d="M375 340 Q400 365 425 340" fill="none" stroke="black" strokeWidth="5"/></svg>}
   </div>
   <AbsoluteFill style={{background:'radial-gradient(ellipse at center, transparent 50%, black 125%)',opacity:vignette,pointerEvents:'none'}}/>
  </AbsoluteFill>
 </AbsoluteFill>;
};
