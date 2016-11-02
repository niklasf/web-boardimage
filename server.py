import asyncio
import aiohttp.web
import chess
import chess.svg


async def render_svg(request):
    try:
        board = chess.Board(request.GET["fen"])
    except KeyError:
        raise aiohttp.web.HTTPBadRequest(reason="fen required")
    except ValueError:
        raise aiohttp.web.HTTPBadRequest(reason="invalid fen")

    return aiohttp.web.Response(
        text=chess.svg.board(board, coordinates=False),
        content_type="image/svg+xml")


if __name__ == "__main__":
    app = aiohttp.web.Application()
    app.router.add_get("/", render_svg)

    aiohttp.web.run_app(app)
