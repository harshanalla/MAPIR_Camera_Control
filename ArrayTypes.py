'''This function adjusts the IMU data of the camera to match the image captured by the sensor.'''
def AdjustYPR(atype = 0, arid = 0, imu=[0.0,0.0,0.0]):
    if atype == 101:
        orientation = arid % 2
        if orientation:
            imu[0] += 180 % 360
            imu[1] = -imu[1]
            imu[2] = -imu[2]
    if atype != 100:
        index = atype % 4
        orientation = arid % 2
        imu[0] += (index * 90.0)
        if orientation:
            imu[0] += 180.0
        imu[0] = imu[0] % 360
        if orientation:
            if index == 2:
                pass
            elif index == 3:
                imu[1], imu[2] = -imu[2], imu[1]
            elif index == 0:
                imu[1], imu[2] = -imu[1], -imu[2]
            else:
                imu[1], imu[2] = imu[2], -imu[1]
        else:
            if index == 0:
                pass
            elif index == 1:
                imu[1], imu[2] = -imu[2], imu[1]
            elif index == 2:
                imu[1], imu[2] = -imu[1], -imu[2]
            else:
                imu[1], imu[2] = imu[2], -imu[1]

''' 
These numbers (CURVE_NUMBERS_MASTER) represent the rotations of the 100 series of kernel arrays. 
They are negative because they use the master camera as their reference point.
'''
CURVE_NUMBERS_MASTER ={
    "YAW": -2.5,
    "PITCH": -17.3,
    "ROLL": -13.5
}
''' 
This function adds the numbers above to adjust imu for curved arrays.
'''
def CurveAdjustment(atype = 100, arid = 0, imu = [0.0,0.0,0.0]):
    if atype == 100:
        if arid == 0 or arid == 3:
            imu[0] += CURVE_NUMBERS_MASTER["YAW"]
            imu[1] += CURVE_NUMBERS_MASTER["PITCH"]
            imu[2] += CURVE_NUMBERS_MASTER["ROLL"]
        else:
            imu[0] -= CURVE_NUMBERS_MASTER["YAW"]
            imu[1] += CURVE_NUMBERS_MASTER["PITCH"]
            imu[2] -= CURVE_NUMBERS_MASTER["ROLL"]
    elif atype == 101:
        if arid == 0:
            imu[0] += CURVE_NUMBERS_MASTER["YAW"]
            imu[1] += CURVE_NUMBERS_MASTER["PITCH"]
            imu[2] += CURVE_NUMBERS_MASTER["ROLL"]
        elif arid == 1:
            imu[0] -= CURVE_NUMBERS_MASTER["YAW"]
            imu[1] -= CURVE_NUMBERS_MASTER["PITCH"]
            imu[2] += CURVE_NUMBERS_MASTER["ROLL"]
        elif arid == 2:
            imu[0] -= CURVE_NUMBERS_MASTER["YAW"]
            imu[1] += CURVE_NUMBERS_MASTER["PITCH"]
            imu[2] -= CURVE_NUMBERS_MASTER["ROLL"]
        else:
            imu[0] -= CURVE_NUMBERS_MASTER["YAW"]
            imu[1] -= CURVE_NUMBERS_MASTER["PITCH"]
            imu[2] -= CURVE_NUMBERS_MASTER["ROLL"]
    return imu
