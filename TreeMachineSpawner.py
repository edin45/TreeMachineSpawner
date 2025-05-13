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

import bpy
import os
from bpy.types import Panel, Operator, AddonPreferences, PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty, PointerProperty
import bpy.utils.previews
import math

# Global variables
preview_collections = {}
object_list = []

class ObjectLibraryPreferences(AddonPreferences):
    bl_idname = __name__.split(".")[0]  # Gets the parent module name

    library_path: StringProperty(
        name="Library File Path",
        subtype='FILE_PATH',
        default="",
        description="Path to the Blender file containing objects to append"
    )
    
    # grid_columns: IntProperty(
    #     name="Grid Columns",
    #     default=3,
    #     min=1,
    #     max=8,
    #     description="Number of columns in the object grid"
    # )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "library_path")
        # layout.prop(self, "grid_columns")
        layout.label(text="Set the path to the Tree Machine Library File")

class OBJECT_PG_library_settings(PropertyGroup):
    selected_object: StringProperty(
        name="Selected Object",
        default="",
        description="Currently selected object"
    )
    active_tree_type: StringProperty(
        default="deciduous",
    )

    resolution: StringProperty(
        default="4k",
    )

def load_object_list(context):
    """Load objects from the library file and their previews"""
    global object_list
    object_list = []
    
    # Get addon preferences
    addon_prefs = context.preferences.addons[__name__.split(".")[0]].preferences
    library_path = addon_prefs.library_path
    
    if not library_path or not os.path.exists(library_path):
        return False
    
    # Get the directory where the library file is located
    library_dir = os.path.dirname(library_path)
    preview_dir = os.path.join(library_dir, "preview_images")
    
    # Check if preview_images folder exists
    if not os.path.exists(preview_dir):
        print(f"Preview directory not found: {preview_dir}")
        os.makedirs(preview_dir, exist_ok=True)
    
    # Load previews
    global preview_collections
    if "thumbnail_previews" not in preview_collections:
        preview_collections["thumbnail_previews"] = bpy.utils.previews.new()
    
    pcoll = preview_collections["thumbnail_previews"]
    
    try:
        # Access objects in the library file without appending them
        with bpy.data.libraries.load(library_path, link=False) as (data_from, data_to):
            for obj_name in data_from.objects:
                # Load preview image
                image_path = os.path.join(preview_dir, obj_name.replace(" (1k)","").replace(" (2k)","").replace(" (4k)","").replace(" (8k)","").replace(" (Max)","") + ".png")
                    
                if obj_name not in pcoll:
                    if os.path.exists(image_path):
                        pcoll.load(obj_name, image_path, 'IMAGE')
                    else:
                        # Create a blank preview if image doesn't exist
                        pcoll.load(obj_name, os.path.join(os.path.dirname(__file__), "blank.png"), 'IMAGE')
                        print(f"Preview image not found: {image_path}")
                    
                # Add item to object list
                object_list.append(obj_name)
        object_list.sort()
        
        return True
    except Exception as e:
        print(f"Error loading library file: {e}")
        return False

class OBJECT_OT_library_select(Operator):
    bl_idname = "object.library_select"
    bl_label = "Select Object"
    bl_description = "Select an object from the library"
    bl_options = {'REGISTER', 'UNDO'}
    
    object_name: StringProperty(
        name="Object Name",
        description="Name of the object to select"
    )
    
    def execute(self, context):
        settings = context.scene.object_library_settings
        settings.selected_object = self.object_name
        return {'FINISHED'}

class OBJECT_OT_library_spawn(Operator):
    bl_idname = "object.library_spawn"
    bl_label = "Spawn Object"
    bl_description = "Append the selected object from the library"
    bl_options = {'REGISTER', 'UNDO'}

    object_to_append: bpy.props.StringProperty(name="Which Object to Append")

    def execute(self, context):
        # Get the selected object
        settings = context.scene.object_library_settings
        obj_name = self.object_to_append
        
        if not obj_name:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}
        
        # Get the library path from preferences
        addon_prefs = context.preferences.addons[__name__.split(".")[0]].preferences
        library_path = addon_prefs.library_path
        
        if not library_path or not os.path.exists(library_path):
            self.report({'ERROR'}, "Library file not found")
            return {'CANCELLED'}
        
        # Append the object
        try:
            collections_before = set(bpy.data.collections.keys())

            # Specify 'Object' as the data type
            inner_path = 'Object'
            bpy.ops.wm.append(
                filepath=os.path.join(library_path, inner_path, obj_name),
                directory=os.path.join(library_path, inner_path),
                filename=obj_name
            )
            obj = bpy.context.selected_objects[0]  # Will get the selected object after append

            obj.matrix_world.translation = bpy.context.scene.cursor.location

            # Step 3: Get collections after appending
            collections_after = set(bpy.data.collections.keys())

            # Step 4: Identify newly added collections
            new_collections = collections_after - collections_before

            # Step 5: Disable new collections in the active view layer
            layer_collection = bpy.context.view_layer.layer_collection

            def disable_collection_in_view_layer(target_collection, layer_coll):
                if layer_coll.collection == target_collection:
                    layer_coll.exclude = True  # This hides the collection
                for child in layer_coll.children:
                    disable_collection_in_view_layer(target_collection, child)

            for col_name in new_collections:
                collection = bpy.data.collections.get(col_name)
                if collection:
                    disable_collection_in_view_layer(collection, layer_collection)

            self.report({'INFO'}, f"Appended object: {obj_name}")
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error appending object: {e}")
            return {'CANCELLED'}

