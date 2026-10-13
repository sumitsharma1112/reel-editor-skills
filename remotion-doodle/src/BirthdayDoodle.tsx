import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Html5Audio,continueRender,delayRender,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
type Props={duration:number;audio:string;name:string;font?:string;energy:number[];beats:number[]};
const ink='#24202A';
const Cake:React.FC<{x:number;y:number;s?:number;tilt?:number}>=({x,y,s=1,tilt=0})=><g transform={`translate(${x} ${y}) rotate(${tilt}) scale(${s})`} stroke={ink} strokeWidth="5" strokeLinejoin="round"><path d="M-95 0 L95 0 L95 88 L-95 88Z" fill="#FFD87E"/><path d="M-95 25 Q-80 55 -65 25 Q-50 55 -35 25 Q-20 55 -5 25 Q10 55 25 25 Q40 55 55 25 Q70 55 95 25 L95 0 L-95 0Z" fill="#F5A6C7"/><path d="M-115 94 H115" fill="none"/>{[-48,0,48].map(v=><g key={v}><path d={`M${v} -45 V0`} stroke="#64BDD1" strokeWidth="11"/><path d={`M${v} -49 Q${v-12} -67 ${v} -82 Q${v+13} -62 ${v} -49`} fill="#FFD866" strokeWidth="3"/></g>)}</g>;
const Gift:React.FC<{x:number;y:number;open?:number}>=({x,y,open=0})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth="5"><rect x="-82" y="0" width="164" height="115" rx="7" fill="#AFD8B9"/><path d="M0 0 V115" stroke="#FFABBB" strokeWidth="22"/><g transform={`translate(0 ${-open*100}) rotate(${open*12})`}><rect x="-93" y="-25" width="186" height="31" rx="5" fill="#AFE0C8"/><path d="M0 -23 Q-100 -80 -46 -75 Q-14 -73 0 -23 Q18 -75 52 -73 Q100 -65 0 -23" fill="#FFABBB"/></g></g>;
const Blob:React.FC<{x:number;y:number;scale?:number;phase:number;level:number;colour:string;hat?:boolean;pose?:string;party?:boolean}>=({x,y,scale=1,phase,level,colour,hat=true,pose='dance',party=false})=>{
 const swing=Math.sin(phase),bounce=Math.abs(Math.sin(phase))*(pose==='dance'?24:7);const left=-55+75*swing,right=55-75*swing;
 return <g transform={`translate(${x} ${y-bounce}) rotate(${swing*3}) scale(${scale})`} stroke={ink} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round">
  <path d="M-85 -55 Q-87 -155 -15 -174 Q79 -195 91 -57 L83 95 Q16 122 -83 95 Z" fill={party?colour:'#FFFFFF'}/>
  {hat?<g transform={`rotate(${swing*3} 0 -168)`}><path d="M-48 -158 L12 -268 L61 -172 Z" fill={colour}/><path d="M-28 -193 L36 -210 M-12 -220 L26 -239" stroke="#fff" strokeWidth="8"/><circle cx="12" cy="-270" r="12" fill="#FFD671"/></g>:null}
  <ellipse cx="-30" cy="-92" rx="7" ry="9" fill={ink}/><ellipse cx="39" cy="-99" rx="7" ry="9" fill={ink}/>
  <ellipse cx="-50" cy="-60" rx="16" ry="8" fill="#FFBDCC" stroke="none"/><ellipse cx="59" cy="-67" rx="16" ry="8" fill="#FFBDCC" stroke="none"/>
  <ellipse cx="8" cy="-53" rx={18+level*8} ry={6+level*25} fill="#8B3455" strokeWidth="3"/>
  <path d={`M-77 -29 Q-128 ${left} -153 ${pose==='cake'?20:left-28}`} fill="none"/>
  <path d={`M87 -38 Q131 ${right} 160 ${pose==='cake'?20:right-35}`} fill="none"/>
  <path d={`M-48 102 L${-50-swing*25} 180 L${-93-swing*35} ${185-Math.max(0,swing)*38}`} fill="none"/>
  <path d={`M47 108 L${54+swing*24} 179 L${93+swing*35} ${187-Math.max(0,-swing)*38}`} fill="none"/>
 </g>;
};
export const BirthdayDoodle:React.FC<Props>=p=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();const t=f/fps;const level=p.energy[Math.min(f,p.energy.length-1)]??.2;
 const beat=p.beats.reduce((v,b)=>b<=f?Math.max(v,Math.exp(-(f-b)/5)):v,0);const phase=t*6.3;
 const [h]=useState(()=>delayRender('Birthday type'));
 useEffect(()=>{if(!p.font){continueRender(h);return;}const face=new FontFace('BirthdayInk',`url(${staticFile(p.font)})`);face.load().then(x=>{document.fonts.add(x);continueRender(h)}).catch(()=>continueRender(h));},[h,p.font]);
 const scene=t<5?0:t<11?1:t<17?2:t<23?3:t<29?4:t<35?5:6;
 const titles=[`HAPPY BIRTHDAY\n${p.name}!`,'OYE!\nNACHO SAARE!','BHANGRA MODE:\nFULL ON!','CAKE NU\nBACHAAO!','GIFT KHOLIYE?',`SAADI ${p.name}\nDI PARTY!`,`HAPPY BIRTHDAY\n${p.name}!`];
 const jokes=['birthday loading...','pair rukde hi nahi!','dhol loud. mood louder.','cake vi bhangra pa reha!','surprise da surprise!','saare nacho, saare hasso!','khush raho. nachde raho.'];
 return <AbsoluteFill style={{background:'#FFFEFA',overflow:'hidden'}}>
  <Html5Audio src={staticFile(p.audio)}/>
  <div style={{position:'absolute',top:300,left:75,width:850,textAlign:'center',fontFamily:'BirthdayInk, sans-serif',fontWeight:900,fontSize:70,lineHeight:1.09,whiteSpace:'pre-line',color:ink,transform:`rotate(${Math.sin(t*2)*1.5}deg) scale(${1+beat*.025})`}}>{titles[scene]}</div>
  <svg width="1080" height="1920" viewBox="0 0 1080 1920" style={{position:'absolute'}}>
   {Array.from({length:23},(_,i)=>{const x=80+(i*139)%900;const y=620+((i*197+f*1.1)%800);return <g key={i} transform={`translate(${x} ${y}) rotate(${i*32+f*.6})`} opacity=".65"><path d={i%3===0?'M-7 0 L7 0':i%3===1?'M0 -9 L0 9':'M-6 -5 L6 5'} stroke={['#F5A6C7','#7AC5D5','#F2CF68','#A4D9B0'][i%4]} strokeWidth="5" strokeLinecap="round"/></g>})}
   {scene===0?<><Blob x={510} y={1040} phase={phase*.6} level={level} colour="#F4A9CA" pose="cake"/><Cake x={315} y={1000} s={.75} tilt={Math.sin(t*3)*5}/><g transform={`translate(770 ${830+Math.sin(t*2)*15})`} stroke={ink} strokeWidth="4"><path d="M0 0 Q-40 190 -80 290" fill="none"/><ellipse cx="0" cy="0" rx="43" ry="60" fill="#8ED5C0"/><ellipse cx="60" cy="-35" rx="43" ry="60" fill="#F9BCD2"/><path d="M60 25 Q20 205 -80 290" fill="none"/></g></>:null}
   {scene===1?<><Blob x={260} y={1080} scale={.8} phase={phase} level={level*.7} colour="#9ED6C2"/><Blob x={540} y={980} scale={1.08} phase={phase+.8} level={level} colour="#FFB9D1"/><Blob x={810} y={1090} scale={.8} phase={phase+2} level={level*.6} colour="#A6D4F1"/></>:null}
   {scene===2?<><Blob x={560} y={1050} scale={1.15} phase={phase} level={level} colour="#8CCADC"/><g transform={`translate(560 ${1090+beat*8}) rotate(${Math.sin(phase)*6})`} stroke={ink} strokeWidth="5"><rect x="-128" y="-38" width="256" height="126" rx="52" fill="#F3CB83"/><ellipse cx="-106" cy="25" rx="25" ry="59" fill="#FFF4D7"/><ellipse cx="106" cy="25" rx="25" ry="59" fill="#FFF4D7"/><path d="M-90 -32 L80 82 M-80 82 L90 -32" stroke="#DB9275"/></g><Blob x={230} y={1130} scale={.57} phase={phase+2} level={level*.5} colour="#FFADC7"/><Blob x={840} y={1130} scale={.57} phase={phase+1} level={level*.5} colour="#AAD8A4"/></>:null}
   {scene===3?<><Blob x={240} y={1060} scale={.85} phase={phase*1.4} level={level} colour="#9AD6CF" pose="cake"/><Blob x={820} y={1060} scale={.85} phase={phase*1.4+2} level={level} colour="#F4AFCC" pose="cake"/><Cake x={540+Math.sin(t*5)*70} y={1100-Math.abs(Math.sin(t*5))*80} s={1.35} tilt={Math.sin(t*5)*19}/></>:null}
   {scene===4?<><Blob x={400} y={1030} scale={1.0} phase={phase*.7} level={level} colour="#BEB3E1"/><Gift x={670} y={1180} open={Math.max(0,Math.sin((t-23)*1.4))}/><g transform={`translate(690 ${1030-Math.max(0,Math.sin((t-23)*1.4))*100})`}><text fontSize="100" textAnchor="middle" fill="#E39C4B">★</text></g></>:null}
   {scene===5?<><Blob x={220} y={1120} scale={.74} phase={phase} level={level*.6} colour="#96D8CC"/><Blob x={520} y={990} scale={1.12} phase={phase+.6} level={level} colour="#F5AECA" party/><Blob x={840} y={1120} scale={.74} phase={phase+2} level={level*.6} colour="#A8D0ED"/><Cake x={535} y={1390} s={.9} tilt={Math.sin(phase)*4}/></>:null}
   {scene===6?<><Blob x={240} y={1100} scale={.74} phase={phase} level={level*.5} colour="#93D4C7"/><Blob x={520} y={1040} scale={1.03} phase={phase+1} level={level} colour="#FAB2CA" party/><Blob x={820} y={1100} scale={.74} phase={phase+2} level={level*.5} colour="#B4C8EE"/><Cake x={520} y={1320} s={.9} tilt={Math.sin(phase)*5}/><Gift x={825} y={1325}/></>:null}
  </svg>
  <div style={{position:'absolute',top:1490,left:95,width:820,textAlign:'center',fontFamily:'BirthdayInk, sans-serif',fontSize:34,color:'#706878'}}>{jokes[scene]}</div>
 </AbsoluteFill>;
};
