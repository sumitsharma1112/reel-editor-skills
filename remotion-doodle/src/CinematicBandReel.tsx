import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Html5Audio,Loop,OffthreadVideo,Sequence,continueRender,delayRender,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
type Clip={start:number;end:number;video:string;sourceDuration:number;speed:number};
type Word={start:number;end:number;text:string};
export type BandProps={duration:number;clips:Clip[];words:Word[];audio?:string;font?:string;colour:string;outroStart?:number;handle?:string};
export const CinematicBandReel:React.FC<BandProps>=p=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();const t=f/fps;
 const [h]=useState(()=>delayRender('Band lyric font'));
 useEffect(()=>{if(!p.font){continueRender(h);return;}const face=new FontFace('BandSerif',`url(${staticFile(p.font)})`);face.load().then(x=>{document.fonts.add(x);continueRender(h)}).catch(()=>continueRender(h));},[p.font,h]);
 const word=p.words.find(w=>w.start<=t&&t<w.end);
 const age=word?t-word.start:0;const remaining=word?word.end-t:1;
 return <AbsoluteFill style={{backgroundColor:'black'}}>
  {p.audio?<Html5Audio src={staticFile(p.audio)}/>:null}
  <div style={{position:'absolute',left:0,top:555,width:1080,height:810,overflow:'hidden'}}>
   {p.clips.map((c,i)=><Sequence key={i} from={Math.round(c.start*fps)} durationInFrames={Math.round((c.end-c.start)*fps)} premountFor={fps} name={`Cinematic scene ${i+1}`}>
    <Loop durationInFrames={Math.max(1,Math.round(c.sourceDuration*fps/c.speed))}>
     <OffthreadVideo src={staticFile(c.video)} muted playbackRate={c.speed} style={{width:1080,height:810,objectFit:'cover'}}/>
    </Loop>
   </Sequence>)}
   {word?<div style={{position:'absolute',left:110,top:195,width:860,textAlign:'center',fontFamily:p.font?'BandSerif':'Georgia',fontSize:word.text.length>12?130:165,color:p.colour,scale:'0.8 1',opacity:Math.min(interpolate(age,[0,.1],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),interpolate(remaining,[0,.1],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})),translate:`0px ${interpolate(age,[0,.18],[12,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}px`}}>{word.text}</div>:null}
  </div>
  {p.outroStart!==undefined&&t>=p.outroStart?<div style={{position:'absolute',top:970,left:110,width:860,textAlign:'center',color:'#F6EBD6',fontFamily:'Georgia',fontSize:46,background:'rgba(0,0,0,.65)',padding:'32px 12px',opacity:interpolate(t-p.outroStart,[0,.4],[0,1],{extrapolateRight:'clamp'})}}>Follow for more soulful reels<div style={{fontSize:35,marginTop:16}}>{p.handle}</div></div>:null}
 </AbsoluteFill>;
};
