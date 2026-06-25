"""Explicit registry of the playable shapes.

This replaces the previous runtime directory-scanning plugin loader with a
static mapping. The keys match the ``shape_type`` stored in each object's
position payload, so they must stay stable to remain compatible with the
network protocol and saved logs.
"""

from objects.generic import GenericShape
from objects.hero import HeroShape
from objects.ricky import RickyShape
from objects.teewee import TeeweeShape
from objects.z import ZShape

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
