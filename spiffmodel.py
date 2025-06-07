


class SpiffModelFileHandler:
    def __init__(self,file,rawdata = None,mode = "r"):
        self.file = file
        self.rawdata = rawdata
        self.mode = mode
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
                objectData["type"] = "object"
                objectData["objectID"] = data[1]
                objectX,objectY,objectZ = data[2],data[3],data[4]
                objectData["position"] = {"x":objectX,"y":objectY,"z":objectZ}
                objectData["radius"] = data[5]
            if ObjectType == 1:
                objectData["type"] = "light"
                objectX,objectY,objectZ = data[1],data[2],data[3]
                objectData["position"] = {"x":objectX,"y":objectZ,"z":objectZ}
                objectData["radius"] = data[4]
                objectData["color"] = {x:y for x,y in zip(list("rgb"),[data[x] for x in range(5,8)])}
            if ObjectType == 2:
                objectData["type"] = "portal"
                objectX,objectY,objectZ = data[1],data[2],data[3]
                objectData["position"] = {"x":objectX,"y":objectZ,"z":objectZ}
                objectData["radius"] = data[4]
                objectData["otherPortal"] = data[5]
            self.objects.append(objectData)
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

class SpiffModel:
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
            self.filehander = SpiffModelFileHandler(self.file)
            # You can return anything you want to assign to 'test'
            return self.filehander

        def __exit__(self, exc_type, exc_value, traceback):
            self.file.close()
            print("Exiting the context")
            # You can handle exceptions here if needed
            # Return True to suppress exceptions, False to propagate
            return False

if __name__ == '__main__':
    with SpiffModel.open("TestModel.spiffModel") as file:
        print(file.objects)
