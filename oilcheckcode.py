#coding=utf-8
#!/usr/bin/python3
#像素为640X480
from SimpleCV import Camera, Image, Color
import time
import numpy as np
import math
import ctypes
import lzai

#捕捉图片
def snapshot(cam, x):
    img = cam.getImage().rotate(180)
    img.save("image"+str(x)+".png")
    return img

#识别管子线条用于判断转弯等行为操作
def line(img, number):
    bin = img.binarize()
    # bin.save("bin" + str(number) + ".png")
    lines = bin.findLines(threshold=25, minlinelength=65, maxlinegap=25)  #二值化并且设定参数阈值，线条间距等
    pos = []
    neg = []
    width = []
    height = []
    xc = []
    yc = []
    turn = 0
    tr = 0
    tl = 0
    horizon = 0
    if len(lines.angle()) > 20:
        lines = bin.findLines()
    lines.draw(width=3, color=Color.RED)
    
    #筛选符合要求的线条角度值
    angles = [i for i in range(len(lines.angle())) if ((lines.angle()[i] != 90.0) & ((lines.angle()[i] != -90.0) | (lines.coordinates()[i][0] < 638)))]
    #符合要求的所有线条进行循环
    for i in range(len(lines.angle())):
        if i in angles:
            #所有线条的宽、高、x、y的总和
            width = width + [lines.width()[i]]
            height = height + [lines.height()[i]]
            xc = xc + [lines.coordinates()[i][0]]
            yc = yc + [lines.coordinates()[i][1]]
            if lines.angle()[i] > 35:
                pos = pos + [lines.angle()[i]]
            elif lines.angle()[i] < -35:
                neg = neg + [lines.angle()[i]]
            elif lines.angle()[i] != 0.0:
                #直线角度在-35与35度之间且y坐标在整张图的120与470像素之间（图片总长是480像素）
                if (lines.coordinates()[i][1] >= 120) & (lines.coordinates()[i][1] <= 470):
                    horizon = horizon + 1
                    #连续三次判断是转弯那么进行转弯，防止1次失误判断而进行转弯
                    if horizon >= 3:
                        turn = 1
        else:
            pass
    #求出管子两边以及上下各自的直线坐标
    x_left = np.mean([j for j in xc if j <= np.mean(xc)])
    x_right = np.mean([j for j in xc if j >= np.mean(xc)])
    y_up = np.mean([j for j in yc if j <= np.mean(yc)])
    y_down = np.mean([j for j in yc if j >= np.mean(yc)])
    #np.mean()即numpy.mean()是求平均值
    width_mean = np.mean(width)
    height_mean = np.mean(height)
    #由于当右上角有转弯管子的时候所有线的宽是远大于高的，故而有如下条件判断转弯
    if (width_mean >= 10 * height_mean) & (638.0 not in lines.length()) & (-90.0 in lines.angle()) & (x_right >= 400):
        turn = 1
    #随着机器鱼的前进以及视野，当最低Y坐标大于300转弯
    if (y_up >= 300) & (len(lines.length()) >= 5):
        turn = 1
    if (x_left >= 350) & (y_up >= 245):
        turn = 1
    #simplecv里面角度正负判定：当角指向左为负，当角指向右为正
    #故而当没有>35度的角，有<-35度，那么管子应该是斜向左上方，鱼要右转
    if (pos == []) & (neg != []):
        angle = np.mean(neg)
        if (abs(angle) >= 75) & (abs(angle) <= 82) & (abs(x_right - x_left) >= 100) & (x_right >= 440):
            tr = 1
    elif (neg == []) & (pos != []) :
        angle = np.mean(pos)
        if (abs(angle) >= 75) & (abs(angle) <= 82) & (abs(x_right - x_left) >= 100) & (x_left <= 200):
            tl = 1
    elif (pos == []) & (neg == []):
        angle = []
    #此句由于我们鱼摄像头摆放位置的原因会使得直线发生弯曲，这下面是bug修复添加语句
    else:
        angle = np.mean(pos) + np.mean(neg)
        if (angle > 10) & (x_right >= 440) & (angle < 30):
            tr = 1
        elif (angle < -10) & (x_left <= 200) & (angle > -30):
            tl = 1
        # elif (angle <= 10) & (angle >= -10) & (x_right > 605):
        #     tr = 1
        # elif (angle <= 10) & (angle >= -10) & (x_left < 35):
        #     tl = 1

        # try:
        #     img.drawText("xl_yu", x_left, y_up)
        #     img.drawText("xr_yd", x_right, y_down)
        #     img.save("newImage" + str(number) + ".png")
        # except:
        #     pass
    #下面的coordinates[number][x]中的x数值，由如下返回值决定
    return x_left, x_right, y_up, y_down, width_mean, height_mean, angle, turn, tl, tr

