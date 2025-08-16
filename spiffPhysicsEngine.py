

from spiffCollision import SpiffCollision


with SpiffCollision.open("TestModel.spiffCollision") as file:

    CollisionMeshes = []
    CollisionSet = set()
    for Object in file.getCollisionObjects():
        x,y,z = [Object["position"][x] for x in ["x","y","z"]]
        r = Object["radius"]
        CollisionMeshes.append([x,y,z,r])
        CollisionSet.add((int(x),int(y),int(z)))
        #print(x,y,z)
#CollisionSet = set(CollisionMeshes)

def PointIsColliding(point,resFunc = lambda p : [int(x) for x in p ]):
    print(tuple(resFunc(point)) )
    if tuple(resFunc(point)) in CollisionSet:
        return True
    return False
        

#print(PointIsColliding((1,1,7)))
#print(CollisionSet)
