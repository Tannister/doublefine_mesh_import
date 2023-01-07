import bpy
import bmesh, mathutils
import math

### Generate the Armature from the collected rig data
def GenerateArmature(collection, rig_data):
    print(f"Generating armature ...")
    
    #Create the armature data and object
    armature = bpy.data.armatures.new("armature")
    obj = bpy.data.objects.new("Armature", armature)
    
    #Add it to the collection
    collection.objects.link(obj)
    
    #Set to EDIT mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    #Grab the edit bones
    eb = armature.edit_bones
    
    for bone_data in rig_data:
        #Add a new named bone
        bone = eb.new(bone_data.name)
        bone.length = 0.1
        
        #Set the bone matrix
        bone_imatrix = mathutils.Matrix((bone_data.mat4[0:4], bone_data.mat4[4:8], bone_data.mat4[8:12], bone_data.mat4[12:16])).inverted()    
        bone.matrix = bone_imatrix[0:16]
        
        #Set the bone Parent
        if(bone_data.pid < 65535):
            bone.parent = armature.edit_bones[rig_data[bone_data.pid].name]
    
    #Go Back to Object Mode after all the bones are created
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return obj

### Generate Meshes from collected data
def GenerateMeshes(collection, meshes_data, rig_data):
    armature_obj = None
    if(rig_data is not None):
        #Generate the armature object if the rig data was collected
        armature_obj = GenerateArmature(collection, rig_data)

    print(f"Generating meshes ...")
    
    #Grab the scene
    scene = bpy.context.scene
    
    #Generate Mesh Objects from Submeshes data
    objects = []
    for i, mesh_data in enumerate(meshes_data):
    
        #Create the MESH data & Object
        mesh = bpy.data.meshes.new("mesh") 
        obj = bpy.data.objects.new(f"Mesh.{i}", mesh)
        
        #Keep track of that object
        objects.append(obj)
        
        if(armature_obj is not None):
            #Parent the object to the armature (if created)
            obj.parent = armature_obj
            
            #Add the armature modifier
            modifier = obj.modifiers.new(type='ARMATURE', name="Armature")
            modifier.object = armature_obj
            
            #Create the vertex groups
            for bone_data in rig_data:
                obj.vertex_groups.new(name=bone_data.name)
        
        #Add the object to the collection
        collection.objects.link(obj)
        
        # Create the BMesh and the apropriate layers
        bm = bmesh.new() 
        uv_layer = bm.loops.layers.uv.verify()
        dvert_layer = bm.verts.layers.deform.verify()
        
        for vertex_data in mesh_data.VerticeList:
            #Create the Vertex
            vert = bm.verts.new(vertex_data.Position)
            dvert = vert[dvert_layer]
            
            if(rig_data is not None):
                #Each vertex can have up to 4 weights associated
                for i in range(4):
                    #Grab both the bonemap index and the weight value
                    skin_indice = vertex_data.skinIndiceList[i]
                    skin_weight = vertex_data.skinWeightList[i]
                    
                    #Get the bone index from the mesh's bonemap
                    if(isinstance(mesh_data.BoneMap, int)):
                        skin_index = mesh_data.BoneMap
                    else:
                        skin_index = mesh_data.BoneMap[skin_indice]
                    
                    #Get the vertex group index from the bone index
                    group_name = rig_data[skin_index].name
                    group_index = obj.vertex_groups[group_name].index
                    
                    #Set the weight for that vertex on that vertex group
                    dvert[group_index] = skin_weight / 255.0
                
        #Make sure the vertices are indexable
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        
        face_list = []
        #Create the mesh's facelist
        if(mesh_data.TList):
            #The indice list is a Triangle List
            for i in range(0, len(mesh_data.IndiceList)-2, 3):
                a = mesh_data.IndiceList[i+0]
                b = mesh_data.IndiceList[i+1]
                c = mesh_data.IndiceList[i+2]
                face_list.append((bm.verts[a], bm.verts[b], bm.verts[c]))
        else:    
            #The indice list is a Triangle Strip
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
        
        #Create the faces on the mesh
        for face_indices in face_list:
            try:
                face = bm.faces.new(face_indices)
            except ValueError as e:
                pass

        #Add the UVs to the mesh
        for face in bm.faces:
            for loop in face.loops:
                uvs = list(mesh_data.VerticeList[loop.vert.index].UV)
                uvs[1] = -uvs[1]+1 #Vertical correction (Inverted)
                loop[uv_layer].uv = uvs  
        
        #Apply the BMesh to the mesh data
        bm.to_mesh(mesh)
        bm.free()
        
    return objects