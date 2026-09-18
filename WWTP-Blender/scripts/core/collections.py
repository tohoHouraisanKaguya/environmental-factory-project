"""Fixed WWTP collection hierarchy; safe to call repeatedly."""
import bpy

TREE = {
    "WWTP": {"SITE": {}, "ROADS": {}, "BUILDINGS": {},
             "WATER_STRUCTURES": {"PRETREATMENT": {}, "PRIMARY": {}, "BIOLOGICAL": {}, "SECONDARY": {}, "DISINFECTION": {}},
             "EQUIPMENT": {"PUMPS": {}, "BLOWERS": {}, "SCREENS": {}, "SCRAPERS": {}, "DOSING": {}},
             "PIPES": {"WASTEWATER": {}, "SLUDGE_RETURN": {}, "INTERNAL_RECYCLE": {}, "AIR": {}, "CHEMICAL": {}},
             "VEGETATION": {}, "LIGHTING": {}, "REFERENCES": {}}
}

def _ensure(name, parent=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    owner = bpy.context.scene.collection if parent is None else parent
    if col.name not in owner.children:
        owner.children.link(col)
    return col

def ensure_tree(tree=TREE, parent=None):
    result = {}
    for name, children in tree.items():
        col = _ensure(name, parent)
        result[name] = col
        result.update(ensure_tree(children, col))
    return result

def remove_collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        return
    for child in list(col.children):
        remove_collection(child.name)
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(col)
