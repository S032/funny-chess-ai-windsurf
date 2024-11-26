import pygame
import sys
import threading
import time

# Initialize Pygame
pygame.init()

# Screen dimensions and colors
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
BOARD_SIZE = 8
SQUARE_SIZE = SCREEN_HEIGHT // BOARD_SIZE

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)  # Light wood color
DARK_SQUARE = (181, 136, 99)    # Dark wood color
HIGHLIGHT_COLOR = (100, 249, 83)  # Bright green highlight
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
TRANSPARENT_GREEN = (100, 249, 83, 128)

# AI settings
MIN_AI_DEPTH = 1
MAX_AI_DEPTH = 5
AI_DEPTH = 2  # Default difficulty

class ChessPiece:
    def __init__(self, color, piece_type, position):
        self.color = color
        self.piece_type = piece_type
        self.position = position
        self.has_moved = False
        self.en_passant_vulnerable = False

    def draw(self, screen, x, y):
        """Draw the piece directly on the screen"""
        piece_color = WHITE if self.color == 'white' else BLACK
        accent_color = GOLD if self.color == 'white' else SILVER
        
        if self.piece_type == 'pawn':
            # Simple pawn - circle with a smaller circle on top
            pygame.draw.circle(screen, piece_color, (x + SQUARE_SIZE//2, y + SQUARE_SIZE*3//5), SQUARE_SIZE//4)
            pygame.draw.circle(screen, piece_color, (x + SQUARE_SIZE//2, y + SQUARE_SIZE//3), SQUARE_SIZE//6)
        
        elif self.piece_type == 'rook':
            # Castle-like rook
            pygame.draw.rect(screen, piece_color, (x + SQUARE_SIZE//4, y + SQUARE_SIZE//4, 
                                                 SQUARE_SIZE//2, SQUARE_SIZE//2))
            # Battlements
            for i in range(3):
                pygame.draw.rect(screen, piece_color, (x + SQUARE_SIZE//4 + i*(SQUARE_SIZE//6), 
                                                     y + SQUARE_SIZE//6, SQUARE_SIZE//8, SQUARE_SIZE//4))
        
        elif self.piece_type == 'knight':
            # Horse head shape
            points = [(x + SQUARE_SIZE//4, y + SQUARE_SIZE*3//4), 
                     (x + SQUARE_SIZE*3//4, y + SQUARE_SIZE*3//4),
                     (x + SQUARE_SIZE*3//4, y + SQUARE_SIZE//3),
                     (x + SQUARE_SIZE//2, y + SQUARE_SIZE//4),
                     (x + SQUARE_SIZE//3, y + SQUARE_SIZE//2)]
            pygame.draw.polygon(screen, piece_color, points)
            # Eye
            pygame.draw.circle(screen, accent_color, (x + SQUARE_SIZE*2//3, y + SQUARE_SIZE//2), 3)
        
        elif self.piece_type == 'bishop':
            # Bishop hat shape
            points = [(x + SQUARE_SIZE//2, y + SQUARE_SIZE//4), 
                     (x + SQUARE_SIZE*3//4, y + SQUARE_SIZE*3//4),
                     (x + SQUARE_SIZE//4, y + SQUARE_SIZE*3//4)]
            pygame.draw.polygon(screen, piece_color, points)
            # Cross
            pygame.draw.rect(screen, accent_color, (x + SQUARE_SIZE*7//16, y + SQUARE_SIZE//4, 
                                                  SQUARE_SIZE//8, SQUARE_SIZE//4))
        
        elif self.piece_type == 'queen':
            # Crown shape
            points = [(x + SQUARE_SIZE//4, y + SQUARE_SIZE*3//4),
                     (x + SQUARE_SIZE*3//4, y + SQUARE_SIZE*3//4),
                     (x + SQUARE_SIZE*2//3, y + SQUARE_SIZE//3),
                     (x + SQUARE_SIZE//2, y + SQUARE_SIZE//2),
                     (x + SQUARE_SIZE//3, y + SQUARE_SIZE//3)]
            pygame.draw.polygon(screen, piece_color, points)
            # Crown points
            for i in range(3):
                pygame.draw.circle(screen, accent_color, 
                                 (x + SQUARE_SIZE//3 + i*(SQUARE_SIZE//6), y + SQUARE_SIZE//3), 4)
        
        elif self.piece_type == 'king':
            # Base
            pygame.draw.rect(screen, piece_color, (x + SQUARE_SIZE//3, y + SQUARE_SIZE//3, 
                                                 SQUARE_SIZE//3, SQUARE_SIZE//2))
            # Crown
            points = [(x + SQUARE_SIZE//4, y + SQUARE_SIZE//3),
                     (x + SQUARE_SIZE*3//4, y + SQUARE_SIZE//3),
                     (x + SQUARE_SIZE*3//4, y + SQUARE_SIZE//6),
                     (x + SQUARE_SIZE//2, y + SQUARE_SIZE//4),
                     (x + SQUARE_SIZE//4, y + SQUARE_SIZE//6)]
            pygame.draw.polygon(screen, piece_color, points)
            # Cross
            pygame.draw.rect(screen, accent_color, (x + SQUARE_SIZE*7//16, y + SQUARE_SIZE//8, 
                                                  SQUARE_SIZE//8, SQUARE_SIZE//4))
            pygame.draw.rect(screen, accent_color, (x + SQUARE_SIZE//3, y + SQUARE_SIZE//6, 
                                                  SQUARE_SIZE//3, SQUARE_SIZE//8))

class ChessBoard:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Funny Chess Game - Press A for AI, Z to Undo, +/- for AI Difficulty')
        
        # Game state
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.selected_piece = None
        self.selected_pos = None
        self.valid_moves = []
        self.white_turn = True
        self.move_history = []
        self.promotion_pawn = None
        self.game_over = False
        self.ai_playing = False
        self.ai_thinking = False
        self.ai_depth = AI_DEPTH
        
        # AI thread
        self.ai_thread = None
        
        # Piece values for AI
        self.piece_values = {
            'pawn': 1,
            'knight': 3,
            'bishop': 3,
            'rook': 5,
            'queen': 9,
            'king': 100
        }
        
        # Position bonuses for AI (center control)
        self.position_bonus = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0],
            [0.0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.2, 0.0],
            [0.0, 0.2, 0.4, 0.6, 0.6, 0.4, 0.2, 0.0],
            [0.0, 0.2, 0.4, 0.6, 0.6, 0.4, 0.2, 0.0],
            [0.0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.2, 0.0],
            [0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        ]
        
        self.setup_board()

    def evaluate_board(self):
        """Evaluate the current board position"""
        score = 0
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    value = self.piece_values[piece.piece_type]
                    # Add position bonus
                    value += value * self.position_bonus[row][col]
                    if piece.color == 'white':
                        score += value
                    else:
                        score -= value
        return score

    def minimax(self, depth, alpha, beta, is_maximizing):
        """Minimax algorithm for AI decision making"""
        if depth == 0 or self.game_over:
            return self.evaluate_board(), None
        
        if is_maximizing:
            best_score = float('-inf')
            best_move = None
            
            for row in range(8):
                for col in range(8):
                    piece = self.board[row][col]
                    if piece and piece.color == 'black':
                        for move in self.get_valid_moves(piece, (row, col)):
                            new_row, new_col = move
                            captured_piece = self.board[new_row][new_col]
                            self.board[new_row][new_col] = piece
                            self.board[row][col] = None
                            piece.position = move
                            piece.has_moved = True
                            
                            score, _ = self.minimax(depth - 1, alpha, beta, False)
                            
                            self.board[row][col] = piece
                            self.board[new_row][new_col] = captured_piece
                            piece.position = (row, col)
                            piece.has_moved = False
                            
                            if score > best_score:
                                best_score = score
                                best_move = (piece, (row, col), move)
                            
                            alpha = max(alpha, score)
                            if beta <= alpha:
                                break
            return best_score, best_move
        
        else:
            best_score = float('inf')
            best_move = None
            
            for row in range(8):
                for col in range(8):
                    piece = self.board[row][col]
                    if piece and piece.color == 'white':
                        for move in self.get_valid_moves(piece, (row, col)):
                            new_row, new_col = move
                            captured_piece = self.board[new_row][new_col]
                            self.board[new_row][new_col] = piece
                            self.board[row][col] = None
                            piece.position = move
                            piece.has_moved = True
                            
                            score, _ = self.minimax(depth - 1, alpha, beta, True)
                            
                            self.board[row][col] = piece
                            self.board[new_row][new_col] = captured_piece
                            piece.position = (row, col)
                            piece.has_moved = False
                            
                            if score < best_score:
                                best_score = score
                                best_move = (piece, (row, col), move)
                            
                            beta = min(beta, score)
                            if beta <= alpha:
                                break
            return best_score, best_move

    def is_king_in_check(self, color, board=None):
        """Check if the king of given color is in check"""
        if board is None:
            board = self.board
            
        # Find king position
        king_pos = None
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.piece_type == 'king' and piece.color == color:
                    king_pos = (row, col)
                    break
        if not king_pos:
            return False
            
        # Check if any opponent piece can capture the king
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color != color:
                    moves = self.get_raw_moves(piece, (row, col), board)
                    if king_pos in moves:
                        return True
        return False

    def get_raw_moves(self, piece, pos, board=None):
        """Get moves without considering check"""
        if board is None:
            board = self.board
        row, col = pos
        moves = []
        
        if piece.piece_type == 'pawn':
            direction = -1 if piece.color == 'white' else 1
            # Forward move
            if 0 <= row + direction < 8:
                if not board[row + direction][col]:
                    moves.append((row + direction, col))
                    # Double move from starting position
                    if ((piece.color == 'white' and row == 6) or 
                        (piece.color == 'black' and row == 1)):
                        if not board[row + 2*direction][col]:
                            moves.append((row + 2*direction, col))
            
            # Captures
            for c in [-1, 1]:
                if 0 <= col + c < 8 and 0 <= row + direction < 8:
                    target = board[row + direction][col + c]
                    if target and target.color != piece.color:
                        moves.append((row + direction, col + c))
        
        elif piece.piece_type == 'knight':
            for dr, dc in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = board[new_row][new_col]
                    if not target or target.color != piece.color:
                        moves.append((new_row, new_col))
        
        elif piece.piece_type in ['bishop', 'rook', 'queen']:
            directions = []
            if piece.piece_type in ['bishop', 'queen']:
                directions += [(1,1), (1,-1), (-1,1), (-1,-1)]
            if piece.piece_type in ['rook', 'queen']:
                directions += [(0,1), (0,-1), (1,0), (-1,0)]
            
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                while 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = board[new_row][new_col]
                    if not target:
                        moves.append((new_row, new_col))
                    else:
                        if target.color != piece.color:
                            moves.append((new_row, new_col))
                        break
                    new_row += dr
                    new_col += dc
        
        elif piece.piece_type == 'king':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        target = board[new_row][new_col]
                        if not target or target.color != piece.color:
                            moves.append((new_row, new_col))
        
        return moves

    def get_valid_moves(self, piece, pos):
        """Get valid moves considering check and pins"""
        moves = self.get_raw_moves(piece, pos)
        valid_moves = []
        row, col = pos
        
        # Test each move
        for move in moves:
            # Make temporary move
            new_row, new_col = move
            temp_board = [row[:] for row in self.board]
            temp_board[new_row][new_col] = piece
            temp_board[row][col] = None
            
            # If move doesn't leave king in check, it's valid
            if not self.is_king_in_check(piece.color, temp_board):
                valid_moves.append(move)
        
        return valid_moves

    def make_ai_move(self):
        """Start AI move in a separate thread"""
        def ai_move_thread():
            self.ai_thinking = True
            _, best_move = self.minimax(self.ai_depth, float('-inf'), float('inf'), True)  # True for maximizing (black)
            self.ai_thinking = False
            
            if best_move and not self.game_over:
                piece, old_pos, new_pos = best_move
                old_row, old_col = old_pos
                new_row, new_col = new_pos
                
                # Make the move
                captured_piece = self.board[new_row][new_col]
                self.board[new_row][new_col] = piece
                self.board[old_row][old_col] = None
                piece.position = new_pos
                piece.has_moved = True
                
                # Record move
                self.move_history.append({
                    'piece': piece,
                    'from': old_pos,
                    'to': new_pos,
                    'captured': captured_piece,
                    'is_ai_move': True  # Mark this as an AI move
                })
                
                # Switch turns
                self.white_turn = True
                
                # Check for checkmate
                if self.is_king_in_check('white'):
                    if self.is_checkmate('white'):
                        self.game_over = True
                        print("Checkmate! Black wins!")
                    else:
                        print("Check!")
        
        self.ai_thread = threading.Thread(target=ai_move_thread)
        self.ai_thread.start()

    def setup_board(self):
        # Piece setup
        piece_order = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']
        
        # White pieces
        for i in range(BOARD_SIZE):
            self.board[6][i] = ChessPiece('white', 'pawn', (6, i))
            if i < 8:
                self.board[7][i] = ChessPiece('white', piece_order[i], (7, i))
        
        # Black pieces
        for i in range(BOARD_SIZE):
            self.board[1][i] = ChessPiece('black', 'pawn', (1, i))
            if i < 8:
                self.board[0][i] = ChessPiece('black', piece_order[i], (0, i))

    def draw_board(self):
        # Draw checkered board
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, 
                               (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                SQUARE_SIZE, SQUARE_SIZE))
                
                # Highlight selected piece and valid moves
                if (row, col) == self.selected_pos:
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                    s.set_alpha(128)
                    s.fill(HIGHLIGHT_COLOR)
                    self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                elif (row, col) in self.valid_moves:
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                    s.set_alpha(128)
                    s.fill(TRANSPARENT_GREEN)
                    self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        
        # Draw pieces
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece:
                    piece.draw(self.screen, col * SQUARE_SIZE, row * SQUARE_SIZE)
        
        # Draw game status
        font = pygame.font.Font(None, 36)
        
        # Draw turn indicator
        turn_text = "White's Turn" if self.white_turn else "Black's Turn"
        if self.game_over:
            turn_text = f"Game Over! {'Black' if not self.white_turn else 'White'} wins!"
        text = font.render(turn_text, True, RED)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 10))
        
        # Draw AI status and difficulty
        if self.ai_playing:
            status = f"AI: ON (Depth: {self.ai_depth})" + (" (thinking...)" if self.ai_thinking else "")
        else:
            status = "AI: OFF (Press A to toggle)"
        text = font.render(status, True, RED)
        self.screen.blit(text, (10, 10))
        
        # Draw difficulty controls
        if self.ai_playing:
            diff_text = "Use +/- to adjust AI difficulty"
            text = font.render(diff_text, True, BLUE)
            self.screen.blit(text, (10, SCREEN_HEIGHT - 30))
        
        # Draw undo hint
        undo_text = font.render("Press Z to undo", True, RED)
        self.screen.blit(undo_text, (SCREEN_WIDTH - 200, 10))

    def get_square_under_mouse(self):
        x, y = pygame.mouse.get_pos()
        return (y // SQUARE_SIZE, x // SQUARE_SIZE)

    def is_valid_pos(self, pos):
        row, col = pos
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def handle_click(self, pos):
        row, col = pos
        
        if not self.selected_piece:
            # Select piece
            piece = self.board[row][col]
            if piece and ((piece.color == 'white' and self.white_turn) or 
                         (piece.color == 'black' and not self.white_turn)):
                self.selected_piece = piece
                self.selected_pos = pos
                self.valid_moves = self.get_valid_moves(piece, pos)
        else:
            # Move piece if valid
            if pos in self.valid_moves:
                old_row, old_col = self.selected_pos
                captured_piece = self.board[row][col]
                
                # Record move for undo
                self.move_history.append({
                    'piece': self.selected_piece,
                    'from': self.selected_pos,
                    'to': pos,
                    'captured': captured_piece
                })
                
                # Make move
                self.board[row][col] = self.selected_piece
                self.board[old_row][old_col] = None
                self.selected_piece.position = pos
                self.selected_piece.has_moved = True
                
                # Switch turns
                self.white_turn = not self.white_turn
                
                # Check for checkmate
                if self.is_king_in_check('white' if not self.white_turn else 'black'):
                    if self.is_checkmate('white' if not self.white_turn else 'black'):
                        self.game_over = True
                        print(f"Checkmate! {'Black' if not self.white_turn else 'White'} wins!")
                    else:
                        print(f"Check! {'White' if not self.white_turn else 'Black'} is in check.")
                
                # AI move
                if self.ai_playing and not self.white_turn and not self.game_over:
                    self.make_ai_move()
            
            # Clear selection
            self.selected_piece = None
            self.selected_pos = None
            self.valid_moves = []

    def undo_move(self):
        if self.move_history:
            move = self.move_history.pop()
            piece = move['piece']
            old_pos = move['from']
            new_pos = move['to']
            captured_piece = move['captured']
            
            self.board[old_pos[0]][old_pos[1]] = piece
            self.board[new_pos[0]][new_pos[1]] = captured_piece
            piece.position = old_pos
            
            # Switch turns
            self.white_turn = not self.white_turn

    def is_checkmate(self, color):
        """Check if the given color is in checkmate"""
        # First check if king is in check
        if not self.is_king_in_check(color):
            return False
            
        # For each piece of the given color
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    # Get all valid moves for this piece
                    moves = self.get_valid_moves(piece, (row, col))
                    # If there are any legal moves, it's not checkmate
                    if moves:
                        return False
        
        # If we get here, it's checkmate
        return True

    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN and not self.ai_thinking:
                    pos = self.get_square_under_mouse()
                    if self.is_valid_pos(pos):
                        self.handle_click(pos)
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z and not self.ai_thinking:  # Undo
                        # Undo twice if AI is playing (player's move + AI's move)
                        self.undo_move()
                        if self.ai_playing and not self.white_turn:
                            self.undo_move()
                    elif event.key == pygame.K_a:  # Toggle AI
                        self.ai_playing = not self.ai_playing
                        if self.ai_playing and not self.white_turn and not self.ai_thinking:
                            self.make_ai_move()
                    elif event.key in [pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS]:  # Increase difficulty
                        if self.ai_playing and self.ai_depth < MAX_AI_DEPTH:
                            self.ai_depth += 1
                    elif event.key in [pygame.K_MINUS, pygame.K_KP_MINUS]:  # Decrease difficulty
                        if self.ai_playing and self.ai_depth > MIN_AI_DEPTH:
                            self.ai_depth -= 1
            
            # Make AI move if it's AI's turn
            if self.ai_playing and not self.white_turn and not self.ai_thinking and not self.game_over:
                self.make_ai_move()
            
            # Draw everything
            self.screen.fill(WHITE)
            self.draw_board()
            pygame.display.flip()
            
            # Control game speed
            clock.tick(60)

def main():
    game = ChessBoard()
    game.run()

if __name__ == '__main__':
    main()