#根据Line()函数对于直线的判断，下面是相应的控制鱼的运动指令
def check_line(coordinates, number):
    if coordinates[number][7] & (coordinates[number][2] >= 50) & (coordinates[number][1] >= 400):
        time.sleep(0.2)
        Lmst.SetSteerSpeed(1, 0)
        Lmst.SetSteerDirection(1, 14)           # turn right 70 degree
        time.sleep(2.8)                         # time need to be modified
        Lmst.SetSteerDirection(1, 8)            # turn right 10 degree
        time.sleep(0.5)                         # time need to be modified
        Lmst.SetSteerDirection(1, 7)
        print("0Turn Right 90 degrees!")
    elif (coordinates[number][4] >= 6 * coordinates[number][5]) & (coordinates[number][2] >= 120) & (coordinates[number][1] >= 400):
        time.sleep(0.2)
        Lmst.SetSteerSpeed(1, 0)
        Lmst.SetSteerDirection(1, 14)           # turn right 70 degree
        time.sleep(2.8)                         # time need to be modified
        Lmst.SetSteerDirection(1, 8)            # turn right 10 degree
        time.sleep(0.5)                         # time need to be modified
        Lmst.SetSteerDirection(1, 7)
        print("1Turn Right 90 degrees!")
    elif coordinates[number][8]:
        Lmst.SetSteerDirection(1, 5)            # turn left 20 degree
        Lmst.SetSteerSpeed(1, 0)
        # time.sleep(0.5)                         # time need to be modified
        # Lmst.SetSteerDirection(1, 7)
        print("0Turn Left!")
    elif coordinates[number][9]:
        Lmst.SetSteerDirection(1, 9)            # turn right 20 degree
        Lmst.SetSteerSpeed(1, 0)
        # time.sleep(0.5)                         # time need to be modified
        # Lmst.SetSteerDirection(1, 7)
        print("0Turn Right!")
    elif abs(coordinates[number][0] - coordinates[number][1]) < 100:
        if coordinates[number][0] <= 320:
            if coordinates[number][0] <= 150:
                if coordinates[number][6] > 0:
                    Lmst.SetSteerDirection(1, 3)    # turn left 40 degree
                    Lmst.SetSteerSpeed(1, 0)
                    # time.sleep(0.5)                 # time need to be modified
                    # Lmst.SetSteerDirection(1, 7)
                    print("1Turn Left!")
                else:
                    Lmst.SetSteerDirection(1, 4)    # turn left 30 degree
                    Lmst.SetSteerSpeed(1, 0)
                    # time.sleep(0.5)                 # time need to be modified
                    # Lmst.SetSteerDirection(1, 7)
                    print("2Turn Left!")
            else:
                if coordinates[number][6] > 0:
                    Lmst.SetSteerDirection(1, 4)    # turn left 30 degree
                    Lmst.SetSteerSpeed(1, 0)
                    # time.sleep(0.5)                 # time need to be modified
                    # Lmst.SetSteerDirection(1, 7)
                    print("3Turn Left!")
                else:
                    Lmst.SetSteerDirection(1, 5)    # turn left 20 degree
                    Lmst.SetSteerSpeed(1, 0)
                    # time.sleep(0.5)                 # time need to be modified
                    # Lmst.SetSteerDirection(1, 7)
                    print("4Turn Left!")
        else:
            if coordinates[number][1] >= 490:
                if coordinates[number][6] < 0:
                    Lmst.SetSteerDirection(1, 11)    # turn right 40 degree
                    Lmst.SetSteerSpeed(1, 0)
                    # time.sleep(0.5)                 # time need to be modified
                    # Lmst.SetSteerDirection(1, 7)
                    print("1Turn Right!")
                else:
                    Lmst.SetSteerDirection(1, 10)    # turn right 30 degree
                    Lmst.SetSteerSpeed(1, 0)
                    # time.sleep(0.5)                 # time need to be modified
                    # Lmst.SetSteerDirection(1, 7)
                    print("2Turn Right!")
            else:
                if coordinates[number][6] < 0:
                    Lmst.SetSteerDirection(1, 10)    # turn right 30 degree
                    Lmst.SetSteerSpeed(1, 0)
                    # time.sleep(0.5)                 # time need to be modified
                    # Lmst.SetSteerDirection(1, 7)
                    print("3Turn Right!")
                else:
                    Lmst.SetSteerDirection(1, 9)    # turn right 20 degree
                    Lmst.SetSteerSpeed(1, 0)
                    # time.sleep(0.5)                 # time need to be modified
                    # Lmst.SetSteerDirection(1, 7)
                    print("4Turn Right!")
    elif (coordinates[number][6] < 75) & (coordinates[number][6] >= 50) & (coordinates[number][1] <= 440):
        Lmst.SetSteerDirection(1, 4)        # turn left 30 degree
        Lmst.SetSteerSpeed(1, 0)
        # time.sleep(1)                       # time need to be modified
        # Lmst.SetSteerDirection(1, 7)
        print("5Turn Left!")
    elif (coordinates[number][6] > -75) & (coordinates[number][6] <= -50) & (coordinates[number][0] >= 200):
        Lmst.SetSteerDirection(1, 10)        # turn right 30 degree
        Lmst.SetSteerSpeed(1, 0)
        print("5Turn Right!")
    elif (coordinates[number][0] + coordinates[number][1]) < 380:
        Lmst.SetSteerDirection(1, 5)        # turn left 20 degree
        Lmst.SetSteerSpeed(1, 0)
        print("6Turn Left!")
    elif (coordinates[number][0] + coordinates[number][1]) > 900:
        Lmst.SetSteerDirection(1, 9)        # turn right 20 degree
        Lmst.SetSteerSpeed(1, 0)
        print("6Turn Right!")
    else:
        Lmst.SetSteerSpeed(1, 1)
        Lmst.SetSteerDirection(1, 7)
        print("Go Ahead!")


