BOARD_SIZE = 8

def is_on_board(x, y):
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE

def square_index(x, y):
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
                moves.append((nx, ny))
            elif is_enemy(target, turn):
                moves.append((nx, ny))
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
            if target == '.' or is_enemy(target, turn):
                moves.append((nx, ny))
    return moves

def generate_pawn_moves(board, turn, square):
    x, y = square
    moves = []
    direction = -1 if turn == 'w' else 1
    start_row = 6 if turn == 'w' else 1

    # One step forward
    if is_on_board(x, y + direction) and board[square_index(x, y + direction)] == '.':
        moves.append((x, y + direction))
        # Two steps forward on first move
        if y == start_row and board[square_index(x, y + 2 * direction)] == '.':
            moves.append((x, y + 2 * direction))

    # Diagonal captures
    for dx in (-1, 1):
        nx, ny = x + dx, y + direction
        if is_on_board(nx, ny):
            target = board[square_index(nx, ny)]
            if is_enemy(target, turn):
                moves.append((nx, ny))
    return moves

def generate_king_moves(board, turn, square):
    x, y = square
    moves = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if is_on_board(nx, ny):
                target = board[square_index(nx, ny)]
                if target == '.' or is_enemy(target, turn):
                    moves.append((nx, ny))
    return moves

def generate_piece_moves(board, turn, square):
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
        return generate_pawn_moves(board, turn, (x, y))
    if lower_piece == 'k':
        return generate_king_moves(board, turn, (x, y))
    
    return []
