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
pygame.scrap.init()

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

FONT = pygame.font.SysFont("arial", 24)
SMALL_FONT = pygame.font.SysFont("arial", 20)

MOVE_SOUND = pygame.mixer.Sound(f"{base_path}/sound_effects/move-self.mp3")
CAPTURE_SOUND = pygame.mixer.Sound(f"{base_path}/sound_effects/capture.mp3")
PROMOTION_SOUND = pygame.mixer.Sound(f"{base_path}/sound_effects/promote.mp3")

selected_square = None
legal_moves = []
hovering_copy = False
show_copied = False
copy_timer = 0

def draw(board, fen, flip_board, last_move, show_copied, copy_timer):
    draw_chessboard(board, flip_board, last_move)
    button_rect = draw_fen_display(fen)
    show_copied = draw_copy_feedback(show_copied, copy_timer, button_rect)
    pygame.display.flip()
    return show_copied, button_rect


def interpret_fen_board(fen):
    board_part = fen.split(" ")[0]
    interpretation = ""
    for c in board_part:
        if c == '/':
            continue
        interpretation += c if not c.isdigit() else "." * int(c)
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

def get_fen_en_passent(en_pass):
    if en_pass == "-":
        return ()
    return (ord(en_pass[0].lower()) - ord('a'), 8 - int(en_pass[1]))

def make_fen_en_passent(en_pass):
    return chr(en_pass[0] + 97) + str(8 - en_pass[1]) if en_pass != () else "-"

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
        empty = 0
        for c in row:
            if c == '.':
                empty += 1
            else:
                if empty:
                    fen_row += str(empty)
                    empty = 0
                fen_row += c
        if empty:
            fen_row += str(empty)
        fen_rows.append(fen_row)
    return f"{'/'.join(fen_rows)} {turn} {castling} {en_passant} {halfmove} {fullmove}"

def update_castling_rights(castling, selected_square, moved_piece):
    x, y = selected_square

    # Remove castling rights if the king moves
    if moved_piece.lower() == 'k':
        if moved_piece.isupper():
            castling = castling.replace('K', '').replace('Q', '')
        else:
            castling = castling.replace('k', '').replace('q', '')

    # Remove castling rights if a rook moves from its original square
    elif moved_piece.lower() == 'r':
        rights_to_remove = {
            (0, 7): 'Q',  # White queenside
            (7, 7): 'K',  # White kingside
            (0, 0): 'q',  # Black queenside
            (7, 0): 'k',  # Black kingside
        }
        to_remove = rights_to_remove.get((x, y))
        if to_remove:
            castling = castling.replace(to_remove, '')

    return castling

def show_promotion_menu(board, screen, promotion_square, turn):
    x, y = promotion_square
    direction = -1 if turn == 'b' else 1
    piece_choices = ['q', 'n', 'r', 'b']
    selected_piece = None

    while selected_piece is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i in range(4):
                    square_y = y + i * direction
                    rect = pygame.Rect(
                        OFFSET_X + x * SQUARE_SIZE,
                        OFFSET_Y + square_y * SQUARE_SIZE,
                        SQUARE_SIZE,
                        SQUARE_SIZE
                    )
                    if rect.collidepoint(mx, my):
                        selected_piece = piece_choices[i].upper() if turn == 'w' else piece_choices[i]
                        break

        # Draw everything behind first
        draw_chessboard(board, flip_board=False, last_move=None)

        # Draw overlay squares
        for i in range(4):
            square_y = y + i * direction
            rect = pygame.Rect(
                OFFSET_X + x * SQUARE_SIZE,
                OFFSET_Y + square_y * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE
            )
            # Choose base overlay color based on promoting side
            overlay_color = (100, 100, 100) if turn == 'b' else (200, 200, 200)

            # Highlight hovered one
            if rect.collidepoint(pygame.mouse.get_pos()):
                overlay_color = tuple(min(c + 30, 255) for c in overlay_color)

            pygame.draw.rect(screen, overlay_color, rect)

            # Draw the piece image
            piece_key = piece_choices[i].upper() if turn == 'w' else piece_choices[i]
            piece_img = pieces[piece_key]
            screen.blit(piece_img, (rect.x, rect.y))

        pygame.display.flip()

    return selected_piece



