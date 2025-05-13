'''
Copyright (C) 2025 Edin Spiegel

apps4trainers@gmail.com

Created by Edin Spiegel. This file is part of a Blender add-on.

    This Blender Add-on is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <https://www.gnu.org/licenses>.
'''

bl_info = {
    "name": "Tree Machine Spawner",
    "author": "Edin Spiegel",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Tree Machine Spawner (Ctrl+T)",
    "description": "Spawner for the Tree Machine Trees",
    "category": "Object",
}

import bpy
from .TreeMachineSpawner import (
    OBJECT_PT_library_popup, 
    OBJECT_OT_library_show_popup, 
    OBJECT_OT_library_refresh, 
    OBJECT_OT_library_spawn,
    OBJECT_OT_library_select,
    OBJECT_PG_library_settings,
    OBJECT_OT_SetTreeType,
    ObjectLibraryPreferences,
    preview_collections
)

addon_keymaps = []

def register():
    # Register classes
    bpy.utils.register_class(ObjectLibraryPreferences)
    bpy.utils.register_class(OBJECT_PG_library_settings)
    bpy.utils.register_class(OBJECT_OT_library_select)
    bpy.utils.register_class(OBJECT_OT_library_spawn)
    bpy.utils.register_class(OBJECT_OT_library_refresh)
    bpy.utils.register_class(OBJECT_OT_library_show_popup)
    bpy.utils.register_class(OBJECT_PT_library_popup)
    bpy.utils.register_class(OBJECT_OT_SetTreeType)
    
    # Register properties
    bpy.types.Scene.object_library_settings = bpy.props.PointerProperty(type=OBJECT_PG_library_settings)
    
    # Register keymapping
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new(
            "object.show_library_popup", 
            type='T', 
            value='PRESS', 
            ctrl=True
        )
        addon_keymaps.append((km, kmi))

def unregister():
    # Remove keymapping
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    # Unregister classes
    bpy.utils.unregister_class(OBJECT_PT_library_popup)
    bpy.utils.unregister_class(OBJECT_OT_library_show_popup)
    bpy.utils.unregister_class(OBJECT_OT_library_refresh)
    bpy.utils.unregister_class(OBJECT_OT_library_spawn)
    bpy.utils.unregister_class(OBJECT_OT_library_select)
    bpy.utils.unregister_class(OBJECT_PG_library_settings)
    bpy.utils.unregister_class(OBJECT_OT_SetTreeType)
    bpy.utils.unregister_class(ObjectLibraryPreferences)
    
    # Delete properties
    del bpy.types.Scene.object_library_settings
    
    # Clear preview collections
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

if __name__ == "__main__":
    register()
