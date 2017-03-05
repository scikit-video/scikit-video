import numpy as np
import os
import time

from ..utils import *


def _costMAD(block1, block2):
    block1 = block1.astype(np.float32)
    block2 = block2.astype(np.float32)
    return np.mean(np.abs(block1 - block2))

def _minCost(costs):
    h, w = costs.shape
    mi = costs[np.int((h-1)/2), np.int((w-1)/2)]
    dy = np.int((h-1)/2)
    dx = np.int((w-1)/2)
    #mi = 65535
    #dy = 0
    #dx = 0

    for i in range(h): 
      for j in range(w): 
        if costs[i, j] < mi:
          mi = costs[i, j]
          dy = i
          dx = j

    return dx, dy, mi

def _checkBounded(xval, yval, w, h, mbSize):
    if ((yval < 0) or
       (yval + mbSize >= h) or
       (xval < 0) or
       (xval + mbSize >= w)):
        return False
    else:
        return True


def _DS(imgP, imgI, mbSize, p):
    # Computes motion vectors using Diamond Search method
    #
    # Input
    #   imgP : The image for which we want to find motion vectors
    #   imgI : The reference image
    #   mbSize : Size of the macroblock
    #   p : Search parameter  (read literature to find what this means)
    #
    # Ouput
    #   motionVect : the motion vectors for each integral macroblock in imgP
    #   DScomputations: The average number of points searched for a macroblock

    h, w = imgP.shape

    vectors = np.zeros((np.int(h / mbSize), np.int(w / mbSize), 2))
    costs = np.ones((9))*65537

    L = np.floor(np.log2(p + 1))

    LDSP = []
    LDSP.append([0, -2])
    LDSP.append([-1, -1])
    LDSP.append([1, -1])
    LDSP.append([-2, 0])
    LDSP.append([0, 0])
    LDSP.append([2, 0])
    LDSP.append([-1, 1])
    LDSP.append([1, 1])
    LDSP.append([0, 2])

    SDSP = []
    SDSP.append([0, -1])
    SDSP.append([-1, 0])
    SDSP.append([0, 0])
    SDSP.append([1, 0])
    SDSP.append([0, 1])

    computations = 0

    for i in range(0, h - mbSize + 1, mbSize):
        for j in range(0, w - mbSize + 1, mbSize):
            x = j
            y = i
            costs[4] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[i:i + mbSize, j:j + mbSize])
            cost = 0
            point = 4
            if costs[4] != 0:
                computations += 1
                for k in range(9):
                    refBlkVer = y + LDSP[k][1]
                    refBlkHor = x + LDSP[k][0]
                    if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                        continue
                    if k == 4:
                        continue
                    costs[k] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                    computations += 1

                point = np.argmin(costs)
                cost = costs[point]

            SDSPFlag = 1
            if point != 4:
                SDSPFlag = 0
                cornerFlag = 1
                if (np.abs(LDSP[point][0]) == np.abs(LDSP[point][1])):
                    cornerFlag = 0
                xLast = x
                yLast = y
                x = x + LDSP[point][0]
                y = y + LDSP[point][1]
                costs[:] = 65537
                costs[4] = cost

            while SDSPFlag == 0:
                if cornerFlag == 1:
                    for k in range(9):
                        refBlkVer = y + LDSP[k][1]
                        refBlkHor = x + LDSP[k][0]
                        if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                            continue
                        if k == 4:
                            continue

                        if ((refBlkHor >= xLast - 1) and
                           (refBlkHor <= xLast + 1) and
                           (refBlkVer >= yLast - 1) and
                           (refBlkVer <= yLast + 1)):
                            continue
                        elif ((refBlkHor < j-p) or
                              (refBlkHor > j+p) or
                              (refBlkVer < i-p) or
                              (refBlkVer > i+p)):
                            continue
                        else:
                            costs[k] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                            computations += 1
                else:
                    lst = []
                    if point == 1:
                        lst = np.array([0, 1, 3])
                    elif point == 2:
                        lst = np.array([0, 2, 5])
                    elif point == 6:
                        lst = np.array([3, 6, 8])
                    elif point == 7:
                        lst = np.array([5, 7, 8])

                    for idx in lst:
                        refBlkVer = y + LDSP[idx][1]
                        refBlkHor = x + LDSP[idx][0]
                        if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                            continue
                        elif ((refBlkHor < j - p) or
                              (refBlkHor > j + p) or
                              (refBlkVer < i - p) or
                              (refBlkVer > i + p)):
                            continue
                        else:
                            costs[idx] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                            computations += 1

                point = np.argmin(costs)
                cost = costs[point]

                SDSPFlag = 1
                if point != 4:
                    SDSPFlag = 0
                    cornerFlag = 1
                    if (np.abs(LDSP[point][0]) == np.abs(LDSP[point][1])):
                        cornerFlag = 0
                    xLast = x
                    yLast = y
                    x += LDSP[point][0]
                    y += LDSP[point][1]
                    costs[:] = 65537
                    costs[4] = cost
            costs[:] = 65537
            costs[2] = cost

            for k in range(5):
                refBlkVer = y + SDSP[k][1]
                refBlkHor = x + SDSP[k][0]

                if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                    continue
                elif ((refBlkHor < j - p) or
                      (refBlkHor > j + p) or
                      (refBlkVer < i - p) or
                      (refBlkVer > i + p)):
                    continue

                if k == 2:
                    continue

                costs[k] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                computations += 1

            point = 2
            cost = 0 
            if costs[2] != 0:
                point = np.argmin(costs)
                cost = costs[point]

            x += SDSP[point][0]
            y += SDSP[point][1]

            vectors[np.int(i / mbSize), np.int(j / mbSize), :] = [x - j, y - i]

            costs[:] = 65537

    return vectors, computations / ((h * w) / mbSize**2)


