BOARD_SIZE = 8

def get_opponents_attacked_squares(board, color_of_victim):
    attacked_squares = []
    color_of_enemy = 'w' if color_of_victim == 'b' else 'b'

    for square, piece in enumerate(board):
        if is_enemy(piece, color_of_victim):
            x, y = index_square(square)

            if piece.lower() == 'p':  # Handle pawn separately
                direction = -1 if piece == 'P' else 1  # White goes up, black goes down
                for dx in (-1, 1):  # Diagonal attack directions
                    nx = x + dx
                    ny = y + direction
                    if is_on_board(nx, ny):
                        attacked_squares.append((nx, ny))

            else:
                moves = generate_piece_pseudo_legal_moves(board, color_of_enemy, (x, y), en_pass=None, castling_rights="")
                for (nx, ny), move_type in moves:
                    attacked_squares.append((nx, ny))
    return attacked_squares

def is_pseudo_legal_move_legal(board,start_square,end_square,turn):
    # start_square and end_square are in (x,y) format (0,1) (0,3) -> a2 to a4
    start_square, end_square = square_index(start_square), square_index(end_square)
    fake_board = list(board)
    fake_board[end_square] = fake_board[start_square]
    fake_board[start_square] = '.'
    attack_squares = get_opponents_attacked_squares(fake_board,turn)
    victim_king = 'K' if turn == 'w' else 'k'
    return not fake_board.index(victim_king) in list(map(square_index, attack_squares))

        

def is_on_board(x, y):
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE

def index_square(square):
    x = square % 8
    y = square // 8
    return (x,y)

def square_index(pos, y=None):
    if y is None:
        x = pos[0]
        y = pos[1]
    else:
        x = pos
        #y = y
    return y * BOARD_SIZE + x

def is_enemy(piece, turn):
    if piece == '.':
        return False
    return (turn == 'w' and piece.islower()) or (turn == 'b' and piece.isupper())

def generate_sliding_moves(board, turn, square, directions):
    x, y = square
    moves = []
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while is_on_board(nx, ny):
            target = board[square_index(nx, ny)]
            if target == '.':
                moves.append(((nx, ny), "QUIET"))
            elif is_enemy(target, turn):
                moves.append(((nx, ny), "CAPTURE"))
                break
            else:
                break
            nx += dx
            ny += dy
    return moves

def generate_bishop_moves(board, turn, square):
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return generate_sliding_moves(board, turn, square, directions)

def generate_rook_moves(board, turn, square):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return generate_sliding_moves(board, turn, square, directions)

def generate_queen_moves(board, turn, square):
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
    return generate_sliding_moves(board, turn, square, directions)

def generate_knight_moves(board, turn, square):
    x, y = square
    moves = []
    for dx, dy in [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]:
        nx, ny = x + dx, y + dy
        if is_on_board(nx, ny):
            target = board[square_index(nx, ny)]
            if target == '.':
                moves.append(((nx, ny), "QUIET"))
            elif is_enemy(target, turn):
                moves.append(((nx, ny), "CAPTURE"))
    return moves

def generate_pawn_moves(board, turn, square, en_pass):
    x, y = square
    moves = []
    direction = -1 if turn == 'w' else 1
    start_row = 6 if turn == 'w' else 1
    promotion_row = 0 if turn == 'w' else 7

    def add_move(nx, ny, move_type):
        if ny == promotion_row:
            moves.append(((nx, ny), "PROMOTION"))
        else:
            moves.append(((nx, ny), move_type))

    # One step forward
    if is_on_board(x, y + direction) and board[square_index(x, y + direction)] == '.':
        add_move(x, y + direction, "QUIET")

        # Two steps forward on first move
        if y == start_row and board[square_index(x, y + 2 * direction)] == '.':
            add_move(x, y + 2 * direction, "QUIET")

    # Diagonal captures
    for dx in (-1, 1):
        nx, ny = x + dx, y + direction
        if is_on_board(nx, ny):
            target = board[square_index(nx, ny)]
            if is_enemy(target, turn):
                add_move(nx, ny, "CAPTURE")
            if en_pass == (nx, ny):
                add_move(nx, ny, "CAPTURE")
    return moves

