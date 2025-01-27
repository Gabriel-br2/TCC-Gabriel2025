import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

def calcTransform(cx, cy, rz, relacao_vertices):
    matriz_transformacao = np.array([
        [np.cos(rz), -np.sin(rz), 0, cx],
        [np.sin(rz),  np.cos(rz), 0, cy],
        [         0,           0, 1,  0],
        [         0,           0, 0,  1]
    ])

    vertices_transformados = []
    for vertice in relacao_vertices:
        vertice_array = np.array([*vertice, 0, 1])
        vertice_transformado = np.dot(matriz_transformacao, vertice_array)
        vertices_transformados.append(tuple(vertice_transformado[:2]))
    
    return vertices_transformados

def reorganizationData(data, IoUModelsName):
    objects = {"generic": [],
               "teewee":  []}
    
    for key, value in data.items():
        if key.startswith('P'):            
            for obj in value['pos'][1:]:
                objects[obj[3]].append(Polygon(calcTransform(*obj[:3], IoUModelsName[obj[3]])))
    return objects

def calculateUnion(polygons):
    polygons = polygons["generic"] + polygons["teewee"] 
    return unary_union(polygons).area

def calculate_intersections(polygons):
    areaValue = 0
    for key, polygon_list in polygons.items():
        
        intersection_result = polygon_list[0].intersection(polygon_list[1])
        
        for polygon in polygon_list[2:]:
            intersection_result = intersection_result.intersection(polygon)
    
        areaValue += polygon.area
    return areaValue


if __name__ == "__main__":
    genericModel = [(25.0, -25.0), (25.0, 25.0), (-25.0, 25.0), (-25.0, -25.0)]
    teeweeModel = [(-60.0, 0.0), (60.0, 0.0), (60.0, 40.0), (20.0, 40.0), (20.0, 80.0), (-20.0, 80.0), (-20.0, 40.0), (-60.0, 40.0)]
    
    IoUModels = {"generic": genericModel, "teewee":teeweeModel}

    data = {'P0': {'id': 0, 
            'color': 'red', 
            'pos': [[246, 25, 0, 'humanPlayer'], 
                    [173, 227, 0, 'generic'],
                    [72, 265, 0, 'teewee']]}, 
            
            'P1': {'id': 1, 
            'color': 'green', 
            'pos': [[101, 150, 0, 'humanPlayer'], 
                    [391, 297, 0, 'generic'], 
                    [458, 59, 0, 'teewee']]}, 
                    
            'P2': {'id': 2, 
                    'color': 'blue', 
                    'pos': [[143, 226, 0, 'humanPlayer'], 
                            [244, 300, 0, 'generic'], 
                            [226, 469, 0, 'teewee']]}, 
            'P3': {'id': 3, 
                    'color': 'pink', 
                    'pos': [[127, 452, 0, 'humanPlayer'], 
                            [194, 359, 0, 'generic'], 
                            [364, 83, 0, 'teewee']]},
            'IoU': 0}
    
    d = reorganizationData(data, IoUModels)
    print(calculateUnion(d))
    print(calculate_intersections(d))