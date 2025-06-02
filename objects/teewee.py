from objects._shape._shape_ import Shape

class TeeweeShape(Shape):
    def __init__(self, cfg, id="P9", obj_id=10, screen=None, color=None, initial_position=None):
        self.id = int(id[-1])
        self.obj_id = obj_id

        size = cfg.data['game']['objectBaseSquareTam'] / 2
        
        self.vertices = [(-3*size,  -size),
                         ( 3*size,  -size),
                         ( 3*size,   size),  
                         (   size,   size),
                         (   size, 3*size),
                         (  -size, 3*size),
                         (  -size,   size),  
                         (-3*size,   size)]
             
        if screen is not None:
            super().__init__(screen, color, initial_position, cfg, self.vertices, "teewee")
