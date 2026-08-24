import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union


def apply_transformation(center_x, center_y, rotation_z, vertex_list):
    rotation_z = np.radians(rotation_z)
    transformation_matrix = np.array(
        [
            [np.cos(rotation_z), -np.sin(rotation_z), 0, center_x],
            [np.sin(rotation_z), np.cos(rotation_z), 0, center_y],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )

    transformed_vertices = []
    for vertex in vertex_list:
        vertex_array = np.array([*vertex, 0, 1])
        transformed_vertex = np.dot(transformation_matrix, vertex_array)
        transformed_vertices.append(tuple(transformed_vertex[:2]))

    return transformed_vertices


def calculate_goal_area(models):
    total_area = sum(Polygon(vertices).area for vertices in models)
    return total_area


def reorganize_data(data, model_mappings):
    objects = []
    for key, value in data.items():

        if key.startswith("P"):
            polygons = [
                Polygon(apply_transformation(*obj[:3], model_mappings[obj[3]]))
                for obj in value["pos"]
            ]
            unified_polygon = unary_union(polygons)
            objects.append(unified_polygon)
    return objects


def reorganize_data_map(data, model_mappings):
    """Return a mapping player_key -> unified polygon for that player's objects."""
    mapping: dict[str, Polygon] = {}
    for key, value in data.items():
        if key.startswith("P"):
            polygons = [
                Polygon(apply_transformation(*obj[:3], model_mappings[obj[3]]))
                for obj in value["pos"]
            ]
            unified_polygon = unary_union(polygons)
            mapping[key] = unified_polygon
    return mapping


def player_individual_polygons(data, model_mappings, pkey: str):
    """Return a list of shapely Polygons for each object belonging to `pkey`."""
    polygons = []
    value = data.get(pkey)
    if not value:
        return polygons

    for obj in value.get("pos", []):
        try:
            poly = Polygon(apply_transformation(*obj[:3], model_mappings[obj[3]]))
            polygons.append(poly)
        except Exception:
            continue
    return polygons


def calculate_union_area(polygons):
    return unary_union(polygons).area


def calculate_progress(iteration, goal_area, union_area):
    progress = (iteration * goal_area - union_area) / ((iteration - 1) * goal_area)

    if progress < 0:
        progress = 0
    elif progress > 100:
        progress = 100

    # print(f"Goal Area: {goal_area} | Union Area: {union_area} | Progress: {progress}")
    return abs(progress)