def _ARPS(imgP, imgI, mbSize, p):
    # Computes motion vectors using Adaptive Rood Pattern Search method
    #
    # Input
    #   imgP : The image for which we want to find motion vectors
    #   imgI : The reference image
    #   mbSize : Size of the macroblock
    #   p : Search parameter  (read literature to find what this means)
    #
    # Ouput
    #   motionVect : the motion vectors for each integral macroblock in imgP
    #   ARPScomputations: The average number of points searched for a macroblock

    h, w = imgP.shape

    vectors = np.zeros((np.int(h / mbSize), np.int(w / mbSize), 2))
    costs = np.ones((6))*65537

    SDSP = []
    SDSP.append([0, -1])
    SDSP.append([-1, 0])
    SDSP.append([0, 0])
    SDSP.append([1, 0])
    SDSP.append([0, 1])

    LDSP = {}

    checkMatrix = np.zeros((2 * p + 1, 2 * p + 1))

    computations = 0

    for i in range(0, h - mbSize + 1, mbSize):
        for j in range(0, w - mbSize + 1, mbSize):
            x = j
            y = i

            costs[2] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[i:i + mbSize, j:j + mbSize])

            checkMatrix[p, p] = 1
            computations += 1

            if (j == 0):
                stepSize = 2
                maxIndex = 5
            else:
                u = vectors[np.int(i / mbSize), np.int(j / mbSize) - 1, 0]
                v = vectors[np.int(i / mbSize), np.int(j / mbSize) - 1, 1]
                stepSize = np.int(np.max((np.abs(u), np.abs(v))))

                if (((np.abs(u) == stepSize) and (np.abs(v) == 0)) or
                    ((np.abs(v) == stepSize) and (np.abs(u) == 0))):
                    maxIndex = 5
                else:
                    maxIndex = 6
                    LDSP[5] = [np.int(v), np.int(u)]

            # large diamond search
            LDSP[0] = [0, -stepSize]
            LDSP[1] = [-stepSize, 0]
            LDSP[2] = [0, 0]
            LDSP[3] = [stepSize, 0]
            LDSP[4] = [0, stepSize]

            for k in range(maxIndex):
                refBlkVer = y + LDSP[k][1]
                refBlkHor = x + LDSP[k][0]

                if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                    continue

                if ((k == 2) or (stepSize == 0)):
                    continue

                costs[k] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                computations += 1
                checkMatrix[LDSP[k][1] + p, LDSP[k][0] + p] = 1

            if costs[2] != 0:
                point = np.argmin(costs)
                cost = costs[point]
            else:
                point = 2
                cost = costs[point]

            x += LDSP[point][0]
            y += LDSP[point][1]
            costs[:] = 65537
            costs[2] = cost

            doneFlag = 0
            while (doneFlag == 0):
                for k in range(5):
                    refBlkVer = y + SDSP[k][1]
                    refBlkHor = x + SDSP[k][0]

                    if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                        continue

                    if k == 2:
                        continue
                    elif ((refBlkHor < j - p) or 
                          (refBlkHor > j + p) or
                          (refBlkVer < i - p) or
                          (refBlkVer > i + p)):
                        continue
                    elif (checkMatrix[y - i + SDSP[k][1] + p, x - j + SDSP[k][0] + p] == 1):
                        continue

                    costs[k] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                    checkMatrix[y - i + SDSP[k][1] + p, x - j + SDSP[k][0] + p] = 1
                    computations += 1

                if costs[2] != 0:
                    point = np.argmin(costs)
                    cost = costs[point]
                else:
                    point = 2
                    cost = costs[point]

                doneFlag = 1
                if point != 2:
                    doneFlag = 0
                    y += SDSP[point][1]
                    x += SDSP[point][0]
                    costs[:] = 65537
                    costs[2] = cost

            vectors[np.int(i / mbSize), np.int(j / mbSize), :] = [x - j, y - i]

            costs[:] = 65537

            checkMatrix[:, :] = 0

    return vectors, computations / ((h * w) / mbSize**2)


