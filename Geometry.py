import numpy as np

class Geometry:
    @staticmethod
    def get_distance_between_two_points(a, b):
        return np.sqrt(np.power((a[0] - b[0]), 2) + np.power((a[1] - b[1]), 2))

    @staticmethod
    def get_hypotenuse(points):
        line1 = Geometry.get_distance_between_two_points(points[0], points[1])
        line2 = Geometry.get_distance_between_two_points(points[1], points[2])
        line3 = Geometry.get_distance_between_two_points(points[2], points[0])
        return  max([line1, line2, line3])
