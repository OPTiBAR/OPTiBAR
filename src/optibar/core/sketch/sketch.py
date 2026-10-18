from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, List, Union

import cairo

from . import setting

WIDTH = setting.WIDTH # mm
HEIGHT = setting.HEIGHT # mm
MM = 72 / 25.4 # points per mm, cairo pdf surfaces are measured in points

Table = List[List[Union[str, float]]]


class Point():
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)


class Sketch():
    """draws the output of a calculation as an A4 pdf: one page per strip with its additional rebar
    meshes, followed by the summary, specification and piece tables.

    Args:
        output (Dict): the "data" part of the engine output
    """
    def __init__(self, output: Dict) -> None:
        self.__output = output

    def save(self, file_path: Union[str, Path]) -> None:
        surface = cairo.PDFSurface(str(file_path), WIDTH * MM, HEIGHT * MM)
        context = cairo.Context(surface)
        context.scale(MM, MM)
        context.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        for strip in self.__output["strips"]:
            self.__draw_strip(strip, context)
            context.show_page()

        tables = [
            ("Rebar Mass Summary", self.__get_summary_table()),
            ("Technical Specifications", self.__get_technical_spec_table()),
            ("Rebar Specifications", self.__get_rebar_spec_table()),
            ("Additional Piece List", self.__get_piece_table("additional")),
            ("Typical Piece List", self.__get_piece_table("typical")),
            ("Thermal Piece List", self.__get_piece_table("thermal")),
            ("Shear Piece List", self.__get_shear_piece_table()),
            ("Shear Type Table", self.__get_shear_type_table()),
        ]
        for name, table in tables:
            if len(table) > 1: # skip tables that only have a header
                self.__draw_table(table, context, name)
        surface.finish()

    def __get_summary_table(self) -> Table:
        rebar = self.__output["summary"]["rebar"]
        table = []
        table.append([' ', 'additional', 'typical', 'thermal', 'shear'])
        for level in ('top', 'bottom'):
            table.append([level, rebar["additional"][level], rebar["typical"][level], rebar["thermal"][level], '-'])
        table.append([
            'total',
            round(rebar["additional"]["top"] + rebar["additional"]["bottom"],3),
            round(rebar["typical"]["top"] + rebar["typical"]["bottom"],3),
            round(rebar["thermal"]["top"] + rebar["thermal"]["bottom"],3),
            rebar["shear"]
        ])
        return table

    def __get_technical_spec_table(self) -> Table:
        spec = self.__output["technical_spec"]
        table = []
        table.append(['item', 'value', 'unit'])
        # material
        table.extend([
            ['f\'c', round(spec["material"]["fc"]), "ton/m^2"],
            ['fy', round(spec["material"]["fy"]),  "ton/m^2"],
        ])
        # covers
        table.extend([
            ['top cover', round(100*spec["covers"]["top"], 1), "cm"],
            ['bottom cover', round(100*spec["covers"]["bottom"], 1), "cm"],
            ['side cover', round(100*spec["covers"]["side"], 1), "cm"],
        ])
        # Type number
        table.extend([
            ['Total type num.', spec["length_type"]["total"], "-"],
            ['Stack type num.', spec["length_type"]["stack"], "-"],
        ])
        return table

    def __get_rebar_spec_table(self) -> Table:
        table = []
        table.append(['diameter', 'Ld top', 'Ld bottom', 'overlap top', 'overlap bottom', 'Bend 135', 'Bend 90'])
        for rebar in self.__output["technical_spec"]["rebars"]:
            table.append([
                rebar["diameter"],
                rebar["Ld"]["top"],
                rebar["Ld"]["bottom"],
                rebar["overlap"]["top"],
                rebar["overlap"]["bottom"],
                rebar["bend"]["B135"],
                rebar["bend"]["B90"],
            ])
        return table

    def __get_shear_type_table(self) -> Table:
        table = []
        table.append(['Type ID', 'diameter', 'interval', 'number'])
        for shear_type in self.__output["shear_types"]:
            table.append([shear_type["id"], shear_type["diameter"], shear_type["interval"], shear_type["number"]])
        return table

    def __get_piece_table(self, rebar_type: str) -> Table:
        table = []
        table.append([' ', 'diameter', 'length', 'number', 'no_bend', 'one_bend', 'two_bend'])
        for i,piece in enumerate(self.__output["pieces"][rebar_type]):
            table.append([i+1, piece["diameter"], piece["length"], piece["number"], piece["bend"]["no_side"], piece["bend"]["one_side"], piece["bend"]["two_side"]])
        return table

    def __get_shear_piece_table(self) -> Table:
        table = []
        table.append([' ', 'diameter', 'length', 'number'])
        for i,piece in enumerate(self.__output["pieces"]["shear"]):
            table.append([i+1, piece["diameter"], piece["length"], piece["number"]])
        return table

    def __draw_strip(self, strip: Dict, context: cairo.Context) -> None:
        context.set_source_rgba(*setting.TITLE_COLOR)
        context.set_font_size(setting.TITLE_FONT_SIZE)
        context.move_to(WIDTH/10, HEIGHT/10)
        context.show_text(strip["name"])

        stations = strip["moment"]["ultimate"]["top"]["stations"]
        start = min(stations)
        length = max(stations) - start
        for level, base_point in (("top", Point(0,0)), ("bottom", Point(0,HEIGHT/2))):
            context.set_source_rgba(*setting.TITLE_COLOR)
            context.set_font_size(setting.TITLE_FONT_SIZE)
            context.move_to(WIDTH/10, base_point.y + (3/20) * HEIGHT)
            context.show_text(f"{level.capitalize()} additional rebar")
            self.__draw_mesh(strip["mesh"]["additional"][level], context, base_point, start, length)

    def __draw_mesh(self, mesh: List, context: cairo.Context, base_point: Point, start: float, length: float) -> None:
        h_step = (8/10) * WIDTH / length # step of one meter in strip
        v_step = (1/25) * HEIGHT
        x = lambda station: base_point.x + (1/10) * WIDTH + (station - start) * h_step
        # meter line
        context.set_source_rgba(*setting.DIM_LINE_COLOR)
        context.set_line_width(setting.DIM_LINE_WIDTH)
        context.move_to(base_point.x + (1/10) * WIDTH, base_point.y + (4/10) * HEIGHT)
        context.line_to(base_point.x + (9/10) * WIDTH, base_point.y + (4/10) * HEIGHT)
        context.stroke()

        context.set_font_size(setting.TITLE_FONT_SIZE)
        for i in range(math.ceil(length) + 1):
            # meter ticks
            context.set_source_rgba(*setting.DIM_LINE_COLOR)
            context.move_to(base_point.x + (1/10) * WIDTH + i * h_step, base_point.y + (4/10) * HEIGHT - (1/10) * v_step)
            context.line_to(base_point.x + (1/10) * WIDTH + i * h_step, base_point.y + (4/10) * HEIGHT + (1/10) * v_step)
            context.stroke()
            # meter text
            context.set_source_rgba(*setting.TITLE_COLOR)
            xbearing, ybearing, width, height, dx, dy = context.text_extents(str(i))
            context.move_to(base_point.x + (1/10) * WIDTH + i * h_step - width/2, base_point.y + (4/10) * HEIGHT + height + (2/10) * v_step)
            context.show_text(str(i))

        # draw pieces
        context.set_line_width(setting.PIECE_LINE_WIDTH)
        for i,row in enumerate(mesh):
            shift = False
            last_bunch = None
            for piece in row:
                for j,bunch in enumerate(piece):
                    stations = bunch["stations"]
                    bends = bunch["bends"]
                    if last_bunch is not None and last_bunch["stations"][1] > bunch["stations"][0]:
                        shift = not shift
                    else:
                        shift = False
                    y = base_point.y + (4/10) * HEIGHT - v_step * (i+1) + shift * (v_step/5)

                    context.set_source_rgba(*setting.PIECE_COLOR_TOTAL)
                    context.move_to(x(stations[0] + bends[0]), y)
                    context.line_to(x(stations[1] - bends[1]), y)
                    context.stroke()

                    # connection marks
                    if j < len(piece)-1 :
                        # end connection mark
                        context.move_to(x(stations[1] - bends[1]), y)
                        context.arc(x(stations[1] - bends[1]), y, 2 * setting.DIM_LINE_WIDTH, 0, math.pi * 2)
                    if j > 0:
                        # start connection mark
                        context.move_to(x(stations[0] + bends[0]), y)
                        context.arc(x(stations[0] + bends[0]), y, 2 * setting.DIM_LINE_WIDTH, 0, math.pi * 2)
                    context.fill()

                    # left bend
                    if bends[0] > 0:
                        context.move_to(x(stations[0] + bends[0]), y)
                        context.line_to(x(stations[0] + bends[0]), y + v_step/6)
                        context.stroke()
                    # right bend
                    if bends[1] > 0:
                        context.move_to(x(stations[1] - bends[1]), y)
                        context.line_to(x(stations[1] - bends[1]), y + v_step/6)
                        context.stroke()

                    context.set_source_rgba(*setting.DIM_FONT_COLOR)
                    context.set_font_size(setting.DIM_FONT_SIZE)
                    context.move_to(x(stations[0] + bends[0]), y - v_step/4)
                    context.show_text(str(round(stations[1] - stations[0],2)) + 'X' + str(bunch["number"]) + ' T' + str(bunch["diameter"]))
                    last_bunch = bunch

    def __draw_table(self, table: Table, context: cairo.Context, name: str) -> None:
        """draws the table on new pages, continuing on the next page with the header repeated when it is too long"""
        cell_padding = setting.TABLE_CELL_PADDING
        context.set_font_size(setting.TABLE_FONT_SIZE)

        # determine the width of columns and height of row
        text_height = 0
        col_widths = [0] * len(table[0])
        for row in table:
            for j,cell in enumerate(row):
                xbearing, ybearing, width, height, dx, dy = context.text_extents(str(cell))
                col_widths[j] = max(col_widths[j], width + 2 * cell_padding)
                text_height = max(text_height, height)
        # height of all rows should be equal
        row_height = text_height + 2 * cell_padding

        x_base = (WIDTH * (8/10) - sum(col_widths))/2 + (1/10) * WIDTH
        y_base = (1/10) * HEIGHT
        rows_per_page = max(2, int((HEIGHT - y_base - setting.MARGIN) // row_height))
        header, body = table[0], table[1:]
        chunk = rows_per_page - 1
        pages = [body[i:i + chunk] for i in range(0, len(body), chunk)]
        for page_index, page_rows in enumerate(pages):
            title = name if len(pages) == 1 else f"{name} ({page_index + 1}/{len(pages)})"
            self.__draw_table_page([header] + page_rows, context, title, col_widths, x_base, y_base, row_height, text_height)
            context.show_page()

    def __draw_table_page(self, table: Table, context: cairo.Context, name: str, col_widths: List[float],
            x_base: float, y_base: float, row_height: float, text_height: float) -> None:
        cell_padding = setting.TABLE_CELL_PADDING
        context.set_line_width(setting.TABLE_LINE_WIDTH)
        context.set_font_size(setting.TABLE_FONT_SIZE)

        context.set_source_rgba(*setting.TITLE_COLOR)
        xbearing, ybearing, width, height, dx, dy = context.text_extents(name)
        context.move_to((WIDTH - width)/2 , y_base - height * (3/2))
        context.show_text(name)

        for i,row in enumerate(table):
            # draw upper line
            context.set_source_rgba(*setting.TABLE_LINE_COLOR)
            context.move_to(x_base , y_base + row_height * i)
            context.line_to(x_base + sum(col_widths), y_base + row_height * i)
            context.stroke()
            # draw lower line for last row
            if i == len(table)-1:
                context.move_to(x_base , y_base + row_height * (i+1))
                context.line_to(x_base + sum(col_widths), y_base + row_height * (i+1))
                context.stroke()

            # draw cell info
            context.set_source_rgba(*setting.TABLE_FONT_COLOR)
            for j,cell in enumerate(row):
                xbearing, ybearing, width, height, dx, dy = context.text_extents(str(cell))
                context.move_to(x_base + sum(col_widths[0:j]) + (col_widths[j]-width)/2, y_base + row_height * i + cell_padding + text_height)
                context.show_text(str(cell))

        # draw seperating vertical lines
        context.set_source_rgba(*setting.TABLE_LINE_COLOR)
        for j in range(len(table[0])+1):
            context.move_to(x_base + sum(col_widths[0:j]), y_base)
            context.line_to(x_base + sum(col_widths[0:j]), y_base + row_height * len(table))
            context.stroke()
