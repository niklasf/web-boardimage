#!/usr/bin/env python

"""HTTP service that renders chess board images"""

import argparse
import asyncio
import aiohttp.web
import chess
import chess.svg
import cairosvg


def make_svg(request):
    try:
        parts = request.GET["fen"].split(" ", 1)
        board = chess.BaseBoard(parts[0])
    except KeyError:
        raise aiohttp.web.HTTPBadRequest(reason="fen required")
    except ValueError:
        raise aiohttp.web.HTTPBadRequest(reason="invalid fen")

    try:
        size = min(max(int(request.GET.get("size", 100)), 16), 1024)
    except ValueError:
        raise aiohttp.web.HTTPBadRequest(reason="size is not a number")

    try:
        lastmove = chess.Move.from_uci(request.GET["lastMove"])
    except KeyError:
        lastmove = None
    except ValueError:
        raise aiohttp.web.HTTPBadRequest(reason="lastMove is not a valid uci move")

    try:
        check = chess.SQUARE_NAMES.index(request.GET["check"])
    except KeyError:
        check = None
    except ValueError:
        raise aiohttp.web.HTTPBadRequest(reason="check is not a valid square name")

    return chess.svg.board(board, coordinates=False, lastmove=lastmove, check=check, size=size)


@asyncio.coroutine
def render_svg(request):
    return aiohttp.web.Response(text=make_svg(request), content_type="image/svg+xml")


@asyncio.coroutine
def render_png(request):
    svg_data = make_svg(request)
    png_data = cairosvg.svg2png(bytestring=svg_data)
    return aiohttp.web.Response(body=png_data, content_type="image/png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", "-p", default=8080, help="web server port")
    parser.add_argument("--bind", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    args = parser.parse_args()

    app = aiohttp.web.Application()
    app.router.add_get("/board.png", render_png)
    app.router.add_get("/board.svg", render_svg)

    aiohttp.web.run_app(app, port=args.port, host=args.bind)
