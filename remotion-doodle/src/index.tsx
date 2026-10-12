import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {DoodleReel} from './DoodleReel';
const Root=()=> <Composition id="DoodleReel" component={DoodleReel} fps={30} width={1080} height={1920} durationInFrames={180}
  defaultProps={{duration:6,scenes:[{start:0,end:3,lines:['White-page doodles'],motion:'none'},{start:3,end:6,lines:['A page turns'],motion:'hinge'}]}}
  calculateMetadata={({props})=>({durationInFrames:Math.ceil(props.duration*30)})}/>;
registerRoot(Root);