def _SE3SS(imgP, imgI, mbSize, p):
    # Computes motion vectors using Simple and Efficient TSS method
    #
    # Input
    #   imgP : The image for which we want to find motion vectors
    #   imgI : The reference image
    #   mbSize : Size of the macroblock
    #   p : Search parameter  (read literature to find what this means)
    #
    # Ouput
    #   motionVect : the motion vectors for each integral macroblock in imgP
    #   SESTSScomputations: The average number of points searched for a macroblock

    h, w = imgP.shape

    vectors = np.zeros((np.int(h / mbSize), np.int(w / mbSize), 2))
    L = np.floor(np.log2(p + 1))
    stepMax = 2**(L - 1)

    costs = np.ones((6))*65537

    computations = 0

    for i in range(0, h - mbSize + 1, mbSize):
        for j in range(0, w - mbSize + 1, mbSize):

            stepSize = np.int(stepMax)
            x = j
            y = i

            while (stepSize >= 1):
                refBlkVerPointA = y
                refBlkHorPointA = x

                refBlkVerPointB = y
                refBlkHorPointB = x + stepSize

                refBlkVerPointC = y + stepSize
                refBlkHorPointC = x

                if _checkBounded(refBlkHorPointA, refBlkVerPointA, w, h, mbSize):
                    costs[0] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointA:refBlkVerPointA + mbSize, refBlkHorPointA:refBlkHorPointA + mbSize])
                    computations += 1

                if _checkBounded(refBlkHorPointB, refBlkVerPointB, w, h, mbSize):
                    costs[1] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointB:refBlkVerPointB + mbSize, refBlkHorPointB:refBlkHorPointB + mbSize])
                    computations += 1

                if _checkBounded(refBlkHorPointC, refBlkVerPointC, w, h, mbSize):
                    costs[2] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointC:refBlkVerPointC + mbSize, refBlkHorPointC:refBlkHorPointC + mbSize])
                    computations += 1

                quadrant = 0
                if ((costs[0] >= costs[1]) and (costs[0] >= costs[2])):
                    quadrant = 4
                elif ((costs[0] >= costs[1]) and (costs[0] < costs[2])):
                    quadrant = 1
                elif ((costs[0] < costs[1]) and (costs[0] < costs[2])):
                    quadrant = 2
                elif ((costs[0] < costs[1]) and (costs[0] >= costs[2])):
                    quadrant = 3

                if quadrant == 1:
                    refBlkVerPointD = y - stepSize
                    refBlkHorPointD = x

                    refBlkVerPointE = y - stepSize
                    refBlkHorPointE = x + stepSize

                    if _checkBounded(refBlkHorPointD, refBlkVerPointD, w, h, mbSize):
                        costs[3] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointD:refBlkVerPointD + mbSize, refBlkHorPointD:refBlkHorPointD + mbSize])
                        computations += 1

                    if _checkBounded(refBlkHorPointE, refBlkVerPointE, w, h, mbSize):
                        costs[4] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointE:refBlkVerPointE + mbSize, refBlkHorPointE:refBlkHorPointE + mbSize])
                        computations += 1
                elif quadrant == 2:
                    refBlkVerPointD = y - stepSize
                    refBlkHorPointD = x

                    refBlkVerPointE = y - stepSize
                    refBlkHorPointE = x - stepSize

                    refBlkVerPointF = y
                    refBlkHorPointF = x - stepSize

                    if _checkBounded(refBlkHorPointD, refBlkVerPointD, w, h, mbSize):
                        costs[3] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointD:refBlkVerPointD + mbSize, refBlkHorPointD:refBlkHorPointD + mbSize])
                        computations += 1

                    if _checkBounded(refBlkHorPointE, refBlkVerPointE, w, h, mbSize):
                        costs[4] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointE:refBlkVerPointE + mbSize, refBlkHorPointE:refBlkHorPointE + mbSize])
                        computations += 1

                    if _checkBounded(refBlkHorPointF, refBlkVerPointF, w, h, mbSize):
                        costs[5] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointF:refBlkVerPointF + mbSize, refBlkHorPointF:refBlkHorPointF + mbSize])
                        computations += 1
                elif quadrant == 3:
                    refBlkVerPointD = y
                    refBlkHorPointD = x - stepSize

                    refBlkVerPointE = y - stepSize
                    refBlkHorPointE = x - stepSize

                    if _checkBounded(refBlkHorPointD, refBlkVerPointD, w, h, mbSize):
                        costs[3] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointD:refBlkVerPointD + mbSize, refBlkHorPointD:refBlkHorPointD + mbSize])
                        computations += 1

                    if _checkBounded(refBlkHorPointE, refBlkVerPointE, w, h, mbSize):
                        costs[4] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointE:refBlkVerPointE + mbSize, refBlkHorPointE:refBlkHorPointE + mbSize])
                        computations += 1
                elif quadrant == 4:
                    refBlkVerPointD = y + stepSize
                    refBlkHorPointD = x + stepSize

                    if _checkBounded(refBlkHorPointD, refBlkVerPointD, w, h, mbSize):
                        costs[3] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVerPointD:refBlkVerPointD + mbSize, refBlkHorPointD:refBlkHorPointD + mbSize])
                        computations += 1

                dxy = np.argmin(costs)
                cost = costs[dxy]

                if dxy == 2:
                    x = refBlkHorPointB
                    y = refBlkVerPointB
                elif dxy == 3:
                    x = refBlkHorPointC
                    y = refBlkVerPointC
                elif dxy == 4:
                    x = refBlkHorPointD
                    y = refBlkVerPointD
                elif dxy == 5:
                    x = refBlkHorPointE
                    y = refBlkVerPointE
                elif dxy == 6:
                    x = refBlkHorPointF
                    y = refBlkVerPointF

                costs[:] = 65537
                stepSize /= 2

            vectors[np.int(i / mbSize), np.int(j / mbSize), :] = [y - i, x - j]

            costs[:] = 65537

    return vectors, computations / ((h * w) / mbSize**2)


