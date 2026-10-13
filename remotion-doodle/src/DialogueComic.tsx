import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Html5Audio,Img,continueRender,delayRender,interpolate,staticFile,useCurrentFrame} from 'remotion';
type Line={start:number;end:number;text:string;speaker:number;left:number;right:number;object:string};
type Props={duration:number;audio:string;handle?:string;font?:string;poses:string[];lines:Line[]};
const ink='#302921';
const Cat:React.FC<{x:number;y:number;mask?:boolean;s?:number}>=({x,y,mask=false,s=1})=><g transform={`translate(${x} ${y}) scale(${s})`} stroke={ink} strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"><path d="M-40 18 Q-100 60 -68 118 Q0 145 60 116 L43 24" fill="#D7A464"/><path d="M62 104 Q143 92 110 20" fill="none" stroke="#D7A464" strokeWidth="20"/><path d="M-60 -18 L-55 -88 L-13 -56 L31 -60 L62 -87 L63 -10 Q57 59 0 55 Q-66 55 -60 -18Z" fill="#DAB57D"/><path d="M-50 -69 L-23 -54 M40 -57 L55 -69" stroke="#C2757D" strokeWidth="9"/><circle cx="-27" cy="-7" r="7" fill={ink}/><circle cx="31" cy="-7" r="7" fill={ink}/><path d="M-3 13 L9 13 L3 20Z" fill="#AB6770"/><path d="M3 20 Q-9 31 -18 23 M3 20 Q13 31 21 23 M-35 14 L-80 8 M-35 22 L-77 29 M35 15 L82 8 M36 24 L77 32" fill="none" strokeWidth="3"/>{mask?<><path d="M-42 5 Q3 -4 44 7 L36 37 Q1 49 -38 35Z" fill="#A5CED0"/><path d="M-39 14 L-64 1 M42 14 L64 1 M-27 18 H29 M-26 28 H28" stroke="#648E94" strokeWidth="3"/></>:null}</g>;
const Bowl:React.FC<{x:number;y:number;up?:boolean}>=({x,y,up=false})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth="4">{up?<><path d="M-88 46 Q-66 -28 0 -28 Q64 -28 89 46Z" fill="#7BA5AF"/><ellipse cx="0" cy="45" rx="91" ry="12" fill="#91B4BD"/></>:<><path d="M-87 0 Q-72 73 0 74 Q75 71 89 0Z" fill="#7BA5AF"/><ellipse cx="0" cy="0" rx="88" ry="21" fill="#FFF3DD"/></>}</g>;
const Dog:React.FC<{x:number;y:number}>=({x,y})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth="5" strokeLinejoin="round"><path d="M-55 29 Q-82 102 -53 139 H52 Q71 89 43 21Z" fill="#A77550"/><path d="M-62 -34 Q0 -93 60 -29 L42 43 Q0 70 -44 38Z" fill="#B98960"/><path d="M-59 -32 Q-116 -10 -82 62 L-52 18 M57 -32 Q104 -16 80 63 L50 18" fill="#744D37"/><circle cx="-24" cy="-9" r="6"/><circle cx="27" cy="-9" r="6"/><ellipse cy="18" rx="13" ry="8" fill={ink}/><path d="M0 27 V45"/><path d="M-12 37 Q0 50 13 37" fill="none"/><path d="M-13 47 V66 Q0 77 13 66 V48" fill="#DA8C96"/><path d="M-30 94 V139 M31 94 V139" fill="none"/></g>;
export const DialogueComic:React.FC<Props>=p=>{
 const frame=useCurrentFrame();const t=frame/30;const idx=Math.max(0,p.lines.findLastIndex(x=>x.start<=t));const line=p.lines[idx];
 const [h]=useState(()=>delayRender('Comic lettering'));
 useEffect(()=>{if(!p.font){continueRender(h);return;}const f=new FontFace('ComicInk',`url(${staticFile(p.font)})`);f.load().then(x=>{document.fonts.add(x);continueRender(h)}).catch(()=>continueRender(h));},[h,p.font]);
 const age=t-line.start;const settle=interpolate(age,[0,.18],[12,0],{extrapolateRight:'clamp'});
 const obj=line.object;
 return <AbsoluteFill style={{background:'#B49774',overflow:'hidden'}}>
  <Html5Audio src={staticFile(p.audio)}/>
  {p.handle?<div style={{position:'absolute',left:85,top:240,fontFamily:'sans-serif',fontSize:30,color:'#FFF2D9',opacity:.9}}>{p.handle}</div>:null}
  <svg width="1080" height="1920" viewBox="0 0 1080 1920" style={{position:'absolute'}}>
   <path d={line.speaker===0?'M120 310 Q510 270 920 310 Q998 333 990 488 L974 682 Q970 754 813 768 L370 770 L245 871 L272 764 Q92 758 80 682 L72 403 Q70 332 120 310Z':'M120 310 Q510 270 920 310 Q998 333 990 488 L974 682 Q970 754 813 768 L813 764 L857 862 L699 770 L233 770 Q92 758 80 682 L72 403 Q70 332 120 310Z'} fill="#FFFCF3" stroke={ink} strokeWidth="5"/>
   <path d="M80 1490 Q535 1483 1000 1490" stroke="#80684C" strokeWidth="3" fill="none"/>
   {obj==='money'?<g><rect x="355" y="1260" width="370" height="154" rx="18" fill="#E6D9AD" stroke={ink} strokeWidth="4"/><text x="540" y="1365" textAnchor="middle" fontFamily="sans-serif" fontSize="65" fontWeight="bold" fill={ink}>₹5,000</text></g>:null}
   {['bowl','up','mask','frame','dog'].includes(obj)?<g transform={`translate(0 ${Math.sin(t*2)*2})`}>
    {obj==='frame'?<rect x="307" y="1222" width="235" height="255" rx="5" fill="#E1C899" stroke="#6C462C" strokeWidth="18"/>:null}
    <Cat x={obj==='frame'?423:410} y={obj==='frame'?1330:1320} s={obj==='frame'?.85:1} mask={obj==='mask'}/>
    <Bowl x={620} y={1420} up={obj==='up'}/>
    {obj==='dog'?<Dog x={860} y={1308}/>:null}
   </g>:null}
  </svg>
  <div style={{position:'absolute',left:125,top:353,width:790,height:360,display:'flex',alignItems:'center',justifyContent:'center',textAlign:'center',fontFamily:'ComicInk, sans-serif',fontSize:line.text.length>140?48:line.text.length>90?53:67,lineHeight:1.08,color:ink,transform:`translateY(${settle}px)`}}>{line.text}</div>
  {[0,1].map(person=><div key={person} style={{position:'absolute',left:person===0?35:563,top:845,width:480,height:415,opacity:line.speaker===person?1:.91,transform:`translateY(${line.speaker===person?Math.sin(t*4)*3:0}px) rotate(${line.speaker===person?Math.sin(t*2)*.3:0}deg)`}}><Img src={staticFile(p.poses[(person===0?line.left:line.right)*2+person])} style={{width:'100%',height:'100%',objectFit:'contain'}}/></div>)}
 </AbsoluteFill>;
};
