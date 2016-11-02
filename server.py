import asyncio
import aiohttp.web
import chess
import chess.svg
import cairosvg


def render_svg(request):
    try:
        board = chess.Board(request.GET["fen"])
    except KeyError:
        raise aiohttp.web.HTTPBadRequest(reason="fen required")
    except ValueError:
        raise aiohttp.web.HTTPBadRequest(reason="invalid fen")

    return chess.svg.board(board, coordinates=False)


async def render_png(request):
    svg_data = render_svg(request)
    buf = cairosvg.svg2png(bytestring=svg_data)
    return aiohttp.web.Response(body=buf, content_type="image/png")


if __name__ == "__main__":
    app = aiohttp.web.Application()
    app.router.add_get("/", render_png)

    aiohttp.web.run_app(app)
