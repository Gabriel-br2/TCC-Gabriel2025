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

def calcA_Goal(Models):
    A = 0
    for key, value in Models.items():
        A += Polygon(value).area

    return A

def reorganizationData(data, IoUModelsName):    
    objects = []

    for key, value in data.items():
        if key.startswith('P'):
            
            p = []
            for obj in value['pos'][1:]:
                p.append(Polygon(calcTransform(*obj[:3], IoUModelsName[obj[3]])))
            
            U = unary_union(p)            
            objects.append(U)

    return objects

def calcUnion(polygons):
    return unary_union(polygons).area

def calcPercentage(n, A_goal, A_Union):
    progress = ((n * A_goal - A_Union) / ((n-1)*A_goal))
    print(f"A_goal: {A_goal} | A_Union: {A_Union} | Calc: {progress}")

    return progress

