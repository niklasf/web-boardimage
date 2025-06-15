import pychess
import math
import os
from typing import Dict, Tuple, Union

import svgutils
from lxml.etree import tostring

import xml.etree.ElementTree as ET


SQUARE_SIZE = 45
MARGIN = 20

SVG_PIECES = {}
SVG_PATH_PIECES = {}


XX = """<g id="xx"><path d="M35.865 9.135a1.89 1.89 0 0 1 0 2.673L25.173 22.5l10.692 10.692a1.89 1.89 0 0 1 0 2.673 1.89 1.89 0 0 1-2.673 0L22.5 25.173 11.808 35.865a1.89 1.89 0 0 1-2.673 0 1.89 1.89 0 0 1 0-2.673L19.827 22.5 9.135 11.808a1.89 1.89 0 0 1 0-2.673 1.89 1.89 0 0 1 2.673 0L22.5 19.827 33.192 9.135a1.89 1.89 0 0 1 2.673 0z" fill="#000" stroke="#fff" stroke-width="1.688"/></g>"""  # noqa: E501

CHECK_GRADIENT = """<radialGradient id="check_gradient" r="0.5"><stop offset="0%" stop-color="#ff0000" stop-opacity="1.0" /><stop offset="50%" stop-color="#e70000" stop-opacity="1.0" /><stop offset="100%" stop-color="#9e0000" stop-opacity="0.0" /></radialGradient>"""  # noqa: E501

DEFAULT_COLORS = {
    "square light": "#f0d9b5",
    "square dark": "#b58863",
    "square dark lastmove": "#aaa23b",
    "square light lastmove": "#cdd16a",
    "margin": "#212121",
    "inner border": "#111",
    "outer border": "#111",
    "coord": "#333333",
    "arrow green": "#15781B80",
    "arrow red": "#88202080",
    "arrow yellow": "#e68f00b3",
    "arrow blue": "#00308880",
}


STATIC_PATH = "pychess-variants/static/"


def get_svg_pieces_from_css(css):
    SVG_PIECES[css] = {}
    SVG_PATH_PIECES[css] = {}
    css_path = os.path.join(STATIC_PATH, "piece", css + ".css")
    if not os.path.isfile(css_path):
        print("ERROR: FileNotFoundError %s" % css_path)
        return
    with open(css_path) as css_file:
        color, symbol, url = "", "", ""
        promoted = False
        for line in css_file:
            if line.strip():
                if "piece." in line:
                    color = "white" if ("white" in line or "ally" in line) else "black"
                    start = line.find("piece.") + 6
                    end = line.find("-piece")
                    symbol = line[start:end]
                    if "promoted" in line:
                        promoted = True
                if "url" in line:
                    start = line.find("url(") + 5
                    end = line.find(")") - 1
                    url = line[start:end]
                if symbol and url:
                    if color == "white":
                        letters = list(symbol)
                        letters[-1] = letters[-1].upper()
                        symbol = ''.join(letters)
                    if promoted:
                        symbol = "p" + symbol
                    SVG_PATH_PIECES[css][symbol] = url
                    color, symbol, url = "", "", ""
                    promoted = False


def square_file(square):
    return ord(square[0]) - 97


def square_rank(square):
    return int(square[1:]) - 1


def parse_squares(board, squares):
    parsed = []
    for square in squares:
        parsed.append((board.rows - square_rank(square) - 1, square_file(square)))
    return parsed


def read_piece_svg(css, piece):
    symbol = piece.symbol
    piece_name = "%s-piece" % symbol

    if symbol not in SVG_PATH_PIECES[css]:
        return

    piece_svg = SVG_PATH_PIECES[css][symbol]

    orig_file = os.path.normpath(os.path.join(STATIC_PATH, "piece", css, "..", piece_svg))
    if not os.path.isfile(orig_file):
        print("ERROR: FileNotFoundError %s" % orig_file)
        return

    if orig_file[-3:] != "svg":
        print("ERROR: %s is not in .svg format" % orig_file)
        return

    # This can read "viewBox" but can't do scale()
    svg_full = svgutils.transform.fromfile(orig_file)

    viewBox = svg_full.root.get("viewBox")

    # This can't read "viewBox" but can do scale()
    try:
        svg = svgutils.compose.SVG(orig_file)
    except AttributeError:
        print("ERROR: Possible %s referenced in %s.css has no 'width/height'" % (orig_file, css))
        # TODO: add "width/height" to .svg
        raise

    if viewBox is not None:
        width = float(viewBox.split()[2])
    elif svg.width is not None:
        width = svg.width
    else:
        SVG_PIECES[css][symbol] = ""
        return

    if width != SQUARE_SIZE:
        new = SQUARE_SIZE / width
        svg.scale(new)

    head = """<g id="%s-%s">""" % (pychess.COLOR_NAMES[piece.color], piece_name)
    tail = """</g>"""

    SVG_PIECES[css][symbol] = "%s%s%s" % (head, tostring(svg.root), tail)


class SvgWrapper(str):
    def _repr_svg_(self):
        return self


def _svg(viewbox_x, viewbox_y, width, height):
    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "viewBox": "0 0 %d %d" % (viewbox_x, viewbox_y),
    })

    if width is not None:
        svg.set("width", str(width))
    if height is not None:
        svg.set("height", str(height))

    return svg


