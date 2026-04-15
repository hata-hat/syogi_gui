import copy
import tkinter as tk
from tkinter import messagebox
from collections import Counter

CELL_SIZE = 50

class ShogiGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("将棋")

        self.board = init_board()
        self.hands = {True: [], False: []}
        self.turn = True

        self.selected = None
        self.selected_hand = None

        self.buttons = [[None]*9 for _ in range(9)]

        # =====================
        # 盤面
        # =====================
        self.frame = tk.Frame(root)
        self.frame.pack()

        for x in range(9):
            for y in range(9):
                btn = tk.Button(self.frame, width=4, height=2,
                                command=lambda x=x, y=y: self.on_click(x, y))
                btn.grid(row=x, column=y)
                self.buttons[x][y] = btn

        # =====================
        # 持ち駒UI（フレーム先）
        # =====================
        self.hand_frame_top = tk.Frame(root)
        self.hand_frame_top.pack()

        tk.Label(self.hand_frame_top, text="後手").pack()

        self.hand_frame_bottom = tk.Frame(root)
        self.hand_frame_bottom.pack()

        tk.Label(self.hand_frame_bottom, text="先手").pack()

        self.hand_buttons_top = []
        self.hand_buttons_bottom = []

        # 初期描画
        self.update_board()
        self.update_hands()    

    def update_hands(self):
        # =====================
        # クリア
        # =====================
        for btn in self.hand_buttons_top:
            btn.destroy()
        for btn in self.hand_buttons_bottom:
            btn.destroy()

        self.hand_buttons_top.clear()
        self.hand_buttons_bottom.clear()

        # =====================
        # 後手（False）＝上
        # =====================
        counter_top = Counter(self.hands[False])

        for piece, count in counter_top.items():
            display = display_piece(piece)
            if count > 1:
                display += f"x{count}"

            btn = tk.Button(
                self.hand_frame_top,
                text=display,
                command=lambda p=piece: self.select_hand(p)
            )
            btn.piece = piece
            btn.pack(side=tk.LEFT)
            self.hand_buttons_top.append(btn)

        # =====================
        # 先手（True）＝下
        # =====================
        counter_bottom = Counter(self.hands[True])

        for piece, count in counter_bottom.items():
            display = display_piece(piece)
            if count > 1:
                display += f"x{count}"

            btn = tk.Button(
                self.hand_frame_bottom,
                text=display,
                command=lambda p=piece: self.select_hand(p)
            )
            btn.piece = piece
            btn.pack(side=tk.LEFT)
            self.hand_buttons_bottom.append(btn)

    def update_board(self):
        for x in range(9):
            for y in range(9):
                self.buttons[x][y]["text"] = display_piece(self.board[x][y])

    def select_hand(self, piece):
        self.clear_selection()
        self.selected_hand = piece

        # 自分の持ち駒だけ光らせる
        if self.turn:
            for btn in self.hand_buttons_bottom:
                if btn.piece == piece:
                    btn["bg"] = "yellow"
        else:
            for btn in self.hand_buttons_top:
                if btn.piece == piece:
                    btn["bg"] = "yellow"

    def on_click(self, x, y):
        # 持ち駒打ち
        if self.selected_hand:
            success = drop_piece(self.board, self.hands,
                                 self.selected_hand, x, y, self.turn)

            self.selected_hand = None

            if success:
                if is_checkmate(self.board, self.hands, not self.turn):
                    self.update_board()
                    messagebox.showinfo("終了", "詰み！")
                    return

                elif is_check(self.board, not self.turn):
                    messagebox.showinfo("チェック", "王手！")

                self.turn = not self.turn

            self.update_board()
            self.update_hands()
            return

        piece = self.board[x][y]

        # 選択開始
        if self.selected is None:
            if piece != EMPTY and owner(piece) == self.turn:
                self.selected = (x, y)
                self.buttons[x][y]["bg"] = "yellow"
            return

        fx, fy = self.selected
        legal = get_legal_moves(self.board, self.hands, fx, fy, self.turn)

        candidates = [a for a in legal if a[2] == (x, y)]

        if not candidates:
            self.clear_selection()
            return

        # 成り選択
        if len(candidates) == 2:
            ans = messagebox.askyesno("成り", "成りますか？")
            action = candidates[0] if candidates[0][3] == ans else candidates[1]
        else:
            action = candidates[0]

        success = move_piece(self.board, self.hands, action, self.turn)

        self.clear_selection()

        if success:
            if is_checkmate(self.board, self.hands, not self.turn):
                self.update_board()
                messagebox.showinfo("終了", "詰み！")
                return

            elif is_check(self.board, not self.turn):
                messagebox.showinfo("チェック", "王手！")

            self.turn = not self.turn

        self.update_board()
        self.update_hands()

    def clear_selection(self):
        if self.selected:
            x, y = self.selected
            self.buttons[x][y]["bg"] = "SystemButtonFace"

        for btn in self.hand_buttons_top:
            btn["bg"] = "SystemButtonFace"

        for btn in self.hand_buttons_bottom:
            btn["bg"] = "SystemButtonFace"

        self.selected = None
        self.selected_hand = None

