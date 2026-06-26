from game.shared.shapes.generic import GenericShape
from game.shared.shapes.hero import HeroShape
from game.shared.shapes.ricky import RickyShape
from game.shared.shapes.teewee import TeeweeShape
from game.shared.shapes.z import ZShape

SHAPE_CLASSES = {
    "generic": GenericShape,
    "hero": HeroShape,
    "ricky": RickyShape,
    "teewee": TeeweeShape,
    "z": ZShape,
}

__all__ = [
    "SHAPE_CLASSES",
    "GenericShape",
    "HeroShape",
    "RickyShape",
    "TeeweeShape",
    "ZShape",
]
