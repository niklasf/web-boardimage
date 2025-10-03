web-boardimage
==============

An HTTP service that renders chess board images.

Installation
------------

Requires Python, [uv](https://docs.astral.sh/uv/), and these libraries:

```
sudo apt-get install python3-dev libffi-dev libxml2-dev libxslt1-dev libcairo2
```

Usage
-----

```
uv run python server.py [--port 8080] [--bind 127.0.0.1]
```

HTTP API
--------

### `GET /board.svg` render an SVG

name | type | default | description
--- | --- | --- | ---
**fen** | string | required | FEN of the position with at least the board part
**orientation** | string | white | `white` or `black`
**size** | int | 360 | The width and height of the image
**lastMove** | string | *(none)* | The last move to highlight, e.g., `f4g6`
**check** | string | *(none)* | A square to highlight for check, e.g., `h8`
**arrows** | string | *(none)* | Draw arrows and circles, e.g., `Ge6g8,Bh7`, possible color prefixes: `G`, `B`, `R`, `Y`
**squares** | string | *(none)* | Marked squares, e.g., `a3,c3`
**coordinates** | bool | *false* | Show a coordinate margin
**colors** | string | lichess-brown | Theme: `wikipedia`, `lichess-brown`, `lichess-blue`

```
https://backscattering.de/web-boardimage/board.svg?fen=5r1k/1b4pp/3pB1N1/p2Pq2Q/PpP5/6PK/8/8&lastMove=f4g6&check=h8&arrows=Ge6g8,Bh7&squares=a3,c3
```

![example board image](https://backscattering.de/web-boardimage/board.svg?fen=5r1k/1b4pp/3pB1N1/p2Pq2Q/PpP5/6PK/8/8&lastMove=f4g6&check=h8&arrows=Ge6g8,Bh7&squares=a3,c3)

### `GET /board.png` render a PNG

License
-------

web-boardimage is licensed under the AGPLv3+. See LICENSE.txt for the full
license text.