def _N3SS(imgP, imgI, mbSize, p):
    # Computes motion vectors using *NEW* Three Step Search method
    #
    # Input
    #   imgP : The image for which we want to find motion vectors
    #   imgI : The reference image
    #   mbSize : Size of the macroblock
    #   p : Search parameter  (read literature to find what this means)
    #
    # Ouput
    #   motionVect : the motion vectors for each integral macroblock in imgP
    #   NTSScomputations: The average number of points searched for a macroblock

    h, w = imgP.shape

    h = np.int(h/mbSize) * mbSize
    w = np.int(w/mbSize) * mbSize
    imgP = imgP[:h, :w]
    imgI = imgI[:h, :w]

    vectors = np.zeros((np.int(h / mbSize), np.int(w / mbSize), 2), dtype=np.float32)

    costs = np.ones((3, 3), dtype=np.float32)*65537

    computations = 0

    L = np.floor(np.log2(p + 1))
    stepMax = np.int(2**(L - 1))

    l_count = 0
    for i in range(0, h - mbSize + 1, mbSize):
        for j in range(0, w - mbSize + 1, mbSize):
            x = j
            y = i

            costs[1, 1] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[i:i + mbSize, j:j + mbSize])
            computations += 1

            stepSize = stepMax

            for m in range(-stepSize, stepSize + 1, stepSize):
                for n in range(-stepSize, stepSize + 1, stepSize):
                    refBlkVer = y + m
                    refBlkHor = x + n
                    if ((refBlkVer < 0) or
                       (refBlkVer + mbSize > h) or
                       (refBlkHor < 0) or
                       (refBlkHor + mbSize > w)):
                            continue
                    costRow = np.int(m / stepSize) + 1
                    costCol = np.int(n / stepSize) + 1
                    if ((costRow == 1) and (costCol == 1)):
                        continue
                    costs[costRow, costCol] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                    computations = computations + 1


            dx, dy, min1 = _minCost(costs)  # finds which macroblock in imgI gave us min Cost

            x1 = x + (dx - 1) * stepSize
            y1 = y + (dy - 1) * stepSize

            stepSize = 1
            for m in range(-stepSize, stepSize + 1, stepSize):
                for n in range(-stepSize, stepSize + 1, stepSize):
                    refBlkVer = y + m
                    refBlkHor = x + n
                    if ((refBlkVer < 0) or
                       (refBlkVer + mbSize > h) or
                       (refBlkHor < 0) or
                       (refBlkHor + mbSize > w)):
                            continue
                    costRow = m + 1
                    costCol = n + 1
                    if ((costRow == 1) and (costCol == 1)):
                        continue
                    costs[costRow, costCol] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                    computations += 1

            dx, dy, min2 = _minCost(costs)  # finds which macroblock in imgI gave us min Cost
            x2 = x + (dx - 1)
            y2 = y + (dy - 1)

            NTSSFlag = 0
            if ((x1 == x2) and (y1 == y2)):
                NTSSFlag = -1
                #x = x1
                #y = y1
            elif (min2 <= min1):
                x = x2
                y = y2
                NTSSFlag = 1
            else:
                x = x1
                y = y1

            if NTSSFlag == 1:
                costs[:, :] = 65537
                costs[1, 1] = min2
                stepSize = 1
                for m in range(-stepSize, stepSize + 1, stepSize):
                    for n in range(-stepSize, stepSize + 1, stepSize):
                        refBlkVer = y + m
                        refBlkHor = x + n
                        if ((refBlkVer < 0) or
                           (refBlkVer + mbSize > h) or
                           (refBlkHor < 0) or
                           (refBlkHor + mbSize > w)):
                                continue

                        if ((refBlkVer >= i - 1) and
                            (refBlkVer <= i + 1) and
                            (refBlkHor >= j - 1) and
                            (refBlkHor <= j + 1)):
                                continue
                        costRow = np.int(m/stepSize) + 1
                        costCol = np.int(n/stepSize) + 1
                        if ((costRow == 1) and (costCol == 1)):
                            continue
                        costs[costRow, costCol] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                        computations += 1
                dx, dy, min2 = _minCost(costs)

                x += (dx - 1)
                y += (dy - 1)


            elif NTSSFlag == 0:
                costs[:, :] = 65537
                costs[1, 1] = min1
                stepSize = stepMax / 2
                while(stepSize >= 1):
                    for m in range(-stepSize, stepSize+1, stepSize):
                        for n in range(-stepSize, stepSize+1, stepSize):
                            refBlkVer = y + m
                            refBlkHor = x + n
                            if ((refBlkVer < 0) or
                               (refBlkVer + mbSize > h) or
                               (refBlkHor < 0) or
                               (refBlkHor + mbSize > w)):
                                    continue
                            costRow = m/stepSize + 1
                            costCol = n/stepSize + 1
                            if ((costRow == 1) and (costCol == 1)):
                                continue
                            costs[costRow, costCol] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                            computations = computations + 1
                            l_count += 1
                    dx, dy, mi = _minCost(costs)  # finds which macroblock in imgI gave us min Cost
                    x += (dx - 1) * stepSize
                    y += (dy - 1) * stepSize

                    stepSize /= 2
                    costs[1, 1] = costs[dy, dx]


            vectors[np.int(i / mbSize), np.int(j / mbSize), :] = [y - i, x - j]

            costs[:, :] = 65537

    return vectors, computations / ((h * w) / mbSize**2)


