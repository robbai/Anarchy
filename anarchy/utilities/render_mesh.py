from dataclasses import dataclass

@dataclass
class ColorGroup:
    name: str
    polygons: list
    color: tuple


def parse_obj_mesh_file(file_path, mesh_scale=1):
    file = open(file_path)
    points = list()
    groups = list()
    lines = file.readlines()

    for line in lines:
        if line.startswith("v "):
            s = line.split(" ")
            t = [float(s[3]) * mesh_scale, float(s[1]) * mesh_scale, float(s[2]) * mesh_scale]
            points.append(t)

    for line in lines:

        if line.startswith("o "):
            data = line.split(" ")[1].split("_")
            groups.append(ColorGroup(
                name=data[0],
                polygons=list(),
                color=tuple(int(data[1][i:i+2], 16) for i in (0, 2, 4))
            ))
            
        if line.startswith("f "):
            s = line.split(" ")
            polygon = []
            for point in s[1:]:
                i = int(point.split("/")[0]) - 1
                polygon.append(points[i]) 
            groups[-1].polygons.append(polygon)

    return groups

def render_mesh(self):
    if self.current_color_group < len(self.color_groups):
        self.renderer.begin_rendering(str(self.polygons_rendered)+str(self.current_color_group))
        group: ColorGroup = self.color_groups[self.current_color_group]
        color = self.renderer.create_color(255, int(group.color[0]), int(group.color[1]), int(group.color[2]))
        for i in range(50):
                if self.polygons_rendered < len(group.polygons):
                    self.renderer.draw_polyline_3d(group.polygons[self.polygons_rendered], color)
                    self.polygons_rendered += 1
                else:
                    self.polygons_rendered = 0
                    self.current_color_group += 1
                    break
        self.renderer.end_rendering()