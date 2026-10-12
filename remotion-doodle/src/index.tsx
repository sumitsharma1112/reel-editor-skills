import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {DoodleReel} from './DoodleReel';
import {BrandedReel} from './BrandedReel';
import {ColourfulReel} from './ColourfulReel';
const Root=()=> <>
 <Composition id="DoodleReel" component={DoodleReel} fps={30} width={1080} height={1920} durationInFrames={180}
  defaultProps={{duration:6,scenes:[{start:0,end:3,lines:['White-page doodles'],motion:'none'},{start:3,end:6,lines:['A page turns'],motion:'hinge'}]}}
  calculateMetadata={({props})=>({durationInFrames:Math.ceil(props.duration*30)})}/>
 <Composition id="BrandedReel" component={BrandedReel} fps={30} width={1080} height={1920} durationInFrames={360}
  defaultProps={{duration:6,scenes:[{start:0,end:6,lines:['Your reel'],motion:'none'}],introSeconds:2.5,outroSeconds:3.5,handle:'@yourpage',introLines:['Made with ChatGPT','No manual editing'],outroLines:['Want to learn?','Follow my page']}}
  calculateMetadata={({props})=>({durationInFrames:Math.round(props.introSeconds*30)+Math.ceil(props.duration*30)+Math.round(props.outroSeconds*30)})}/>
 <Composition id="ColourfulReel" component={ColourfulReel} fps={30} width={1080} height={1920} durationInFrames={300}
  defaultProps={{duration:6,outroSeconds:4,handle:'@yourpage',scenes:[{start:0,background:'#FFF1DA'}],energy:[],beats:[]}}
  calculateMetadata={({props})=>({durationInFrames:Math.ceil((props.duration+props.outroSeconds)*30)})}/>
</>;
registerRoot(Root);
