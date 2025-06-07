from spiffmodel import SpiffModel
import numpy as np
import math
import tqdm



def inObject(current_pos,ObjectIDList,ObjectIDS,ObjectMeshes):
    for CurrentObjectID in ObjectIDList:
        CurrentObjectMetaballCount = 0
        TotalDistance = 0
        count = 0
        for j in range(len(ObjectMeshes)):
            if ObjectIDS[j] == CurrentObjectID:
                #print(j,CurrentObjectID)
                center = [ObjectMeshes[j][i] for i in range(3)]
                radius = ObjectMeshes[j][3]
                offset = center - np.array(current_pos,dtype=np.float32)
                #print(offset)
                #print(offset**2)
                distance = math.sqrt(sum(offset**2))
                count +=1
                if distance == 0:
                    return True
                if distance > 0:
                    
                    TotalDistance += radius/distance
                #if math.sqrt()
                #print(center)
        #print(count)
        if TotalDistance > count:
            return True
    return False

def GenerateIntersectionPoints(ObjectIDList,ObjectIDS,ObjectMeshes,size = (16,16,16),gap = (1,1,1)):
    pointCount = (int(size[0]/gap[0]),int(size[1]/gap[1]),int(size[2]/gap[2]))
    points = {}
    for x in tqdm.tqdm([x*gap[0] for x in range(-pointCount[0],pointCount[0]+1)]):
        #print(x)
        for y in [y*gap[1] for y in range(-pointCount[1],pointCount[1]+1)]:
            for z in [z*gap[2] for z in range(-pointCount[2],pointCount[2]+1)]:
            
                points[(x,y,z)] = inObject((x,y,z),ObjectIDList,ObjectIDS,ObjectMeshes)
    return points

"""
def GenerateIntersectionPointsWithGuidance(ObjectIDList,ObjectIDS,ObjectMeshes,size = (16,16,16),gap = (1,1,1),guidance = {}):
    pointCount = (int(size[0]/gap[0]),int(size[1]/gap[1]),int(size[2]/gap[2]))
    points = {}
    for x in tqdm.tqdm([x*gap[0] for x in range(-pointCount[0],pointCount[0]+1)]):
        #print(x)
        for y in [y*gap[1] for y in range(-pointCount[1],pointCount[1]+1)]:
            for z in [z*gap[2] for z in range(-pointCount[2],pointCount[2]+1)]:
                if (x,y,z) in guidance and False == True:
                    pass
                    #points[(x,y,z)] = guidance[(x,y,z)]
                else:
                    toofar = True
                    for point in guidance:
                        if guidance[point]:
                            offset = np.array(point)-np.array((x,y,z))
                            distance = math.sqrt(sum(offset**2))
                            #print(distance)
                            if distance < 15:
                                
                                toofar = False
                                break
                        
                    if not toofar:
                        
                        pointInObject = inObject((x,y,z),ObjectIDList,ObjectIDS,ObjectMeshes)
                        #print(x,y,z)
                            
                        #print(pointInObject)
                        points[(x,y,z)] = pointInObject
    return points
"""
        


def GenerateCollisionPoints(points,hitbox = [2,5,2]):

    collision = set()
    #hitboxHalfSize = [x/2 for x in hitbox]
    for point in points:
        #x,y,z = point
        if points[point]:
            for box_x in range(hitbox[0]):
                for box_y in range(hitbox[1]):
                    for box_z in range(hitbox[2]):
                        hitbox_pos = [i-(j/2) for i,j in zip((box_x,box_y,box_z),hitbox)]
                        collision_point = [i+j for i,j in zip(hitbox_pos,point)]
                        collision.add(tuple(collision_point))
                        #print(collision_point)
    return collision
                    
        
    


def _Project3dPointInto2D(x,y,z,d):
    if z > 0:
        return d*(x/z),d*(y/z)


if __name__ == '__main__':
    ObjectMeshes = np.array([[0.0, 0.0, -3.0, 1.0],[2, 0.0, -3.0, 1.0]], dtype=np.float32)
    ObjectIDList = np.array([0], dtype=np.float32)
    ObjectIDS = np.array([0,0],dtype=np.float32)
    with SpiffModel.open("TestModel.spiffmodel") as file:

        ObjectMeshes = []
        ObjectIDS = []
        for Object in file.getModelObjects():
            x,y,z = [Object["position"][x] for x in ["x","y","z"]]
            r = Object["radius"]
            objectId = Object["objectID"]
            ObjectMeshes.append([x,y,z,r])
            ObjectIDS.append(objectId)
    ObjectIDList = np.array(list(set(ObjectIDS)),dtype=np.float32)
    ObjectIDS = np.array(ObjectIDS,dtype=np.float32)
    ObjectMeshes = np.array(ObjectMeshes,dtype=np.float32)

    inObject((0,0,0),ObjectIDList,ObjectIDS,ObjectMeshes)


    print("Generating Points")
    points = GenerateIntersectionPoints(ObjectIDList,ObjectIDS,ObjectMeshes,gap = (1,1,1))
    #print("Generating Points")
    #points = GenerateIntersectionPointsWithGuidance(ObjectIDList,ObjectIDS,ObjectMeshes,gap = (1,1,1),guidance = points)

    collision = GenerateCollisionPoints(points)



    
    import turtle
    import time
    turtle.penup()
    turtle.hideturtle()

    RenderCollision = {}

    for CPoint in collision:
        RenderCollision[CPoint] = True

    i = 0
    print("Rendering")
    frameStart = time.time()
    turtle.tracer(0)
    while True:
        DeltaTime =  time.time() - frameStart
        frameStart = time.time()
        print(DeltaTime)
        angle = math.radians(i)
        renderPoints = {}

        for position in RenderCollision:
            if RenderCollision[position]:
                
                x,y,z = position

                z-=0

                x,z = x*math.cos(angle) - z*math.sin(angle), z * math.cos(angle) + x *math.sin(angle)
                if z not in renderPoints:
                    renderPoints[z] = []
                renderPoints[z].append((x,y,z,1))
        for position in points:
            if points[position]:
                
                x,y,z = position

                z-=0

                x,z = x*math.cos(angle) - z*math.sin(angle), z * math.cos(angle) + x *math.sin(angle)
                if z not in renderPoints:
                    renderPoints[z] = []
                renderPoints[z].append((x,y,z,0))
    
        #i+=DeltaTime*20
        turtle.clear()
        for z1 in sorted(list(renderPoints),reverse = True):
            for position in renderPoints[z1]:
                x,y,z,t = position
                z += 16
                if z > 0:
                    px,py = _Project3dPointInto2D(x,y,z,500)
                    b=1-((z1-16)/16)
                    b = max(b,0)
                    b = min(b,1)
                    if t == 0:
                        turtle.pensize(10)
                        turtle.color(b,0,0)
                    elif t == 1:
                        turtle.pensize(5)
                        turtle.color(0,b,0)
                    turtle.goto(px,py)
                    turtle.dot()
                #print(position)
        turtle.update()