# Three step search
def _3SS(imgP, imgI, mbSize, p):
    h, w = imgP.shape

    vectors = np.zeros((np.int(h / mbSize), np.int(w / mbSize), 2))
    costs = np.ones((3, 3), dtype=np.float32)*65537

    computations = 0

    L = np.floor(np.log2(p + 1))
    stepMax = np.int(2**(L - 1))

    for i in range(0, h - mbSize + 1, mbSize):
        for j in range(0, w - mbSize + 1, mbSize):
            x = j
            y = i

            costs[1, 1] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[i:i + mbSize, j:j + mbSize])
            computations += 1
    
            stepSize = stepMax

            while(stepSize >= 1):
                for m in range(-stepSize, stepSize+1, stepSize):
                    for n in range(-stepSize, stepSize+1, stepSize):
                        refBlkVer = y + m
                        refBlkHor = x + n
                        if ((refBlkVer < 0) or
                           (refBlkVer + mbSize > h) or
                           (refBlkHor < 0) or
                           (refBlkHor + mbSize > w)):
                                continue
                        costRow = np.int(m/stepSize) + 1
                        costCol = np.int(n/stepSize) + 1
                        if ((costRow == 1) and (costCol == 1)):
                            continue
                        costs[costRow, costCol] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                        computations = computations + 1
                dx, dy, mi = _minCost(costs)  # finds which macroblock in imgI gave us min Cost
                x += (dx - 1) * stepSize
                y += (dy - 1) * stepSize

                stepSize /= 2
                costs[1, 1] = costs[dy, dx]
            vectors[np.int(i / mbSize), np.int(j / mbSize), :] = [y - i, x - j]

            costs[:, :] = 65537

    return vectors, computations / ((h * w) / mbSize**2)

