import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from functools import reduce

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
    objects = []
    for key, value in data.items():
        if key.startswith('P'):
            for obj in value['pos']:
                if obj[3] == 'generic':
                    objects.append(Polygon(calcTransform(*obj[:3], IoUModelsName[obj[3]])))
    return objects

def calculateUnion(polygons):
    return unary_union(polygons).area


def calculateInter(polygons):
    polygon = polygons[0].intersection(polygons[1])

    for i in range(2, len(polygons)):
        polygon.intersection(polygons[i])

    return polygon.area

if __name__ == "__main__":
    genericModel = [(25.0, -25.0), (25.0, 25.0), (-25.0, 25.0), (-25.0, -25.0)]
    IoUModels = {"generic": genericModel}

    data = {'P0': {'id': 0, 
            'color': 'red', 
            'pos': [[246, 25, 0, 'humanPlayer'], 
                    [173, 227, 0, 'generic'],
                    [72, 265, 0, 'generic']]}, 
            
            'P1': {'id': 1, 
            'color': 'green', 
            'pos': [[101, 150, 0, 'humanPlayer'], 
                    [391, 297, 0, 'generic'], 
                    [458, 59, 0, 'generic']]}, 
                    
            'P2': {'id': 2, 
                    'color': 'blue', 
                    'pos': [[143, 226, 0, 'humanPlayer'], 
                            [244, 300, 0, 'generic'], 
                            [226, 469, 0, 'generic']]}, 
            'P3': {'id': 3, 
                    'color': 'pink', 
                    'pos': [[127, 452, 0, 'humanPlayer'], 
                            [194, 359, 0, 'generic'], 
                            [364, 83, 0, 'generic']]},
            'IoU': 0}
    
    d = reorganizationData(data, IoUModels)
    print(calculateUnion(d))
    print(calculateInter(d))