def make_move(board, selected_square, cur_sq_pos, type_of_move, en_passant, halfmove, turn, fullmove, castling):
    moved_piece = board[to_index(selected_square)]

    is_en_passant = (
        moved_piece.lower() == 'p' and
        cur_sq_pos == en_passant and
        board[to_index(cur_sq_pos)] == '.'
    )

    captured = board[to_index(cur_sq_pos)] != '.' or is_en_passant
    if is_en_passant:
        cap_y = cur_sq_pos[1] + (1 if moved_piece.isupper() else -1)
        cap_x = cur_sq_pos[0]
        capture_idx = to_index((cap_x, cap_y))
        board = list(board)
        board[capture_idx] = '.'
        board = ''.join(board)

    board = update_board(board, selected_square, cur_sq_pos)
    castling = update_castling_rights(castling,selected_square,moved_piece)

    # === Handle castling ===
    if type_of_move == "CASTLE":
        board = list(board)
        if cur_sq_pos == (6, 7):  # White king-side
            board[to_index((5, 7))] = board[to_index((7, 7))]
            board[to_index((7, 7))] = '.'
        elif cur_sq_pos == (2, 7):  # White queen-side
            board[to_index((3, 7))] = board[to_index((0, 7))]
            board[to_index((0, 7))] = '.'
        elif cur_sq_pos == (6, 0):  # Black king-side
            board[to_index((5, 0))] = board[to_index((7, 0))]
            board[to_index((7, 0))] = '.'
        elif cur_sq_pos == (2, 0):  # Black queen-side
            board[to_index((3, 0))] = board[to_index((0, 0))]
            board[to_index((0, 0))] = '.'
        board = ''.join(board)

    if type_of_move == "PROMOTION":
        # pawn already at 8th or 1st rank only need to change it
        user_choise = show_promotion_menu(board,screen,cur_sq_pos,turn)
        temp  = list(board)
        temp[to_index(cur_sq_pos)] = user_choise
        board = ''.join(temp)
        PROMOTION_SOUND.play()
    elif captured:
        CAPTURE_SOUND.play()
    else:
        MOVE_SOUND.play()

    if moved_piece.lower() == 'p' or captured:
        halfmove = 0
    else:
        halfmove += 1

    if moved_piece.lower() == 'p' and abs(cur_sq_pos[1] - selected_square[1]) == 2:
        en_passant = (cur_sq_pos[0], (cur_sq_pos[1] + selected_square[1]) // 2)
    else:
        en_passant = ()


    if turn == 'b':
        fullmove += 1
    turn = 'b' if turn == 'w' else 'w'

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
            rect = pygame.Rect(OFFSET_X + draw_x * SQUARE_SIZE, OFFSET_Y + draw_y * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, color, rect)

            if selected_square == (x, y) or (last_move and ((x, y) == last_move[0] or (x, y) == last_move[1])):
                pygame.draw.rect(screen, HIGHLIGHT_LIGHT if (x + y) % 2 == 0 else HIGHLIGHT_DARK, rect)

            piece = board[y * 8 + x]
            if piece != '.':
                screen.blit(pieces[piece], (rect.x, rect.y))

            if (x, y) in legal_moves:
                pygame.draw.circle(screen, (80, 80, 80), (rect.centerx, rect.centery), 10)

def draw_fen_display(fen):
    global hovering_copy
    x, y = 20, 0
    label = FONT.render("FEN:", True, (255, 255, 255))
    screen.blit(label, (x, y))
    input_rect = pygame.Rect(x, y + 30, 900, 30)
    pygame.draw.rect(screen, (40, 40, 40), input_rect)
    pygame.draw.rect(screen, (200, 200, 200), input_rect, 2)
    screen.blit(SMALL_FONT.render(fen, True, (255, 255, 255)), (input_rect.x + 10, input_rect.y + 5))
    button_rect = pygame.Rect(input_rect.right + 10, input_rect.y, 80, 30)
    pygame.draw.rect(screen, (60, 60, 60), button_rect)
    pygame.draw.rect(screen, (160, 160, 160), button_rect, 2)
    screen.blit(SMALL_FONT.render("Copy", True, (255, 255, 255)), (button_rect.x + 15, button_rect.y + 5))
    hovering_copy = button_rect.collidepoint(pygame.mouse.get_pos())
    if hovering_copy:
        screen.blit(SMALL_FONT.render("Copy to clipboard", True, (200, 200, 200)), (button_rect.x, button_rect.y - 25))
    return button_rect

def draw_copy_feedback(show_copied, copy_timer, button_rect):
    if show_copied and pygame.time.get_ticks() - copy_timer < 1000:
        screen.blit(SMALL_FONT.render("Copied!", True, (0, 255, 0)), (button_rect.x, button_rect.y + 35))
        return True
    return False

def get_square_at_pos(pos, flip_board):
    mx, my = pos
    if OFFSET_X <= mx < OFFSET_X + BOARD_WIDTH and OFFSET_Y <= my < OFFSET_Y + BOARD_HEIGHT:
        fx = int((mx - OFFSET_X) // SQUARE_SIZE)
        fy = int((my - OFFSET_Y) // SQUARE_SIZE)
        return (BOARD_SIZE - 1 - fx if flip_board else fx, BOARD_SIZE - 1 - fy if flip_board else fy)
    return None

def main():
    global selected_square, legal_moves, hovering_copy, show_copied, copy_timer
    test_fen = ""
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" if test_fen == "" else test_fen
    board, turn, castling, en_passant, halfmove, fullmove = interpret_fen(fen)
    en_passant = get_fen_en_passent(en_passant)
    flip_board = False
    running = True
    last_move = None

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                flip_board = not flip_board
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hovering_copy:
                    pygame.scrap.put(pygame.SCRAP_TEXT, fen.encode())
                    show_copied = True
                    copy_timer = pygame.time.get_ticks()
                else:
                    cur_sq_pos = get_square_at_pos(pygame.mouse.get_pos(), flip_board)
                    if cur_sq_pos:
                        sq = cur_sq_pos[1] * 8 + cur_sq_pos[0]
                        if is_select_valid(board, sq, turn):
                            selected_square = cur_sq_pos
                            legal_moves = [i[0] for i in generate_piece_moves(board, turn, cur_sq_pos, en_passant, castling)]
                            full_legal_moves = generate_piece_moves(board, turn, cur_sq_pos, en_passant, castling)
                       
                        elif selected_square and cur_sq_pos in legal_moves:
                            type_of_move = full_legal_moves[legal_moves.index(cur_sq_pos)][1]
                            board, turn, castling, en_passant, halfmove, fullmove = make_move(board, selected_square, cur_sq_pos,type_of_move, en_passant, halfmove, turn, fullmove, castling)
                            last_move = (selected_square, cur_sq_pos)
                            fen = board_to_fen(board, turn, castling, make_fen_en_passent(en_passant), halfmove, fullmove)
                            legal_moves = []
                            selected_square = None
                        else:
                            selected_square = None
                            legal_moves = []
        show_copied, button_rect = draw(board, fen, flip_board, last_move, show_copied, copy_timer)


    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
