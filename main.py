import cv2
import time,  math, numpy as np
import HandTrackingModule as htm
import pyautogui, autopy
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3,wCam)
cap.set(4,hCam)
pTime = 0
#cTime = 0
frameR = 100

#손 인식 떨림 방지를 위해 매개변수 값 조정
detector = htm.handDetector(maxHands=1, detectionCon=0.5, trackCon=0.5)

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()   #(-63.5, 0.0, 0.5) min max

minVol = -63
maxVol = volRange[1]
print(volRange)
hmin = 50
hmax = 200
volBar = 400
volPer = 0
vol = 0
color = (0,215,255)

tipIds = [4, 8, 12, 16, 20]
mode = ''
active = 0

pyautogui.FAILSAFE = False
while True:
    success, img = cap.read()
    img = cv2.flip(img, 1) # 화면을 좌우반전시켜 손가락이 왼쪽으로 움직이면 커서도 왼쪽으로 움직이도록 변경
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

   # print(lmList)
    fingers = []

    if len(lmList) != 0:

        #Thumb
        if lmList[tipIds[0]][1] > lmList[tipIds[-1]][1]:
            if lmList[tipIds[0]][1] >= lmList[tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        elif lmList[tipIds[0]][1] < lmList[tipIds[0 -1]][1]:
            if lmList[tipIds[0]][1] <= lmList[tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        for id in range(1,5):
            if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)


      #  print(fingers)
        if (fingers == [0,0,0,0,0]) & (active == 0 ):
            mode='N'
        elif (fingers == [0, 1, 0, 0, 0] or fingers == [0, 1, 1, 0, 0]) & (active == 0 ):
            mode = 'Scroll'
            active = 1
        elif (fingers == [1, 1, 0, 0, 0] ) & (active == 0 ):
             mode = 'Volume'
             active = 1
        elif (fingers == [1 ,1 , 1, 1, 1] ) & (active == 0 ):
             mode = 'Cursor'
             active = 1

############# Scroll 👇👇👇👇##############
    if mode == 'Scroll':
        active = 1
     #   print(mode)
        putText(mode)
        cv2.rectangle(img, (200, 410), (245, 460), (255, 255, 255), cv2.FILLED)
        if len(lmList) != 0:
            if fingers == [0,1,0,0,0]:
              #print('up')
              #time.sleep(0.1)
                putText(mode = 'U', loc=(200, 455), color = (0, 255, 0))
                pyautogui.scroll(300)

            if fingers == [0,1,1,0,0]:
                #print('down')
              #  time.sleep(0.1)
                putText(mode = 'D', loc =  (200, 455), color = (0, 0, 255))
                pyautogui.scroll(-300)
            elif fingers == [0, 0, 0, 0, 0]:
                active = 0
                mode = 'N'
################# Volume 👇👇👇####################
    if mode == 'Volume':
        active = 1
       #print(mode)
        putText(mode)
        if len(lmList) != 0:
            if fingers[-1] == 1:
                active = 0
                mode = 'N'
                print(mode)

            else:

                 #   print(lmList[4], lmList[8])
                    x1, y1 = lmList[4][1], lmList[4][2]
                    x2, y2 = lmList[8][1], lmList[8][2]
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    cv2.circle(img, (x1, y1), 10, color, cv2.FILLED)
                    cv2.circle(img, (x2, y2), 10, color, cv2.FILLED)
                    cv2.line(img, (x1, y1), (x2, y2), color, 3)
                    cv2.circle(img, (cx, cy), 8, color, cv2.FILLED)

                    length = math.hypot(x2 - x1, y2 - y1)
                    # print(length)

                    # hand Range 50-300
                    # Volume Range -65 - 0
                    vol = np.interp(length, [hmin, hmax], [minVol, maxVol])
                    volBar = np.interp(vol, [minVol, maxVol], [400, 150])
                    volPer = np.interp(vol, [minVol, maxVol], [0, 100])
                    print(vol)
                    volN = int(vol)
                    if volN % 4 != 0:
                        volN = volN - volN % 4
                        if volN >= 0:
                            volN = 0
                        elif volN <= -64:
                            volN = -64
                        elif vol >= -11:
                            volN = vol

                #    print(int(length), volN)
                    volume.SetMasterVolumeLevel(vol, None)
                    if length < 50:
                        cv2.circle(img, (cx, cy), 11, (0, 0, 255), cv2.FILLED)

                    cv2.rectangle(img, (30, 150), (55, 400), (209, 206, 0), 3)
                    cv2.rectangle(img, (30, int(volBar)), (55, 400), (215, 255, 127), cv2.FILLED)
                    cv2.putText(img, f'{int(volPer)}%', (25, 430), cv2.FONT_HERSHEY_COMPLEX, 0.9, (209, 206, 0), 3)


#######################################################################
    if mode == 'Cursor':
        active = 1
        #print(mode)
        putText(mode) #캠 켜지기 전에 손들고 있으면 mode값 없다고 에러남
        # 커서 박스 크기, 위치 조정
        cv2.rectangle(img, (frameR, frameR - 50), (wCam-frameR, hCam-frameR-50), (255, 255, 255), 3)

        if fingers[1:] == [0,0,0,0]: #thumb excluded
            active = 0
            mode = 'N'
            print(mode)
        else: # 박스 끝으로 손가락이 움직이면 화면 끝으로 움직이도록 수정함
            if len(lmList) != 0:
                x1, y1 = lmList[8][1], lmList[8][2]
                w, h = autopy.screen.size()
                X = int(np.interp(x1, [frameR, wCam - frameR], [0, w]))
                Y = int(np.interp(y1, [frameR - 50, hCam - frameR - 50], [0, h]))
                cv2.circle(img, (lmList[8][1], lmList[8][2]), 7, (255, 255, 255), cv2.FILLED)
                cv2.circle(img, (lmList[4][1], lmList[4][2]), 10, (0, 255, 0), cv2.FILLED)  #thumb

                if X%2 !=0:
                    X = X - X%2
                if Y%2 !=0:
                    Y = Y - Y%2
                print(w-X,Y)
                #autopy.mouse.move(w-X,Y)
                # 손가락이 박스 바깥으로 나가면 발생하던 out of range 에러 예외처리
                try:
                    autopy.mouse.move(X, Y)
                except:
                    if X > w - 1 and Y > h - 1:
                        autopy.mouse.move(w - 1, h - 1)
                    elif X > w - 1:
                        autopy.mouse.move(w - 1, Y)
                    elif Y > h - 1:
                        autopy.mouse.move(X, h - 1)

              #  pyautogui.moveTo(X,Y)
                if fingers[0] == 0:
                    cv2.circle(img, (lmList[4][1], lmList[4][2]), 10, (0, 0, 255), cv2.FILLED)  # thumb
                    pyautogui.click()
                    print("click")

    cTime = time.time()
    fps = 1/((cTime + 0.01)-pTime)
    pTime = cTime

    cv2.putText(img,f'FPS:{int(fps)}',(480,50), cv2.FONT_ITALIC,1,(255,0,0),2)
    cv2.imshow('Hand LiveFeed',img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    def putText(mode,loc = (250, 450), color = (0, 255, 255)):
        cv2.putText(img, str(mode), loc, cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    3, color, 3)