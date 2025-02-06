import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

def apply_transformation(center_x, center_y, rotation_z, vertex_list):
    """
    Applies a 2D affine transformation (rotation and translation) to a list of vertices.

    Args:
        center_x (float): The x-coordinate of the transformation center.
        center_y (float): The y-coordinate of the transformation center.
        rotation_z (float): The rotation angle in radians.
        vertex_list (list): A list of tuples, where each tuple represents a vertex (x, y).

    Returns:
        list: A list of tuples representing the transformed vertices.
    """
    transformation_matrix = np.array([
        [np.cos(rotation_z), -np.sin(rotation_z), 0, center_x],
        [np.sin(rotation_z),  np.cos(rotation_z), 0, center_y],
        [                 0,                   0, 1,         0],
        [                 0,                   0, 0,         1]
    ])

    transformed_vertices = []
    for vertex in vertex_list:
        vertex_array = np.array([*vertex, 0, 1])  # Create homogeneous coordinates
        transformed_vertex = np.dot(transformation_matrix, vertex_array)
        transformed_vertices.append(tuple(transformed_vertex[:2]))  # Extract x and y coordinates
    
    return transformed_vertices

def calculate_goal_area(models):
    """
    Calculates the total area of the goal region, which is the sum of the areas of all models.

    Args:
        models (dict): A dictionary where keys are model identifiers and values are lists of vertices.

    Returns:
        float: The total area of the goal region.
    """
    total_area = sum(Polygon(vertices).area for vertices in models.values())
    return total_area

def reorganize_data(data, model_mappings):    
    """
    Reorganizes the data into a list of Shapely polygons.

    This function iterates through the data, applies transformations to the vertices based on
    the model mappings, and creates Shapely polygons. It then unifies the polygons for each object.

    Args:
        data (dict): A dictionary containing the object data, including position information.
        model_mappings (dict): A dictionary mapping object identifiers to vertex lists.

    Returns:
        list: A list of Shapely polygons representing the objects.
    """
    objects = []

    for key, value in data.items():
        if key.startswith('P'):  # Process objects starting with 'P'
            polygons = [Polygon(apply_transformation(*obj[:3], model_mappings[obj[3]])) for obj in value['pos'][1:]]
            unified_polygon = unary_union(polygons)  # Combine individual polygons into a single one
            objects.append(unified_polygon)

    return objects

def calculate_union_area(polygons):
    """
    Calculates the area of the union of multiple polygons.

    Args:
        polygons (list): A list of Shapely polygons.

    Returns:
        float: The area of the union of the polygons.
    """
    return unary_union(polygons).area

def calculate_progress(iteration, goal_area, union_area):
    """
    Calculates the progress towards the goal, based on the current iteration, goal area, and union area.

    Args:
        iteration (int): The current iteration number.
        goal_area (float): The total area of the goal region.
        union_area (float): The area of the union of the current object polygons.

    Returns:
        float: The progress towards the goal (a value that might be negative or greater than 1).
    """
    progress = ((iteration * goal_area - union_area) / ((iteration - 1) * goal_area))
    #print(f"Goal Area: {goal_area} | Union Area: {union_area} | Progress: {progress}")
    return progress