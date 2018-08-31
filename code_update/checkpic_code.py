#!/usr/bin/python3
from SimpleCV import Camera, Image, Color
import time
import numpy as np
import math


def line(img, number):
    bin = img.binarize()
    # bin.save("bin" + str(number) + ".png")
    lines = bin.findLines(threshold=25, minlinelength=65, maxlinegap=25)
    # print(len(lines.length()))
    # print(lines.angle())
    # print(lines.coordinates())
    pos = []     # positive angle
    neg = []     # negative angle
    width = []   # line deta x
    height = []  # line deta y
    xc = []      # line x coordinate
    yc = []      # line y coordinate
    turn = 0     # turn right 90 degrees
    tr = 0       # turn right
    tl = 0       # turn left
    horizon = 0
    if len(lines.angle()) > 20:
        lines = bin.findLines()
        # print(len(lines.length()))
    lines.draw(width=3, color=Color.RED)

    angles = [i for i in range(len(lines.angle())) if ((lines.angle()[i] != 90.0) & (lines.angle()[i] != 0.0) & ((lines.angle()[i] != -90.0) | (lines.coordinates()[i][0] < 635)))]
    for i in range(len(lines.angle())):
        if i in angles:
            width = width + [lines.width()[i]]
            height = height + [lines.height()[i]]
            xc = xc + [lines.coordinates()[i][0]]
            yc = yc + [lines.coordinates()[i][1]]
            if lines.angle()[i] > 35:
                pos = pos + [lines.angle()[i]]
            elif lines.angle()[i] < -35:
                neg = neg + [lines.angle()[i]]
            elif lines.angle()[i] != 0.0:
                if (lines.coordinates()[i][1] >= 120) & (lines.coordinates()[i][1] <= 470):
                    horizon = horizon + 1
                    if horizon >= 3:
                        turn = 1
        else:
            pass
    x_left = np.mean([j for j in xc if j <= np.mean(xc)])
    x_right = np.mean([j for j in xc if j >= np.mean(xc)])
    y_up = np.mean([j for j in yc if j <= np.mean(yc)])
    y_down = np.mean([j for j in yc if j >= np.mean(yc)])
    width_mean = np.mean(width)
    height_mean = np.mean(height)
    if (width_mean >= 10 * height_mean) & (638.0 not in lines.length()) & (-90.0 in lines.angle()) & (x_right >= 400):
        turn = 1
    if (y_up >= 300) & (len(lines.length()) >= 5):
        turn = 1
    if (x_left >= 350) & (y_up >= 245):
        turn = 1
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

    try:
        img.drawText("xl_yu", x_left, y_up)
        img.drawText("xr_yd", x_right, y_down)
        img.addDrawingLayer(bin.dl())
        img.save("newImage" + str(number) + ".png")
    except:
        pass
    return x_left, x_right, y_up, y_down, width_mean, height_mean, angle, turn, tl, tr


def check_line(coordinates, number):
    if coordinates[number][7] & (coordinates[number][2] >= 50) & (coordinates[number][1] >= 400):           # turn = 1
        print("0Turn Right 90 degrees!")
    elif (coordinates[number][4] >= 5 * coordinates[number][5]) & (coordinates[number][2] >= 120) & (coordinates[number][1] >= 400):    # width >= 5 * height & y_up >= 120
        print("1Turn Right 90 degrees!")
    elif coordinates[number][8]:
        print("0Turn Left!")                # turn left 10 degrees
    elif coordinates[number][9]:
        print("0Turn Right!")               # turn left 10 degrees
    elif abs(coordinates[number][0] - coordinates[number][1]) < 100:
        if coordinates[number][0] <= 320:
            if coordinates[number][0] <= 150:
                if coordinates[number][6] > 0:
                    print("1Turn Left!")         # turn left 30 degrees
                else:
                    print("2Turn Left!")         # turn left 20 degrees
            else:
                if coordinates[number][6] > 0:
                    print("3Turn Left!")        # turn left 20 degrees
                else:
                    print("4Turn Left!")        # turn left 10 degrees
        else:
            if coordinates[number][1] >= 490:
                if coordinates[number][6] < 0:
                    print("1Turn Right!")         # turn right 30 degrees
                else:
                    print("2Turn Right!")         # turn right 20 degrees
            else:
                if coordinates[number][6] < 0:
                    print("3Turn Right!")       # turn right 20 degrees
                else:
                    print("4Turn Right!")       # turn right 10 degrees
    elif (coordinates[number][6] < 75) & (coordinates[number][6] >= 50) & (coordinates[number][1] <= 440):
        print("5Turn Left!")                # turn left 20 degrees
    elif (coordinates[number][6] > -75) & (coordinates[number][6] <= -50) & (coordinates[number][0] >= 200):
        print("5Turn Right!")               # turn right 20 degrees
    elif (coordinates[number][0] + coordinates[number][1]) < 380:
        print("6Turn Left!")                 # turn left 10 degrees
    elif (coordinates[number][0] + coordinates[number][1]) > 900:
        print("6Turn Right!")               # turn right 10 degrees
    else:
        print("Go Ahead!")


