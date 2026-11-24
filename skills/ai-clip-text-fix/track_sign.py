import cv2, numpy as np
cap=cv2.VideoCapture('../src/c_postal.mp4'); frames=[]
for i in range(120):
    ok,f=cap.read(); frames.append(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY))
orb=cv2.ORB_create(4000); bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True)
mask=np.zeros((1280,720),np.uint8); mask[:760,:]=255   # building area, above people
H=np.eye(3); Hs=[H.copy()]
kp0,d0=orb.detectAndCompute(frames[0],mask)
prev=(kp0,d0)
for i in range(1,120):
    kp,d=orb.detectAndCompute(frames[i],None)
    m=sorted(bf.match(prev[1],d),key=lambda x:x.distance)[:600]
    src=np.float32([prev[0][x.queryIdx].pt for x in m]); dst=np.float32([kp[x.trainIdx].pt for x in m])
    A,inl=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=2.0)
    A3=np.vstack([A,[0,0,1]]); H=A3@H; Hs.append(H.copy())
    # next keyframe: keep features restricted to upper region in new frame coords
    mk=np.zeros_like(mask); 
    corners=cv2.perspectiveTransform(np.float32([[[0,0]],[[720,0]],[[720,760]],[[0,760]]]),H).reshape(-1,2)
    cv2.fillPoly(mk,[np.int32(corners)],255)
    prev=orb.detectAndCompute(frames[i],mk)
np.save('sign_H.npy',np.array(Hs))
rect=np.float32([[[216,430]],[[566,430]],[[566,504]],[[216,504]]])
for i in [0,40,80,100,119]:
    print(i,cv2.perspectiveTransform(rect,Hs[i]).reshape(-1,2).round().tolist())
