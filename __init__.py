import bpy
import addon_utils

import os

from pathlib import Path
from .parsers import *
from .generators import *
bl_info = {
    "name": "Import DoubleFine Model (.Mesh)",
    "description": "Import DoubleFine's proprietary 3D model format",
    "author": "Tannister",
    "version": ("ALPHA", 0, 0, 0),
    "blender": (3, 0, 0),
    "location": "File > Import > DoubleFine Model (.Mesh)",
    "doc_url": "",
    "tracker_url": "",
    "warning": "",
    "category": "Import-Export"
}

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator

#Main Importer Class
class Importer(Operator, ImportHelper):
    """Import DoubleFine Model format (.Mesh)"""
    bl_idname = "import_doublefine.model"
    bl_label = "Import DoubleFine Model (.Mesh)"
    filename_ext = ".Mesh"
    
    get_extern_assets: BoolProperty(
        name="Get External Assets",
        description="Enable to find external assets (textures, materials, armature).",
        default=True,
    )

    filter_glob: StringProperty(
        default="*.Mesh",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        print("\nImporting DoubleFine Model...")
        print(" |->", self.filepath)
    
        print("\nChecking...")
        
        plugin_path = None
        for mod in addon_utils.modules():
            if mod.bl_info['name'] == bl_info['name']:
                plugin_path = os.path.dirname(mod.__file__)
            else:
                pass
                
        buddha_materials_path = Path(plugin_path, "BUDDHA_MATERIALS.blend")
    
        create_materials = True
        if(buddha_materials_path.exists()):
            print(' |->', buddha_materials_path, "found ! Importing material templates")
            with bpy.data.libraries.load(str(buddha_materials_path), link=False) as (data_from, data_to):
                data_to.materials = data_from.materials
                for mat in data_to.materials:
                    if mat is not None:
                        print(' |   |->', mat)
        else:
            print(' |->', buddha_materials_path, "not found !")
            self.report({'ERROR'}, "Couldn't find the included material template library !\nMaterials will look blank !\nPlease re-install the plug-in to fix this !")
            create_materials = False

        basepath = None
        if(self.get_extern_assets):
            if("audio" in self.filepath):
                basepath = self.filepath.split("audio")[0]
            elif("buildings" in self.filepath):
                basepath = self.filepath.split("buildings")[0]
            elif("characters" in self.filepath):
                basepath = self.filepath.split("characters")[0]
            elif("data" in self.filepath):
                basepath = self.filepath.split("data")[0]
            elif("dlc" in self.filepath):
                basepath = self.filepath.split("dlc")[0]
            elif("dlc1" in self.filepath):
                basepath = self.filepath.split("dlc1")[0]
            elif("dlc2" in self.filepath):
                basepath = self.filepath.split("dlc2")[0]
            elif("encounters" in self.filepath):
                basepath = self.filepath.split("encounters")[0]
            elif("environments" in self.filepath):
                basepath = self.filepath.split("environments")[0]
            elif("gameplay" in self.filepath):
                basepath = self.filepath.split("gameplay")[0]
            elif("interactions" in self.filepath):
                basepath = self.filepath.split("interactions")[0]
            elif("lighting" in self.filepath):
                basepath = self.filepath.split("lighting")[0]
            elif("localized" in self.filepath):
                basepath = self.filepath.split("localized")[0]
            elif("missions" in self.filepath):
                basepath = self.filepath.split("missions")[0]
            elif("particles" in self.filepath):
                basepath = self.filepath.split("particles")[0]
            elif("patch1" in self.filepath):
                basepath = self.filepath.split("patch1")[0]
            elif("physics" in self.filepath):
                basepath = self.filepath.split("physics")[0]
            elif("props" in self.filepath):
                basepath = self.filepath.split("props")[0]
            elif("rederer" in self.filepath):
                basepath = self.filepath.split("rederer")[0]
            elif("stringtable" in self.filepath):
                basepath = self.filepath.split("stringtable")[0]
            elif("ui" in self.filepath):
                basepath = self.filepath.split("ui")[0]
            elif("vehicles" in self.filepath):
                basepath = self.filepath.split("vehicles")[0]
            elif("win" in self.filepath):
                basepath = self.filepath.split("win")[0]
            elif("worlds" in self.filepath):
                basepath = self.filepath.split("worlds")[0]
            print(" |-> Base Path :", basepath)
        
        if(basepath == None):
            self.report({'WARNING'},"Importing a MESH outside of BUDDHA's file structure ! Some materials & textures will be missing !")
        
        #get local paths
        rig_header_path = Path(f"{self.filepath.split('.Mesh')[0]}.Rig.header")
        rig_path = Path(f"{self.filepath.split('.Mesh')[0]}.Rig")
        mesh_header_path = Path(f"{self.filepath}.header")
        mesh_path = Path(self.filepath)
        
        has_rig = (rig_header_path.exists() and rig_path.exists())
        
        print("\nParsing files ...")
        
        #Parse Files
        rig_data = None
        if(has_rig):
            rig_header_data = ParseRigHeader(rig_header_path)
            rig_data        = ParseRig(rig_path, rig_header_data)
        else:
            print('No Rig Found.')
        
        meshes_header_data = ParseMeshesHeader(f"{self.filepath}.header")
        meshes_data = ParseMeshes(self.filepath, meshes_header_data)
        
        materials_data = []
        for mat_path in meshes_header_data["Materials"]:
            mat_data = {"Name": mat_path.split('/')[-1], "Data": None}   
            if(create_materials):
                mat_filepath = Path(f"{basepath}{mat_path}.material")
                if(mat_filepath.exists()):
                    mat_data["Data"] = ParseMaterial(mat_filepath)
                else:
                    print(" |->", mat_data["Name"], "Not Found")
                    self.report({'WARNING'},f"Couldn't find the material definition file for : {mat_data['Name']} !")
            materials_data.append(mat_data)
        
        print("\nCreating objects ...")
        
        #Generate Objects
        collection = bpy.data.collections.new(self.filepath.split("\\")[-1])
        bpy.context.scene.collection.children.link(collection)

        material_objects, reports = GenerateMaterials(materials_data, basepath)  
        for report in reports:
            self.report(report[0], report[1])
        
        mesh_objects = GenerateMeshes(collection, meshes_data, rig_data, material_objects)
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(Importer.bl_idname, text="DoubleFine Model (.Mesh)")

def register():
    bpy.utils.register_class(Importer)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(Importer)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)