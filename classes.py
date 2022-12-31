class Bone:
    def __init__(self):
        self.name = ''
        self.id = -1
        self.pid  = -1
        self.mat4 = None
    
    def __repr__(self):
        return f"<BONE {self.name}, {self.id}, {self.pid}>"

class Mesh:
    def __init__(self):
        self.MatID = -1
        self.VerticeCount = 0
        self.IndiceCount  = 0
        self.BoneMap = None
        self.VerticeList = []
        self.IndiceList  = None
        self.TList = False
    
    def __repr__(self):
        return f"<Mesh {self.MatID}, {self.VerticeCount}, {self.IndiceCount}>"

class Vertex:
    def __init__(self):
        self.skinIndiceList = None
        self.skinWeightList = None
        self.Position = None
        self.UV = None