#黑点寻找模块
def black_blob(img, coordinates, number):
    next_light = 0
    #SimpleCv里面的斑点寻找命令
    blob1 = img.colorDistance(Color.BLACK).dilate(10).binarize(100)
    blobs = blob1.findBlobs()
    if blobs != None:
        if len(blobs.width()) <= 4:
            for xx in range(len(blobs.width())):
                #黑点在管子左右两线的中间判断
                if (blobs.coordinates()[xx][0] > coordinates[number][0]) & (blobs.coordinates()[xx][0] < coordinates[number][1]):
                    if blobs.coordinates()[xx][1] >= 240:
                        # print(coordinates[number][0], blobs.coordinates()[0][0], coordinates[number][1])
                        # time.sleep(0.5)
                        Lmst.OpenHeadLight()
                        print("Open HeadLight!", 1)
                    elif blobs.coordinates()[xx][1] >= 100:
                        next_light = 1
        else:
            for xx in range(len(blobs.width()) - 4, len(blobs.width())):
                if (blobs.coordinates()[xx][0] > coordinates[number][0]) & (blobs.coordinates()[xx][0] < coordinates[number][1]):
                    if blobs.coordinates()[xx][1] >= 240:
                        # print(coordinates[number][0], blobs.coordinates()[0][0], coordinates[number][1])
                        # time.sleep(0.5)
                        Lmst.OpenHeadLight()
                        print("Open HeadLight!", 1)
                    elif blobs.coordinates()[xx][1] >= 100:
                        next_light = 1
    # else:
    #     blob2 = img.colorDistance(Color.BLACK).dilate(10).binarize(125)
    #     blob2s = blob2.findBlobs()
    #     if blob2s != None:
    #         if len(blob2s.width()) <= 4:
    #             for xx in range(len(blob2s.width())):
    #                 if (blob2s.coordinates()[xx][0] > coordinates[number][0]) & (blob2s.coordinates()[xx][0] < coordinates[number][1]):
    #                     if blob2s.coordinates()[xx][1] >= 240:
    #                         # print(coordinates[number][0], blob2s.coordinates()[0][0], coordinates[number][1])
    #                         # time.sleep(0.5)
    #                         Lmst.OpenHeadLight()
    #                         print("Open HeadLight!", 2)
    #                     elif blob2s.coordinates()[xx][1] >= 100:
    #                         next_light = 1
    #         else:
    #             for xx in range(len(blob2s.width()) - 4, len(blob2s.width())):
    #                 if (blob2s.coordinates()[xx][0] > coordinates[number][0]) & (blob2s.coordinates()[xx][0] < coordinates[number][1]):
    #                     if blob2s.coordinates()[xx][1] >= 240:
    #                         # print(coordinates[number][0], blob2s.coordinates()[0][0], coordinates[number][1])
    #                         # time.sleep(0.5)
    #                         Lmst.OpenHeadLight()
    #                         print("Open HeadLight!", 2)
    #                     elif blob2s.coordinates()[xx][1] >= 100:
    #                         next_light = 1
    else:
        print("No Blobs!")
    return next_light

