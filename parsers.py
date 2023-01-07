from pathlib import Path
from .BinaryLib import *
from .classes import *

#Custom CType for BinaryFile
#Used for vertex data
class HalfFloat(UInt16):
    @staticmethod
    def HalfToFloat(h):
        s = int((h >> 15) & 0x00000001) # sign
        e = int((h >> 10) & 0x0000001f) # exponent
        f = int(h & 0x000003ff)   # fraction

        if e == 0:
            if f == 0:
                return int(s << 31)
            else:
                while not (f & 0x00000400):
                    f <<= 1
                    e -= 1
                e += 1
                f &= ~0x00000400
        elif e == 31:
            if f == 0:
                return int((s << 31) | 0x7f800000)
            else:
                return int((s << 31) | 0x7f800000 | (f << 13))

        e = e + (127 -15)
        f = f << 13
        return int((s << 31) | (e << 23) | f)
    
    @staticmethod
    def convert(data):
        ndata = []
        
        for value in data:
            a = HalfFloat.HalfToFloat(value)
            s = struct.pack('I', a)
            ndata.append(struct.unpack('f', s)[0])
        
        return tuple(ndata)

### Parser for the *.Material files
def ParseMaterial(filepath):
    print(f"Parsing \"{filepath}\" ...")  
    data = {}
    return data

### Parser for the *.Mesh.header files
def ParseMeshesHeader(filepath):
    print(f"Parsing \"{filepath}\" ...")
    data = {}
    bfile = BinaryFile(filepath, Endian.Little)
    
    if(bfile.read(Char, 4) != "hsem"):
        raise Exception("Invalid File !")
    
    bfile.seek(20, 1) # UNK DATA
    data['BBox'] = bfile.read(Float32, 6)
    bfile.seek(32, 1) # UNK DATA
    
    if(bfile.read(Char, 4) != "lrtm"):
        raise Exception("Invalid File !")
    
    mat_count = bfile.read(UInt32, 1)
    data['Materials'] = []
    for m in range(mat_count):
        str_length = bfile.read(UInt32, 1)
        data['Materials'].append(bfile.read(Char, str_length)[:-1])
    
    mesh_count = bfile.read(UInt32, 1)
    data["Meshes"] = []
    for m in range(mesh_count):
        mesh = Mesh()
        
        while(bfile.read(Char, 4) != "tsbs"):
            bfile.seek(-3, 1)
        mesh.MatID = bfile.read(UInt32, 1)
        bfile.seek(4, 1)
        
        while(bfile.read(Char, 4) != "BVXD"):
            bfile.seek(-3, 1)
        mesh.VerticeCount = bfile.read(UInt32, 1)
        bfile.seek(6, 1)
        
        while(bfile.read(Char, 4) != "BIXD"):
            bfile.seek(-3, 1)
        bfile.seek(4, 1)
        mesh.IndiceCount = bfile.read(UInt32, 1)
        if(bfile.read(UInt32, 1) == 2): mesh.TList = True   
        bonemap_length = bfile.read(UInt8, 1)
        mesh.BoneMap = bfile.read(UInt8, bonemap_length)
        
        data["Meshes"].append(mesh)
            
    bfile.close()
    return data

### Parser for the *.Mesh files
def ParseMeshes(filepath, meshes_header_data):
    print(f"Parsing \"{filepath}\" ...") 
    bfile = BinaryFile(filepath, Endian.Little)  
    for mesh in meshes_header_data["Meshes"]:
        for m in range(mesh.VerticeCount):
            offset = bfile.tell()
            vert = Vertex()
            vert.skinIndiceList = bfile.read(UInt8, 4)
            vert.skinWeightList = bfile.read(UInt8, 4)
            bfile.seek(offset+8)
            vert.Position = bfile.read(HalfFloat, 3)
            bfile.seek(offset+16)
            vert.UV = bfile.read(HalfFloat, 2)
            bfile.seek(offset+48)     
            mesh.VerticeList.append(vert)
        mesh.IndiceList=bfile.read(UInt16, mesh.IndiceCount)
    
    bfile.close()
    return meshes_header_data["Meshes"]

### Parser for the .Rig.header Files
def ParseRigHeader(filepath):
    print(f"Parsing \"{filepath}\" ...")
    bfile = BinaryFile(filepath, Endian.Little)
    data = bfile.read(UInt32, 25)
    bfile.close()
    return {
        "Bone_Count"  : data[4],
        "PID_Offset"  : data[20],
        "MAT4_Offset" : data[24],
    }

### Parser for the .Rig Files
def ParseRig(filepath, header_data):
    print(f"Parsing \"{filepath}\" ...")
    Bones = []   
    bfile = BinaryFile(filepath, Endian.Little)
    
    for m in range(header_data["Bone_Count"]):
        nbone = Bone()
        end = bfile.find_next(UInt8, 0)
        nbone.name = bfile.read(Char, (end - bfile.tell()))
        nbone.id   = len(Bones)
        Bones.append(nbone)
    
    bfile.seek(header_data["PID_Offset"])
    for bone in Bones:
        bone.pid = bfile.read(UInt16, 1)
    
    bfile.seek(header_data["MAT4_Offset"])
    for bone in Bones:
        bone.mat4 = bfile.read(Float32, 16)
    
    bfile.close() 
    return Bones