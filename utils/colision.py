import math

from shapely.geometry import Polygon


def detect_polygon_intersection(poly1_points, poly2_points):

    poly1 = Polygon(poly1_points)
    poly2 = Polygon(poly2_points)

    intersection = poly1.intersection(poly2)

    return not intersection.is_empty


def point_in_polygon(point, polygon):
    x, y = point
    inside = False

    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[(i + 1) % len(polygon)]

        if (yi > y) != (yj > y):
            xinters = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xinters:
                inside = not inside

    return inside


def get_axis_aligned_bounding_box(vertices):
    min_x = min(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_x = max(v[0] for v in vertices)
    max_y = max(v[1] for v in vertices)
    return (min_x, min_y, max_x, max_y)


def aabbs_intersect(box1, box2):
    no_overlap = (
        box1[2] < box2[0] or box1[0] > box2[2] or box1[3] < box2[1] or box1[1] > box2[3]
    )
    return not no_overlap
