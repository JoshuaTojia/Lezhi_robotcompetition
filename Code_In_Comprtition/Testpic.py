#!/usr/bin/python3
from SimpleCV import Camera, Image, Color
import time
import numpy as np
import math
import threading
# from FindBlobThread import *


global pic_width, pic_height
global temp_turn

#   检测管道直线的算法
def line(img, number):
    #   二值化图片，simplecv采用的是ostu最大类间方差法
    bin = img.binarize()
    # bin.save("bin" + str(number) + ".png")  #   可查看二值化图片的效果
    #    设置找线的阈值为25、最小长度为50、两直线之间的最大间距为30（否则认为是同一条线）
    #    这些值是需要下水调试的，目前这个版本是给480*360的
    #    换成其他大小的图片则要微调，只能取整数
    lines = bin.findLines(threshold=25, minlinelength=50, maxlinegap=30)
    #    直线角度正负的判断方法：
    #    以图片最下方的线为x轴，直线逆时针旋转0-90度为负
    #    顺时针旋转0-90度为正（或者说是逆时针90-180度为正）
    #    pos为直线角度为正的角度的集合
    pos = []
    #    neg为直线角度为负的角度的集合
    neg = []
    #    width为直线的在x方向上的投影长度的集合
    width = []
    #    height为直线在y轴方向上的投影长度的集合
    height = []
    #    xc为直线的横坐标x的集合
    xc = []
    #    yc为直线的纵坐标y的集合
    yc = []
    #    turn表示允许拐弯的初步判断的标志位
    turn = 0
    #    turn_right表示最终允许拐弯的标志位
    turn_right = 0
    #    tr表示小角度向右调整方向（10-20度）
    tr = 0
    #    tl表示小角度向左调整方向（10-20度）
    tl = 0
    #    horizon为识别出横线的数目
    horizon = 0
    #    如果识别的直线过多，会影响处理速度
    #    尽量控制在20条直线以内，可以降低到15试下
    if len(lines.angle()) > 20:
        lines = bin.findLines()
        # print(len(lines.length()))
    lines.draw(width=3, color=Color.RED)
    #打印出各直线的相关信息

    # print(lines.length())
    # print(lines.coordinates())
    # print(lines.angle())

    #    indexs为符合条件的直线的索引集合，排除边缘直线和左右竖线的影响
    #    底下的横线有非常大的作用，要保留
    indexs = []
    index = 0
    for l in lines:
        angle = l.angle()
        #    排除左右竖线，上方直线
        if ((angle != 90.0) & ((angle != -90.0) | (l.coordinates()[0] < pic_width - 2))) & (l.coordinates()[1] > 0.05 * pic_height):
            indexs.append(index)
        index += 1
    try:
        #    根据下方直线中间+直线长度的一半=midway_x_mean
        #    若横线的横坐标在midway_x_mean的右方，则认为是管道的横线，准备拐弯
        midway_x = [lines.coordinates()[x1][0] for x1 in range(index) if (lines.coordinates()[x1][1] == pic_height - 2) & (lines.length()[x1] < 0.6 * pic_width) & (lines.length()[x1] > 0.15 * pic_width)]
        heng_length = [lines.length()[x1] for x1 in range(index) if (lines.coordinates()[x1][1] == pic_height - 2)]
        if midway_x != []:
            # print(midway_x, midway_x != [], heng_length, np.mean(heng_length))
            midway_x_mean = [np.mean(midway_x) + np.mean(heng_length) / 2]
            # print(midway_x_mean)
        else:
            midway_x_mean = [lines.coordinates()[x1][0] for x1 in range(index) if (lines.coordinates()[x1][1] == pic_height - 2) & (lines.length()[x1] < 0.6 * pic_width)]

        if midway_x_mean == []:
            # print(midway_x_mean != [])
            midway_x_mean = pic_width / 2
            img.drawText("midway", midway_x_mean, pic_height - 20)
        else:
            midway_x_mean = np.mean(midway_x_mean)
            print(number, midway_x_mean)
            img.drawText("midway", np.mean(midway_x_mean), pic_height - 20)
    except:
        #   出错或者没有下方直线识别到时，取图片的宽的一半作为midway_x_mean
        print("Error!")
        midway_x_mean = pic_width / 2
        img.drawText("midway", midway_x_mean, pic_height - 20)
    for index in indexs:
        l = lines[index]
        width.append(l.width())
        height.append(l.height())
        coords = l.coordinates()
        xc.append(coords[0])
        yc.append(coords[1])
        angle = l.angle()
        #   取正负35度以上或以下的直线进入pos和neg集合中
        #   否则认为是横线
        if angle > 35:
            pos.append(angle)
        elif angle < -35:
            neg.append(angle)
        elif (angle != 0.0) | (coords[1] < pic_height - 10):
            # print(coords[1])
            #    midway_x_mean - 0.05 * pic_width这个是根据图片效果决定的
            #    一般这个值是可以准确识别的，对于比赛场地这样没问题
            #    对于学校的水池，就直接使用midway_x_mean，不要左移
            if (coords[1] >= 0.1 * pic_height) & (coords[1] < pic_height - 10) & (abs(angle) < 20) & (coords[0] > midway_x_mean - 0.05 * pic_width):
                img.drawText("heng", coords[0], coords[1])
                horizon = horizon + 1
            elif (coords[1] >= 0.15 * pic_height) & (coords[1] < pic_height - 10) & (abs(angle) > 20) & (coords[0] > midway_x_mean - 0.1 * pic_width):
                img.drawText("heng", coords[0], coords[1])
                horizon = horizon + 1
    xc_mean = np.mean(xc)
    yc_mean = np.mean(yc)
    #    计算上下左右的线的坐标均值，以及线宽和线高的均值
    x_left = np.mean([j for j in xc if j <= xc_mean])
    x_right = np.mean([j for j in xc if j >= xc_mean])
    y_up = np.mean([j for j in yc if j <= yc_mean])
    y_down = np.mean([j for j in yc if j >= yc_mean])
    width_mean = np.mean(width)
    height_mean = np.mean(height)
    # check turn right 90 degrees
    #    初步判断是否允许拐弯
    #    有两条横线以上，或是一条横线但是midway_x_mean >= 0.8 * pic_width
    if (horizon >= 2) | ((horizon >= 1) & (midway_x_mean >= 0.75 * pic_width)):
        turn = 1
    #     线宽均值大于10倍线高均值，排除右侧直线的线高的影响
    if (width_mean >= 10 * height_mean) & (pic_width - 2 not in lines.length()) & (-90.0 in lines.angle()):
        turn = 1
    #     其余类推，还可以根据图片情况添加
    if (width_mean >= 3.5 * height_mean) & (y_up >= 0.25 * pic_height):
        turn = 1
    if (y_up >= 0.6 * pic_height) & (len(lines.length()) >= 5) & (width_mean > height_mean):
        turn = 1
    if (x_left >= 0.5 * pic_width) & (y_up >= 0.5 * pic_height) & (len(lines.length()) >= 5) & (width_mean > height_mean):
        turn = 1
    #    初步允许拐弯后，再次判断，可将共有的约束条件写在这里
    if (turn == 1) & (y_up >= 0.08 * pic_height) & (x_right >= 0.55 * pic_width):
        turn_right = 1
    # check angles
    #    根据直线的角度进行处理
    #    (x_right - x_left) >= 0.15625 * pic_width 和 (x_right - x_left) <= 0.625 * pic_width
    #    是对直线识别效果的判断，如果不满足，一般是识别有误，或者遇到拐弯
    if (pos == []) & (neg != []):
        angle = np.mean(neg)
        if (angle <= -75) & (angle >= -82) & ((x_right - x_left) >= 0.15625 * pic_width) & ((x_right - x_left) <= 0.625 * pic_width) & (x_right >= 0.6875 * pic_width):
            tr = 1
    elif (neg == []) & (pos != []) :
        angle = np.mean(pos)
        if (angle >= 75) & (angle <= 82) & ((x_right - x_left) >= 0.15625 * pic_width) & ((x_right - x_left) <= 0.625 * pic_width) & (x_left <= 0.3125 * pic_width):
            tl = 1
    elif (pos == []) & (neg == []):
        angle = []
    else:
        angle = np.mean(pos) + np.mean(neg)
        if (angle > 11) & (x_right >= 0.6875 * pic_width) & (angle < 30):
            tr = 1
        elif (angle < -11) & (x_left <= 0.3125 * pic_width) & (angle > -30):
            tl = 1
    #打印出相关信息在图片
    try:
        img.drawText("xl_yu", x_left, y_up)
        img.drawText("xr_yd", x_right, y_down)
        img.addDrawingLayer(bin.dl())
        img.save("newImage" + str(number) + ".png")
    except:
        pass
    return x_left, x_right, y_up, y_down, width_mean, height_mean, angle, turn_right, tl, tr, horizon

