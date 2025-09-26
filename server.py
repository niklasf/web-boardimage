#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# web-boardimage is an HTTP service that renders chess board images.
# Copyright (C) 2016-2017 Niklas Fiekas <niklas.fiekas@backscattering.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""An HTTP service that renders chess board images"""

import argparse
import asyncio
import aiohttp.web
import chess
import chess.svg
import cairosvg
import json
import os
import re


def load_theme(name):
    with open(os.path.join(os.path.dirname(__file__), "themes", f"{name}.json")) as f:
        return json.load(f)


THEMES = {name: load_theme(name) for name in ["wikipedia", "lichess-blue", "lichess-brown"]}


class Service:
    def make_svg(self, request):
        try:
            board = chess.Board(request.query["fen"])
        except KeyError:
            raise aiohttp.web.HTTPBadRequest(reason="fen required")
        except ValueError:
            raise aiohttp.web.HTTPBadRequest(reason="invalid fen")

        try:
            size = min(max(int(request.query.get("size", 360)), 16), 1024)
        except ValueError:
            raise aiohttp.web.HTTPBadRequest(reason="size is not a number")

        try:
            uci = request.query.get("lastMove") or request.query["lastmove"]
            lastmove = chess.Move.from_uci(uci)
        except KeyError:
            lastmove = None
        except ValueError:
            raise aiohttp.web.HTTPBadRequest(reason="lastMove is not a valid uci move")

        try:
            check = chess.parse_square(request.query["check"])
        except KeyError:
            check = None
        except ValueError:
            raise aiohttp.web.HTTPBadRequest(reason="check is not a valid square name")

        try:
            arrows = [chess.svg.Arrow.from_pgn(s.strip()) for s in request.query.get("arrows", "").split(",") if s.strip()]
        except ValueError:
            raise aiohttp.web.HTTPBadRequest(reason="invalid arrow")

        try:
            squares = chess.SquareSet(chess.parse_square(s.strip()) for s in request.query.get("squares", "").split(",") if s.strip())
        except ValueError:
            raise aiohttp.web.HTTPBadRequest(reason="invalid squares")

        flipped = request.query.get("orientation", "white") == "black"

        coordinates = request.query.get("coordinates", "0") in ["", "1", "true", "True", "yes"]

        try:
            colors = THEMES[request.query.get("colors", "lichess-brown")]
        except KeyError:
            raise aiohttp.web.HTTPBadRequest(reason="theme colors not found")

        return chess.svg.board(board,
                               coordinates=coordinates,
                               flipped=flipped,
                               lastmove=lastmove,
                               check=check,
                               arrows=arrows,
                               squares=squares,
                               size=size,
                               colors=colors)

    async def render_svg(self, request):
        return aiohttp.web.Response(text=self.make_svg(request), content_type="image/svg+xml")

    async def render_png(self, request):
        svg_data = self.make_svg(request)
        png_data = cairosvg.svg2png(bytestring=svg_data)
        return aiohttp.web.Response(body=png_data, content_type="image/png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", "-p", type=int, default=8080, help="web server port")
    parser.add_argument("--bind", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    args = parser.parse_args()

    app = aiohttp.web.Application()
    service = Service()
    app.router.add_get("/board.png", service.render_png)
    app.router.add_get("/board.svg", service.render_svg)

    aiohttp.web.run_app(app, port=args.port, host=args.bind, access_log=None)
