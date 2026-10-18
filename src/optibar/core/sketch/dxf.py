"""draws the detailing map of a calculation as a DXF file.

Ported from the AutoCAD .NET plugin (AU.dll, "Create Autocad drawing"). The drawing is in model
space, in meters, laid out as a row of sheets:

    -1 strip names and widths      3 top additional, Y         7 bottom additional, Y
     0 top typical, X              4 bottom typical, X         8 shear zones
     1 top typical, Y              5 bottom typical, Y         9 shear type sections
     2 top additional, X           6 bottom additional, X     10 piece lists, summary and
                                                                  technical tables, moment diagrams

and below them, portrait sheets with the cutting plan of every diameter.

Differences from the plugin: English only; grid lines use the CENTER linetype and table lines the
Border layer, which the plugin intended but lost by calling SetDatabaseDefaults() after setting
them; cutting sheets have a title and their column headers on every sheet.
"""
from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

import ezdxf
from ezdxf.enums import TextEntityAlignment, MTextEntityAlignment

Point = Tuple[float, float]

STYLE = 'OPTiBAR'
DIMSTYLE = 'OPTiBAR'
# name: ACI color, as assigned by the plugin
LAYERS = {
    'Border': 1,
    'Sheet': 2,
    'Strip': 3,
    'Typical Rebar Top': 4,
    'Typical Rebar Bottom': 4,
    'Additional Rebar Top': 5,
    'Additional Rebar Bottom': 5,
    'continuous Rebar': 6,
    'Dimension': 7,
    'Dimension Text': 8,
    'Column': 9,
    'Rebar Text': 10,
    'moment': 11,
}
HATCH_PATTERNS = ("GOST_GLASS", "ANGLE", "ANSI31", "ANSI37", "ANSI32", "NET3", "LINE", "NET", "DOTS", "ZIGZAG")

# sheet index of each plan
STRIP_WIDTH, TOP_TYPICAL_X, TOP_TYPICAL_Y, TOP_ADDITIONAL_X, TOP_ADDITIONAL_Y = -1, 0, 1, 2, 3
BOTTOM_TYPICAL_X, BOTTOM_TYPICAL_Y, BOTTOM_ADDITIONAL_X, BOTTOM_ADDITIONAL_Y, SHEAR = 4, 5, 6, 7, 8
PLAN_TITLES = {
    STRIP_WIDTH: "Name & Width Of Strips",
    TOP_TYPICAL_X: "Top Typical Rebars Of X Direction",
    TOP_TYPICAL_Y: "Top Typical Rebars Of Y Direction",
    TOP_ADDITIONAL_X: "Top Additional Rebars Of X Direction",
    TOP_ADDITIONAL_Y: "Top Additional Rebars Of Y Direction",
    BOTTOM_TYPICAL_X: "Bottom Typical Rebars Of X Direction",
    BOTTOM_TYPICAL_Y: "Bottom Typical Rebars Of Y Direction",
    BOTTOM_ADDITIONAL_X: "Bottom Additional Rebars Of X Direction",
    BOTTOM_ADDITIONAL_Y: "Bottom Additional Rebars Of Y Direction",
    SHEAR: "Shear Rebars",
}


def num(value: float, digits: int = 3) -> str:
    """a number without trailing zeros, like C#'s float.ToString()"""
    text = f"{round(value, digits):.{digits}f}".rstrip('0').rstrip('.')
    return '0' if text in ('', '-0') else text


class Layout():
    """sheet size and base points; a sheet is A4 landscape scaled so the foundation fills 70% of it"""
    def __init__(self, areas: Dict) -> None:
        points = [p for exterior in areas['union']['exteriors'] for p in exterior]
        self.min_x = min(p[0] for p in points)
        self.max_x = max(p[0] for p in points)
        self.min_y = min(p[1] for p in points)
        self.max_y = max(p[1] for p in points)
        self.width_of_foundation = self.max_x - self.min_x
        self.height_of_foundation = self.max_y - self.min_y
        scale = max((self.width_of_foundation / 0.7) / 29.7, (self.height_of_foundation / 0.7) / 21)
        self.WIDTH = scale * 29.7
        self.HEIGHT = scale * 21

    def plan_base(self, sheet: int) -> Point:
        """offset that places the foundation in the middle of a sheet"""
        return (
            (self.WIDTH - self.width_of_foundation) / 2 - self.min_x + sheet * self.WIDTH,
            (self.HEIGHT - self.height_of_foundation) / 2 - self.min_y,
        )

    def section_base(self) -> Point:
        return ((self.WIDTH - self.width_of_foundation) / 4 + 9 * self.WIDTH, 29 * self.HEIGHT / 32)

    def list_base(self) -> Point:
        return ((self.WIDTH - self.width_of_foundation) / 2 + 10 * self.WIDTH, (self.HEIGHT + self.height_of_foundation) / 2)

    def moment_base(self) -> Point:
        x, y = self.list_base()
        return (x + 105, y)


def flip_up(vector: List[float]) -> List[float]:
    """normals point up, or right when horizontal"""
    if vector[1] < 0 or (vector[1] == 0 and vector[0] < 0):
        return [-vector[0], -vector[1]]
    return vector


class StripLine():
    """the mid line of a strip as segments with lengths, directions and normals"""
    def __init__(self, mid_line: List[Dict]) -> None:
        self.points = [p['point'] for p in mid_line]
        self.widths = [p['width'] for p in mid_line]
        self.lengths, self.directions, self.normals = [], [], []
        for (x0, y0), (x1, y1) in zip(self.points, self.points[1:]):
            length = math.hypot(x1 - x0, y1 - y0)
            direction = [(x1 - x0) / length, (y1 - y0) / length]
            self.lengths.append(length)
            self.directions.append(direction)
            self.normals.append(flip_up([-direction[1], direction[0]]))
        self.length = sum(self.lengths)
        delta_x = self.points[-1][0] - self.points[0][0]
        delta_y = self.points[-1][1] - self.points[0][1]
        self.direction = [delta_x / self.length, delta_y / self.length]
        self.normal = flip_up([-self.direction[1], self.direction[0]])
        self.is_start_left = self.direction[0] > 0 or (self.direction[0] == 0 and self.direction[1] < 0)
        self.axis = 'y' if abs(delta_x) < abs(delta_y) else 'x'

    def at(self, segment: int, distance: float, offset: Sequence[float] = (0, 0), base: Point = (0, 0)) -> Point:
        """point at a distance along a segment, shifted by an offset and a base point"""
        x0, y0 = self.points[segment]
        d = self.directions[segment]
        return (x0 + d[0] * distance + offset[0] + base[0], y0 + d[1] * distance + offset[1] + base[1])


