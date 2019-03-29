
def parse_obj_mesh_file(file_path, mesh_scale=1):
    file = open(file_path)
    points = []
    tris = []
    lines = file.readlines()
    for line in lines:
        if line.startswith("v "):
            s = line.split(" ")
            t = [float(s[3]) * mesh_scale, float(s[1]) * mesh_scale, float(s[2]) * mesh_scale]
            points.append(t)
    for line in lines:
        if line.startswith("f "):
            s = line.split(" ")
            polygon = []
            for point in s[1:]:
                i = int(point.split("/")[0]) - 1
                polygon.append(points[i]) 
            tris.append(polygon)
    return tris