#圆形检测，黑点检测的补充。由于摄像头位置，圆点黑点并不是圆形，此函数只是补充
def circle(img):
    circles = img.findCircle()
    if circles != None:
        return 1
    else:
        return 0

#主函数
if __name__ == "__main__":
    next_light1 = 0
    kong = 0
    cam1 = Camera()
    #调用C语言库
    ll = ctypes.cdll.LoadLibrary
    Lmst = ll("./libpycall.so")

    Lmst.YJ_LmstCtrl(5, 0)
    Lmst.SetSteerSpeed(1, 1)
    Lmst.SetSteerDirection(1, 7)
    coordinates1 = list(range(101))
    for x in range(100):
        img1 = snapshot(cam1, x)
        coordinates1[x] = line(img1, x)
        print(coordinates1[x], x)
        if any([coordinates1[x][6]]):

            if next_light1:
                Lmst.OpenHeadLight()
                print("Open HeadLight!", 0)

            check_line(coordinates1, x)
            #  find black blobs
            next_light1 = black_blob(img1, coordinates1, x)
            kong = 0
        elif coordinates1[x][7]:
            time.sleep(0.2)
            Lmst.SetSteerSpeed(1, 0)
            Lmst.SetSteerDirection(1, 14)               # turn right 70 degree
            time.sleep(2.8)                             # time need to be modified
            Lmst.SetSteerDirection(1, 8)                # turn right 10 degree
            time.sleep(0.5)                             # time need to be modified
            Lmst.SetSteerDirection(1, 7)
            print("2Turn Right 90 degrees!")
        else:
            if (kong == 1) & (x != 1):
                if coordinates1[x - 2][0] >= 320:
                    Lmst.SetSteerSpeed(1, 0)
                    Lmst.SetSteerDirection(1, 11)       # turn right 40 degree
                    time.sleep(0.5)                     # time need to be modified
                    Lmst.SetSteerDirection(1, 7)
                    print("7Turn Right!")
                elif coordinates1[x - 2][1] <= 320:
                    Lmst.SetSteerSpeed(1, 0)
                    Lmst.SetSteerDirection(1, 3)        # turn left 40 degree
                    time.sleep(0.5)                     # time need to be modified
                    Lmst.SetSteerDirection(1, 7)
                    print("7Turn Left!")
            else:
                if x != 0:
                    check_line(coordinates1, x - 1)
                kong = 1

        # if circle(img1):
        #     # time.sleep(0.5)
        #     Lmst.OpenHeadLight()
        #     time.sleep(0.5)
        #     print("Open HeadLight!", 0)

        Lmst.SetSteerDirection(1, 7)
        Lmst.CloseHeadLight()
    Lmst.StopTheFish()
