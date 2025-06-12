import pygame
import sys
from move_generator import generate_piece_moves

pygame.init()

base_path = "Assets"

pieces = {
    "p": pygame.image.load(f"{base_path}/black/pawn.png"),
    "n": pygame.image.load(f"{base_path}/black/knight.png"),
    "b": pygame.image.load(f"{base_path}/black/bishop.png"),
    "r": pygame.image.load(f"{base_path}/black/rook.png"),
    "q": pygame.image.load(f"{base_path}/black/queen.png"),
    "k": pygame.image.load(f"{base_path}/black/king.png"),
    "P": pygame.image.load(f"{base_path}/white/PAWN.png"),
    "N": pygame.image.load(f"{base_path}/white/KNIGHT.png"),
    "B": pygame.image.load(f"{base_path}/white/BISHOP.png"),
    "R": pygame.image.load(f"{base_path}/white/ROOK.png"),
    "Q": pygame.image.load(f"{base_path}/white/QUEEN.png"),
    "K": pygame.image.load(f"{base_path}/white/KING.png"),
}

for key in pieces:
    pieces[key] = pygame.transform.smoothscale(pieces[key], (85, 85))

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Chessboard Colors")

FPS = 60
clock = pygame.time.Clock()

BOARD_SIZE = 8
SQUARE_SIZE = 85
BOARD_WIDTH = BOARD_SIZE * SQUARE_SIZE
BOARD_HEIGHT = BOARD_SIZE * SQUARE_SIZE
OFFSET_X = (WIDTH - BOARD_WIDTH) / 2
OFFSET_Y = (HEIGHT - BOARD_HEIGHT) / 2

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
BLACK = (0, 0, 0)

HIGHLIGHT_LIGHT = (205, 162, 82)
HIGHLIGHT_DARK = (163, 114, 41)

selected_square = None
legal_moves = []

def intrepret_fen_board(fen):
    fen = fen.split(" ")[0]
    intrepretion = ""
    for c in fen:
        if c == '/':
            continue
        if c.isdigit():
            intrepretion += "." * int(c)
        else:
            intrepretion += c
    return intrepretion

def isSelectValid(board,square,turn):
    return board[square] !="." and (board[square].isupper() and turn == "w") or (board[square].islower() and turn=="b")

def draw_chessboard(fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", flip_board=False):
    board = intrepret_fen_board(fen)
    screen.fill(BLACK)
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            draw_x = BOARD_SIZE - 1 - x if flip_board else x
            draw_y = BOARD_SIZE - 1 - y if flip_board else y

            color = LIGHT_SQUARE if (x + y) % 2 == 0 else DARK_SQUARE

            rect = pygame.Rect(
                OFFSET_X + draw_x * SQUARE_SIZE,
                OFFSET_Y + draw_y * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE
            )
            pygame.draw.rect(screen, color, rect)

            if selected_square == (x, y):
                highlight_color = HIGHLIGHT_LIGHT if (x + y) % 2 == 0 else HIGHLIGHT_DARK
                pygame.draw.rect(screen, highlight_color, rect)

            cur_piece = board[y * BOARD_SIZE + x]
            if cur_piece != '.':
                screen.blit(pieces[cur_piece], (rect.x, rect.y))

            for move in legal_moves:
                if move == (x, y):
                    center_x = rect.x + SQUARE_SIZE // 2
                    center_y = rect.y + SQUARE_SIZE // 2
                    radius = 10
                    pygame.draw.circle(screen, (80, 80, 80), (center_x, center_y), radius)


def get_square_at_pos(pos, flip_board):
    mx, my = pos
    if OFFSET_X <= mx < OFFSET_X + BOARD_WIDTH and OFFSET_Y <= my < OFFSET_Y + BOARD_HEIGHT:
        fx = int((mx - OFFSET_X) // SQUARE_SIZE)
        fy = int((my - OFFSET_Y) // SQUARE_SIZE)
        if flip_board:
            fx = BOARD_SIZE - 1 - fx
            fy = BOARD_SIZE - 1 - fy
        return (fx, fy)
    return None

def main():
    global selected_square, legal_moves
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    board = intrepret_fen_board(fen)
    flip_board = False
    running = True
    turn = "w"
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_f:
                    flip_board = not flip_board

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                sq_pos = get_square_at_pos(pos, flip_board)
                if sq_pos is not None:
                    sq = sq_pos[1] * BOARD_SIZE + sq_pos[0]
                    if isSelectValid(board,sq,turn):
                        selected_square = sq_pos
                        legal_moves = generate_piece_moves(board, turn, sq_pos)
                    else:
                        selected_square = None
                        legal_moves = []
        draw_chessboard(fen, flip_board)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