def _4SS(imgP, imgI, mbSize, p):
    # Computes motion vectors using Four Step Search method
    #
    # Input
    #   imgP : The image for which we want to find motion vectors
    #   imgI : The reference image
    #   mbSize : Size of the macroblock
    #   p : Search parameter  (read literature to find what this means)
    #
    # Ouput
    #   motionVect : the motion vectors for each integral macroblock in imgP
    #   SS4computations: The average number of points searched for a macroblock
    h, w = imgP.shape

    vectors = np.zeros((np.int(h / mbSize), np.int(w / mbSize), 2))
    costs = np.ones((3, 3), dtype=np.float32)*65537

    computations = 0
    for i in range(0, h - mbSize + 1, mbSize):
        for j in range(0, w - mbSize + 1, mbSize):
            x = j
            y = i

            costs[1, 1] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[i:i + mbSize, j:j + mbSize])
            computations += 1

            for m in range(-2, 3, 2):
                for n in range(-2, 3, 2):
                    refBlkVer = y + m   # row/Vert co-ordinate for ref block
                    refBlkHor = x + n   # col/Horizontal co-ordinate

                    if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                        continue

                    costRow = np.int(m/2 + 1)
                    costCol = np.int(n/2 + 1)
                    if ((costRow == 1) and (costCol == 1)):
                        continue
                    costs[costRow, costCol] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])
                    computations = computations + 1
            dx, dy, mi = _minCost(costs)  # finds which macroblock in imgI gave us min Cost

            flag_4ss = 0
            if (dx == 1 and dy == 1):
                flag_4ss = 1
            else:
                xLast = x
                yLast = y
                x += (dx - 1) * 2
                y += (dy - 1) * 2
            
            costs[:, :] = 65537
            costs[1, 1] = mi

            stage = 1

            while (flag_4ss == 0 and stage <= 2):
                for m in range(-2, 3, 2):
                    for n in range(-2, 3, 2):
                        refBlkVer = y + m
                        refBlkHor = x + n
                        if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                            continue

                        if ((refBlkHor >= xLast - 2) and
                            (refBlkHor <= xLast + 2) and
                            (refBlkVer >= yLast - 2) and
                            (refBlkVer >= yLast + 2)):
                            continue

                        costRow = np.int(m/2) + 1
                        costCol = np.int(n/2) + 1

                        if (costRow == 1 and costCol == 1):
                            continue

                        costs[costRow, costCol] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])

                        computations += 1
                dx, dy, mi = _minCost(costs)  # finds which macroblock in imgI gave us min Cost

                if (dx == 1 and dy == 1):
                    flag_4ss = 1
                else:
                    flag_4ss = 0
                    xLast = x
                    yLast = y
                    x = x + (dx - 1) * 2
                    y = y + (dy - 1) * 2

                costs[:, :] = 65537
                costs[1, 1] = mi
                stage += 1

            for m in range(-1, 2):
                for n in range(-1, 2):
                    refBlkVer = y + m
                    refBlkHor = x + n

                    if not _checkBounded(refBlkHor, refBlkVer, w, h, mbSize):
                        continue
                    costRow = m + 1
                    costRow = n + 1
                    if (costRow == 2 and costCol == 2):
                        continue
                    costs[costRow, costCol] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])

                    computations += 1

            dx, dy, mi = _minCost(costs)  # finds which macroblock in imgI gave us min Cost

            x += dx - 1
            y += dy - 1

            vectors[np.int(i / mbSize), np.int(j / mbSize), :] = [y - i, x - j]

            costs[:, :] = 65537

    return vectors, computations / ((h * w) / mbSize**2)


