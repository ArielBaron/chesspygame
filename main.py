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
pygame.display.set_caption("Chessboard")
pygame.scrap.init()  # Enable clipboard

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
hovering_copy = False
show_copied = False
copy_timer = 0

FONT = pygame.font.SysFont("arial", 24)
SMALL_FONT = pygame.font.SysFont("arial", 20)

MOVE_SOUND = pygame.mixer.Sound(f"{base_path}/sound_effects/move-self.mp3")
CAPTURE_SOUND = pygame.mixer.Sound(f"{base_path}/sound_effects/capture.mp3")

def interpret_fen_board(fen):
    board_part = fen.split(" ")[0]
    interpretation = ""
    for c in board_part:
        if c == '/':
            continue
        if c.isdigit():
            interpretation += "." * int(c)
        else:
            interpretation += c
    return interpretation

def interpret_fen(fen):
    parts = fen.split()
    board = interpret_fen_board(fen)
    turn = parts[1]
    castling = parts[2] if len(parts) > 2 else "-"
    en_passant = parts[3] if len(parts) > 3 else "-"
    halfmove = int(parts[4]) if len(parts) > 4 else 0
    fullmove = int(parts[5]) if len(parts) > 5 else 1
    return board, turn, castling, en_passant, halfmove, fullmove

def is_select_valid(board, square, turn):
    return board[square] != "." and (
        (board[square].isupper() and turn == "w") or (board[square].islower() and turn == "b")
    )

def draw_chessboard(board, flip_board=False, last_move=None):
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

            if selected_square == (x, y) or (last_move is not None and (x, y) == last_move[0]) or (last_move is not None and (x, y) == last_move[1]):
                highlight_color = HIGHLIGHT_LIGHT if (x + y) % 2 == 0 else HIGHLIGHT_DARK
                pygame.draw.rect(screen, highlight_color, rect)

            cur_piece = board[y * BOARD_SIZE + x]
            if cur_piece != '.':
                screen.blit(pieces[cur_piece], (rect.x, rect.y))

            center_x = rect.x + SQUARE_SIZE // 2
            center_y = rect.y + SQUARE_SIZE // 2
            radius = 10
            for move in legal_moves:
                if move == (x, y):
                    pygame.draw.circle(screen, (80, 80, 80), (center_x, center_y), radius)

def to_index(pos):
    x, y = pos
    return y * 8 + x

def update_board(board, start, end):
    board = list(board)
    start_idx = to_index(start)
    end_idx = to_index(end)
    board[end_idx] = board[start_idx]
    board[start_idx] = '.'
    return ''.join(board)

def board_to_fen(board, turn, castling, en_passant, halfmove, fullmove):
    fen_rows = []
    for y in range(8):
        row = board[y * 8:(y + 1) * 8]
        fen_row = ''
        empty_count = 0
        for c in row:
            if c == '.':
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                fen_row += c
        if empty_count > 0:
            fen_row += str(empty_count)
        fen_rows.append(fen_row)
    board_part = '/'.join(fen_rows)
    return f"{board_part} {turn} {castling} {en_passant} {halfmove} {fullmove}"

def get_fen_en_passent(en_pass):  # from e4
    if en_pass == "-":
        return ()
    return (ord(en_pass[0].lower()) - ord('a'), 8 - int(en_pass[1]))

def make_fen_en_passent(en_pass):  # from (x,y)
    return chr(en_pass[0] + 97) + str(en_pass[1]) if en_pass != () else "-"