def _attrs(attrs: Dict[str, Union[str, int, float, None]]) -> Dict[str, str]:
    return {k: str(v) for k, v in attrs.items() if v is not None}


def _select_color(colors: Dict[str, str], color: str) -> Tuple[str, float]:
    return _color(colors.get(color, DEFAULT_COLORS[color]))


def _color(color: str) -> Tuple[str, float]:
    if color.startswith("#"):
        try:
            if len(color) == 5:
                return color[:4], int(color[4], 16) / 0xf
            elif len(color) == 9:
                return color[:7], int(color[7:], 16) / 0xff
        except ValueError:
            pass  # Ignore invalid hex value
    return color, 1.0


def piece(css, piece, size=None):
    """
    Renders the given :class:`pychess.Piece` as an SVG image.
    """
    svg = _svg(SQUARE_SIZE, SQUARE_SIZE, size, size)
    svg.append(ET.fromstring(SVG_PIECES[css][piece.symbol]))
    return SvgWrapper(ET.tostring(svg).decode("utf-8"))


def _colors_to_css(colors: Dict[str, str]) -> str:
    """Convert a color mapping dictionary into a CSS string."""
    lines = []
    for selector, value in colors.items():
        classes = "." + ".".join(selector.split())
        lines.append(f"{classes} {{ fill: {value}; }}")
    return "\n".join(lines)