# Exhaustive Search
def _ES(imgP, imgI, mbSize, p):
    h, w = imgP.shape

    vectors = np.zeros((np.int(h / mbSize), np.int(w / mbSize), 2), dtype=np.float32)
    costs = np.ones((2 * p + 1, 2 * p + 1), dtype=np.float32)*65537

    # we start off from the top left of the image
    # we will walk in steps of mbSize
    # for every marcoblock that we look at we will look for
    # a close match p pixels on the left, right, top and bottom of it
    for i in range(0, h - mbSize + 1, mbSize):
        for j in range(0, w - mbSize + 1, mbSize):
            # the exhaustive search starts here
            # we will evaluate cost for  (2p + 1) blocks vertically
            # and (2p + 1) blocks horizontaly
            # m is row(vertical) index
            # n is col(horizontal) index
            # this means we are scanning in raster order

            if ((j + p + mbSize >= w) or
                (j - p < 0) or
                (i - p < 0) or
                (i + p + mbSize >= h)):
                for m in range(-p, p + 1):
                    for n in range(-p, p + 1):
                        refBlkVer = i + m   # row/Vert co-ordinate for ref block
                        refBlkHor = j + n   # col/Horizontal co-ordinate
                        if ((refBlkVer < 0) or
                           (refBlkVer + mbSize > h) or
                           (refBlkHor < 0) or
                           (refBlkHor + mbSize > w)):
                                continue

                        costs[m + p, n + p] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])

            else:
                for m in range(-p, p + 1):
                    for n in range(-p, p + 1):
                        refBlkVer = i + m   # row/Vert co-ordinate for ref block
                        refBlkHor = j + n   # col/Horizontal co-ordinate
                        costs[m + p, n + p] = _costMAD(imgP[i:i + mbSize, j:j + mbSize], imgI[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize])


            # Now we find the vector where the cost is minimum
            # and store it ... this is what will be passed back.
            dx, dy, mi = _minCost(costs)  # finds which macroblock in imgI gave us min Cost
            vectors[np.int(i / mbSize), np.int(j / mbSize), :] = [dy - p, dx - p]

            costs[:, :] = 65537

    return vectors


