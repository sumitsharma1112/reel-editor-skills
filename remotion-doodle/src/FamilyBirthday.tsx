import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Html5Audio,Img,continueRender,delayRender,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
type Props={duration:number;image:string;audio:string;name:string;font?:string;energy:number[];beats:number[]};
export const FamilyBirthday:React.FC<Props>=p=>{
 const frame=useCurrentFrame();const {fps}=useVideoConfig();const t=frame/fps;
 const level=p.energy[Math.min(frame,p.energy.length-1)]??.3;
 const beat=p.beats.reduce((v,b)=>b<=frame?Math.max(v,Math.exp(-(frame-b)/5)):v,0);
 const [h]=useState(()=>delayRender('Family birthday captions'));
 useEffect(()=>{if(!p.font){continueRender(h);return;}const f=new FontFace('FamilyInk',`url(${staticFile(p.font)})`);f.load().then(x=>{document.fonts.add(x);continueRender(h)}).catch(()=>continueRender(h));},[h,p.font]);
 const shots=[{start:0,scale:1,origin:'50% 50%'},{start:10,scale:1.19,origin:'49% 50%'},{start:17,scale:1.1,origin:'70% 57%'},{start:24,scale:1.13,origin:'34% 50%'},{start:31,scale:1.03,origin:'50% 50%'}];
 const i=shots.findLastIndex(s=>s.start<=t);const sh=shots[Math.max(0,i)];const prev=shots[Math.max(0,i-1)];const zoom=interpolate(t-sh.start,[0,.6],[prev.scale,sh.scale],{extrapolateRight:'clamp'})+Math.sin(t*.5)*.004;
 const captions=[`HAPPY BIRTHDAY, ${p.name}!`,'OYE! NACHO SAARE!','BHANGRA PAO!','CAKE VI READY AA!',`SAADI ${p.name} DI PARTY!`];
 const ci=t<8?0:t<16?1:t<24?2:t<31?3:4;
 return <AbsoluteFill style={{background:'#BD8554',overflow:'hidden'}}>
  <Html5Audio src={staticFile(p.audio)}/>
  <AbsoluteFill style={{transform:`scale(${zoom}) translateY(${Math.sin(t*.7)*2}px)`,transformOrigin:sh.origin}}>
   <Img src={staticFile(p.image)} style={{width:1080,height:1920,objectFit:'cover'}}/>
   <svg width="1080" height="1920" viewBox="0 0 1080 1920" style={{position:'absolute'}}>
    <defs><clipPath id="leadMouth"><path d="M505 908 Q530 917 556 919 Q550 950 524 949 Q511 943 505 908Z"/></clipPath><clipPath id="girlMouth"><path d="M876 1012 Q895 1024 917 1024 Q912 1048 893 1046 Q881 1043 876 1012Z"/></clipPath></defs>
    <g clipPath="url(#leadMouth)"><rect x="500" y="902" width="62" height="53" fill="#682218"/><ellipse cx="531" cy={937-level*5} rx={17+level*4} ry={5+level*8} fill="#E96051"/><path d={`M506 911 Q531 ${916+level*3} 555 920`} stroke="#FFF3DC" strokeWidth="7" fill="none"/></g>
    <g clipPath="url(#girlMouth)"><rect x="872" y="1009" width="51" height="42" fill="#682218"/><ellipse cx="896" cy="1041" rx="13" ry={3+level*5} fill="#E96051"/><path d="M877 1015 Q896 1025 917 1025" stroke="#FFF1DC" strokeWidth="5" fill="none"/></g>
    {Array.from({length:14},(_,j)=>{const x=80+j*67;const y=450+((frame*1.25+j*123)%1000);return <path key={j} d="M-5 -8 L5 8" transform={`translate(${x} ${y}) rotate(${j*32+frame})`} stroke={['#FFE092','#FAAFBF','#83C8D4','#B7DD9A'][j%4]} strokeWidth="5" strokeLinecap="round" opacity={.25+beat*.4}/>})}
    {[60,91,135].map((x,j)=><ellipse key={x} cx={x} cy={1300+Math.sin(t*7+j)*4} rx="5" ry={10+beat*4} fill="#FFDB69" opacity=".7"/>)}
   </svg>
  </AbsoluteFill>
  <div style={{position:'absolute',top:300,left:80,width:850,textAlign:'center',fontFamily:'FamilyInk, sans-serif',fontSize:55,fontWeight:900,lineHeight:1.15,color:'#FFE182',background:'rgba(25,18,20,.88)',padding:'22px 18px',borderRadius:22,transform:`scale(${1+beat*.01})`}}>{captions[ci]}</div>
 </AbsoluteFill>;
};