class OBJECT_OT_library_refresh(Operator):
    bl_idname = "object.library_refresh"
    bl_label = "Refresh Tree Machine Library"
    bl_description = "Refresh the tree machine library"
    
    def execute(self, context):
        if load_object_list(context):
            self.report({'INFO'}, "Tree Machine library refreshed")
        else:
            self.report({'ERROR'}, "Failed to refresh tree machine library")
        return {'FINISHED'}

class OBJECT_PT_library_panel(Panel):
    bl_label = "Tree Machine"
    bl_idname = "OBJECT_PT_library_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tree Machine"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.object_library_settings
        addon_prefs = context.preferences.addons[__name__.split(".")[0]].preferences
        
        # Check if library path is set
        if not addon_prefs.library_path or not os.path.exists(addon_prefs.library_path):
            layout.label(text="No library file set")
            layout.label(text="Set path in Preferences > Add-ons")
            layout.operator("wm.addon_prefs_show", text="Open Preferences").module = __name__.split(".")[0]
            return
        
        # Refresh button
        layout.operator("object.library_refresh", text="Refresh Library", icon='FILE_REFRESH')
        
        # Selected object display
        if settings.selected_object:
            box = layout.box()
            box.label(text=f"Selected: {settings.selected_object}")
            
            # Display preview of selected object
            pcoll = preview_collections["thumbnail_previews"]
            if settings.selected_object in pcoll:
                col = box.column(align=True)
                col.template_icon(icon_value=pcoll[settings.selected_object].icon_id, scale=5)
                col.separator()
            
            # Spawn button
            box.operator("object.library_spawn", text=f"Spawn {settings.selected_object}", icon='IMPORT')
        
        layout.label(text="Library Objects:")
        
        # Display grid of object previews
        global object_list
        if not object_list:
            if not load_object_list(context):
                layout.label(text="No objects found")
                return
        
        pcoll = preview_collections["thumbnail_previews"]
        grid_columns = 3
        
        # Create grid layout
        grid = layout.grid_flow(columns=grid_columns, even_columns=True, even_rows=True)
        
        for obj_name in object_list:
            if settings.active_tree_type in obj_name:
                # Create a column for each object
                col = grid.column(align=True)
                
                # Add button with preview image
                op = col.operator(
                    "object.library_select", 
                    text="", 
                    icon_value=pcoll[obj_name].icon_id,
                    depress=(settings.selected_object == obj_name)
                )
                op.object_name = obj_name
                
                # Add label below the image
                col.label(text=obj_name, icon='NONE')

class OBJECT_OT_library_show_popup(Operator):
    bl_idname = "object.show_library_popup"
    bl_label = "Object Library"
    bl_description = "Show the object library popup"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="OBJECT_PT_library_popup")
        return {'FINISHED'}

class OBJECT_OT_SetTreeType(Operator):
    bl_idname = "object.resolution"
    bl_label = "Set Tree Resolution"
    resolution: bpy.props.StringProperty()
    
    def execute(self, context):
        context.scene.object_library_settings.resolution = self.resolution
        return {'FINISHED'}

class OBJECT_PT_library_popup(Panel):
    bl_label = "Tree Machine Library"
    bl_idname = "OBJECT_PT_library_popup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 70
    bl_ui_units_y = 60
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.object_library_settings
        addon_prefs = context.preferences.addons[__name__.split(".")[0]].preferences

        # Check if library path is set
        if not addon_prefs.library_path or not os.path.exists(addon_prefs.library_path):
            layout.label(text="No library file set")
            layout.label(text="Set path in Preferences > Add-ons")
            layout.operator("wm.addon_prefs_show", text="Open Preferences").module = __name__.split(".")[0]
            return
        
        # Display grid of object previews
        global object_list
        if not object_list:
            if not load_object_list(context):
                layout.label(text="No objects found")
                return
        
        pcoll = preview_collections["thumbnail_previews"]
        
        main_col = layout.column(align=True)
        
        row = main_col.row()

        row.operator("object.resolution", text="Max (8k+)", depress=settings.resolution=="Max").resolution = 'Max'
        row.operator("object.resolution", text="8k", depress=settings.resolution=="8k").resolution = '8k'
        row.operator("object.resolution", text="4k", depress=settings.resolution=="4k").resolution = '4k'
        row.operator("object.resolution", text="2k", depress=settings.resolution=="2k").resolution = '2k'
        row.operator("object.resolution", text="1k", depress=settings.resolution=="1k").resolution = '1k'

        layout.separator()
        
        # Create grid layout
        grid = layout.grid_flow(columns=5, even_columns=True, even_rows=True)
        
        for obj_name in object_list:
            # Create a column for each object
            if settings.resolution in obj_name:
                col = grid.column(align=True)
                
                col.template_icon(icon_value=pcoll[obj_name].icon_id,scale=10)
                library_spawn_operator = col.operator("object.library_spawn", text=f"Spawn " + obj_name.replace(" (Deciduous)","").replace(" (Coniferous)",""), icon='IMPORT') 
                library_spawn_operator.object_to_append = obj_name
