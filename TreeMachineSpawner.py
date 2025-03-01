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
import os
from bpy.types import Panel, Operator, AddonPreferences, PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty, PointerProperty
import bpy.utils.previews

# Global variables
preview_collections = {}
object_list = []

class ObjectLibraryPreferences(AddonPreferences):
    bl_idname = __name__

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
        layout.prop(self, "grid_columns")
        layout.label(text="Set the path to the Tree Machine Library File")
        # layout.label(text="Preview images should be in a 'preview_images' folder next to the library file")
        # layout.label(text="Images should be named 'object_name.jpg'")

class OBJECT_PG_library_settings(PropertyGroup):
    selected_object: StringProperty(
        name="Selected Object",
        default="",
        description="Currently selected object"
    )
    active_tree_type : StringProperty(
        default="deciduous",
    )

def load_object_list(context):
    """Load objects from the library file and their previews"""
    global object_list
    object_list = []
    
    # Get addon preferences
    addon_prefs = context.preferences.addons[__name__].preferences
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
            # Generate items for each object
            # data_to.collections = data_from.collections
            # print(f"data_from.collections - {data_from.collections}")
            # for collection in data_from.collections:
            #     # if obj.name in collection.objects:
            #     loaded_collection = bpy.data.collections.get(collection)
            #     print("dfsafdsf: " + str(loaded_collection.objects));
            for obj_name in data_from.objects:
                # Load preview image
                image_path = os.path.join(preview_dir, obj_name.replace(" (Deciduous)","").replace(" (Coniferous)","") + ".jpg")
                    
                if obj_name not in pcoll:
                    if os.path.exists(image_path):
                        pcoll.load(obj_name, image_path, 'IMAGE')
                    else:
                        # Create a blank preview if image doesn't exist
                        pcoll.load(obj_name, os.path.join(os.path.dirname(__file__), "blank.png"), 'IMAGE')
                        print(f"Preview image not found: {image_path}")
                    
                    # Add item to object list
                object_list.append(obj_name)
                    # if collection.name in object_list:
                    #     object_list[collection.name].append(obj_name)
                    # else:
                    #     object_list[collection.name] = obj_name
                    # print("object_list_1: " + str(object_list))
        # print(object_list)
        
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
        #settings.selected_object
        
        if not obj_name:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}
        
        # Get the library path from preferences
        addon_prefs = context.preferences.addons[__name__].preferences
        library_path = addon_prefs.library_path
        
        if not library_path or not os.path.exists(library_path):
            self.report({'ERROR'}, "Library file not found")
            return {'CANCELLED'}
        
        # Append the object
        try:
            # Specify 'Object' as the data type
            inner_path = 'Object'
            bpy.ops.wm.append(
                filepath=os.path.join(library_path, inner_path, obj_name),
                directory=os.path.join(library_path, inner_path),
                filename=obj_name
            )
            obj = bpy.context.selected_objects[0]  # Will get the selected object after append

            # Get cursor location
            cursor_loc = bpy.context.scene.cursor.location

            # Set the object's location to the cursor location
            obj.location = cursor_loc

            self.report({'INFO'}, f"Appended object: {obj_name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error appending object: {e}")
            return {'CANCELLED'}

class OBJECT_OT_library_refresh(Operator):
    bl_idname = "object.library_refresh"
    bl_label = "Refresh Object Library"
    bl_description = "Refresh the object library"
    
    def execute(self, context):
        if load_object_list(context):
            self.report({'INFO'}, "Object library refreshed")
        else:
            self.report({'ERROR'}, "Failed to refresh object library")
        return {'FINISHED'}

class OBJECT_PT_library_panel(Panel):
    bl_label = "Object Library"
    bl_idname = "OBJECT_PT_library_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Library"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.object_library_settings
        addon_prefs = context.preferences.addons[__name__].preferences
        
        # Check if library path is set
        if not addon_prefs.library_path or not os.path.exists(addon_prefs.library_path):
            layout.label(text="No library file set")
            layout.label(text="Set path in Preferences > Add-ons")
            layout.operator("wm.addon_prefs_show", text="Open Preferences").module = __name__
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
        grid_columns = addon_prefs.grid_columns
        
        # Create grid layout
        grid = layout.grid_flow(columns=grid_columns, even_columns=True, even_rows=True)
        
        for obj_name in object_list[settings.active_tree_type]:
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
    bl_idname = "object.selected_tree_type"
    bl_label = "Set Tree Type"
    tree_type: bpy.props.StringProperty()
    
    def execute(self, context):
        context.scene.object_library_settings.active_tree_type = self.tree_type
        return {'FINISHED'}