class DxfDrawing():
    """draws the output of a calculation as a dxf detailing map.

    Args:
        output (Dict): the "data" part of the engine output
    """
    def __init__(self, output: Dict) -> None:
        self.output = output
        self.layout = Layout(output['areas'])

    def save(self, file_path: Union[str, Path]) -> None:
        doc = ezdxf.new('R2010', setup=True, units=ezdxf.units.M)
        self._setup(doc)
        self.msp = doc.modelspace()
        self._draw_sheets()
        self._draw_titles()
        self._draw_area_borders()
        self._draw_columns()
        self._draw_grids()
        self._draw_grid_dimensions()
        self._draw_pieces()
        self._draw_strip_widths()
        self._draw_shear_zones()
        self._draw_sections()
        self._draw_piece_lists()
        self._draw_summary()
        self._draw_technical_tables()
        self._draw_moments()
        self._draw_cutting_plans()
        doc.set_modelspace_vport(height=self.layout.HEIGHT * 1.2, center=(self.layout.WIDTH * 4.5, self.layout.HEIGHT / 2))
        doc.saveas(str(file_path))

    # --- setup and primitives ---------------------------------------------------------------

    def _setup(self, doc) -> None:
        doc.styles.add(STYLE, font='arial.ttf')
        for name, color in LAYERS.items():
            doc.layers.add(name, color=color)
        dimstyle = doc.dimstyles.new(DIMSTYLE)
        dimstyle.dxf.dimtxsty = STYLE
        dimstyle.dxf.dimsah = 1
        dimstyle.dxf.dimblk1 = 'OBLIQUE'
        dimstyle.dxf.dimblk2 = 'OBLIQUE'
        dimstyle.dxf.dimexe = 0
        dimstyle.dxf.dimexo = 0
        dimstyle.dxf.dimdec = 2
        dimstyle.dxf.dimdsep = ord('.')
        dimstyle.dxf.dimtad = 1
        dimstyle.dxf.dimzin = 0

    def text(self, content: str, position: Point, height: float, layer: str = '0', rotation: float = 0,
            align: TextEntityAlignment = TextEntityAlignment.MIDDLE, color: int = None) -> None:
        attribs = {'style': STYLE, 'height': height, 'layer': layer, 'rotation': rotation}
        if color is not None:
            attribs['color'] = color
        self.msp.add_text(content, dxfattribs=attribs).set_placement(position, align=align)

    def mtext(self, content: str, position: Point, height: float, width: float = None, layer: str = '0', color: int = None) -> None:
        attribs = {'style': STYLE, 'char_height': height, 'layer': layer}
        if width is not None:
            attribs['width'] = width
        if color is not None:
            attribs['color'] = color
        self.msp.add_mtext(content, dxfattribs=attribs).set_location(position, attachment_point=MTextEntityAlignment.MIDDLE_CENTER)

    def polyline(self, points: Sequence, layer: str = '0', color: int = None, closed: bool = False, width: float = 0) -> None:
        """points are (x, y) or (x, y, start_width, end_width, bulge)"""
        attribs = {'layer': layer}
        if color is not None:
            attribs['color'] = color
        if width:
            attribs['const_width'] = width
        if points and len(points[0]) == 5:
            self.msp.add_lwpolyline(points, format='xyseb', close=closed, dxfattribs=attribs)
        else:
            self.msp.add_lwpolyline([p[:2] for p in points], close=closed, dxfattribs=attribs)

    def line(self, start: Point, end: Point, layer: str = 'Border', color: int = None, linetype: str = None, ltscale: float = None) -> None:
        attribs = {'layer': layer}
        if color is not None:
            attribs['color'] = color
        if linetype is not None:
            attribs['linetype'] = linetype
        if ltscale is not None:
            attribs['ltscale'] = ltscale
        self.msp.add_line(start, end, dxfattribs=attribs)

    def aligned_dim(self, p1: Point, p2: Point, arrow: float, text_height: float, gap: float, text: str = '<>', layer: str = 'Dimension') -> None:
        override = {'dimasz': arrow, 'dimtxt': text_height, 'dimgap': gap}
        dim = self.msp.add_aligned_dim(p1=p1, p2=p2, distance=0, text=text, dimstyle=DIMSTYLE, override=override, dxfattribs={'layer': layer})
        dim.render()

    def hatch_polygon(self, points: Sequence[Point], pattern: str, color: int) -> None:
        hatch = self.msp.add_hatch(color=color)
        hatch.set_pattern_fill(pattern, scale=0.1)
        hatch.paths.add_polyline_path(points, is_closed=True)

    def solid_circles(self, centers: Sequence[Point], radius: float, color: int) -> None:
        for center in centers:
            self.msp.add_circle(center, radius, dxfattribs={'color': color})
        hatch = self.msp.add_hatch(color=color)
        hatch.set_solid_fill(color=color)
        for center in centers:
            hatch.paths.add_edge_path().add_arc(center, radius, 0, 360)

    # --- sheets and plans ---------------------------------------------------------------------

    def _draw_sheets(self) -> None:
        L = self.layout
        spacing = L.HEIGHT / 21 * 0.10
        margin = L.HEIGHT / 21 * 0.5
        for i in range(-1, 9):
            x0 = i * L.WIDTH
            def rectangle(inset):
                return [(x0 + inset, inset), (x0 + L.WIDTH - inset, inset), (x0 + L.WIDTH - inset, L.HEIGHT - inset), (x0 + inset, L.HEIGHT - inset)]
            self.polyline(rectangle(0), layer='Sheet', closed=True)
            self.polyline(rectangle(spacing), layer='Border', closed=True)
            self.polyline(rectangle(margin + spacing), layer='Border', closed=True)

    def _draw_titles(self) -> None:
        L = self.layout
        for sheet, title in PLAN_TITLES.items():
            bx, by = L.plan_base(sheet)
            x = bx + L.width_of_foundation / 2 + L.min_x
            y = by + L.min_y
            self.mtext(title, (x, y - 0.05 * L.HEIGHT), 0.01 * L.HEIGHT, width=L.HEIGHT / 2)
            w = 0.002 * L.HEIGHT
            self.polyline([(x - 0.15 * L.HEIGHT, y - 0.06 * L.HEIGHT, w, w, 0), (x + 0.15 * L.HEIGHT, y - 0.06 * L.HEIGHT, w, w, 0)])

    def _plan_bases(self) -> List[Point]:
        return [self.layout.plan_base(sheet) for sheet in PLAN_TITLES]

    def _draw_area_borders(self) -> None:
        union = self.output['areas']['union']
        for bx, by in self._plan_bases():
            for ring in union['exteriors'] + union['interiors']:
                self.polyline([(x + bx, y + by) for x, y in ring], layer='Strip')

    def _draw_columns(self) -> None:
        for bx, by in self._plan_bases():
            for column in self.output['columns']:
                (x, y), (dx, dy) = column['point'], column['dim']
                corners = [(x - dx / 2, y - dy / 2), (x + dx / 2, y - dy / 2), (x - dx / 2, y + dy / 2), (x + dx / 2, y + dy / 2)]
                self.msp.add_solid([(cx + bx, cy + by) for cx, cy in corners], dxfattribs={'layer': 'Column'})

    def _grid_shift(self, grids: List[Dict], i: int, radius: float) -> float:
        """bubbles of grids closer than a bubble are moved aside, along the axis"""
        if i == 0:
            return 0
        gap = grids[i]['ordinate'] - grids[i - 1]['ordinate']
        if gap >= 2 * radius:
            return 0
        if i < len(grids) - 1 and grids[i + 1]['ordinate'] - grids[i - 1]['ordinate'] > 4.5 * radius:
            return 2.5 * radius - gap
        if i == len(grids) - 1:
            return 2.5 * radius - gap
        return 0

    def _draw_grids(self) -> None:
        L = self.layout
        radius = 0.01 * L.HEIGHT
        above = L.max_y + 0.1 * L.height_of_foundation
        left = L.min_x - 0.1 * L.width_of_foundation
        ltscale = 2 * radius
        grids = self.output['grid']
        for sheet in PLAN_TITLES:
            bx, by = L.plan_base(sheet)
            for axis, items in (('X', grids['X']), ('Y', grids['Y'])):
                if sheet == STRIP_WIDTH: # grid lines run across the plan only on the first sheet
                    length = 1.1 * (L.height_of_foundation if axis == 'X' else L.width_of_foundation)
                else:
                    length = 2 * radius
                for i, grid in enumerate(items):
                    o = grid['ordinate']
                    shift = self._grid_shift(items, i, radius)
                    if axis == 'X':
                        # (along the grid, across the grid) -> plan coordinates
                        at = lambda along, across: (o + across + bx, above - along + by)
                    else:
                        at = lambda along, across: (left + along + bx, o + across + by)
                    self.msp.add_circle(at(0, shift), radius)
                    self.text(grid['name'], at(0, shift), radius / 2)
                    if shift:
                        self.line(at(radius, shift), at(2 * radius, 0), layer='0', linetype='CENTER', ltscale=ltscale)
                        self.line(at(2 * radius, 0), at(radius + length, 0), layer='0', linetype='CENTER', ltscale=ltscale)
                    else:
                        self.line(at(radius, 0), at(radius + length, 0), layer='0', linetype='CENTER', ltscale=ltscale)

    def _draw_grid_dimensions(self) -> None:
        L = self.layout
        radius = 0.01 * L.HEIGHT
        size = 0.4 * radius
        grids = self.output['grid']
        y_line = L.max_y + 0.1 * L.height_of_foundation - 2 * radius
        x_line = L.min_x - 0.1 * L.width_of_foundation + 2 * radius
        for bx, by in self._plan_bases():
            for a, b in zip(grids['X'], grids['X'][1:]):
                self.aligned_dim((a['ordinate'] + bx, y_line + by), (b['ordinate'] + bx, y_line + by), size, size, size)
            for a, b in zip(grids['Y'], grids['Y'][1:]):
                self.aligned_dim((x_line + bx, a['ordinate'] + by), (x_line + bx, b['ordinate'] + by), size, size, size)

    def _draw_pieces(self) -> None:
        L = self.layout
        bases = {
            ('Typical Rebar Top', 'x'): L.plan_base(TOP_TYPICAL_X),
            ('Typical Rebar Top', 'y'): L.plan_base(TOP_TYPICAL_Y),
            ('Typical Rebar Bottom', 'x'): L.plan_base(BOTTOM_TYPICAL_X),
            ('Typical Rebar Bottom', 'y'): L.plan_base(BOTTOM_TYPICAL_Y),
            ('Additional Rebar Top', 'x'): L.plan_base(TOP_ADDITIONAL_X),
            ('Additional Rebar Top', 'y'): L.plan_base(TOP_ADDITIONAL_Y),
            ('Additional Rebar Bottom', 'x'): L.plan_base(BOTTOM_ADDITIONAL_X),
            ('Additional Rebar Bottom', 'y'): L.plan_base(BOTTOM_ADDITIONAL_Y),
        }
        for strip in self.output['strips']:
            line = StripLine(strip['geometry']['mid_line'])
            width = strip['geometry']['mid_line'][0]['width']
            mesh = strip['mesh']
            for level in ('top', 'bottom'):
                layer = f'Additional Rebar {level.capitalize()}'
                for row_number, row in enumerate(mesh['additional'][level]):
                    bunches = [dict(bunch, continuous=len(piece) > 1) for piece in row for bunch in piece]
                    self._draw_row(line, width, row_number, bunches, layer, bases[(layer, line.axis)])
                layer = f'Typical Rebar {level.capitalize()}'
                bunches = [dict(bunch, continuous=False) for bunch in mesh['typical'][level]]
                self._draw_row(line, width, 1, bunches, layer, bases[(layer, line.axis)])

    def _draw_row(self, line: StripLine, width: float, row_number: int, bunches: List[Dict], layer: str, base: Point) -> None:
        """draws a row of bars along the strip, labelled with number, diameter and length"""
        dist = 0.2 # spacing between rows
        bar_width = dist * 0.04
        shifted = False
        for k, bunch in enumerate(bunches):
            if bunch['number'] == 0:
                continue
            stations, bends = bunch['stations'], bunch['bends']
            if k > 0:
                # overlapping neighbours are drawn on alternating sides
                shifted = (not shifted) if bunches[k - 1]['stations'][1] > stations[0] else False
            piece_start = stations[0] + bends[0]
            piece_end = stations[1] - bends[1]

            # the segment the bar starts on
            cumulative = 0
            for segment, segment_length in enumerate(line.lengths):
                cumulative += segment_length
                if piece_start < cumulative:
                    break
            else:
                continue # starts beyond the strip

            normal = line.normals[segment]
            offset = (row_number + 1) * dist - 0.5 * width
            up = [normal[0] * offset, normal[1] * offset]
            if shifted:
                sign = 1 if line.is_start_left else -1
                up = [up[0] + sign * normal[0] * 0.15 * dist, up[1] + sign * normal[1] * 0.15 * dist]
            bend_down = [-normal[0] * dist * 0.5, -normal[1] * dist * 0.5]
            text_up = [up[0] + line.normal[0] * 0.2 * dist, up[1] + line.normal[1] * 0.2 * dist]

            points = []
            start_distance = piece_start - cumulative + segment_length
            if bends[0] > 0:
                points.append(line.at(segment, start_distance, [up[0] + bend_down[0], up[1] + bend_down[1]], base))
            points.append(line.at(segment, start_distance, up, base))

            text_position, text_angle = None, 0
            if line.is_start_left:
                d = line.directions[segment]
                if k > 0 and bunches[k - 1]['stations'][1] - bunches[k - 1]['stations'][0] < 3 and stations[1] < bunches[k - 1]['stations'][0]:
                    text_position = line.at(segment, start_distance + 2, text_up, base)
                    text_angle = math.degrees(math.atan2(line.direction[1], line.direction[0]))
                else:
                    text_position = line.at(segment, start_distance, text_up, base)
                    text_angle = math.degrees(math.atan2(d[1], d[0]))

            # follow the mid line until the bar ends
            while not (piece_end <= cumulative or piece_end > line.length):
                points.append((line.points[segment + 1][0] + up[0] + base[0], line.points[segment + 1][1] + up[1] + base[1]))
                segment += 1
                cumulative += line.lengths[segment]
            end_distance = piece_end - cumulative + line.lengths[segment]
            points.append(line.at(segment, end_distance, up, base))
            if bends[1] > 0:
                points.append(line.at(segment, end_distance, [up[0] + bend_down[0], up[1] + bend_down[1]], base))

            self.polyline([(x, y, bar_width, bar_width, 0) for x, y in points], layer='continuous Rebar' if bunch['continuous'] else layer)

            if not line.is_start_left:
                d = line.directions[segment]
                text_angle = math.degrees(math.atan2(-d[1], -d[0]))
                if k < len(bunches) - 1 and bunches[k + 1]['stations'][1] - bunches[k + 1]['stations'][0] < 4 and stations[1] > bunches[k + 1]['stations'][0]:
                    text_position = line.at(segment, end_distance - 2, text_up, base)
                else:
                    text_position = line.at(segment, end_distance, text_up, base)
            label = f"{bunch['number']}%%C{num(bunch['diameter'])}-L={num(stations[1] - stations[0], 2)}"
            self.text(label, text_position, dist * 0.7, layer='Rebar Text', rotation=text_angle, align=TextEntityAlignment.LEFT)

    def _draw_strip_widths(self) -> None:
        L = self.layout
        base = L.plan_base(STRIP_WIDTH)
        scale = L.HEIGHT / 21
        size = 0.4 * 0.01 * L.HEIGHT
        for strip in self.output['strips']:
            mid_line = strip['geometry']['mid_line']
            for p0, p1 in zip(mid_line, mid_line[1:]):
                (x0, y0), (x1, y1) = p0['point'], p1['point']
                middle = ((x0 + x1) / 2 + base[0], (y0 + y1) / 2 + base[1])
                length = math.hypot(x1 - x0, y1 - y0)
                direction = [(x1 - x0) / length, (y1 - y0) / length]
                normal = [-direction[1], direction[0]]
                if normal[0] < 0 or (normal[0] == 0 and normal[1] < 0): # normals point right here
                    normal = [-normal[0], -normal[1]]
                half = (p0['width'] + p1['width']) / 4
                self.aligned_dim(
                    (middle[0] - normal[0] * half, middle[1] - normal[1] * half),
                    (middle[0] + normal[0] * half, middle[1] + normal[1] * half),
                    size, size, size,
                )
                if not (direction[0] > 0 or (direction[0] == 0 and direction[1] < 0)):
                    direction = [-direction[0], -direction[1]]
                position = (middle[0] + direction[0] * 0.5 * scale, middle[1] + direction[1] * 0.5 * scale)
                self.text(strip['name'], position, scale * 0.1, layer='Dimension', color=7,
                    rotation=math.degrees(math.atan2(direction[1], direction[0])))

    def _draw_shear_zones(self) -> None:
        base = self.layout.plan_base(SHEAR)
        for strip in self.output['strips']:
            line = StripLine(strip['geometry']['mid_line'])
            for zone in strip['shear_zones']:
                start, end = zone['period']
                cumulative = 0
                for segment, segment_length in enumerate(line.lengths):
                    cumulative += segment_length
                    if start < cumulative:
                        break
                else:
                    continue
                def edge(segment, distance, normal, side):
                    w = line.widths[segment] + distance / line.lengths[segment] * (line.widths[segment + 1] - line.widths[segment])
                    return line.at(segment, distance, (side * normal[0] * w / 2, side * normal[1] * w / 2), base)
                start_distance = start - cumulative + segment_length
                right = [edge(segment, start_distance, line.normals[segment], 1)]
                left = [edge(segment, start_distance, line.normals[segment], -1)]
                while end > cumulative:
                    # corner of the mid line, offset with the normal of the next segment
                    corner_normal = line.normals[min(segment + 1, len(line.lengths) - 1)]
                    (x, y), w = line.points[segment + 1], line.widths[segment + 1]
                    right.append((x + corner_normal[0] * w / 2 + base[0], y + corner_normal[1] * w / 2 + base[1]))
                    left.append((x - corner_normal[0] * w / 2 + base[0], y - corner_normal[1] * w / 2 + base[1]))
                    segment += 1
                    if segment == len(line.lengths):
                        break
                    cumulative += line.lengths[segment]
                if segment < len(line.lengths):
                    end_distance = end - cumulative + line.lengths[segment]
                    right.append(edge(segment, end_distance, line.normals[segment], 1))
                    left.append(edge(segment, end_distance, line.normals[segment], -1))
                outline = right + left[::-1]
                color = int(zone['id'])
                self.polyline(outline, color=color, closed=True)
                self.hatch_polygon(outline, HATCH_PATTERNS[color % 10], color)

    # --- sections ------------------------------------------------------------------------------

    def _draw_sections(self) -> None:
        H = self.layout.HEIGHT
        bx, by = self.layout.section_base()
        depth = next((area['thickness'] for area in self.output['areas']['individuals'] if not area['is_opening']), 0)
        bar = 0.0015 * H
        for i, shear_type in enumerate(self.output['shear_types']):
            y0 = by - i * H / 4
            color = int(shear_type['id'])
            number = shear_type['number']
            # legend, with the hatch used for this type in the shear plan
            legend = [(bx, y0), (bx + 1.7 * H / 16, y0), (bx + 1.7 * H / 16, y0 - H / 16), (bx, y0 - H / 16)]
            self.polyline(legend, color=color, closed=True)
            self.hatch_polygon(legend, HATCH_PATTERNS[color % 10], color)
            self.polyline([
                (bx + 3 * H / 16, y0 - H / 32, H / 150, H / 150, 0),
                (bx + 3.5 * H / 16, y0 - H / 32, H / 75, 0, 0),
                (bx + 3.75 * H / 16, y0 - H / 32, 0, 0, 0),
            ], color=74)

            # section outline and dimensions
            w = 2 * H / 8
            inner = w - 2 * (H / 160 + H / 200)
            if number > 11:
                w = (inner / 12) * (number + 1) + 2 * (H / 160 + H / 200)
                inner = w - 2 * (H / 160 + H / 200)
            x0 = bx + 5.05 * H / 16
            top = y0 + H / 32
            bottom = top - H / 8
            self.polyline([(x0, top), (x0 + w, top), (x0 + w, bottom), (x0, bottom)], color=74, closed=True)
            self.aligned_dim((x0, top), (x0 + w, top), 0.002 * H, 0.008 * H, 0.008 * H, text='Width Of Strip')
            self.aligned_dim((x0, top), (x0, bottom), 0.002 * H, 0.008 * H, 0.008 * H, text=f'{num(depth)}m')

            # thermal bars along top and bottom
            self.polyline([
                (x0 + H / 160, top - H / 160 - H / 40, bar, bar, 0),
                (x0 + H / 160, top - H / 80, bar, bar, -0.45),
                (x0 + H / 80, top - H / 160, bar, bar, 0),
                (x0 + w - H / 80, top - H / 160, bar, bar, -0.45),
                (x0 + w - H / 160, top - H / 80, bar, bar, 0),
                (x0 + w - H / 160, top - H / 160 - H / 40, bar, bar, 0),
            ], color=252)
            self.polyline([
                (x0 + H / 160, bottom + H / 160 + H / 40, bar, bar, 0),
                (x0 + H / 160, bottom + H / 80, bar, bar, 0.45),
                (x0 + H / 80, bottom + H / 160, bar, bar, 0),
                (x0 + w - H / 80, bottom + H / 160, bar, bar, 0.45),
                (x0 + w - H / 160, bottom + H / 80, bar, bar, 0),
                (x0 + w - H / 160, bottom + H / 160 + H / 40, bar, bar, 0),
            ], color=252)

            # stirrup legs: positions on a 13-slot grid when they fit, evenly spaced otherwise
            if number <= 11:
                slots = SHEAR_SLOTS[number - 1]
                legs = [(x0 + (s - 1) * inner / 12, s <= 7) for s in slots]
                bar_count, spacing = 13, inner / 12
            else:
                legs = [(x0 + (j + 1) * inner / (number + 1), j <= number / 2) for j in range(number)]
                bar_count, spacing = number + 2, inner / (number + 1)
            for x, hook_right in legs:
                self.polyline(self._stirrup(x, top, bottom, hook_right, bar), color=2)
            centers_top = [(x0 + H / 160 + H / 200 + j * spacing, top - H / 160 - H / 400) for j in range(bar_count)]
            centers_bottom = [(x0 + H / 160 + H / 200 + j * spacing, bottom + H / 160 + H / 400) for j in range(bar_count)]
            for pair in zip(centers_top, centers_bottom):
                self.solid_circles(pair, H / 700, 4)

            # label with a leader
            label = f"{number}%%C{num(shear_type['diameter'])}@{num(shear_type['interval'] * 100)}cm"
            if number == 1:
                tip = (x0 + H / 70 + 6 * inner / 12 - H / 200, top - H / 16 + H / 100)
                end = (x0 + H / 70 + 6 * inner / 12 + H / 5, top - H / 160 - H / 600 + H / 20)
            elif number <= 11:
                tip = (x0 + H / 110 + 11 * inner / 12 + H / 200, top - H / 16 + H / 100)
                end = (x0 + H / 70 + 11 * inner / 12 + H / 5, top - H / 160 - H / 600 + H / 20)
            else:
                tip = (x0 + H / 110 + 12 * inner / (number + 1) + H / 200, top - H / 16 + H / 100)
                end = (tip[0] + H / 5, top - H / 160 - H / 600 + H / 20)
            self.msp.add_leader([tip, end], dimstyle=DIMSTYLE, override={'dimasz': H / 100})
            self.msp.add_mtext(label, dxfattribs={'style': STYLE, 'char_height': H / 100}).set_location(
                (x0 + H / 70 + 6 * inner / 12 + H / 5, top - H / 160 - H / 600 + H / 14))

    def _stirrup(self, x: float, top: float, bottom: float, hook_right: bool, bar: float) -> List:
        """one stirrup leg with 135 degree hooks, as drawn by the plugin"""
        H = self.layout.HEIGHT
        s = 1 if hook_right else -1
        x = x + (H / 70 if hook_right else H / 110)
        return [
            (x + s * 0.1 * H / 8, top - H / 160 - H / 600 - 0.15 * H / 8, bar, bar, 0),
            (x, top - H / 160 - H / 600, bar, bar, s * 0.6),
            (x - s * H / 200, top - H / 160 - H / 450, bar, bar, 0),
            (x - s * H / 200, bottom + H / 100, bar, bar, s * 0.45),
            (x, bottom + H / 100 - H / 280, bar, bar, 0),
            (x + s * 0.25 * H / 8, bottom + H / 100 - H / 280, bar, bar, 0),
        ]

    # --- tables --------------------------------------------------------------------------------

    def _rebar_spec(self, diameter: float) -> Dict:
        return next((r for r in self.output['technical_spec']['rebars'] if r['diameter'] == diameter), None)

    def _draw_piece_lists(self) -> None:
        """one table per rebar type: position, shape with bend lengths, diameter, number, length and weight"""
        bx, by = self.layout.list_base()
        base_x = bx + 3.6
        pieces = self.output['pieces']
        rebar = self.output['summary']['rebar']
        tables = [
            ('Typical Rebars', pieces['typical'], 1000 * (rebar['typical']['top'] + rebar['typical']['bottom'])),
            ('Thermal Rebars', pieces['thermal'], 1000 * (rebar['thermal']['top'] + rebar['thermal']['bottom'])),
            ('Additional Rebars', pieces['additional'], 1000 * (rebar['additional']['top'] + rebar['additional']['bottom'])),
        ]
        shift = 0
        for title, piece_list, total_weight in tables:
            if not piece_list:
                continue
            shift += 15
            rows = []
            for piece in piece_list:
                for shape in ('no_side', 'one_side', 'two_side'):
                    if piece['bend'][shape] != 0:
                        rows.append((shape, piece['diameter'], piece['bend'][shape], piece['length']))
            self._draw_piece_table(base_x + shift, by, title, rows, total_weight)
        if pieces['shear']:
            shift += 15
            rows = [('stirrup', piece['diameter'], piece['number'], piece['length']) for piece in pieces['shear']]
            self._draw_piece_table(base_x + shift, by, 'Shear Rebars', rows, 1000 * rebar['shear'])

    def _draw_piece_table(self, x: float, y: float, title: str, rows: List[Tuple[str, float, int, float]], total_weight: float) -> None:
        columns = [x + 0.5, x + 3, x + 5.5, x + 7, x + 9, x + 11]
        text_y = y - 1
        self.line((x, y), (x + 12, y))
        for column, header in zip(columns, ("POS", "SHAPE", "D.", "Number", "L(m)", "weight(kg)")):
            self.text(header, (column, text_y), 0.25)
        for k, (shape, diameter, number, length) in enumerate(rows, start=1):
            row_y = text_y - k - 0.5
            self.text(str(k), (columns[0], row_y), 0.25)
            self._draw_shape(shape, diameter, length, columns[1], text_y - k)
            self.text(num(diameter), (columns[2], row_y), 0.25)
            self.text(str(number), (columns[3], row_y), 0.25)
            self.text(num(length), (columns[4], row_y), 0.25)
            weight = diameter ** 2 / 4 * number * length * 3.1416 * 7850 / 1000000
            self.text(num(weight, 0), (columns[5], row_y), 0.25)
            self.line((x, y - k - 1), (x + 12, y - k - 1))
        k = len(rows)
        bottom = y - (k + 1) - 1
        self.line((x, bottom), (x + 12, bottom))
        for offset in (0, 1, 5, 6, 8, 10, 12):
            self.line((x + offset, y), (x + offset, bottom))
        # total weight row
        total_bottom = y - (k + 2) - 1
        self.line((x, total_bottom), (x + 12, total_bottom))
        for offset in (0, 10, 12):
            self.line((x + offset, bottom), (x + offset, total_bottom))
        self.text(num(total_weight, 1), (columns[5], text_y - (k + 1) - 0.5), 0.25)
        self.text("Total Weight", (x + 5, text_y - (k + 1) - 0.5), 0.25)
        self.mtext(title, (x + 6, text_y + 1.5), 0.45, width=20)

    def _draw_shape(self, shape: str, diameter: float, length: float, cx: float, row_top: float) -> None:
        """bar shape sketch with its straight and bent lengths"""
        w = 0.03
        spec = self._rebar_spec(diameter)
        b90 = spec['bend']['B90'] if spec else 0
        if shape == 'no_side':
            self.polyline([(cx - 1.3, row_top - 0.7, w, w, 0), (cx + 1.3, row_top - 0.7, w, w, 0)])
            self.text(num(length), (cx, row_top - 0.55), 0.15)
            return
        if shape == 'one_side':
            self.polyline([
                (cx - 1.3, row_top - 0.2, w, w, 0), (cx - 1.3, row_top - 0.6, w, w, 0.45),
                (cx - 1.2, row_top - 0.7, w, w, 0), (cx + 1.3, row_top - 0.7, w, w, 0),
            ])
            straight = length - b90
        elif shape == 'two_side':
            self.polyline([
                (cx - 1.3, row_top - 0.2, w, w, 0), (cx - 1.3, row_top - 0.6, w, w, 0.45),
                (cx - 1.2, row_top - 0.7, w, w, 0), (cx + 1.2, row_top - 0.7, w, w, 0.45),
                (cx + 1.3, row_top - 0.6, w, w, 0), (cx + 1.3, row_top - 0.2, w, w, 0),
            ])
            straight = length - 2 * b90
            if spec:
                self.text(num(b90), (cx + 1.45, row_top - 0.4), 0.15, rotation=270)
        else: # stirrup
            self.polyline([
                (cx - 1.3, row_top - 0.2, w, w, 0), (cx - 1.3, row_top - 0.6, w, w, 0.45),
                (cx - 1.2, row_top - 0.7, w, w, 0), (cx + 1.2, row_top - 0.7, w, w, 0.6),
                (cx + 1.25, row_top - 0.55, w, w, 0), (cx + 0.95, row_top - 0.35, w, w, 0),
            ])
            b135 = spec['bend']['B135'] if spec else 0
            straight = length - b90 - b135
            if spec:
                self.text(num(b135), (cx + 1.2, row_top - 0.35), 0.15, rotation=math.degrees(5.67))
        if spec:
            self.text(num(b90), (cx - 1.45, row_top - 0.4), 0.15, rotation=90)
            self.text(num(straight, 2), (cx, row_top - 0.55), 0.15)

    def _draw_summary(self) -> None:
        bx, by = self.layout.list_base()
        pieces = self.output['pieces']
        shift = 15 * (sum(1 for key in ('typical', 'thermal', 'additional') if pieces[key]) + (1 if pieces['shear'] else 0))
        x = bx + 3.6 + 15 + shift
        width = 11.5
        rebar = self.output['summary']['rebar']
        kg = lambda tons: num(1000 * tons, 1)

        self.mtext("Summary Of Rebars Mass", (x + width / 2, by + 0.5), 0.45, width=20)
        for i in (0, 2, 3, 4, 5, 6, 7):
            self.line((x, by - i), (x + width, by - i))
        for offset in (0, 4, 6.5, 9, 11.5):
            self.line((x + offset, by), (x + offset, by - 7))
        columns = (2, 5.25, 7.75, 10.25)
        for column, header in zip(columns, ("Type of Rebar", "Top(kg)", "Bottom(kg)", "Total(kg)")):
            self.text(header, (x + column, by - 1), 0.25)
        rows = [
            ("Typical Rebars", kg(rebar['typical']['top']), kg(rebar['typical']['bottom']), kg(rebar['typical']['top'] + rebar['typical']['bottom'])),
            ("Thermal Rebars", kg(rebar['thermal']['top']), kg(rebar['thermal']['bottom']), kg(rebar['thermal']['top'] + rebar['thermal']['bottom'])),
            ("Additional Rebars", kg(rebar['additional']['top']), kg(rebar['additional']['bottom']), kg(rebar['additional']['top'] + rebar['additional']['bottom'])),
            ("Shear Rebars", "-", "-", kg(rebar['shear'])),
        ]
        top_total = rebar['typical']['top'] + rebar['thermal']['top'] + rebar['additional']['top']
        bottom_total = rebar['typical']['bottom'] + rebar['thermal']['bottom'] + rebar['additional']['bottom']
        rows.append(("Total", kg(top_total), kg(bottom_total), kg(top_total + bottom_total + rebar['shear'])))
        for i, (label, *values) in enumerate(rows):
            self.mtext(label, (x + columns[0], by - 2.5 - i), 0.25, width=7)
            for column, value in zip(columns[1:], values):
                self.text(value, (x + column, by - 2.5 - i), 0.25)

        # concrete volume
        self.mtext("Summary Of concrete volume(m³)", (x + width / 2, by - 9), 0.45, width=20)
        for i in (0, 1):
            self.line((x, by - 9.5 - 2 * i), (x + width, by - 9.5 - 2 * i))
        for i in range(3):
            self.line((x + i * width / 2, by - 9.5), (x + i * width / 2, by - 11.5))
        self.mtext("Total concrete volume", (x + width / 4, by - 10.5), 0.25, width=7)
        self.text(num(self.output['summary']['concrete']), (x + 3 * width / 4, by - 10.5), 0.25)

    def _draw_technical_tables(self) -> None:
        x, y = self.layout.list_base()
        cell_h, cell_w = 0.8, 1.2
        spec = self.output['technical_spec']
        rebars = spec['rebars']
        width = (len(rebars) + 3) * cell_w

        # overlap lengths
        for i in range(5):
            self.line((x, y - i * cell_h), (x + width, y - i * cell_h))
        for i in range(2):
            self.line((x + i * width, y), (x + i * width, y - 4 * cell_h))
        self.mtext("Length Of Overlap for Foundation in cm", (x + width / 2, y + 0.5), 0.45, width=20)
        material = spec['material']
        self.text(f"F'c={num(material['fc'] / 10, 1)}kg/cm², Fy={num(material['fy'] / 10, 1)}kg/cm²", (x + width / 2, y - 0.5 * cell_h), 0.25)
        for label, row in (("Rebar Size", 1.5), ("Top", 2.5), ("Bottom", 3.5)):
            self.text(label, (x + 1.5 * cell_w, y - row * cell_h), 0.25)
        for i, rebar in enumerate(rebars):
            cx = x + (3.5 + i) * cell_w
            self.text(f"%%C{num(rebar['diameter'])}", (cx, y - 1.5 * cell_h), 0.25)
            self.text(num(rebar['overlap']['top'] * 100), (cx, y - 2.5 * cell_h), 0.25)
            self.text(num(rebar['overlap']['bottom'] * 100), (cx, y - 3.5 * cell_h), 0.25)
            self.line((x + (3 + i) * cell_w, y - cell_h), (x + (3 + i) * cell_w, y - 4 * cell_h))

        # number of length types
        lx = x + width / 2 - 2 * cell_w
        ly = y - 8 * cell_h
        lw = 4 * cell_w
        for i in range(3):
            self.line((lx, ly - i * cell_h), (lx + lw, ly - i * cell_h))
        for offset in (0, 3 * cell_w, lw):
            self.line((lx + offset, ly), (lx + offset, ly - 2 * cell_h))
        self.mtext("Number Of Length Type Of Additional Rebars", (lx + lw / 2, ly + 0.6), 0.25, width=4.8)
        for row, (label, value) in enumerate((("Stack", spec['length_type']['stack']), ("Total", spec['length_type']['total']))):
            self.mtext(label, (lx + (lw - cell_w) / 2, ly - (row + 0.5) * cell_h), 0.25, width=4.8)
            self.text(str(value), (lx + lw - 0.5 * cell_w, ly - (row + 0.5) * cell_h), 0.25)

    # --- moment diagrams --------------------------------------------------------------------

    def _draw_moments(self) -> None:
        """resistance and ultimate moment along each strip, top in one column and bottom in the next"""
        scale = self.layout.HEIGHT / 21
        bx, by = self.layout.moment_base()
        strips = self.output['strips']
        max_length = max((max(s['moment']['resistance']['top']['stations']) for s in strips), default=0)
        shift = max_length + 7 * scale
        for column, level in ((0, 'top'), (1, 'bottom')):
            x0 = bx + column * shift
            for number, strip in enumerate(strips, start=1):
                line = StripLine(strip['geometry']['mid_line'])
                resistance = strip['moment']['resistance'][level]
                ultimate = strip['moment']['ultimate'][level]
                max_resistance = max(resistance['values']) or 1
                strip_length = max(resistance['stations'])
                y0 = by - number * 5 * scale
                def curve(stations, values):
                    return [(x0 + (s if line.is_start_left else line.length - s), y0 + scale * 2 * abs(v) / max_resistance) for s, v in zip(stations, values)]
                self.polyline(curve(resistance['stations'], resistance['values']), layer='moment', color=2)
                self.polyline(curve(ultimate['stations'], ultimate['values']), layer='moment', color=3)
                axis_length = strip_length + 3 * scale
                # axes and arrow heads as separate polylines, some viewers skip zero width parts of tapered ones
                self.polyline([(x0, y0 + 3 * scale), (x0, y0), (x0 + axis_length, y0)], layer='moment', color=1)
                self.polyline([(x0, y0 + 3.2 * scale, 0, 0.2 * scale, 0), (x0, y0 + 3 * scale, 0, 0, 0)], layer='moment', color=1)
                self.polyline([(x0 + axis_length, y0, 0.2 * scale, 0, 0), (x0 + axis_length + 0.2 * scale, y0, 0, 0, 0)], layer='moment', color=1)
                self.line((x0 - 0.1 * scale, y0 + 2 * scale), (x0 + 0.1 * scale, y0 + 2 * scale), layer='moment', color=7)
                self.line((x0 + strip_length, y0 + 0.1 * scale), (x0 + strip_length, y0 - 0.1 * scale), layer='moment', color=7)
                self.text(num(max_resistance, 2), (x0 - 0.7 * scale, y0 + 2 * scale), 0.2 * scale, layer='moment', color=7)
                self.text(num(strip_length, 2), (x0 + strip_length, y0 - 0.3 * scale), 0.2 * scale, layer='moment', color=7)
                self.text("M(ton.m)", (x0 - 1.3 * scale, y0 + 3 * scale), 0.3 * scale, layer='moment', color=7)
                self.text("L(m)", (x0 + axis_length, y0 - 0.5 * scale), 0.3 * scale, layer='moment', color=7)
                if column == 0:
                    self.text(strip['name'], (x0 - 5 * scale, y0 + scale), 0.6 * scale, layer='moment', color=7)
            self.text(level.upper(), (x0 + max_length / 3, by + 4 * scale), scale, layer='moment', color=7)
        # legend
        lx = bx + 2 * shift
        self.text("%%CMn", (lx - 2 * scale, by - 2 * scale), 0.8 * scale, layer='moment', color=2)
        self.text("Mu", (lx - 2 * scale, by - 3.5 * scale), 0.8 * scale, layer='moment', color=3)
        self.polyline([(lx, by - 2 * scale), (lx + 2 * scale, by - 2 * scale)], layer='moment', color=2, width=0.1 * scale)
        self.polyline([(lx, by - 3.5 * scale), (lx + 2 * scale, by - 3.5 * scale)], layer='moment', color=3, width=0.1 * scale)


    # --- cutting plans ----------------------------------------------------------------------

    def _draw_cutting_plans(self) -> None:
        """portrait sheets below the plans, 15 cutting patterns each, one or more sheets per diameter"""
        plans = self.output.get('cut', [])
        H = self.layout.HEIGHT
        W = self.layout.WIDTH / 2
        s = H / 29.7 # one cm of a portrait A4 sheet; a meter of bar is drawn as one s
        margin = 1.4 * s
        rows_per_sheet = 15
        columns = [2.87 * s, 4.33 * s, 5.8 * s, 18.4 * s] # waste | length | number | pattern | row
        headers = ["Waste\n(m)", "Length\n(m)", "Number", "Cutting Pattern", "Row"]
        sheet = 0
        for plan in plans:
            pages = max(1, math.ceil(len(plan['patterns']) / rows_per_sheet))
            for page in range(pages):
                x0, top = 1.5 * sheet * W, -H / 2
                sheet += 1
                # frame and grid
                self.polyline([(x0, top), (x0 + W, top), (x0 + W, top - H), (x0, top - H)], layer='Sheet', closed=True)
                self.polyline([(x0 + margin, top - margin), (x0 + W - margin, top - margin), (x0 + W - margin, top - H + margin), (x0 + margin, top - H + margin)],
                    layer='Border', closed=True, width=0.002 * H)
                for k in range(rows_per_sheet + 1):
                    y = top - 3 * s - 1.5 * k * s
                    bold = k in (0, rows_per_sheet)
                    self.polyline([(x0 + margin, y), (x0 + W - margin, y)], layer='Border', color=None if bold else 3, width=0.0015 * H if bold else 0)
                for x in columns:
                    self.line((x0 + x, top - 1.5 * s), (x0 + x, top - 25.5 * s), color=3)
                centers = [(margin + columns[0]) / 2, (columns[0] + columns[1]) / 2, (columns[1] + columns[2]) / 2, (columns[2] + columns[3]) / 2, (columns[3] + W - margin) / 2]
                for center, header in zip(centers, headers):
                    self.mtext(header.replace('\n', '\\P'), (x0 + center, top - margin - 0.75 * s), 0.24 * s, width=4 * s, layer='Border', color=2)
                title = f"Cutting Plan %%C{num(plan['diameter'])}" + (f" ({page + 1}/{pages})" if pages > 1 else '')
                self.text(title, (x0 + W / 2, top + 0.8 * s), 0.5 * s)
                self.text(f"{plan['bars']} bars of {num(plan['stock_length'])} m, waste {num(plan['waste'], 2)} m ({num(100 * plan['waste_ratio'], 1)}%)",
                    (x0 + W / 2, top - 26.8 * s), 0.3 * s)

                # one row per pattern
                for row, pattern in enumerate(plan['patterns'][page * rows_per_sheet:(page + 1) * rows_per_sheet]):
                    y = top - 3.75 * s - row * 1.5 * s
                    self.text(str(pattern['number']), (x0 + centers[2], y), 0.3 * s, color=2)
                    self.text(num(pattern['waste'], 2), (x0 + centers[0], y), 0.3 * s, color=2)
                    self.text(num(sum(p['length'] for p in pattern['pieces']), 2), (x0 + centers[1], y), 0.3 * s, color=2)
                    self.text(str(page * rows_per_sheet + row + 1), (x0 + centers[4], y), 0.3 * s, color=2)
                    start = 0
                    for piece in pattern['pieces']:
                        a = x0 + 6.1 * s + start * s
                        b = a + piece['length'] * s
                        # the bar with a cut mark at each end
                        self.polyline([(a + 0.1 * s, y + 0.1 * s), (a - 0.1 * s, y - 0.1 * s), (a, y), (b, y), (b + 0.1 * s, y + 0.1 * s), (b - 0.1 * s, y - 0.1 * s)],
                            layer='Border', color=6)
                        self.text(num(piece['length'], 2), ((a + b) / 2, y + 0.2 * s), 0.2 * s, color=6)
                        self.text('/'.join(piece['label']), ((a + b) / 2, y - 0.2 * s), 0.2 * s, color=6)
                        start += piece['length']


# stirrup leg positions (1..13) for 1 to 11 legs
SHEAR_SLOTS = (
    (7,),
    (2, 12),
    (2, 7, 12),
    (2, 5, 9, 12),
    (2, 4, 7, 10, 12),
    (2, 4, 6, 8, 10, 12),
    (2, 4, 6, 7, 8, 10, 12),
    (2, 3, 4, 6, 8, 10, 11, 12),
    (2, 3, 4, 6, 7, 8, 10, 11, 12),
    (2, 3, 4, 5, 6, 8, 9, 10, 11, 12),
    (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
)
