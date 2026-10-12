import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Img,Sequence,continueRender,delayRender,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {DoodleReel,type Props} from './DoodleReel';
export type BrandedProps=Props&{introSeconds:number;outroSeconds:number;handle:string;introLines:string[];outroLines:string[];brandImage?:string};
const Card:React.FC<{lines:string[];image?:string;font?:string;handle?:string}>=({lines,image,font,handle})=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 return <AbsoluteFill style={{background:'white',color:'#9B843E',fontFamily:font?'DoodleSerif':'Georgia',textAlign:'center'}}>
  <div style={{position:'absolute',left:80,top:470,width:820,fontSize:69,lineHeight:1.13,fontStyle:'italic',fontWeight:700}}>
   {lines.map((line,i)=><div key={i} style={{marginBottom:15,opacity:interpolate(f,[i*4,i*4+7],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),translate:`0px ${interpolate(f,[i*4,i*4+7],[20,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}px`}}>{line}</div>)}
  </div>
  {image?<Img src={staticFile(image)} style={{position:'absolute',left:140,top:850,width:700,height:510,objectFit:'contain',translate:`0px ${Math.sin(f/fps*Math.PI*2)*3}px`}}/>:null}
  {handle?<div style={{position:'absolute',left:80,top:1390,width:820,fontSize:58,color:'#20243F',fontWeight:700}}>{handle}</div>:null}
 </AbsoluteFill>;
};
export const BrandedReel:React.FC<BrandedProps>=(props)=>{
 const {fps}=useVideoConfig();
 const [h]=useState(()=>delayRender('Brand font'));
 useEffect(()=>{
  if(!props.font){continueRender(h);return;}
  const face=new FontFace('DoodleSerif',`url(${staticFile(props.font)})`);
  face.load().then(f=>{document.fonts.add(f);continueRender(h)}).catch(()=>continueRender(h));
 },[h,props.font]);
 const intro=Math.round(props.introSeconds*fps),main=Math.ceil(props.duration*fps),outro=Math.round(props.outroSeconds*fps);
 return <AbsoluteFill>
  <Sequence durationInFrames={intro} premountFor={fps} name="Opening hook"><Card lines={props.introLines} image={props.brandImage} font={props.font}/></Sequence>
  <Sequence from={intro} durationInFrames={main} premountFor={fps} name="Bhajan"><DoodleReel {...props}/></Sequence>
  <Sequence from={intro+main} durationInFrames={outro} premountFor={fps} name="Follow message"><Card lines={props.outroLines} image={props.brandImage} font={props.font} handle={props.handle}/></Sequence>
 </AbsoluteFill>;
};