def draw_fen_display(fen):
    global hovering_copy

    x = 20
    y = 0

    label = FONT.render("FEN:", True, (255, 255, 255))
    screen.blit(label, (x, y))

    input_rect = pygame.Rect(x, y + 30, 900, 30)
    pygame.draw.rect(screen, (40, 40, 40), input_rect)
    pygame.draw.rect(screen, (200, 200, 200), input_rect, 2)

    text_surf = SMALL_FONT.render(fen, True, (255, 255, 255))
    screen.blit(text_surf, (input_rect.x + 10, input_rect.y + 5))

    button_rect = pygame.Rect(input_rect.right + 10, input_rect.y, 80, 30)
    pygame.draw.rect(screen, (60, 60, 60), button_rect)
    pygame.draw.rect(screen, (160, 160, 160), button_rect, 2)

    copy_text = SMALL_FONT.render("Copy", True, (255, 255, 255))
    screen.blit(copy_text, (button_rect.x + 15, button_rect.y + 5))

    mouse = pygame.mouse.get_pos()
    hovering_copy = button_rect.collidepoint(mouse)

    if hovering_copy:
        hover_surf = SMALL_FONT.render("Copy to clipboard", True, (200, 200, 200))
        screen.blit(hover_surf, (button_rect.x, button_rect.y - 25))

    return button_rect

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

def draw_copy_feedback(show_copied, copy_timer, button_rect):
    if show_copied and pygame.time.get_ticks() - copy_timer < 1000:
        copied_surf = SMALL_FONT.render("Copied!", True, (0, 255, 0))
        screen.blit(copied_surf, (button_rect.x, button_rect.y + 35))
        return True
    return False

def main():
    global selected_square, legal_moves, hovering_copy, show_copied, copy_timer
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    board, turn, castling, en_passant, halfmove, fullmove = interpret_fen(fen)
    en_passant = get_fen_en_passent(en_passant)
    flip_board = False
    running = True
    last_move = None

    while running:
        clock.tick(FPS)
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_f:
                    flip_board = not flip_board

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if hovering_copy:
                        pygame.scrap.put(pygame.SCRAP_TEXT, fen.encode())
                        show_copied = True
                        copy_timer = pygame.time.get_ticks()
                    else:
                        cur_sq_pos = get_square_at_pos(mouse_pos, flip_board)
                        if cur_sq_pos is not None:
                            sq = cur_sq_pos[1] * BOARD_SIZE + cur_sq_pos[0]
                            if is_select_valid(board, sq, turn):
                                selected_square = cur_sq_pos
                                legal_moves = generate_piece_moves(board, turn, cur_sq_pos, en_passant)

                            elif selected_square is not None and cur_sq_pos in legal_moves:
                                moved_piece = board[to_index(selected_square)]

                                is_en_passant = (
                                    moved_piece.lower() == 'p' and
                                    cur_sq_pos == en_passant and
                                    board[to_index(cur_sq_pos)] == '.'
                                )

                                captured = board[to_index(cur_sq_pos)] != '.' or is_en_passant

                                # Handle en passant capture
                                if is_en_passant:
                                    # Remove the captured pawn behind the en passant square
                                    capture_y = cur_sq_pos[1] + (1 if moved_piece.isupper() else -1)
                                    capture_x = cur_sq_pos[0]
                                    capture_idx = to_index((capture_x, capture_y))
                                    board = list(board)
                                    board[capture_idx] = '.'
                                    board = ''.join(board)

                                board = update_board(board, selected_square, cur_sq_pos)

                                if captured:
                                    CAPTURE_SOUND.play()
                                else:
                                    MOVE_SOUND.play()

                                # Reset or increment halfmove clock
                                if moved_piece.lower() == 'p' or captured:
                                    halfmove = 0
                                else:
                                    halfmove += 1

                                # Update en passant square after pawn double move
                                if moved_piece.lower() == 'p' and abs(cur_sq_pos[1] - selected_square[1]) == 2:
                                    en_passant = (cur_sq_pos[0], (cur_sq_pos[1] + selected_square[1]) // 2)
                                else:
                                    en_passant = ()

                                # Update turn and fullmove
                                if turn == 'b':
                                    fullmove += 1
                                turn = 'b' if turn == 'w' else 'w'

                                last_move = (selected_square, cur_sq_pos)
                                fen = board_to_fen(board, turn, castling, make_fen_en_passent(en_passant), halfmove, fullmove)
                                legal_moves = []
                                selected_square = None

                            else:
                                selected_square = None
                                legal_moves = []

        draw_chessboard(board, flip_board, last_move)
        button_rect = draw_fen_display(fen)
        show_copied = draw_copy_feedback(show_copied, copy_timer, button_rect)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