# SVG path definitions for coordinate glyphs (a-l, 1-12, etc.)
COORD_SVG_PATHS = {
    'a': "<path d='M5.654296875 4.697265625Q3.4765625 4.697265625 2.63671875 5.1953125Q1.796875 5.693359375 1.796875 6.89453125Q1.796875 7.8515625 2.4267578125 8.4130859375Q3.056640625 8.974609375 4.140625 8.974609375Q5.634765625 8.974609375 6.5380859375 7.9150390625Q7.44140625 6.85546875 7.44140625 5.09765625V4.697265625ZM9.23828125 3.955078125V10.1953125H7.44140625V8.53515625Q6.826171875 9.53125 5.908203125 10.0048828125Q4.990234375 10.478515625 3.662109375 10.478515625Q1.982421875 10.478515625 0.9912109375 9.5361328125Q0.0 8.59375 0.0 7.01171875Q0.0 5.166015625 1.2353515625 4.228515625Q2.470703125 3.291015625 4.921875 3.291015625H7.44140625V3.115234375Q7.44140625 1.875 6.6259765625 1.1962890625Q5.810546875 0.517578125 4.3359375 0.517578125Q3.3984375 0.517578125 2.509765625 0.7421875Q1.62109375 0.966796875 0.80078125 1.416015625V-0.244140625Q1.787109375 -0.625 2.71484375 -0.8154296875Q3.642578125 -1.005859375 4.521484375 -1.005859375Q6.89453125 -1.005859375 8.06640625 0.224609375Q9.23828125 1.455078125 9.23828125 3.955078125Z'/>",
    'b': "<path d='M7.919921875 4.736328125Q7.919921875 2.75390625 7.1044921875 1.6259765625Q6.2890625 0.498046875 4.86328125 0.498046875Q3.4375 0.498046875 2.6220703125 1.6259765625Q1.806640625 2.75390625 1.806640625 4.736328125Q1.806640625 6.71875 2.6220703125 7.8466796875Q3.4375 8.974609375 4.86328125 8.974609375Q6.2890625 8.974609375 7.1044921875 7.8466796875Q7.919921875 6.71875 7.919921875 4.736328125ZM1.806640625 0.91796875Q2.373046875 -0.05859375 3.2373046875 -0.5322265625Q4.1015625 -1.005859375 5.302734375 -1.005859375Q7.294921875 -1.005859375 8.5400390625 0.576171875Q9.78515625 2.158203125 9.78515625 4.736328125Q9.78515625 7.314453125 8.5400390625 8.896484375Q7.294921875 10.478515625 5.302734375 10.478515625Q4.1015625 10.478515625 3.2373046875 10.0048828125Q2.373046875 9.53125 1.806640625 8.5546875V10.1953125H0.0V-5.0H1.806640625Z'/>",
    'c': "<path d='M8.65234375 -0.322265625V1.357421875Q7.890625 0.9375 7.1240234375 0.7275390625Q6.357421875 0.517578125 5.576171875 0.517578125Q3.828125 0.517578125 2.861328125 1.6259765625Q1.89453125 2.734375 1.89453125 4.736328125Q1.89453125 6.73828125 2.861328125 7.8466796875Q3.828125 8.955078125 5.576171875 8.955078125Q6.357421875 8.955078125 7.1240234375 8.7451171875Q7.890625 8.53515625 8.65234375 8.115234375V9.775390625Q7.900390625 10.126953125 7.0947265625 10.302734375Q6.2890625 10.478515625 5.380859375 10.478515625Q2.91015625 10.478515625 1.455078125 8.92578125Q0.0 7.373046875 0.0 4.736328125Q0.0 2.060546875 1.4697265625 0.52734375Q2.939453125 -1.005859375 5.498046875 -1.005859375Q6.328125 -1.005859375 7.119140625 -0.8349609375Q7.91015625 -0.6640625 8.65234375 -0.322265625Z'/>",
    'd': "<path d='M7.978515625 0.91796875V-5.0H9.775390625V10.1953125H7.978515625V8.5546875Q7.412109375 9.53125 6.5478515625 10.0048828125Q5.68359375 10.478515625 4.47265625 10.478515625Q2.490234375 10.478515625 1.2451171875 8.896484375Q0.0 7.314453125 0.0 4.736328125Q0.0 2.158203125 1.2451171875 0.576171875Q2.490234375 -1.005859375 4.47265625 -1.005859375Q5.68359375 -1.005859375 6.5478515625 -0.5322265625Q7.412109375 -0.05859375 7.978515625 0.91796875ZM1.85546875 4.736328125Q1.85546875 6.71875 2.6708984375 7.8466796875Q3.486328125 8.974609375 4.912109375 8.974609375Q6.337890625 8.974609375 7.158203125 7.8466796875Q7.978515625 6.71875 7.978515625 4.736328125Q7.978515625 2.75390625 7.158203125 1.6259765625Q6.337890625 0.498046875 4.912109375 0.498046875Q3.486328125 0.498046875 2.6708984375 1.6259765625Q1.85546875 2.75390625 1.85546875 4.736328125Z'/>",
    'e': "<path d='M10.13671875 4.27734375V5.15625H1.875Q1.9921875 7.01171875 2.9931640625 7.9833984375Q3.994140625 8.955078125 5.78125 8.955078125Q6.81640625 8.955078125 7.7880859375 8.701171875Q8.759765625 8.447265625 9.716796875 7.939453125V9.638671875Q8.75 10.048828125 7.734375 10.263671875Q6.71875 10.478515625 5.673828125 10.478515625Q3.056640625 10.478515625 1.5283203125 8.955078125Q0.0 7.431640625 0.0 4.833984375Q0.0 2.1484375 1.4501953125 0.5712890625Q2.900390625 -1.005859375 5.361328125 -1.005859375Q7.568359375 -1.005859375 8.8525390625 0.4150390625Q10.13671875 1.8359375 10.13671875 4.27734375ZM8.33984375 3.75Q8.3203125 2.275390625 7.5146484375 1.396484375Q6.708984375 0.517578125 5.380859375 0.517578125Q3.876953125 0.517578125 2.9736328125 1.3671875Q2.0703125 2.216796875 1.93359375 3.759765625Z'/>",
    'f': "<path d='M6.962890625 -5.0V-3.505859375H5.244140625Q4.27734375 -3.505859375 3.9013671875 -3.115234375Q3.525390625 -2.724609375 3.525390625 -1.708984375V-0.7421875H6.484375V0.654296875H3.525390625V10.1953125H1.71875V0.654296875H0.0V-0.7421875H1.71875V-1.50390625Q1.71875 -3.330078125 2.568359375 -4.1650390625Q3.41796875 -5.0 5.263671875 -5.0Z'/>",
    'g': "<path d='M7.978515625 4.599609375Q7.978515625 2.646484375 7.1728515625 1.572265625Q6.3671875 0.498046875 4.912109375 0.498046875Q3.466796875 0.498046875 2.6611328125 1.572265625Q1.85546875 2.646484375 1.85546875 4.599609375Q1.85546875 6.54296875 2.6611328125 7.6171875Q3.466796875 8.69140625 4.912109375 8.69140625Q6.3671875 8.69140625 7.1728515625 7.6171875Q7.978515625 6.54296875 7.978515625 4.599609375ZM9.775390625 8.837890625Q9.775390625 11.630859375 8.53515625 12.9931640625Q7.294921875 14.35546875 4.736328125 14.35546875Q3.7890625 14.35546875 2.94921875 14.2138671875Q2.109375 14.072265625 1.318359375 13.779296875V12.03125Q2.109375 12.4609375 2.880859375 12.666015625Q3.65234375 12.87109375 4.453125 12.87109375Q6.220703125 12.87109375 7.099609375 11.9482421875Q7.978515625 11.025390625 7.978515625 9.16015625V8.271484375Q7.421875 9.23828125 6.552734375 9.716796875Q5.68359375 10.1953125 4.47265625 10.1953125Q2.4609375 10.1953125 1.23046875 8.662109375Q0.0 7.12890625 0.0 4.599609375Q0.0 2.060546875 1.23046875 0.52734375Q2.4609375 -1.005859375 4.47265625 -1.005859375Q5.68359375 -1.005859375 6.552734375 -0.52734375Q7.421875 -0.048828125 7.978515625 0.91796875V-0.7421875H9.775390625Z'/>",
    'h': "<path d='M9.16015625 3.59375V10.1953125H7.36328125V3.65234375Q7.36328125 2.099609375 6.7578125 1.328125Q6.15234375 0.556640625 4.94140625 0.556640625Q3.486328125 0.556640625 2.646484375 1.484375Q1.806640625 2.412109375 1.806640625 4.013671875V10.1953125H0.0V-5.0H1.806640625V0.95703125Q2.451171875 -0.029296875 3.3251953125 -0.517578125Q4.19921875 -1.005859375 5.341796875 -1.005859375Q7.2265625 -1.005859375 8.193359375 0.1611328125Q9.16015625 1.328125 9.16015625 3.59375Z'/>",
    'i': "<path d='M0.0 -0.7421875H1.796875V10.1953125H0.0ZM0.0 -5.0H1.796875V-2.724609375H0.0Z'/>",
    'j': "<path d='M2.24609375 -0.7421875H4.04296875V10.390625Q4.04296875 12.48046875 3.2470703125 13.41796875Q2.451171875 14.35546875 0.68359375 14.35546875H0.0V12.83203125H0.478515625Q1.50390625 12.83203125 1.875 12.3583984375Q2.24609375 11.884765625 2.24609375 10.390625ZM2.24609375 -5.0H4.04296875V-2.724609375H2.24609375Z'/>",
    '1': "<path d='M0.283203125 8.53515625H3.505859375V-2.587890625L0.0 -1.884765625V-3.681640625L3.486328125 -4.384765625H5.458984375V8.53515625H8.681640625V10.1953125H0.283203125Z'/>",
    '2': "<path d='M2.373046875 8.53515625H9.2578125V10.1953125H0.0V8.53515625Q1.123046875 7.373046875 3.0615234375 5.4150390625Q5.0 3.45703125 5.498046875 2.890625Q6.4453125 1.826171875 6.8212890625 1.0888671875Q7.197265625 0.3515625 7.197265625 -0.361328125Q7.197265625 -1.5234375 6.3818359375 -2.255859375Q5.56640625 -2.98828125 4.2578125 -2.98828125Q3.330078125 -2.98828125 2.2998046875 -2.666015625Q1.26953125 -2.34375 0.09765625 -1.689453125V-3.681640625Q1.2890625 -4.16015625 2.32421875 -4.404296875Q3.359375 -4.6484375 4.21875 -4.6484375Q6.484375 -4.6484375 7.83203125 -3.515625Q9.1796875 -2.3828125 9.1796875 -0.869140625Q9.1796875 0.341796875 8.564453125 1.1767578125Q7.87109375 2.01171875 6.591796875 2.333984375Z'/>",
    '3': "<path d='M6.591796875 2.333984375Q8.0078125 2.63671875 8.8037109375 3.59375Q9.599609375 4.55078125 9.599609375 5.95703125Q9.599609375 8.115234375 8.115234375 9.296875Q6.630859375 10.478515625 3.896484375 10.478515625Q2.978515625 10.478515625 2.0068359375 10.2978515625Q1.03515625 10.1171875 0.0 9.755859375V7.8515625Q0.8203125 8.330078125 1.796875 8.57421875Q2.7734375 8.818359375 3.837890625 8.818359375Q5.693359375 8.818359375 6.6650390625 8.0859375Q7.63671875 7.353515625 7.63671875 5.95703125Q7.63671875 4.66796875 6.7333984375 3.9404296875Q5.830078125 3.212890625 4.21875 3.212890625H2.51953125V1.591796875H4.296875Q5.751953125 1.591796875 6.5234375 1.0107421875Q7.294921875 0.4296875 7.294921875 -0.6640625Q7.294921875 -1.787109375 6.4990234375 -2.3876953125Q5.703125 -2.98828125 4.21875 -2.98828125Q3.408203125 -2.98828125 2.48046875 -2.8125Q1.552734375 -2.63671875 0.439453125 -2.265625V-4.0234375Q1.5625 -4.3359375 2.5439453125 -4.4921875Q3.525390625 -4.6484375 4.39453125 -4.6484375Q6.640625 -4.6484375 7.94921875 -3.6279296875Q9.2578125 -2.607421875 9.2578125 -0.869140625Q9.2578125 0.341796875 8.564453125 1.1767578125Q7.87109375 2.01171875 6.591796875 2.333984375Z'/>",
    '4': "<path d='M6.58203125 -2.666015625 1.6015625 5.1171875H6.58203125ZM6.064453125 -4.384765625H8.544921875V5.1171875H10.625V6.7578125H8.544921875V10.1953125H6.58203125V6.7578125H0.0V4.853515625Z'/>",
    '5': "<path d='M0.615234375 -4.384765625H8.359375V-2.724609375H2.421875V0.849609375Q2.8515625 0.703125 3.28125 0.6298828125Q3.7109375 0.556640625 4.140625 0.556640625Q6.58203125 0.556640625 8.0078125 1.89453125Q9.43359375 3.232421875 9.43359375 5.517578125Q9.43359375 7.87109375 7.96875 9.1748046875Q6.50390625 10.478515625 3.837890625 10.478515625Q2.919921875 10.478515625 1.9677734375 10.322265625Q1.015625 10.166015625 0.0 9.853515625V7.87109375Q0.87890625 8.349609375 1.81640625 8.583984375Q2.75390625 8.818359375 3.798828125 8.818359375Q5.48828125 8.818359375 6.474609375 7.9296875Q7.4609375 7.041015625 7.4609375 5.517578125Q7.4609375 3.994140625 6.474609375 3.10546875Q5.48828125 2.216796875 3.798828125 2.216796875Q3.0078125 2.216796875 2.2216796875 2.392578125Q1.435546875 2.568359375 0.615234375 2.939453125Z'/>",
    '6': "<path d='M5.205078125 2.119140625Q3.876953125 2.119140625 3.1005859375 3.02734375Q2.32421875 3.935546875 2.32421875 5.517578125Q2.32421875 7.08984375 3.1005859375 8.0029296875Q3.876953125 8.916015625 5.205078125 8.916015625Q6.533203125 8.916015625 7.3095703125 8.0029296875Q8.0859375 7.08984375 8.0859375 5.517578125Q8.0859375 3.935546875 7.3095703125 3.02734375Q6.533203125 2.119140625 5.205078125 2.119140625ZM9.12109375 -4.0625V-2.265625Q8.37890625 -2.6171875 7.6220703125 -2.802734375Q6.865234375 -2.98828125 6.123046875 -2.98828125Q4.169921875 -2.98828125 3.1396484375 -1.669921875Q2.109375 -0.3515625 1.962890625 2.314453125Q2.5390625 1.46484375 3.408203125 1.0107421875Q4.27734375 0.556640625 5.322265625 0.556640625Q7.51953125 0.556640625 8.7939453125 1.8896484375Q10.068359375 3.22265625 10.068359375 5.517578125Q10.068359375 7.763671875 8.740234375 9.12109375Q7.412109375 10.478515625 5.205078125 10.478515625Q2.67578125 10.478515625 1.337890625 8.5400390625Q0.0 6.6015625 0.0 2.919921875Q0.0 -0.537109375 1.640625 -2.5927734375Q3.28125 -4.6484375 6.044921875 -4.6484375Q6.787109375 -4.6484375 7.5439453125 -4.501953125Q8.30078125 -4.35546875 9.12109375 -4.0625Z'/>",
    '7': "<path d='M0.0 -4.384765625H9.375V-3.544921875L4.08203125 10.1953125H2.021484375L7.001953125 -2.724609375H0.0Z'/>",
    '8': "<path d='M5.0 3.271484375Q3.59375 3.271484375 2.7880859375 4.0234375Q1.982421875 4.775390625 1.982421875 6.09375Q1.982421875 7.412109375 2.7880859375 8.1640625Q3.59375 8.916015625 5.0 8.916015625Q6.40625 8.916015625 7.216796875 8.1591796875Q8.02734375 7.40234375 8.02734375 6.09375Q8.02734375 4.775390625 7.2216796875 4.0234375Q6.416015625 3.271484375 5.0 3.271484375ZM3.02734375 2.431640625Q1.7578125 2.119140625 1.0498046875 1.25Q0.341796875 0.380859375 0.341796875 -0.869140625Q0.341796875 -2.6171875 1.5869140625 -3.6328125Q2.83203125 -4.6484375 5.0 -4.6484375Q7.177734375 -4.6484375 8.41796875 -3.6328125Q9.658203125 -2.6171875 9.658203125 -0.869140625Q9.658203125 0.380859375 8.9501953125 1.25Q8.2421875 2.119140625 6.982421875 2.431640625Q8.408203125 2.763671875 9.2041015625 3.73046875Q10.0 4.697265625 10.0 6.09375Q10.0 8.212890625 8.7060546875 9.345703125Q7.412109375 10.478515625 5.0 10.478515625Q2.587890625 10.478515625 1.2939453125 9.345703125Q0.0 8.212890625 0.0 6.09375Q0.0 4.697265625 0.80078125 3.73046875Q1.6015625 2.763671875 3.02734375 2.431640625ZM2.3046875 -0.68359375Q2.3046875 0.44921875 3.0126953125 1.083984375Q3.720703125 1.71875 5.0 1.71875Q6.26953125 1.71875 6.9873046875 1.083984375Q7.705078125 0.44921875 7.705078125 -0.68359375Q7.705078125 -1.81640625 6.9873046875 -2.451171875Q6.26953125 -3.0859375 5.0 -3.0859375Q3.720703125 -3.0859375 3.0126953125 -2.451171875Q2.3046875 -1.81640625 2.3046875 -0.68359375Z'/>",
    '9': "<path d='M0.9375 9.892578125V8.095703125Q1.6796875 8.447265625 2.44140625 8.6328125Q3.203125 8.818359375 3.935546875 8.818359375Q5.888671875 8.818359375 6.9189453125 7.5048828125Q7.94921875 6.19140625 8.095703125 3.515625Q7.529296875 4.35546875 6.66015625 4.8046875Q5.791015625 5.25390625 4.736328125 5.25390625Q2.548828125 5.25390625 1.2744140625 3.9306640625Q0.0 2.607421875 0.0 0.3125Q0.0 -1.93359375 1.328125 -3.291015625Q2.65625 -4.6484375 4.86328125 -4.6484375Q7.392578125 -4.6484375 8.7255859375 -2.7099609375Q10.05859375 -0.771484375 10.05859375 2.919921875Q10.05859375 6.3671875 8.4228515625 8.4228515625Q6.787109375 10.478515625 4.0234375 10.478515625Q3.28125 10.478515625 2.51953125 10.33203125Q1.7578125 10.185546875 0.9375 9.892578125ZM4.86328125 3.7109375Q6.19140625 3.7109375 6.9677734375 2.802734375Q7.744140625 1.89453125 7.744140625 0.3125Q7.744140625 -1.259765625 6.9677734375 -2.1728515625Q6.19140625 -3.0859375 4.86328125 -3.0859375Q3.53515625 -3.0859375 2.7587890625 -2.1728515625Q1.982421875 -1.259765625 1.982421875 0.3125Q1.982421875 1.89453125 2.7587890625 2.802734375Q3.53515625 3.7109375 4.86328125 3.7109375Z'/>",
    '0': "<path d='M5.0390625 -3.0859375Q3.515625 -3.0859375 2.7490234375 -1.5869140625Q1.982421875 -0.087890625 1.982421875 2.919921875Q1.982421875 5.91796875 2.7490234375 7.4169921875Q3.515625 8.916015625 5.0390625 8.916015625Q6.572265625 8.916015625 7.3388671875 7.4169921875Q8.10546875 5.91796875 8.10546875 2.919921875Q8.10546875 -0.087890625 7.3388671875 -1.5869140625Q6.572265625 -3.0859375 5.0390625 -3.0859375ZM5.0390625 -4.6484375Q7.490234375 -4.6484375 8.7841796875 -2.7099609375Q10.078125 -0.771484375 10.078125 2.919921875Q10.078125 6.6015625 8.7841796875 8.5400390625Q7.490234375 10.478515625 5.0390625 10.478515625Q2.587890625 10.478515625 1.2939453125 8.5400390625Q0.0 6.6015625 0.0 2.919921875Q0.0 -0.771484375 1.2939453125 -2.7099609375Q2.587890625 -4.6484375 5.0390625 -4.6484375Z'/>",
    '10': "<path d='M-0.6787109375 8.53515625H2.5439453125V-2.587890625L-0.9619140625 -1.884765625V-3.681640625L2.5244140625 -4.384765625H4.4970703125V8.53515625H7.7197265625V10.1953125H-0.6787109375ZM15.9228515625 -3.0859375Q14.3994140625 -3.0859375 13.6328125 -1.5869140625Q12.8662109375 -0.087890625 12.8662109375 2.919921875Q12.8662109375 5.91796875 13.6328125 7.4169921875Q14.3994140625 8.916015625 15.9228515625 8.916015625Q17.4560546875 8.916015625 18.22265625 7.4169921875Q18.9892578125 5.91796875 18.9892578125 2.919921875Q18.9892578125 -0.087890625 18.22265625 -1.5869140625Q17.4560546875 -3.0859375 15.9228515625 -3.0859375ZM15.9228515625 -4.6484375Q18.3740234375 -4.6484375 19.66796875 -2.7099609375Q20.9619140625 -0.771484375 20.9619140625 2.919921875Q20.9619140625 6.6015625 19.66796875 8.5400390625Q18.3740234375 10.478515625 15.9228515625 10.478515625Q13.4716796875 10.478515625 12.177734375 8.5400390625Q10.8837890625 6.6015625 10.8837890625 2.919921875Q10.8837890625 -0.771484375 12.177734375 -2.7099609375Q13.4716796875 -4.6484375 15.9228515625 -4.6484375Z'/>",

}

