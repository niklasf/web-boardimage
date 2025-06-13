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

COORDS = {
    "1": """<path d="M6.754 26.996h2.578v-8.898l-2.805.562v-1.437l2.79-.563h1.578v10.336h2.578v1.328h-6.72z"/>""",  # noqa: E501
    "2": """<path d="M8.195 26.996h5.508v1.328H6.297v-1.328q.898-.93 2.445-2.492 1.555-1.57 1.953-2.024.758-.851 1.055-1.437.305-.594.305-1.164 0-.93-.657-1.516-.648-.586-1.695-.586-.742 0-1.57.258-.82.258-1.758.781v-1.593q.953-.383 1.781-.578.828-.196 1.516-.196 1.812 0 2.89.906 1.079.907 1.079 2.422 0 .72-.274 1.368-.265.64-.976 1.515-.196.227-1.243 1.313-1.046 1.078-2.953 3.023z"/>""",  # noqa: E501
    "3": """<path d="M11.434 22.035q1.132.242 1.765 1.008.64.766.64 1.89 0 1.727-1.187 2.672-1.187.946-3.375.946-.734 0-1.515-.149-.774-.14-1.602-.43V26.45q.656.383 1.438.578.78.196 1.632.196 1.485 0 2.258-.586.782-.586.782-1.703 0-1.032-.727-1.61-.719-.586-2.008-.586h-1.36v-1.297h1.423q1.164 0 1.78-.46.618-.47.618-1.344 0-.899-.64-1.375-.633-.485-1.82-.485-.65 0-1.391.141-.743.14-1.633.437V16.95q.898-.25 1.68-.375.788-.125 1.484-.125 1.797 0 2.844.82 1.046.813 1.046 2.204 0 .968-.554 1.64-.555.664-1.578.922z"/>""",  # noqa: E501
    "4": """<path d="M11.016 18.035L7.03 24.262h3.985zm-.414-1.375h1.984v7.602h1.664v1.312h-1.664v2.75h-1.57v-2.75H5.75v-1.523z"/>""",  # noqa: E501
    "5": """<path d="M6.719 16.66h6.195v1.328h-4.75v2.86q.344-.118.688-.172.343-.063.687-.063 1.953 0 3.094 1.07 1.14 1.07 1.14 2.899 0 1.883-1.171 2.93-1.172 1.039-3.305 1.039-.735 0-1.5-.125-.758-.125-1.57-.375v-1.586q.703.383 1.453.57.75.188 1.586.188 1.351 0 2.14-.711.79-.711.79-1.93 0-1.219-.79-1.93-.789-.71-2.14-.71-.633 0-1.266.14-.625.14-1.281.438z"/>""",  # noqa: E501
    "6": """<path d="M10.137 21.863q-1.063 0-1.688.727-.617.726-.617 1.992 0 1.258.617 1.992.625.727 1.688.727 1.062 0 1.68-.727.624-.734.624-1.992 0-1.266-.625-1.992-.617-.727-1.68-.727zm3.133-4.945v1.437q-.594-.28-1.204-.43-.601-.148-1.195-.148-1.562 0-2.39 1.055-.82 1.055-.938 3.188.46-.68 1.156-1.04.696-.367 1.531-.367 1.758 0 2.774 1.07 1.023 1.063 1.023 2.899 0 1.797-1.062 2.883-1.063 1.086-2.828 1.086-2.024 0-3.094-1.547-1.07-1.555-1.07-4.5 0-2.766 1.312-4.406 1.313-1.649 3.524-1.649.593 0 1.195.117.61.118 1.266.352z"/>""",  # noqa: E501
    "7": """<path d="M6.25 16.66h7.5v.672L9.516 28.324H7.867l3.985-10.336H6.25z"/>""",  # noqa: E501
    "8": """<path d="M10 22.785q-1.125 0-1.773.602-.641.601-.641 1.656t.64 1.656q.649.602 1.774.602t1.773-.602q.649-.61.649-1.656 0-1.055-.649-1.656-.64-.602-1.773-.602zm-1.578-.672q-1.016-.25-1.586-.945-.563-.695-.563-1.695 0-1.399.993-2.211 1-.813 2.734-.813 1.742 0 2.734.813.993.812.993 2.21 0 1-.57 1.696-.563.695-1.571.945 1.14.266 1.773 1.04.641.773.641 1.89 0 1.695-1.04 2.602-1.03.906-2.96.906t-2.969-.906Q6 26.738 6 25.043q0-1.117.64-1.89.641-.774 1.782-1.04zm-.578-2.492q0 .906.562 1.414.57.508 1.594.508 1.016 0 1.586-.508.578-.508.578-1.414 0-.906-.578-1.414-.57-.508-1.586-.508-1.023 0-1.594.508-.562.508-.562 1.414z"/>""",  # noqa: E501
    "a": """<path d="M23.328 10.016q-1.742 0-2.414.398-.672.398-.672 1.36 0 .765.5 1.218.508.445 1.375.445 1.196 0 1.914-.843.727-.852.727-2.258v-.32zm2.867-.594v4.992h-1.437v-1.328q-.492.797-1.227 1.18-.734.375-1.797.375-1.343 0-2.14-.75-.79-.758-.79-2.024 0-1.476.985-2.226.992-.75 2.953-.75h2.016V8.75q0-.992-.656-1.531-.649-.547-1.829-.547-.75 0-1.46.18-.711.18-1.368.539V6.062q.79-.304 1.532-.453.742-.156 1.445-.156 1.898 0 2.836.984.937.985.937 2.985z"/>""",  # noqa: E501
    "b": """<path d="M24.922 10.047q0-1.586-.656-2.485-.649-.906-1.79-.906-1.14 0-1.796.906-.649.899-.649 2.485 0 1.586.649 2.492.656.898 1.797.898 1.14 0 1.789-.898.656-.906.656-2.492zm-4.89-3.055q.452-.781 1.14-1.156.695-.383 1.656-.383 1.594 0 2.586 1.266 1 1.265 1 3.328 0 2.062-1 3.328-.992 1.266-2.586 1.266-.96 0-1.656-.375-.688-.383-1.14-1.164v1.312h-1.446V2.258h1.445z"/>""",  # noqa: E501
    "c": """<path d="M25.96 6v1.344q-.608-.336-1.226-.5-.609-.172-1.234-.172-1.398 0-2.172.89-.773.883-.773 2.485 0 1.601.773 2.492.774.883 2.172.883.625 0 1.234-.164.618-.172 1.227-.508v1.328q-.602.281-1.25.422-.64.14-1.367.14-1.977 0-3.14-1.242-1.165-1.242-1.165-3.351 0-2.14 1.172-3.367 1.18-1.227 3.227-1.227.664 0 1.296.14.633.134 1.227.407z"/>""",  # noqa: E501
    "d": """<path d="M24.973 6.992V2.258h1.437v12.156h-1.437v-1.312q-.453.78-1.149 1.164-.687.375-1.656.375-1.586 0-2.586-1.266-.992-1.266-.992-3.328 0-2.063.992-3.328 1-1.266 2.586-1.266.969 0 1.656.383.696.375 1.149 1.156zm-4.899 3.055q0 1.586.649 2.492.656.898 1.797.898 1.14 0 1.796-.898.657-.906.657-2.492 0-1.586-.657-2.485-.656-.906-1.796-.906-1.141 0-1.797.906-.649.899-.649 2.485z"/>""",  # noqa: E501
    "e": """<path d="M26.555 9.68v.703h-6.61q.094 1.484.89 2.265.806.774 2.235.774.828 0 1.602-.203.781-.203 1.547-.61v1.36q-.774.328-1.586.5-.813.172-1.649.172-2.093 0-3.32-1.22-1.219-1.218-1.219-3.296 0-2.148 1.157-3.406 1.164-1.266 3.132-1.266 1.766 0 2.79 1.14 1.03 1.134 1.03 3.087zm-1.438-.422q-.015-1.18-.664-1.883-.64-.703-1.703-.703-1.203 0-1.93.68-.718.68-.828 1.914z"/>""",  # noqa: E501
    "f": """<path d="M25.285 2.258v1.195H23.91q-.773 0-1.078.313-.297.312-.297 1.125v.773h2.367v1.117h-2.367v7.633H21.09V6.781h-1.375V5.664h1.375v-.61q0-1.46.68-2.124.68-.672 2.156-.672z"/>""",  # noqa: E501
    "g": """<path d="M24.973 9.937q0-1.562-.649-2.421-.64-.86-1.804-.86-1.157 0-1.805.86-.64.859-.64 2.421 0 1.555.64 2.415.648.859 1.805.859 1.164 0 1.804-.86.649-.859.649-2.414zm1.437 3.391q0 2.234-.992 3.32-.992 1.094-3.04 1.094-.757 0-1.429-.117-.672-.11-1.304-.344v-1.398q.632.344 1.25.508.617.164 1.257.164 1.414 0 2.118-.743.703-.734.703-2.226v-.711q-.446.773-1.141 1.156-.695.383-1.664.383-1.61 0-2.594-1.227-.984-1.226-.984-3.25 0-2.03.984-3.257.985-1.227 2.594-1.227.969 0 1.664.383t1.14 1.156V5.664h1.438z"/>""",  # noqa: E501
    "h": """<path d="M26.164 9.133v5.281h-1.437V9.18q0-1.243-.485-1.86-.484-.617-1.453-.617-1.164 0-1.836.742-.672.742-.672 2.024v4.945h-1.445V2.258h1.445v4.765q.516-.789 1.211-1.18.703-.39 1.617-.39 1.508 0 2.282.938.773.93.773 2.742z"/>""",  # noqa: E501
}

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
    "coord": "#e5e5e5",
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


