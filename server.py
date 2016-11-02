import asyncio
import aiohttp.web
import chess
import chess.svg
import cairosvg


def make_svg(request):
    try:
        board = chess.Board(request.GET["fen"])
    except KeyError:
        raise aiohttp.web.HTTPBadRequest(reason="fen required")
    except ValueError:
        raise aiohttp.web.HTTPBadRequest(reason="invalid fen")

    try:
        size = min(max(int(request.GET.get("size", 100)), 16), 1024)
    except ValueError:
        raise aiohttp.web.HTTPBadRequest(reason="size must be a number")

    lastmove = None
    if "lastmove" in request.GET:
        try:
            lastmove = chess.Move.from_uci(request.GET["lastmove"])
        except ValueError:
            raise aiohttp.web.HTTPBadRequest(reason="lastmove not a valid uci move")

    return chess.svg.board(board, coordinates=False, lastmove=lastmove, size=size)


async def render_svg(request):
    return aiohttp.web.Response(text=make_svg(request), content_type="image/svg+xml")


async def render_png(request):
    svg_data = make_svg(request)
    buf = cairosvg.svg2png(bytestring=svg_data)
    return aiohttp.web.Response(body=buf, content_type="image/png")


if __name__ == "__main__":
    app = aiohttp.web.Application()
    app.router.add_get("/", render_png)
    app.router.add_get("/svg", render_svg)

    aiohttp.web.run_app(app)