#    根据line函数的执行效果给出鱼的指令
def check_line(coordinates, number):
    #    coordinates[7]是line函数返回的第8个值，即turn_right的值
    if (coordinates[7]) & (number >= 10):
        #    在拐弯前后决定是否另加延时
        #    拐弯前延时，则鱼向前一段距离后右拐
        #    拐弯后延时，则鱼拐弯的角度大于90度，以致拐回赛道
        if coordinates[2] < 0.15 * pic_height:
            print("Delay 0.15s!")

        #   下面注释的这段在学校可以使用，在比赛时感觉影响了拐弯的时机，所以注释了
        # if coordinates[4] < 4 * coordinates[5]:
        #     if coordinates[2] < 0.175 * pic_height:
        #         print("Delay 0.2s!")
        #     if coordinates[2] < 0.235 * pic_height:
        #         print("Delay 0.25s!")
        #     if coordinates[2] < 0.285 * pic_height:
        #         print("Delay 0.25s!")
        # if coordinates[2] < 0.35 * pic_height:
        #     print("Delay 0.35s!")
        print("0Turn Right 90 degrees!")    # turn right 90 degrees
        # thread = FindBlobThread(img, coordinates)
        # thread.start()
        if coordinates[2] > 0.5 * pic_height:
            print("Delay 0.2s!")
        if coordinates[2] > 0.7 * pic_height:
            print("Delay 0.3s!")
        if coordinates[2] > 0.9 * pic_height:
            print("Delay 0.4s!")
    #print("Delay 3.3s!!")
    #    fudu是控制鱼的转向幅度大小，幅度为1时，则在原版注释上
    #    如“turn left 10 degree”，则多转10*幅度的角度
    elif coordinates[8]:
        print("0Turn Left!")                  # turn left 10 degrees
    elif coordinates[9]:
        print("0Turn Right!")                 # turn right 10 degrees
    #    两条线的值靠的比较近，则(coordinates[1] - coordinates[0]) < 0.15625 * pic_width
    #    可以判断为只剩一侧的线被识别到，也就是鱼身已经偏离较为严重了
    elif (coordinates[1] - coordinates[0]) < 0.15625 * pic_width:
        if coordinates[0] <= 0.5 * pic_width:
            if coordinates[0] <= 0.235 * pic_width:
                if coordinates[6] > 0:
                    print("1Turn Left!")    # turn left 30 degrees
                else:
                    print("2Turn Left!")    # turn left 20 degrees
            else:
                if coordinates[6] > 0:
                    print("3Turn Left!")    # turn left 20 degrees
                else:
                    print("4Turn Left!")    # turn left 10 degrees
        else:
            if coordinates[1] >= 0.765 * pic_width:
                if coordinates[6] < 0:
                    print("1Turn Right!")   # turn right 30 degrees
                else:
                    print("2Turn Right!")   # turn right 20 degrees
            else:
                if coordinates[6] < 0:
                    print("3Turn Right!")   # turn right 20 degrees
                else:
                    print("4Turn Right!")   # turn right 10 degrees
    #    直线的角度集合的均值在以下的范围内
    #    可认为鱼的方向需要调整
    elif (coordinates[6] < 75) & (coordinates[6] >= 50) & (coordinates[1] <= 0.625 * pic_width):
        print("5Turn Left!")                # turn left 20 degrees
    elif (coordinates[6] > -75) & (coordinates[6] <= -50) & (coordinates[0] >= 0.375 * pic_width):
        print("5Turn Right!")               # turn right 20 degrees
    #    鱼的两侧直线加起来的总和偏小，则小角度向左偏
    elif (coordinates[0] + coordinates[1]) < (0.6 * pic_width):
        print("6Turn Left!")                # turn left 10 degrees
    # 鱼的两侧直线加起来的总和偏大，则小角度向右偏
    elif (coordinates[0] + coordinates[1]) > (1.4 * pic_width):
        print("6Turn Right!")               # turn right 10 degrees
    else:
        #    拐弯后的图像识别需单独处理
        if (temp_turn == 1) & ((coordinates[0] + coordinates[1]) > (1.1 * pic_width)):
            print("9Turn Right!")           # turn right 10 degrees
        else:
            #    给出直进的指令
            print("Go Ahead!")