def black_blob(img, coordinates, number):
    next_light = 0
    blob1 = img.colorDistance(Color.BLACK).dilate(10).binarize(110)
    blobs = blob1.findBlobs()
    left = coordinates[number][0]
    right = coordinates[number][1]
    if (right - left) < 150:
        if right < 240:
            left = right - 150
        elif left > 400:
            right = left + 150
    if blobs != None:
        if len(blobs.width()) <= 4:
            for xx in range(len(blobs.width())):     # find the blob x in (x_left, x_right)
                if (blobs.coordinates()[xx][0] > left) & (blobs.coordinates()[xx][0] < right):
                    if blobs.coordinates()[xx][1] >= 240:
                        print(coordinates[number][0], blobs.coordinates()[xx][0], coordinates[number][1])
                        print("Open HeadLight!", 1)
                        blob1.drawText("Blobs", blobs.coordinates()[xx][0], blobs.coordinates()[xx][1])
                        blob1.save("1blob" + str(number) + ".png")
                    elif blobs.coordinates()[xx][1] >= 100:
                        next_light = 1
                        blob1.drawText("1Blobs", blobs.coordinates()[xx][0], blobs.coordinates()[xx][1])
                        blob1.save("1blob" + str(number) + ".png")
        else:
            for xx in range(len(blobs.width()) - 4, len(blobs.width())):
                if (blobs.coordinates()[xx][0] > left) & (blobs.coordinates()[xx][0] < right):
                    if blobs.coordinates()[xx][1] >= 240:
                        print(coordinates[number][0], blobs.coordinates()[xx][0], coordinates[number][1])
                        print("Open HeadLight!", 1)
                        blob1.drawText("1Blobs", blobs.coordinates()[xx][0], blobs.coordinates()[xx][1])
                        blob1.save("1blob" + str(number) + ".png")
                    elif blobs.coordinates()[xx][1] >= 100:
                        next_light = 1
                        blob1.drawText("1Blobs", blobs.coordinates()[xx][0], blobs.coordinates()[xx][1])
                        blob1.save("1blob" + str(number) + ".png")
    # else:
    #     blob2 = img.colorDistance(Color.BLACK).dilate(10).binarize(125)
    #     blob2s = blob2.findBlobs()
    #     if blob2s != None:
    #         if len(blob2s.width()) <= 4:
    #             for xx in range(len(blob2s.width())):
    #                 if (blob2s.coordinates()[xx][0] > coordinates[number][0]) & (blob2s.coordinates()[xx][0] < coordinates[number][1]):
    #                     if blob2s.coordinates()[xx][1] >= 240:
    #                         print(coordinates[number][0], blob2s.coordinates()[0][0], coordinates[number][1])
    #                         print("Open HeadLight!", 2)
    #                         blob2.drawText("Blobs", blob2s.coordinates()[xx][0], blob2s.coordinates()[xx][1])
    #                         blob2.save("2blob" + str(number) + ".png")
    #                     elif blob2s.coordinates()[xx][1] >= 100:
    #                         next_light = 1
    #                         blob2.drawText("Blobs", blob2s.coordinates()[xx][0], blob2s.coordinates()[xx][1])
    #                         blob2.save("2blob" + str(number) + ".png")
    #         else:
    #             for xx in range(len(blob2s.width()) - 4, len(blob2s.width())):
    #                 if (blob2s.coordinates()[xx][0] > coordinates[number][0]) & (blob2s.coordinates()[xx][0] < coordinates[number][1]):
    #                     if blob2s.coordinates()[xx][1] >= 240:
    #                         print(coordinates[number][0], blob2s.coordinates()[0][0], coordinates[number][1])
    #                         print("Open HeadLight!", 2)
    #                         blob2.drawText("1Blobs", blob2s.coordinates()[xx][0], blob2s.coordinates()[xx][1])
    #                         blob2.save("2blob" + str(number) + ".png")
    #                     elif blob2s.coordinates()[xx][1] >= 100:
    #                         next_light = 1
    #                         blob2.drawText("Blobs", blob2s.coordinates()[xx][0], blob2s.coordinates()[xx][1])
    #                         blob2.save("2blob" + str(number) + ".png")
    else:
        print("No Blobs!")
    return next_light

def circle(img):
    circles = img.findCircle()
    if circles != None:
        return 1
    else:
        return 0


if __name__ == "__main__":
    kong = 0
    next_light1 = 0
    coordinates1 = list(range(200))
    for x in range(0, 23):
        img1 = Image("image" + str(x) + ".png")
        coordinates1[x] = line(img1, x)
        print(coordinates1[x], x)
        if any([coordinates1[x][6]]):
            if next_light1:
                print("Open HeadLight!", 0)
            check_line(coordinates1, x)

            # find black blobs
            next_light1 = black_blob(img1, coordinates1, x)
            kong = 0
        else:
            if (coordinates1[x][7]):
                print("2Turn Right 90 degrees!")
            else:
                if (kong == 1) & (x != 1):
                    if coordinates1[x - 2][0] >= 320:
                        print("7Turn Right!")
                    elif coordinates1[x - 2][1] <= 320:
                        print("7Turn Left!")
                else:
                    if x != 0:
                        check_line(coordinates1, x - 1)
                    kong = 1

        if circle(img1):
            print("Open HeadLight!", 0)