def run_gui():
    root = tk.Tk()
    app = ShogiGUI(root)
    root.mainloop()

BOARD_SIZE = 9
EMPTY = "・"

PIECE_DISPLAY = {
    "p": "歩", "P": "歩",
    "l": "香", "L": "香",
    "n": "桂", "N": "桂",
    "s": "銀", "S": "銀",
    "g": "金", "G": "金",
    "b": "角", "B": "角",
    "r": "飛", "R": "飛",
    "k": "玉", "K": "王",
    "+p": "と", "+P": "と",
    "+l": "成香", "+L": "成香",
    "+n": "成桂", "+N": "成桂",
    "+s": "成銀", "+S": "成銀",
    "+b": "馬", "+B": "馬",
    "+r": "龍", "+R": "龍"
}

def display_piece(piece):
    if piece == EMPTY:
        return EMPTY

    text = PIECE_DISPLAY[piece]

    if piece.isupper():
        return "▼" + text  # 後手
    else:
        return "▲" + text  # 先手

PROMOTE_MAP = {
    "p": "+p", "l": "+l", "n": "+n", "s": "+s",
    "b": "+b", "r": "+r"
}

UNPROMOTE_MAP = {v: k for k, v in PROMOTE_MAP.items()}

def action_key(a):
    return (a[0], a[1], a[2], a[3])

def can_drop(board, hands, piece, x, y, turn):
    if board[x][y] != EMPTY:
        return False

    if piece not in hands[turn]:
        return False

    # 二歩
    if piece == "p":
        for i in range(9):
            if board[i][y] != EMPTY and owner(board[i][y]) == turn and board[i][y].lower() == "p":
                return False

        if (turn and x == 0) or ((not turn) and x == 8):
            return False

    # 桂
    if piece == "n":
        if (turn and x <= 1) or ((not turn) and x >= 7):
            return False

    # 香
    if piece == "l":
        if (turn and x == 0) or ((not turn) and x == 8):
            return False

    return True

#成り可能判定
def can_promote(piece, fx, tx, turn):
    return piece.lower() in ["p","l","n","s","b","r"] and (
        (turn and (fx <= 2 or tx <= 2)) or
        ((not turn) and (fx >= 6 or tx >= 6))
    )

def drop_piece(board, hands, piece, x, y, turn):
    action = ("drop", piece, (x, y), None)

    nb, nh = simulate(board, hands, action, turn)

    if nb is None:
        return False

    if is_check(nb, turn):
        return False

    board[:] = [row[:] for row in nb]
    hands[True] = nh[True]
    hands[False] = nh[False]

    return True

#王の位置検索
def find_king(board, turn):
    king = "k" if turn else "K"
    for x in range(9):
        for y in range(9):
            if board[x][y] == king:
                return x, y
    return None

