import bpy
import bmesh, mathutils
import math

def GenerateArmature(collection, rig_data):
    print(f"Generating armature ...")
    
    armature = bpy.data.armatures.new("armature")
    obj = bpy.data.objects.new("Armature", armature)
    
    collection.objects.link(obj)
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    eb = armature.edit_bones
    
    for bone_data in rig_data:
        bone = eb.new(bone_data.name)
        bone.length = 0.1
        
        bone_imatrix = mathutils.Matrix((bone_data.mat4[0:4], bone_data.mat4[4:8], bone_data.mat4[8:12], bone_data.mat4[12:16])).inverted()    
        
        bone.matrix = bone_imatrix[0:16]
        
        if(bone_data.name[1] == "L"):
            bone.tail = bone.head - (bone.tail - bone.head)
        
        if(bone_data.pid < 65535):
            bone.parent = armature.edit_bones[rig_data[bone_data.pid].name]
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return obj

def GenerateMeshes(collection, meshes_data, rig_data):
    armature_obj = None
    if(rig_data is not None):
        armature_obj = GenerateArmature(collection, rig_data)

    print(f"Generating meshes ...")
    scene = bpy.context.scene
    objects = []
    for i, mesh_data in enumerate(meshes_data):
        mesh = bpy.data.meshes.new("mesh") 
        obj = bpy.data.objects.new(f"Mesh.{i}", mesh)
        
        objects.append(obj)
        
        if(armature_obj is not None):
            obj.parent = armature_obj
            modifier = obj.modifiers.new(type='ARMATURE', name="Armature")
            modifier.object = armature_obj
            
            for bone_data in rig_data:
                obj.vertex_groups.new(name=bone_data.name)
                
        collection.objects.link(obj)
        
        bm = bmesh.new()
        
        uv_layer = bm.loops.layers.uv.verify()
        dvert_layer = bm.verts.layers.deform.verify()
        
        print("Bone Map :", mesh_data.BoneMap)
        
        for vertex_data in mesh_data.VerticeList:
            vert = bm.verts.new(vertex_data.Position)
            dvert = vert[dvert_layer]
            for i in range(4):
                skin_indice = vertex_data.skinIndiceList[i]
                skin_weight = vertex_data.skinWeightList[i]
                
                if(isinstance(mesh_data.BoneMap, int)):
                    skin_index = mesh_data.BoneMap
                else:
                    skin_index = mesh_data.BoneMap[skin_indice]
                    
                group_name = rig_data[skin_index].name
                group_index = obj.vertex_groups[group_name].index
                dvert[group_index] = skin_weight / 255.0
                
                print(f"Indice : {skin_indice} ({skin_index} -> {group_name}) -> {skin_weight}")
                
        
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        
        face_list = []
        if(mesh_data.TList):
            for i in range(0, len(mesh_data.IndiceList)-2, 3):
                a = mesh_data.IndiceList[i+0]
                b = mesh_data.IndiceList[i+1]
                c = mesh_data.IndiceList[i+2]
                face_list.append((bm.verts[a], bm.verts[b], bm.verts[c]))
        else:    
            for i in range(len(mesh_data.IndiceList)-2):
                if(i % 2 == 0):
                    a = mesh_data.IndiceList[i+0]
                    b = mesh_data.IndiceList[i+1]
                    c = mesh_data.IndiceList[i+2]
                else:
                    a = mesh_data.IndiceList[i+1]
                    b = mesh_data.IndiceList[i+0]
                    c = mesh_data.IndiceList[i+2]
                face_list.append((bm.verts[a], bm.verts[b], bm.verts[c]))
                 
        for face_indices in face_list:
            try:
                face = bm.faces.new(face_indices)
            except ValueError as e:
                pass

        for face in bm.faces:
            for loop in face.loops:
                uvs = list(mesh_data.VerticeList[loop.vert.index].UV)
                uvs[1] = -uvs[1]+1
                loop[uv_layer].uv = uvs  
        
        # for vert in bm.verts:
            # dvert = vert[dvert_layer]
            # vertex_data = mesh_data.VerticeList[vert.index]
            # for i in range(4):
                # skin_indice = vertex_data.skinIndiceList[i]
                # skin_weight = vertex_data.skinWeightList[i]
                
                # if(isinstance(mesh_data.BoneMap, int)):
                    # skin_index = mesh_data.BoneMap
                # else:
                    # skin_index = mesh_data.BoneMap[skin_indice]
                    
                # group_name = rig_data[skin_indice].name
                # group_index = obj.vertex_groups[group_name].index
                # dvert[group_index] = skin_weight / 255.0
        
        bm.to_mesh(mesh)
        bm.free()
        
    return objects