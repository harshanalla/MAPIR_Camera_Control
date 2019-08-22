from ArrayTypes import AdjustYPR, CurveAdjustment

def test_curve_adjustment():
    array_type = 100

    imu = [0.0, 0.0, 0.0]
    array_id = 0
    adjusted_imu = CurveAdjustment(array_type, array_id, imu)
    assert adjusted_imu == [-2.5, -13.5, -17.3]

    imu = [0.0, 0.0, 0.0]
    array_id = 1
    adjusted_imu = CurveAdjustment(array_type, array_id, imu)
    assert adjusted_imu == [2.5, -13.5, 17.3]

    imu = [0.0, 0.0, 0.0]
    array_id = 2
    adjusted_imu = CurveAdjustment(array_type, array_id, imu)
    assert adjusted_imu == [-2.5, -13.5, -17.3]

    imu = [0.0, 0.0, 0.0]
    array_id = 3
    adjusted_imu = CurveAdjustment(array_type, array_id, imu)
    assert adjusted_imu == [2.5, -13.5, 17.3]