#    查找斑点的函数
def black_blob(img, coordinates, number):
    #    next_light=1时控制灯在下一次亮
    next_light = 0
    #    拐弯时另设置阈值为80
    #    图像膨胀次数随图片效果决定，学校的需要8-10次
    #    比赛时设置为5次则提高了10秒，可再降
    turn_right = coordinates[7]
    if turn_right:
        blob1 = img.colorDistance(Color.BLACK).dilate(5).binarize(100)
    else:
        blob1 = img.colorDistance(Color.BLACK).dilate(5).binarize(110)
    blobs = blob1.findBlobs()
    left = coordinates[0]
    right = coordinates[1]
    #    若两侧直线接近，则视为管道偏向一方，需对左右界限进行微调
    if (right - left) < 0.25 * pic_width:
        if right < 0.375 * pic_width:
            left = right - 0.3 * pic_width
        elif left > 0.625 * pic_width:
            right = left + 0.3 * pic_width
    left1 = left
    right1 = right
    # print(blobs.coordinates(), blobs.area(), blobs.width(), blobs.height())
    if blobs != None:
        if turn_right:
            for xx in range(len(blobs.width())):
                #    斑块的面积占比大于0.25时视为斑点，排除细长线（一般是阴影）的影响
                if ((blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx])) > 0.25) & (blobs.width()[xx] < 0.225 * pic_width):
                    blob_coords = blobs.coordinates()[xx]
                    if (((blob_coords[1] > coordinates[2]) & (blob_coords[1] < coordinates[3])) | ((blob_coords[0] > coordinates[0]) & (blob_coords[0] < coordinates[1]))) & ((blobs.area()[xx] > 2000) | ((blobs.width()[xx] < 0.2 * pic_width) & (blobs.height()[xx] < 0.2 * pic_height) & (blobs.area()[xx] > 190))):
                        blob1.drawText(str(round(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]), 3)), blob_coords[0], blob_coords[1])
                        blob1.save(str(number)+"_0blobs.png")
                        print(blobs.area()[xx], blob_coords, blobs.width()[xx], blobs.height()[xx])
                        print("Open HeadLight!", 0)
        else:
            #    斑块的数目控制在4个以内，调用findBlobs()返回的斑块按照大小升序
            #    只挑最大的4个（或以下）来比较
            if len(blobs.width()) <= 4:
                for xx in range(len(blobs.width())):
                    if ((blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx])) > 0.25) & (blobs.width()[xx] < 0.8 * pic_width):
                        # print(blobs.area()[xx], blobs.height()[xx], blobs.width()[xx])
                        # print(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]))
                        blob_coords = blobs.coordinates()[xx]
                        #   对下方斑点的识别调整
                        #   一般在管道倾斜严重时有用，可以使识别更为准确
                        if blob_coords[1] > 0.65 * pic_height:
                            if (coordinates[6] > - 78) & (coordinates[6] < -50):
                                left1 = left - 0.125 * pic_width
                            elif (coordinates[6] < 78) & (coordinates[6] > 50):
                                right1 = right + 0.125 * pic_width
                            else:
                                left1 = left
                                right1 = right
                        #   斑点夹在left1和right1之间时视为黑点
                        if (blob_coords[0] > left1) & (blob_coords[0] < right1):
                            if blob_coords[1] >= 0.5 * pic_height:
                                blob1.drawText(str(round(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]), 3)), blob_coords[0], blob_coords[1])
                                blob1.save(str(number)+"_1blobs.png")
                                print("Open HeadLight!", 1)
                                print(blob_coords)
                            elif (number >= 8) & (blob_coords[1] > 0.02 * pic_height) & (temp_turn == 0):
                                #    >=8时排除前期起步速度慢的影响，避免提前识别
                                #    temp_turn==1表示前一张图片拐弯
                                #    此时鱼的速度也较慢，则排除上方斑点的识别
                                blob1.drawText(str(round(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]), 3)), blob_coords[0], blob_coords[1])
                                blob1.save(str(number) + "_1blobs.png")
                                if blob_coords[1] >= 0.1 * pic_height:
                                    print("Open HeadLight!", 1)
                                else:
                                    #    next_light = 1则下一张图片点亮头灯
                                    next_light = 1
                                print(blob_coords)
                            elif blob_coords[1] >= 0.16 * pic_height:
                                blob1.drawText(str(round(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]), 3)), blob_coords[0], blob_coords[1])
                                blob1.save(str(number)+"_1blobs.png")
                                next_light = 1
                                print(blob_coords)
                    # else:
                    #     print(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]))
            else:
                for xx in range(len(blobs.width()) - 4, len(blobs.width())):
                    if ((blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx])) > 0.25) & (blobs.width()[xx] < 0.8 * pic_width):
                        blob_coords = blobs.coordinates()[xx]
                        if blob_coords[1] > 0.65 * pic_height:
                            if (coordinates[6] > - 78) & (coordinates[6] < -50):
                                left1 = left - 0.125 * pic_width
                            elif (coordinates[6] < 78) & (coordinates[6] > 50):
                                right1 = right + 0.125 * pic_width
                            else:
                                left1 = left
                                right1 = right
                        if (blob_coords[0] > left1) & (blob_coords[0] < right1):
                            if blob_coords[1] >= 0.5 * pic_height:
                                blob1.drawText(str(round(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]), 3)), blob_coords[0], blob_coords[1])
                                blob1.save(str(number)+"_2blobs.png")
                                print("Open HeadLight!", 2)
                                print(blob_coords)
                            elif (number >= 8) & (blob_coords[1] > 0.02 * pic_height) & (temp_turn == 0):
                                blob1.drawText(str(round(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]), 3)), blob_coords[0], blob_coords[1])
                                blob1.save(str(number) + "_2blobs.png")
                                if blob_coords[1] >= 0.1 * pic_height:
                                    print("Open HeadLight!", 2)
                                else:
                                    next_light = 1
                                print(blob_coords)
                            elif blob_coords[1] >= 0.16 * pic_height:
                                blob1.drawText(str(round(blobs.area()[xx] / (blobs.height()[xx] * blobs.width()[xx]), 3)), blob_coords[0], blob_coords[1])
                                blob1.save(str(number)+"_2blobs.png")
                                next_light = 1
                                print(blob_coords)
    else:
        print("No Blobs!")
    return next_light


