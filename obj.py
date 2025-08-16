def load_obj(file_path):
    try:
        vertices = []
        faces = []
        faceNormals = []
        vertexNormals = []
        with open(file_path) as f:
            for line in f:
                
                if line[0] == "v" and not line[1] in ["t","n"]:
                    
                    vertex = list(map(float, line[2:].strip().split()))
                    vertices.append(vertex)
                elif line[0] == "v" and not line[1] in ["t"] and line[1] in ["n"]:
                    
                    normal = list(map(float, line[2:].strip().split()))
                    vertexNormals.append(normal)
                elif line[0] == "f":
                    #print(line[2:].strip())
                    lineParts = line[2:].strip().split()
                    #print(lineParts)
                    lineParts = list(map(lambda x: x.split("/")[0],lineParts))
                    #print(list(lineParts))
                    face = list(map(int, lineParts))
                    faces.append(face)


                    #print(list(map(lambda x: x.split("/"),lineParts)))
                    lineParts2 = line[2:].strip().split()
                    lineParts2 = list(map(lambda x: x.split("/")[2],lineParts2))
                    faceNormals.append(list(map(int, lineParts2)))

        shape_data = {"vertices": vertices, "faces": faces,"vertexNormals":vertexNormals,"faceNormalIndexes":faceNormals}

        normals = []
        for faceNormal in faceNormals:
            normal = [0,0,0]
            for NormalIndex in faceNormal:
                #print(NormalIndex)
                vertexNormal = vertexNormals[NormalIndex-1]
                normal[0]+=vertexNormal[0]
                normal[1]+=vertexNormal[1]
                normal[2]+=vertexNormal[2]
                
            normal = list(map(lambda x: x/len(faceNormal),normal))
            normals.append(normal)
        shape_data["faceNormals"] = normals

        return shape_data

    except FileNotFoundError:
        print(f"{file_path} not found.")
    except Exception as e:
        print(f"An error occurred while loading the shape. {e}")
        raise(e)


if __name__ == "__main__":
    print(load_obj("cube.obj"))