class OBJECT_PT_library_popup(Panel):
    bl_label = "Tree Machine Library"
    bl_idname = "OBJECT_PT_library_popup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 60
    bl_ui_units_y = 60
    # bl_options = {'INSTANCED'}

    # def draw_header(self, context):
    #     layout = self.layout

    #     layout.label(text="Trees Type:")

    #     row = layout.row()

    #     row.operator("object.selected_tree_type", text="Deciduous", depress=settings.active_tree_type=="deciduous").tree_type = 'deciduous'
    #     row.operator("object.selected_tree_type", text="Coniferous", depress=settings.active_tree_type=="coniferous").tree_type = 'coniferous'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.object_library_settings
        addon_prefs = context.preferences.addons[__name__].preferences

        # layout.template_header()

        # Check if library path is set
        if not addon_prefs.library_path or not os.path.exists(addon_prefs.library_path):
            layout.label(text="No library file set")
            layout.label(text="Set path in Preferences > Add-ons")
            layout.operator("wm.addon_prefs_show", text="Open Preferences").module = __name__
            return
        
        # Refresh button
        # layout.operator("object.library_refresh", text="Refresh Library", icon='FILE_REFRESH')
        
        # Display grid of object previews
        global object_list
        if not object_list:
            if not load_object_list(context):
                layout.label(text="No objects found")
                return
        
        pcoll = preview_collections["thumbnail_previews"]
        # grid_columns = addon_prefs.grid_columns
        
        # Add a row for the selected object and spawn button
        # if settings.selected_object:
        #     box = layout.box()
        #     row = box.row()
            
        #     # Left side: preview image
        #     col_left = row.column()
        #     col_left.template_icon(icon_value=pcoll[settings.selected_object].icon_id, scale=10)
            
        #     # Right side: info and button
        #     col_right = row.column()
        #     col_right.label(text=f"Selected: {settings.selected_object}")
        #     col_right.separator()
        #     col_right.operator("object.library_spawn", text=f"Spawn {settings.selected_object}", icon='IMPORT')
        
        # layout.separator()
        

        

        main_col = layout.column(align=True)
        
        row = main_col.row()

        row.operator("object.selected_tree_type", text="Deciduous", depress=settings.active_tree_type=="deciduous").tree_type = 'deciduous'
        row.operator("object.selected_tree_type", text="Coniferous", depress=settings.active_tree_type=="coniferous").tree_type = 'coniferous'

        layout.separator()

        # layout.label(text="Trees:")

        # col = layout.column()
        # col.ui_units_y = 3
        
        # Create grid layout
        grid = layout.grid_flow(columns=4, even_columns=True, even_rows=True)
        
        for obj_name in object_list:
            # Create a column for each object
            if (settings.active_tree_type == "deciduous" and "Deciduous" in obj_name) or (settings.active_tree_type == "coniferous" and "Coniferous" in obj_name):
                col = grid.column(align=True)
                
                # Add button with preview image
                # op = col.operator(
                #     "object.library_select", 
                #     text="", 
                #     icon_value=pcoll[obj_name].icon_id,
                #     depress=(settings.selected_object == obj_name)
                # )
                # op.object_name = obj_name
                
                col.template_icon(icon_value=pcoll[obj_name].icon_id,scale=10)
                library_spawn_operator = col.operator("object.library_spawn", text=f"Spawn " + obj_name.replace(" (Deciduous)","").replace(" (Coniferous)",""), icon='IMPORT') 
                library_spawn_operator.object_to_append = obj_name
                # Add label below the image
                # col.label(text=obj_name, icon='NONE')

addon_keymaps = []

def register():
    # Register classes
    bpy.utils.register_class(ObjectLibraryPreferences)
    bpy.utils.register_class(OBJECT_PG_library_settings)
    bpy.utils.register_class(OBJECT_OT_library_select)
    bpy.utils.register_class(OBJECT_OT_library_spawn)
    bpy.utils.register_class(OBJECT_OT_library_refresh)
    bpy.utils.register_class(OBJECT_PT_library_panel)
    bpy.utils.register_class(OBJECT_OT_library_show_popup)
    bpy.utils.register_class(OBJECT_PT_library_popup)
    bpy.utils.register_class(OBJECT_OT_SetTreeType)
    
    # Register properties
    bpy.types.Scene.object_library_settings = PointerProperty(type=OBJECT_PG_library_settings)

    # bpy.types.Scene.active_tree_type = PointerProperty(type=OBJECT_PG_library_settings)
    
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
    bpy.utils.unregister_class(OBJECT_PT_library_panel)
    bpy.utils.unregister_class(OBJECT_OT_library_refresh)
    bpy.utils.unregister_class(OBJECT_OT_library_spawn)
    bpy.utils.unregister_class(OBJECT_OT_library_select)
    bpy.utils.unregister_class(OBJECT_PG_library_settings)
    bpy.utils.unregister_class(OBJECT_OT_SetTreeType)
    bpy.utils.unregister_class(ObjectLibraryPreferences)
    
    # Delete properties
    del bpy.types.Scene.object_library_settings
    # del bpy.types.Scene.active_tree_type
    
    # Clear preview collections
    global preview_collections
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

if __name__ == "__main__":
    register()
