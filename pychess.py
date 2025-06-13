import string
from pychess_svg import get_svg_pieces_from_css, read_piece_svg, SVG_PIECES

COLORS = [WHITE, BLACK] = [True, False]
COLOR_NAMES = ["black", "white"]

PIECE_TYPES = range(len(string.ascii_lowercase))
PIECE_LETTERS = string.ascii_lowercase


class Arrow:
    def __init__(self, tail, head, color="green"):
        self.tail = tail
        self.head = head
        self.color = color

    @classmethod
    def from_pgn(cls, pgn):
        if pgn.startswith("G"):
            color = "green"
            pgn = pgn[1:]
        elif pgn.startswith("R"):
            color = "red"
            pgn = pgn[1:]
        elif pgn.startswith("Y"):
            color = "yellow"
            pgn = pgn[1:]
        elif pgn.startswith("B"):
            color = "blue"
            pgn = pgn[1:]
        else:
            color = "green"

        if len(pgn) > 2 and pgn[2].isdigit():
            # rank > 9
            tail = pgn[:3]
            head = pgn[3:] if len(pgn) > 3 else tail
        else:
            tail = pgn[:2]
            head = pgn[2:] if len(pgn) > 2 else tail
        return cls(tail, head, color=color)

    def __repr__(self):
        return "%s%s%s" % (self.color[0].upper(), self.head, self.tail)


class Piece:
    def __init__(self, piece_type, color):
        self.piece_type = piece_type
        self.color = color
        self.promoted = False

    @property
    def symbol(self):
        promoted = "p" if self.promoted else ""
        if self.color == WHITE:
            return promoted + PIECE_LETTERS[self.piece_type].upper()
        else:
            return promoted + PIECE_LETTERS[self.piece_type]

    @classmethod
    def from_letter(cls, letter):
        if letter.islower():
            return cls(PIECE_LETTERS.index(letter), BLACK)
        else:
            return cls(PIECE_LETTERS.index(letter.lower()), WHITE)

    def __repr__(self):
        return self.symbol

    def __str__(self):
        return self.symbol


class Move:
    def __init__(self, from_square, to_square, promotion=None, drop=None):
        self.from_square = from_square
        self.to_square = to_square
        self.promotion = promotion
        self.drop = drop

    @classmethod
    def from_uci(cls, uci):
        if "@" == uci[1]:
            drop = PIECE_LETTERS.index(uci[0].lower())
            square = uci[2:]
            return cls(square, square, drop=drop)
        elif 4 <= len(uci) <= 5:
            if uci[-1].islower():
                promotion = PIECE_LETTERS.index(uci[-1])
                uci = uci[:-1]
            else:
                promotion = None

            if uci[2].isdigit():
                from_square = uci[0:3]
                to_square = uci[3:]
            else:
                from_square = uci[0:2]
                to_square = uci[2:]
            return cls(from_square, to_square, promotion=promotion)


class Board:
    def __init__(self, board_fen, css, rows=8, cols=8):
        self.pieces = {}
        self.rows = rows
        self.cols = cols
        if board_fen is None:
            self.clear_board()
        else:
            self.set_board_fen(css, board_fen)

    def contains_piece(self, piece_type, color):
        for piece in self.pieces.values():
            if piece.piece_type == piece_type and piece.color == color:
                return True
        return False

    def piece_at(self, row, col):
        return self.pieces.get((row, col))

    def set_board_fen(self, css, fen):
        if css not in SVG_PIECES:
            get_svg_pieces_from_css(css)

        fen = fen.strip()
        rows = fen.split("/")

        # Clear the board.
        self.pieces = {}

        # Put pieces on the board.
        for row_index, row in enumerate(rows):
            col_index = 0
            promoted_plus = False
            for c in row:
                try:
                    col_index += int(c)
                except ValueError:
                    if c not in "~+":
                        piece = Piece.from_letter(c)
                        if promoted_plus:
                            piece.promoted = True
                            promoted_plus = False

                        self.pieces[(row_index, col_index)] = piece
                        col_index += 1

                        # Read piece SVG
                        if piece.symbol not in SVG_PIECES[css]:
                            read_piece_svg(css, piece)
                    else:
                        if c == "~":
                            piece.promoted = True
                            if piece.symbol not in SVG_PIECES[css]:
                                read_piece_svg(css, piece)
                        if c == "+":
                            promoted_plus = True

        self.rows = len(rows)
        self.cols = col_index