def _coord(text: str, x: int, y: int, width: int, height: int, horizontal: bool, margin: int, *, color: str, opacity: float) -> ET.Element:
    scale = margin / MARGIN

    if horizontal:
        x += int(width - scale * width) // 2
    else:
        y += int(height - scale * height) // 2

    t = ET.Element("g", _attrs({
        "transform": f"translate({x}, {y}) scale({scale}, {scale})",
        "fill": color,
        "stroke": color,
        "opacity": opacity if opacity < 1.0 else None,
    }))
    t.append(ET.fromstring(COORDS[text]))
    return t


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
                x = (x_index) * SQUARE_SIZE + margin
                y = (y_index) * SQUARE_SIZE + margin

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
                if (display_row, display_col) in parse_squares(board, squares):
                    ET.SubElement(svg, "use", _attrs({
                        "href": "#xx",
                        "xlink:href": "#xx",
                        "x": x,
                        "y": y,
                    }))

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
                x = x_index * SQUARE_SIZE + margin
                y = y_index * SQUARE_SIZE + margin
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

        xtail = outer_border + margin + inner_border + (tail_file + 0.5 if orientation else x_corr - tail_file) * SQUARE_SIZE
        ytail = outer_border + margin + inner_border + (y_corr - tail_rank if orientation else tail_rank + 0.5) * SQUARE_SIZE
        xhead = outer_border + margin + inner_border + (head_file + 0.5 if orientation else x_corr - head_file) * SQUARE_SIZE
        yhead = outer_border + margin + inner_border + (y_corr - head_rank if orientation else head_rank + 0.5) * SQUARE_SIZE

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
