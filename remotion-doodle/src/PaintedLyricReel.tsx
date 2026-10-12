import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Html5Audio,Img,continueRender,delayRender,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
type Painting={start:number;image:string};
type Lyric={start:number;end:number;above:string;hero:string;below:string};
export type PaintedProps={duration:number;outroSeconds:number;audio?:string;serifFont?:string;scriptFont?:string;handle:string;paintings:Painting[];lyrics:Lyric[]};
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
export const PaintedLyricReel:React.FC<PaintedProps>=p=>{
 const frame=useCurrentFrame();const {fps}=useVideoConfig();const t=frame/fps;
 const [h]=useState(()=>delayRender('Painting lyric fonts'));
 useEffect(()=>{Promise.all([[p.serifFont,'PaintSerif'],[p.scriptFont,'PaintScript']].filter(([path])=>path).map(async([path,name])=>{const f=await new FontFace(name!,`url(${staticFile(path!)})`).load();document.fonts.add(f)})).then(()=>continueRender(h)).catch(()=>continueRender(h));},[h,p.serifFont,p.scriptFont]);
 const current=Math.max(0,p.paintings.findLastIndex(s=>s.start<=t));
 const scene=p.paintings[current];const age=t-scene.start;
 const previous=p.paintings[Math.max(0,current-1)];const blend=current?interpolate(age,[0,1.15],[0,1],clamp):1;
 const lyric=p.lyrics.find(l=>t>=l.start&&t<l.end);
 const la=lyric?t-lyric.start:0;const remaining=lyric?lyric.end-t:1;
 const reveal=lyric?Math.min(.75,(lyric.end-lyric.start)*.23):.75;
 const exitFade=lyric&&lyric.end-lyric.start<2?.12:.22;
 const opacity=lyric?(lyric.start===0?1:interpolate(la,[0,Math.min(.3,reveal)],[0,1],clamp))*interpolate(remaining,[0,exitFade],[0,1],clamp):0;
 const ending=t>=p.duration;const last=p.paintings[p.paintings.length-1];
 const heroSize=lyric&&lyric.hero.length>11?135:180;
 return <AbsoluteFill style={{backgroundColor:'#101A32',overflow:'hidden'}}>
  {p.audio?<Html5Audio src={staticFile(p.audio)}/>:null}
  {[previous,ending?last:scene].map((bg,i)=><AbsoluteFill key={i} style={{opacity:i?blend:1,transform:`scale(${1.035+Math.min(age,12)*.0025}) translateX(${Math.sin(t*.12)*6}px)`,transformOrigin:'50% 60%'}}><Img src={staticFile(bg.image)} style={{width:'100%',height:'100%',objectFit:'cover'}}/></AbsoluteFill>)}
  <AbsoluteFill style={{background:'linear-gradient(180deg, rgba(8,14,30,.12) 0%, rgba(8,14,30,.58) 27%, rgba(8,14,30,.48) 55%, rgba(8,14,30,.08) 78%, rgba(8,14,30,.44) 100%)'}}/>
  <AbsoluteFill style={{background:'radial-gradient(ellipse at center, transparent 35%, rgba(4,8,22,.42) 100%)'}}/>
  {lyric?<div style={{position:'absolute',left:75,top:615,width:850,textAlign:'center',opacity,translate:`0px ${interpolate(la,[0,.8],[14,0],clamp)}px`}}>
   <div style={{fontFamily:p.serifFont?'PaintSerif':'Georgia',fontStyle:'italic',fontSize:72,lineHeight:1.18,color:'#F7EBD8',textShadow:'0 3px 16px #071225',minHeight:88}}>{lyric.above}</div>
   <div style={{fontFamily:p.scriptFont?'PaintScript':'cursive',fontSize:heroSize,lineHeight:1.2,color:'#F1D28D',paddingTop:12,paddingBottom:14,textShadow:'0 2px 6px #10203D, 0 0 16px #E5B55B55',scale:1+.008*Math.sin(la*.8),clipPath:`inset(0 ${interpolate(la,[0,reveal],[100,0],clamp)}% 0 0)`}}>{lyric.hero}</div>
   <div style={{fontFamily:p.serifFont?'PaintSerif':'Georgia',fontStyle:'italic',fontSize:72,lineHeight:1.2,color:'#F7EBD8',textShadow:'0 3px 16px #071225',opacity:interpolate(la,[.22,.75],[0,1],clamp)}}>{lyric.below}</div>
  </div>:null}
  {ending?<div style={{position:'absolute',left:95,top:700,width:810,textAlign:'center',color:'#F7EBD8',fontFamily:p.serifFont?'PaintSerif':'Georgia',fontStyle:'italic',fontSize:65,lineHeight:1.18,opacity:interpolate(t-p.duration,[0,.6],[0,1],clamp),textShadow:'0 2px 16px #08142F'}}>Follow {p.handle}<br/><span style={{fontSize:53,color:'#F1D28D'}}>for art that feels.</span></div>:null}
  <div style={{position:'absolute',left:90,top:1400,width:820,textAlign:'center',fontFamily:p.serifFont?'PaintSerif':'Georgia',fontSize:29,letterSpacing:2,color:'#EFE4D5',opacity:.5}}>{p.handle}</div>
 </AbsoluteFill>;
};
