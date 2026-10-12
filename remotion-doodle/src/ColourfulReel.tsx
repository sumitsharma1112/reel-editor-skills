import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Html5Audio,Img,continueRender,delayRender,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
type Mouth={x:number;y:number;skin:string;r:number};
type Scene={start:number;image?:string;background:string;mouth?:Mouth};
export type ColourProps={duration:number;outroSeconds:number;audio?:string;font?:string;handle:string;scenes:Scene[];endingImage?:string;energy:number[];beats:number[]};
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const Heart:React.FC<{x:number;y:number;s:number;color:string;opacity:number}>=({x,y,s,color,opacity})=><path d="M0 8 C-18 -5 -15 -22 0 -13 C15 -22 18 -5 0 8" transform={`translate(${x} ${y}) scale(${s})`} fill={color} opacity={opacity}/>;
export const ColourfulReel:React.FC<ColourProps>=(props)=>{
 const frame=useCurrentFrame();const {fps}=useVideoConfig();const t=frame/fps;
 const [handle]=useState(()=>delayRender('Colourful doodle font'));
 useEffect(()=>{if(!props.font){continueRender(handle);return;}const face=new FontFace('ColourSerif',`url(${staticFile(props.font)})`);face.load().then(f=>{document.fonts.add(f);continueRender(handle)}).catch(()=>continueRender(handle));},[handle,props.font]);
 const outro=t>=props.duration;
 const idx=Math.max(0,props.scenes.findLastIndex(s=>s.start<=t));const scene=props.scenes[idx];
 const age=frame-Math.round(scene.start*fps);
 const beat=props.beats.reduce((v,b)=>b<=frame?Math.max(v,Math.exp(-(frame-b)/4)):v,0);
 const level=props.energy[Math.min(frame,props.energy.length-1)]??.2;
 const bob=Math.sin(t*Math.PI*2)*5+beat*6;
 const incoming=idx>0&&age<18&&!outro;
 const yaw=incoming?interpolate(age,[0,8,18],[-82,8,0],clamp):0;
 const scale=incoming?interpolate(age,[0,8,18],[.6,1.035,1],clamp):1;
 const image=outro?props.endingImage:scene.image;
 return <AbsoluteFill style={{background:'#382440',perspective:1800,overflow:'hidden'}}>
  {props.audio?<Html5Audio src={staticFile(props.audio)}/>:null}
  <AbsoluteFill style={{background:outro?'#FFF2DA':scene.background,transform:`rotateY(${yaw}deg) scale(${scale})`,backfaceVisibility:'hidden'}}>
   <div style={{position:'absolute',width:880,height:880,left:55,top:510,borderRadius:'50%',background:'radial-gradient(circle, #ffffffc9 0%, #ffffff55 50%, #ffffff00 73%)',scale:1+.03*Math.sin(t)}}/>
   <svg width="1080" height="1920" style={{position:'absolute'}}>
    {Array.from({length:16},(_,i)=>{
      const a=i*2.399;const x=490+Math.cos(a)*(290+(i%3)*30);const y=880+Math.sin(a)*(330+(i%4)*28)+Math.sin(t*1.3+i)*13;
      return <Heart key={i} x={x} y={y} s={.35+(i%3)*.12+beat*.06} color={['#F8A5BE','#E8B353','#9FD7CA','#C7B0E1'][i%4]} opacity={.32+.14*Math.sin(t+i)}/>;
    })}
    {[0,1,2,3,4,5].map(i=><g key={i} transform={`translate(${155+i*145} ${540+Math.sin(t+i)*15}) rotate(${t*15+i*30})`} opacity={.55+beat*.2}><path d="M0 -12 Q2 -2 12 0 Q2 2 0 12 Q-2 2 -12 0 Q-2 -2 0 -12" fill={i%2?'#E4AD4A':'#ED90AF'}/></g>)}
    <ellipse cx="490" cy={outro?1440:1360} rx="240" ry="20" fill="#614F6F" opacity=".08"/>
   </svg>
   {outro?<div style={{position:'absolute',left:90,top:430,width:800,textAlign:'center',fontFamily:props.font?'ColourSerif':'Georgia',fontWeight:700,fontSize:64,lineHeight:1.15,color:'#654160',opacity:interpolate(frame-props.duration*fps,[0,8],[0,1],clamp)}}>Follow {props.handle}<br/>Learn to create reels like this.</div>:null}
   <div style={{position:'absolute',left:100,top:outro?660:580,width:780,height:780,transform:`translateY(${bob}px) rotate(${Math.sin(t*2)*.6}deg) scale(${1+beat*.022})`,transformOrigin:'50% 85%'}}>
    {image?<Img src={staticFile(image)} style={{width:780,height:780,objectFit:'contain'}}/>:<svg viewBox="0 0 1000 1000"><ellipse cx="500" cy="580" rx="250" ry="300" fill="#FFD375" stroke="#44304B" strokeWidth="8"/><circle cx="430" cy="470" r="14"/><circle cx="565" cy="470" r="14"/><path d="M470 535 Q500 560 530 535" fill="none" stroke="#44304B" strokeWidth="8"/></svg>}
    {!outro&&scene.mouth?<svg viewBox="0 0 1000 1000" style={{position:'absolute',inset:0,width:'100%',height:'100%',pointerEvents:'none'}}>
      <ellipse cx={scene.mouth.x} cy={scene.mouth.y} rx={scene.mouth.r} ry={scene.mouth.r*.8} fill={scene.mouth.skin}/>
      <ellipse cx={scene.mouth.x} cy={scene.mouth.y+2} rx={scene.mouth.r*.56} ry={3+level*scene.mouth.r*.46} fill="#743E48"/>
      {level>.35?<ellipse cx={scene.mouth.x} cy={scene.mouth.y+scene.mouth.r*.26} rx={scene.mouth.r*.28} ry={scene.mouth.r*.13} fill="#F19AB0"/>:null}
    </svg>:null}
   </div>
   <div style={{position:'absolute',left:90,top:1455,width:800,textAlign:'center',fontFamily:props.font?'ColourSerif':'Georgia',fontSize:30,lineHeight:1.1,color:'#775870',opacity:.7}}>{props.handle}</div>
  </AbsoluteFill>
 </AbsoluteFill>;
};