if __name__ == "__main__":
    #   设置拍照图片大小为480*360
    pic_width = 480
    pic_height = 360

    next_light1 = 0
    temp_turn = 0
    start = time.time()

    #    初始化照片数目
    #    一般是32-37张跑完全程
    coordinates1 = list(range(150))
    for x in range(32, 33):
        img1 = Image("image" + str(x) + ".png")
        #    调用检测管道直线的函数
        coordinates1[x] = line(img1, x)
        #    打印出来，可以对着图片反馈识别效果
        print(coordinates1[x], x)
        #    如果返回的angle为[]则进入elif(coordinates1[x][7]) & (x >= 10):
        if any([coordinates1[x][6]]):
            #   angle不是[]，则检测航道
            check_line(coordinates1[x], x)
            #   找斑块
            if next_light1:
                print("Open HeadLight!", 3)
            #  find black blobs
            next_light1 = black_blob(img1, coordinates1[x], x)
        #    如果angle为[]但是turn_right=1，则拐弯并识别斑点
        elif (coordinates1[x][7]) & (x >= 10):
            if next_light1:
                print("Open HeadLight!", 4)
            if coordinates1[x][10] < 5:
                if coordinates1[x][2] < 0.35 * pic_height:
                    print("Delay 0.7s!")
                if coordinates1[x][2] < 0.5 * pic_height:
                    print("Delay 0.3s!")
            print("1Turn Right 90 degrees!")
            if coordinates1[x][2] > 0.6 * pic_height:
                print("2Delay 0.5s!")
            if coordinates1[x][2] > 0.8 * pic_height:
                print("3Delay 0.5s!")
            if coordinates1[x][2] > 0.9 * pic_height:
                print("4Delay 0.5s!")
            next_light1 = black_blob(img1, coordinates1[x], x)
            next_light1 = 0
        else:
            #    鱼的头舱没有照到任何管道时进入
            #    一般是没有返回值，水池不干净除外
            if (x != 1) & (coordinates1[x - 1][7] == 0):
                if coordinates1[x - 1][0] >= 0.5 * pic_width:
                    print("7Turn Right!")               # turn right 30 degree
                elif coordinates1[x - 1][1] <= 0.5 * pic_width:
                    print("7Turn Left!")                # turn left 30 degree
            else:
                #    因为拐弯出错时进入，coordinates1[x - 1][7] == 1
                if (x != 1) & (coordinates1[x - 1][7] == 1):
                    if coordinates1[x - 1][2] > 0.4 * pic_height:
                        print("8Turn Right!")           # turn right 30 degree
                    else:
                        print("8Turn Left!")            # turn left 30 degree
        #   每张图片处理结束时设置方向向前，头灯关闭，temp_turn赋值
        temp_turn = coordinates1[x][7]
        # print(temp_turn)
    finish = time.time()
    print(finish-start)