def blockMotion(videodata, method='DS', mbSize=8, p=2, **plugin_args):
    """Block-based motion estimation
    
    Given a sequence of frames, this function
    returns motion vectors between frames.

    Parameters
    ----------
    videodata : ndarray, shape (numFrames, height, width, channel)
        A sequence of frames

    method : string
        "ES" --> exhaustive search

        "3SS" --> 3-step search

        "N3SS" --> "new" 3-step search [#f1]_

        "SE3SS" --> Simple and Efficient 3SS [#f2]_

        "4SS" --> 4-step search [#f3]_

        "ARPS" --> Adaptive Rood Pattern search [#f4]_

        "DS" --> Diamond search [#f5]_

    mbSize : int
        Macroblock size

    p : int
        Algorithm search distance parameter

    Returns
    ----------
    motionData : ndarray, shape (numFrames - 1, height/mbSize, width/mbSize, 2)

        The motion vectors computed from videodata. The first element of the last axis contains the y motion component, and second element contains the x motion component.

    References
    ----------
    .. [#f1] Renxiang Li, Bing Zeng, and Ming L. Liou, "A new three-step search algorithm for block motion estimation." IEEE Transactions on Circuits and Systems for Video Technology, 4 (4) 438-442, Aug 1994

    .. [#f2] Jianhua Lu and Ming L. Liou, "A simple and efficient search algorithm for block-matching motion estimation." IEEE Transactions on Circuits and Systems for Video Technology, 7 (2) 429-433, Apr 1997

    .. [#f3] Lai-Man Po and Wing-Chung Ma, "A novel four-step search algorithm for fast block motion estimation." IEEE Transactions on Circuits and Systems for Video Technology, 6 (3) 313-317, Jun 1996

    .. [#f4] Yao Nie and Kai-Kuang Ma, "Adaptive rood pattern search for fast block-matching motion estimation." IEEE Transactions on Image Processing, 11 (12) 1442-1448, Dec 2002

    .. [#f5] Shan Zhu and Kai-Kuang Ma, "A new diamond search algorithm for fast block-matching motion estimation." IEEE Transactions on Image Processing, 9 (2) 287-290, Feb 2000

    """
    videodata = vshape(videodata)

    # grayscale
    luminancedata = rgb2gray(videodata)

    numFrames, height, width, channels = luminancedata.shape
    assert numFrames > 1, "Must have more than 1 frame for motion estimation!"

    # luminance is 1 channel, so flatten for computation
    luminancedata = luminancedata.reshape((numFrames, height, width))

    motionData = np.zeros((numFrames - 1, np.int(height / mbSize), np.int(width / mbSize), 2), np.int8)

    if method == "ES":
        for i in range(numFrames - 1):
            motion = _ES(luminancedata[i + 1, :, :], luminancedata[i, :, :], mbSize, p)
            motionData[i, :, :, :] = motion
    elif method == "4SS":
        for i in range(numFrames - 1):
            motion, comps = _4SS(luminancedata[i + 1, :, :], luminancedata[i, :, :], mbSize, p)
            motionData[i, :, :, :] = motion
    elif method == "3SS":
        for i in range(numFrames - 1):
            motion, comps = _3SS(luminancedata[i + 1, :, :], luminancedata[i, :, :], mbSize, p)
            motionData[i, :, :, :] = motion
    elif method == "N3SS":
        for i in range(numFrames - 1):
            motion, comps = _N3SS(luminancedata[i + 1, :, :], luminancedata[i, :, :], mbSize, p)
            motionData[i, :, :, :] = motion
    elif method == "SE3SS":
        for i in range(numFrames - 1):
            motion, comps = _SE3SS(luminancedata[i + 1, :, :], luminancedata[i, :, :], mbSize, p)
            motionData[i, :, :, :] = motion
    elif method == "ARPS":  # BROKEN, check this
        for i in range(numFrames - 1):
            motion, comps = _ARPS(luminancedata[i + 1, :, :], luminancedata[i, :, :], mbSize, p)
            motionData[i, :, :, :] = motion
    elif method == "DS":
        for i in range(numFrames - 1):
            motion, comps = _DS(luminancedata[i + 1, :, :], luminancedata[i, :, :], mbSize, p)
            motionData[i, :, :, :] = motion
    else:
        raise NotImplementedError

    return motionData

#only handles (M, N, C) shapes
def _subcomp(framedata, motionVect, mbSize):
    M, N, C = framedata.shape

    compImg = np.zeros((M, N, C))

    for i in range(0, M - mbSize + 1, mbSize):
        for j in range(0, N - mbSize + 1, mbSize):
            dy = motionVect[i / mbSize, j / mbSize, 0]
            dx = motionVect[i / mbSize, j / mbSize, 1]

            refBlkVer = i + dy
            refBlkHor = j + dx

            # check bounds
            if not _checkBounded(refBlkHor, refBlkVer, N, M, mbSize):
                continue

            compImg[i:i + mbSize, j:j + mbSize, :] = framedata[refBlkVer:refBlkVer + mbSize, refBlkHor:refBlkHor + mbSize, :]
    return compImg


def blockComp(videodata, motionVect, mbSize=8):
    """Block-based motion compensation
    
    Using the given motion vectors, this function
    returns the motion-compensated video data.

    Parameters
    ----------
    videodata : ndarray
        an input frame sequence, shape (T, M, N, C), (T, M, N), (M, N, C) or (M, N)

    motionVect : ndarray
        ndarray representing block motion vectors. Expects ndarray, shape (T-1, M/mbSize, N/mbSize) or (M/mbSize, N/mbSize).

    mbSize : int
        Size of macroblock in pixels.

    Returns
    -------
    compImg : ndarray
        ndarray holding the motion compensated image frame, shape (T, M, N, C)

    """

    videodata = vshape(videodata)
    T, M, N, C = videodata.shape

    if T == 1:	# a single frame is passed in
        return _subcomp(videodata, motionVect, mbSize)

    else: # more frames passed in
        # allocate compensation data
        compVid = np.zeros((T, M, N, C))
        # pass the first frame uncorrected
        compVid[0, :, :, :] = videodata[0]
        for i in range(1, T):
            compVid[i, :, :, :] = _subcomp(videodata[i], motionVect[i-1], mbSize)
        return compVid
