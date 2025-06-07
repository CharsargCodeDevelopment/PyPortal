


class SpiffCollisionFileHandler:
    def __init__(self,file,rawdata = None,mode = "r"):
        self.file = file
        self.rawdata = rawdata
        self.mode = mode
        print(self.mode)
        
        if rawdata == None:
            if mode == "r":
                self.rawdata = file.read()
            else:
                self.rawdata = ""
        self.objects = []
        
        if self.mode  == "r":
            self.getData()
    def getData(self):
        for line in self.rawdata.split('\n'):
            if '#' in line:
                continue
            if "".join(line.split()) == '':
                continue
            line = "".join(line.split())
            data = line.split('|')
            print(data)
            ObjectType = int(data[0])
            objectData = {}
            if ObjectType == 0:
                objectData["type"] = "CollisionPoint"
                objectData["objectID"] = data[1]
                objectX,objectY,objectZ = data[2],data[3],data[4]
                objectData["position"] = {"x":objectX,"y":objectY,"z":objectZ}
                objectData["radius"] = data[5]
            self.objects.append(objectData)
    def saveData(self,objects):
        lines = []
        for objectData in objects:
            if objectData["type"] == "CollisionPoint":
                data = []
                data.append(0)
                data.append(0)
                data.extend([objectData["position"][i] for i in ["x","y","z"]])
                data.append(objectData["radius"])
                data = [str(x) for x in data]
                lines.append("|".join(data))
                
        print(lines)
        self.file.write("\n".join(lines))

    def getCollisionObjects(self):
        collisions = []
        for Object in self.objects:
            if Object["type"] == "CollisionPoint":
                collisions.append(Object)
        return collisions
                
    def getModelObjects(self):
        models = []
        for Object in self.objects:
            if Object["type"] == "object":
                models.append(Object)
        return models
    def getLightObjects(self):
        lights = []
        for Object in self.objects:
            if Object["type"] == "light":
                lights.append(Object)
        return lights

class SpiffCollision:
    def __init__(self):
        pass
    class open:
        def __init__(self,file,mode='r'):
            self.filename = file
            self.mode = mode
            self.filehandler = None
        def __enter__(self):
            self.file = open(self.filename,self.mode)
            print("Entering the context")
            self.filehander = SpiffCollisionFileHandler(self.file,mode = self.mode)
            # You can return anything you want to assign to 'test'
            return self.filehander

        def __exit__(self, exc_type, exc_value, traceback):
            self.file.close()
            print("Exiting the context")
            # You can handle exceptions here if needed
            # Return True to suppress exceptions, False to propagate
            return False