def generate_king_moves(board, turn, square, castling_rights):
    x, y = square
    moves = []

    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if is_on_board(nx, ny):
                target = board[square_index(nx, ny)]
                if target == '.':
                    moves.append(((nx, ny), "QUIET"))
                elif is_enemy(target, turn):
                    moves.append(((nx, ny), "CAPTURE"))

    # Castling (basic implementation)
    if turn == 'w' and square == (4, 7):  # e1
        if 'K' in castling_rights:
            if board[square_index(5, 7)] == '.' and board[square_index(6, 7)] == '.':
                moves.append(((6, 7), "CASTLE"))  # g1
        if 'Q' in castling_rights:
            if board[square_index(1, 7)] == board[square_index(2, 7)] == board[square_index(3, 7)] == '.':
                moves.append(((2, 7), "CASTLE"))  # c1
    elif turn == 'b' and square == (4, 0):  # e8
        if 'k' in castling_rights:
            if board[square_index(5, 0)] == '.' and board[square_index(6, 0)] == '.':
                moves.append(((6, 0), "CASTLE"))  # g8
        if 'q' in castling_rights:
            if board[square_index(1, 0)] == board[square_index(2, 0)] == board[square_index(3, 0)] == '.':
                moves.append(((2, 0), "CASTLE"))  # c8

    return moves

def generate_piece_moves(board, turn, square, en_pass, castling_rights):
    x, y = square
    piece = board[square_index(x, y)]
    lower_piece = piece.lower()

    pseudo_legal_moves = generate_piece_pseudo_legal_moves(board, turn, (x, y), en_pass, castling_rights)
    legal_moves = []

    for move in pseudo_legal_moves:
        end_pos, move_type = move
        if is_pseudo_legal_move_legal(board, square, end_pos, turn):
            # Simulate the move
            fake_board = list(board)
            start_index = square_index(square)
            end_index = square_index(end_pos)
            fake_board[end_index] = fake_board[start_index]
            fake_board[start_index] = '.'

            # Check if the opponent is in check or checkmate
            enemy_color = 'b' if turn == 'w' else 'w'
            victim_king = 'k' if enemy_color == 'b' else 'K'

            if victim_king in fake_board:
                king_index = fake_board.index(victim_king)
                attacked_squares = get_opponents_attacked_squares(fake_board, enemy_color)

                if king_index in list(map(square_index, attacked_squares)):
                    # Opponent is in check — check if they have any legal moves
                    has_escape = False
                    for i, p in enumerate(fake_board):
                        if p == '.' or is_enemy(p, enemy_color):
                            continue
                        pos = index_square(i)
                        if generate_piece_moves(fake_board, enemy_color, pos, en_pass, castling_rights):
                            has_escape = True
                            break
                    if not has_escape:
                        move_type = "CHECKMATE"
                    else:
                        move_type = "CHECK"

            legal_moves.append((end_pos, move_type))

    return legal_moves

def generate_piece_pseudo_legal_moves(board, turn, square, en_pass, castling_rights):
    x, y = square
    piece = board[square_index(x, y)]
    lower_piece = piece.lower()

    if lower_piece == 'b':
        return generate_bishop_moves(board, turn, (x, y))
    if lower_piece == 'r':
        return generate_rook_moves(board, turn, (x, y))
    if lower_piece == 'q':
        return generate_queen_moves(board, turn, (x, y))
    if lower_piece == 'n':
        return generate_knight_moves(board, turn, (x, y))
    if lower_piece == 'p':
        return generate_pawn_moves(board, turn, (x, y),en_pass)
    if lower_piece == 'k':
        return  generate_king_moves(board, turn, (x, y),castling_rights)

    return []