def get_coord_svg(label, x, y, size, color, opacity=1.0):
    """Return an SVG <g> element for a coordinate label using a path from COORD_SVG_PATHS."""
    if label not in COORD_SVG_PATHS:
        return None
    group = ET.Element("g", {
        "transform": f"translate({x},{y}) scale({size/32.0})",
        "fill": color,
        "stroke": color,
        "opacity": str(opacity),
    })
    group.append(ET.fromstring(COORD_SVG_PATHS[label]))
    return group


def board(css, board=None, orientation=True, flipped=False, check=None, lastmove=None, arrows=(), squares=None, width=None, height=None, colors=None, coordinates=False, borders=False, background_image=None):
    orientation ^= flipped
    inner_border = 1 if borders and coordinates else 0
    outer_border = 1 if borders else 0
    margin = 15 if coordinates else 0
    # full_size = 2 * outer_border + 2 * margin + 2 * inner_border + 8 * SQUARE_SIZE

    svg = _svg(board.cols * SQUARE_SIZE, board.rows * SQUARE_SIZE, width, height)
    if colors:
        ET.SubElement(svg, "style").text = _colors_to_css(colors)

    if lastmove:
        lastmove_from = (board.rows - square_rank(lastmove.from_square) - 1, square_file(lastmove.from_square))
        lastmove_to = (board.rows - square_rank(lastmove.to_square) - 1 , square_file(lastmove.to_square))

    defs = ET.SubElement(svg, "defs")
    if board:
        for symbol in SVG_PIECES[css]:
            defs.append(ET.fromstring(SVG_PIECES[css][symbol]))

    if squares:
        defs.append(ET.fromstring(XX))

    if check is not None:
        defs.append(ET.fromstring(CHECK_GRADIENT))
        check_rank_index = board.rows - square_rank(check) - 1
        check_file_index = square_file(check)

    # Render board background image if provided
    if background_image:
        if background_image.lower().endswith('.svg'):
            # Embed SVG background directly
            bg_path = os.path.join('pychess-variants/static/images/board', background_image)
            try:
                with open(bg_path, 'r', encoding='utf-8') as f:
                    bg_svg = f.read()
                # Remove XML declaration if present
                if bg_svg.startswith('<?xml'):
                    bg_svg = bg_svg.split('?>', 1)[-1]
                # Parse the SVG and extract width/height or viewBox
                bg_tree = ET.fromstring(bg_svg)
                if bg_tree.tag.endswith('svg'):
                    width = bg_tree.get('width')
                    height = bg_tree.get('height')
                    viewBox = bg_tree.get('viewBox')
                    if width and height:
                        try:
                            width_val = float(width.replace('px',''))
                            height_val = float(height.replace('px',''))
                        except Exception:
                            width_val = board.cols * SQUARE_SIZE
                            height_val = board.rows * SQUARE_SIZE
                    elif viewBox:
                        parts = viewBox.strip().split()
                        width_val = float(parts[2])
                        height_val = float(parts[3])
                    else:
                        width_val = board.cols * SQUARE_SIZE
                        height_val = board.rows * SQUARE_SIZE
                    # Remove <svg> wrapper, keep children
                    bg_inner = list(bg_tree)
                    bg_group = ET.Element('g')
                    for elem in bg_inner:
                        bg_group.append(elem)
                    scale_x = (board.cols * SQUARE_SIZE) / width_val
                    scale_y = (board.rows * SQUARE_SIZE) / height_val
                    bg_group.set('transform', f'translate({margin}, {margin}) scale({scale_x}, {scale_y})')
                    svg.insert(1, bg_group)
                else:
                    # fallback: insert as a group
                    bg_elem = ET.fromstring(f'<g>{bg_svg}</g>')
                    svg.insert(1, bg_elem)
            except Exception as e:
                print(f"ERROR: Could not embed SVG background: {e}")
        else:
            # Use <image> for PNG/JPG, embed as data URI
            import base64
            img_path = os.path.join('pychess-variants/static/images/board', background_image)
            try:
                with open(img_path, 'rb') as img_file:
                    img_bytes = img_file.read()
                ext = os.path.splitext(background_image)[1].lower()
                if ext == '.jpg' or ext == '.jpeg':
                    mime = 'image/jpeg'
                elif ext == '.png':
                    mime = 'image/png'
                else:
                    mime = 'application/octet-stream'
                data_uri = f"data:{mime};base64," + base64.b64encode(img_bytes).decode('ascii')
                ET.SubElement(svg, "image", {
                    "{http://www.w3.org/1999/xlink}href": data_uri,
                    "x": str(margin),
                    "y": str(margin),
                    "width": str(board.cols * SQUARE_SIZE),
                    "height": str(board.rows * SQUARE_SIZE),
                    "preserveAspectRatio": "none"
                })
            except Exception as e:
                print(f"ERROR: Could not embed PNG/JPG background: {e}")
        render_squares = False
    else:
        render_squares = True

    # Adjust SVG viewBox and size to include margin for coordinates
    if coordinates:
        total_width = board.cols * SQUARE_SIZE + 2 * margin
        total_height = board.rows * SQUARE_SIZE + 2 * margin
        svg.set("viewBox", f"0 0 {total_width} {total_height}")
        if width is not None:
            svg.set("width", str(total_width))
        if height is not None:
            svg.set("height", str(total_height))

    # Render board squares only if not using a background image
    if render_squares:
        for y_index in range(board.rows):
            for x_index in range(board.cols):
                if orientation:
                    display_row = y_index
                    display_col = x_index
                else:
                    display_row = board.rows - y_index - 1
                    display_col = board.cols - x_index - 1
                x = (x_index) * SQUARE_SIZE + (margin if coordinates else 0)
                y = (y_index) * SQUARE_SIZE + (margin if coordinates else 0)

                cls = ["square", "light" if display_col % 2 == display_row % 2 else "dark"]
                if lastmove and (display_row, display_col) in (lastmove_from, lastmove_to):
                    cls.append("lastmove")
                fill_color = DEFAULT_COLORS[" ".join(cls)]

                ET.SubElement(svg, "rect", {
                    "x": str(x),
                    "y": str(y),
                    "width": str(SQUARE_SIZE),
                    "height": str(SQUARE_SIZE),
                    "class": " ".join(cls),
                    "stroke": "none",
                    "fill": fill_color,
                })

                # Render selected squares.
                if squares and (display_row, display_col) in parse_squares(board, squares):
                    ET.SubElement(svg, "use", _attrs({
                        "href": "#xx",
                        "xlink:href": "#xx",
                        "x": x,
                        "y": y,
                    }))

    # Render coordinates using SVG path glyphs for robustness
    if coordinates:
        coord_size = int(margin * 0.9)
        text_color = DEFAULT_COLORS["coord"]
        offset = 5
        # Center coordinates in the margin area for files (bottom/top)
        for file_index in range(board.cols):
            index = file_index if orientation else board.cols - file_index - 1
            file_char = pychess.COORDS[coordinates][0](index, board.cols)
            x = file_index * SQUARE_SIZE + margin + SQUARE_SIZE // 2 - coord_size // 2 + offset
            y_top = margin // 2 - coord_size // 2 + offset
            y_bottom = margin + board.rows * SQUARE_SIZE + margin // 2 - coord_size // 2 + offset
            for y in (y_top, y_bottom):
                coord_g = get_coord_svg(file_char, x, y, coord_size, text_color)
                if coord_g is not None:
                    svg.append(coord_g)
        # Center coordinates in the margin area for ranks (left/right)
        for rank_index in range(board.rows):
            index = rank_index if orientation else board.rows - rank_index - 1
            rank_char = pychess.COORDS[coordinates][1](index, board.rows)
            y = rank_index * SQUARE_SIZE + margin + SQUARE_SIZE // 2 - coord_size // 2 + offset
            x_left = margin // 2 - coord_size // 2 + offset
            x_right = margin + board.cols * SQUARE_SIZE + margin // 2 - coord_size // 2 + offset
            for x in (x_left, x_right):
                coord_g = get_coord_svg(rank_char, x, y, coord_size, text_color)
                if coord_g is not None:
                    svg.append(coord_g)
    # Render pieces
    if board is not None:
        for y_index in range(board.rows):
            for x_index in range(board.cols):
                if orientation:
                    display_row = y_index
                    display_col = x_index
                else:
                    display_row = board.rows - y_index - 1
                    display_col = board.cols - x_index - 1
                x = x_index * SQUARE_SIZE + (margin if coordinates else 0)
                y = y_index * SQUARE_SIZE + (margin if coordinates else 0)
                piece = board.piece_at(display_row, display_col)
                if piece:
                    # Render check mark.
                    if (check is not None) and check_file_index == display_col and check_rank_index == display_row:
                        ET.SubElement(svg, "rect", _attrs({
                            "x": x,
                            "y": y,
                            "width": SQUARE_SIZE,
                            "height": SQUARE_SIZE,
                            "class": "check",
                            "fill": "url(#check_gradient)",
                        }))

                    color = pychess.COLOR_NAMES[piece.color]
                    href = "#%s-%s-piece" % (color, piece.symbol)
                    ET.SubElement(svg, "use", {
                        "xlink:href": href,
                        "transform": "translate(%d, %d)" % (x, y),
                    })

    # Render arrows.
    for arrow in arrows:
        try:
            tail, head, color = arrow.tail, arrow.head, arrow.color  # type: ignore
        except AttributeError:
            tail, head = arrow  # type: ignore
            color = "green"

        try:
            color, opacity = _select_color(colors, " ".join(["arrow", color]))
        except KeyError:
            opacity = 1.0

        tail_file = square_file(tail)
        tail_rank = square_rank(tail)
        head_file = square_file(head)
        head_rank = square_rank(head)

        x_corr = board.cols - 0.5
        y_corr = board.rows - 0.5

        xtail = outer_border + (margin if coordinates else 0) + inner_border + (tail_file + 0.5 if orientation else x_corr - tail_file) * SQUARE_SIZE
        ytail = outer_border + (margin if coordinates else 0) + inner_border + (y_corr - tail_rank if orientation else tail_rank + 0.5) * SQUARE_SIZE
        xhead = outer_border + (margin if coordinates else 0) + inner_border + (head_file + 0.5 if orientation else x_corr - head_file) * SQUARE_SIZE
        yhead = outer_border + (margin if coordinates else 0) + inner_border + (y_corr - head_rank if orientation else head_rank + 0.5) * SQUARE_SIZE

        if (head_file, head_rank) == (tail_file, tail_rank):
            ET.SubElement(svg, "circle", _attrs({
                "cx": xhead,
                "cy": yhead,
                "r": SQUARE_SIZE * 0.93 / 2,
                "stroke-width": SQUARE_SIZE * 0.07,
                "stroke": color,
                "opacity": opacity if opacity < 1.0 else None,
                "fill": "none",
                "class": "circle",
            }))
        else:
            marker_size = 0.75 * SQUARE_SIZE
            marker_margin = 0.1 * SQUARE_SIZE

            dx, dy = xhead - xtail, yhead - ytail
            hypot = math.hypot(dx, dy)

            shaft_x = xhead - dx * (marker_size + marker_margin) / hypot
            shaft_y = yhead - dy * (marker_size + marker_margin) / hypot

            xtip = xhead - dx * marker_margin / hypot
            ytip = yhead - dy * marker_margin / hypot

            ET.SubElement(svg, "line", _attrs({
                "x1": xtail,
                "y1": ytail,
                "x2": shaft_x,
                "y2": shaft_y,
                "stroke": color,
                "opacity": opacity if opacity < 1.0 else None,
                "stroke-width": SQUARE_SIZE * 0.2,
                "stroke-linecap": "butt",
                "class": "arrow",
            }))

            marker = [(xtip, ytip),
                      (shaft_x + dy * 0.5 * marker_size / hypot,
                       shaft_y - dx * 0.5 * marker_size / hypot),
                      (shaft_x - dy * 0.5 * marker_size / hypot,
                       shaft_y + dx * 0.5 * marker_size / hypot)]

            ET.SubElement(svg, "polygon", _attrs({
                "points": " ".join(f"{x},{y}" for x, y in marker),
                "fill": color,
                "opacity": opacity if opacity < 1.0 else None,
                "class": "arrow",
            }))

    return SvgWrapper(ET.tostring(svg).decode("utf-8"))