def get_legal_moves(board, hands, x, y, turn):
    piece = board[x][y]
    if piece == EMPTY or owner(piece) != turn:
        return []

    legal = []

    for tx, ty in get_moves(board, x, y, turn):

        base = ("move", (x, y), (tx, ty), False)

        actions = [base]

        if can_promote(piece, x, tx, turn):
            actions.append(("move", (x, y), (tx, ty), True))

        for a in actions:
            nb, nh = simulate(board, hands, a, turn)
            if nb and not is_check(nb, turn):
                legal.append(a)

    return legal

def get_moves(board, x, y, turn):
    piece = board[x][y]
    p = piece.lower()
    moves = []

    owner_turn = owner(piece)
    forward = -1 if turn else 1

    def add(dx, dy, repeat=False):
        nx, ny = x + dx, y + dy
        while is_inside(nx, ny):
            if board[nx][ny] == EMPTY:
                moves.append((nx, ny))
            else:
                if is_enemy(board[nx][ny], owner_turn):
                    moves.append((nx, ny))
                break
            if not repeat:
                break
            nx += dx
            ny += dy

    if p == "p":
        add(forward, 0)

    elif p == "l":
        add(forward, 0, True)

    elif p == "n":
        for dy in [-1, 1]:
            nx, ny = x + 2 * forward, y + dy
            if is_inside(nx, ny):
                moves.append((nx, ny))

    elif p == "s":
        dirs = [(forward,0),(forward,-1),(forward,1),(-forward,-1),(-forward,1)]
        for dx, dy in dirs:
            add(dx, dy)

    elif p in ["g", "+p", "+l", "+n", "+s"]:
        dirs = [(forward,0),(0,-1),(0,1),(-forward,0),(forward,-1),(forward,1)]
        for dx, dy in dirs:
            add(dx, dy)

    elif p == "k":
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx or dy:
                    add(dx, dy)

    elif p == "b":
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            add(dx, dy, True)

    elif p == "r":
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            add(dx, dy, True)

    elif p == "+b":
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            add(dx, dy, True)
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            add(dx, dy)

    elif p == "+r":
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            add(dx, dy, True)
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            add(dx, dy)

    return moves

#初期配置
def init_board():
    board = [[EMPTY]*9 for _ in range(9)]

    # 後手
    board[0] = ["L","N","S","G","K","G","S","N","L"]
    board[1][1] = "R"
    board[1][7] = "B"
    for i in range(9):
        board[2][i] = "P"

    # 先手
    board[8] = ["l","n","s","g","k","g","s","n","l"]
    board[7][7] = "r"
    board[7][1] = "b"
    for i in range(9):
        board[6][i] = "p"

    return board

#成れる条件
def in_promotion_zone(x, turn):
    return (turn and x <= 2) or ((not turn) and x >= 6)

#王手判定
def is_check(board, turn):
    pos = find_king(board, turn)
    if pos is None:
        return True

    kx, ky = pos

    for x in range(9):
        for y in range(9):
            piece = board[x][y]
            if piece != EMPTY and owner(piece) != turn:
                for mx, my in get_moves(board, x, y, owner(piece)):
                    if (mx, my) == (kx, ky):
                        return True

    return False

#詰み判定
def is_checkmate(board, hands, turn):
    if not is_check(board, turn):
        return False

    # move
    for x in range(9):
        for y in range(9):
            piece = board[x][y]
            if piece != EMPTY and owner(piece) == turn:
                for action in get_legal_moves(board, hands, x, y, turn):
                    nb, nh = simulate(board, hands, action, turn)
                    if not is_check(nb, turn):
                        return False

    # drop
    for piece in hands[turn]:
        for x in range(9):
            for y in range(9):
                if board[x][y] == EMPTY:
                    action = ("drop", piece, (x, y), None)
                    nb, _ = simulate(board, hands, action, turn)
                    if not is_check(nb, turn):
                        return False

    return True

def is_enemy(piece, turn):
    if piece == EMPTY:
        return False
    return owner(piece) != turn

def is_inside(x,y):
    return 0 <= x < 9 and 0 <= y < 9

def is_king_alive(board, turn):
    king = "k" if turn else "K"
    return any(king in row for row in board)
#二歩
def is_nifu(board, y, turn):
    pawn = "p" if turn else "P"
    for x in range(9):
        if board[x][y] == pawn:
            return True
    return False

def move_piece(board, hands, action, turn):
    nb, nh = simulate(board, hands, action, turn)

    if nb is None:
        return False

    if is_check(nb, turn):
        return False

    # ★ここが核心（state更新は1回だけ）
    board[:] = [row[:] for row in nb]
    hands[True] = nh[True]
    hands[False] = nh[False]

    return True

#強制成り判定
def must_promote(piece, tx, turn):
    p = piece.lower()

    # 歩・香（最終段）
    if p in ["p", "l"]:
        return (turn and tx == 0) or ((not turn) and tx == 8)

    # 桂（最終2段）
    if p == "n":
        return (turn and tx <= 1) or ((not turn) and tx >= 7)

    return False

def owner(piece):
    if piece == EMPTY:
        return None
    return piece.islower()  # True=先手, False=後手

def print_board(board, hands):
    print("   0 1 2 3 4 5 6 7 8")
    for i, row in enumerate(board):
        print(i, " ".join(row))
    print("先手持ち駒:", hands[True])
    print("後手持ち駒:", hands[False])
    print()

def promote_if_possible(piece, x, turn):
    if piece.lower() not in PROMOTE_MAP:
        return piece

    if (turn and x <= 2) or ((not turn) and x >= 6):
        return PROMOTE_MAP[piece.lower()]
    return piece

def simulate(board, hands, action, turn):
    import copy

    nb = [row[:] for row in board]
    nh = {True: hands[True][:], False: hands[False][:]}

    kind = action[0]

    # =====================
    # move
    # =====================
    if kind == "move":
        fx, fy = action[1]
        tx, ty = action[2]
        promote = action[3]

        piece = nb[fx][fy]
        target = nb[tx][ty]

        if piece == EMPTY:
            return None, None

        # 取る
        if target != EMPTY:
            nh[turn].append(target.lower().replace("+", ""))

        nb[fx][fy] = EMPTY

        if promote:
            piece = PROMOTE_MAP[piece.lower()]
            piece = piece if turn else piece.upper()

        nb[tx][ty] = piece

    # =====================
    # drop
    # =====================
    elif kind == "drop":
        piece = action[1]
        x, y = action[2]

        if nb[x][y] != EMPTY:
            return None, None

        nb[x][y] = piece if turn else piece.upper()
        nh[turn].remove(piece)

    return nb, nh

def main():
    board = init_board()
    hands = {True: [], False: []}
    turn = True

    while True:
        print_board(board, hands)
        print("先手" if turn else "後手", "の番")
        mode = input("move or drop? ")

        if mode == "move":
            fx = int(input("from x: "))
            fy = int(input("from y: "))

            # 合法手を取得
            legal_actions = get_legal_moves(board, hands, fx, fy, turn)

            if not legal_actions:
                print("合法手がありません")
                continue

            # 一覧表示
            print("選べる手:")
            for i, act in enumerate(legal_actions):
                tx, ty = act[2]
                p = "成" if act[3] else "不成"
                print(f"{i}: ({tx},{ty}) {p}")

            idx = int(input("番号を選択: "))
            if idx < 0 or idx >= len(legal_actions):
                print("無効な選択")
                continue

            action = legal_actions[idx]
            success = move_piece(board, hands, action, turn)

        elif mode == "drop":
            piece = input("駒(p,l,n,s,g,b,r): ")
            x = int(input("x: "))
            y = int(input("y: "))

            success = drop_piece(board, hands, piece, x, y, turn)

        else:
            continue

        if success:
            # 相手側チェック
            if is_checkmate(board, hands, not turn):
                print_board(board, hands)
                print("詰み！", "先手勝ち" if turn else "後手勝ち")
                break

            elif is_check(board, not turn):
                print("王手！")

            turn = not turn



if __name__ == "__main__":
    mode = input("cui or gui? ")

    if mode == "cui":
        main()
    else:
        run_gui()

