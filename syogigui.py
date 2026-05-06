import copy
import tkinter as tk
from tkinter import messagebox
from collections import Counter



# =====================
# 定数・表示関連
# =====================
BOARD_SIZE = 9
EMPTY = "・"

# 持ち駒の表示順
HAND_ORDER = ["p", "l", "n", "s", "g", "b", "r"]

# 駒の表示文字
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

CELL_SIZE = 50

#成り駒対応表
PROMOTE_MAP = {
    "p": "+p", "l": "+l", "n": "+n", "s": "+s",
    "b": "+b", "r": "+r"
}
#成り解除対応表
UNPROMOTE_MAP = {v: k for k, v in PROMOTE_MAP.items()}

class ShogiGUI:

    #GUI初期化
    def __init__(self, root):
        self.root = root
        self.root.title("将棋")

        self.board = init_board()
        self.hands = {True: [], False: []}
        self.turn = True

        self.history = [] 

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

        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10)

        tk.Button(
            self.control_frame,
            text="新規対局",
            command=self.reset_game
        ).pack() 

        tk.Button(
            self.control_frame,
            text="待った（UNDO）",
            command=self.undo_move
        ).pack() 

    #持ち駒表示を更新
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

        for piece in HAND_ORDER:
            if piece not in counter_top:
                continue

            count = counter_top[piece]
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

        for piece in HAND_ORDER:
            if piece not in counter_bottom:
                continue

            count = counter_bottom[piece]
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

    #盤面ボタンの表示を更新
    def update_board(self):
        for x in range(9):
            for y in range(9):
                self.buttons[x][y]["text"] = display_piece(self.board[x][y])

    # 持ち駒を選択状態にする
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

    # 盤クリック時の処理分岐
    def on_click(self, x, y):
        """
        クリック時の分岐制御だけ行う
        """
        if self.selected_hand:
            self.handle_drop(x, y)
        elif self.selected is None:
            self.handle_select(x, y)
        else:
            self.handle_move(x, y)

    # 持ち駒を打つ処理
    def handle_drop(self, x, y):
        self.history.append((
                copy.deepcopy(self.board),
                copy.deepcopy(self.hands),
                self.turn
            ))
        
        success = drop_piece(
            self.board, self.hands,
            self.selected_hand, x, y, self.turn
        )

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

    # 駒の選択処理
    def handle_select(self, x, y):
        piece = self.board[x][y]

        if is_friend(piece, self.turn):
            self.selected = (x, y)
            self.buttons[x][y]["bg"] = "yellow"

    # 駒の移動処理
    def handle_move(self, x, y):
        fx, fy = self.selected
        legal = get_legal_moves(self.board, self.hands, fx, fy, self.turn)

        candidates = [a for a in legal if a[3] == x and a[4] == y]

        if not candidates:
            self.clear_selection()
            return

        self.history.append((
                copy.deepcopy(self.board),
                copy.deepcopy(self.hands),
                self.turn
            ))
        
        # 成り選択
        if len(candidates) == 2:
            ans = messagebox.askyesno("成り", "成りますか？")

            promote_action = None
            normal_action = None

            for a in candidates:
                if a[5]:
                    promote_action = a
                else:
                    normal_action = a

            action = promote_action if ans else normal_action
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

    # 選択状態とハイライトを解除
    def clear_selection(self):
        if self.selected:
            x, y = self.selected
            self.buttons[x][y].configure(bg="SystemButtonFace")

        for btn in self.hand_buttons_top:
            btn["bg"] = "SystemButtonFace"

        for btn in self.hand_buttons_bottom:
            btn["bg"] = "SystemButtonFace"

        self.selected = None
        self.selected_hand = None
    
    #待った用
    def undo_move(self):
        if not self.history:
            return

        self.board, self.hands, self.turn = self.history.pop()

        self.clear_selection()
        self.update_board()
        self.update_hands()
            
    #初期化
    def reset_game(self):
        if not messagebox.askyesno("確認", "新しい対局を開始しますか？"):
            return

        self.board = init_board()
        self.hands = {True: [], False: []}
        self.turn = True

        self.clear_selection()
        self.history.clear()

        self.update_board()
        self.update_hands()


#将来的な手の比較、ソート用
def action_key(a):
    return (a[0], a[1], a[2], a[3])

# 駒打ちがルール上可能か判定
def can_drop(board, hands, piece, x, y, turn):
    if board[x][y] != EMPTY:
        return False

    if piece not in hands[turn]:
        return False

    # 歩
    if piece == "p":
        # 二歩チェック
        if is_nifu(board, y, turn):
            return False

        # 行き場なし
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

# 成り可能判定
def can_promote(piece, fx, tx, turn):
    return (
        piece.lower() in ["p","l","n","s","b","r"]
        and (in_promo_zone(fx, turn) or in_promo_zone(tx, turn))
    )

# 駒をGUI表示用の文字列に変換(▲：先手 / ▼：後手)
def display_piece(piece):

    if piece == EMPTY:
        return EMPTY

    text = PIECE_DISPLAY[piece]

    if piece.isupper():
        return "▼" + text  # 後手
    else:
        return "▲" + text  # 先手

# 駒打ち処理(合法位置、打ち歩詰、自玉の王手禁止)
def drop_piece(board, hands, piece, x, y, turn):
    
    if not can_drop(board, hands, piece, x, y, turn):
        return False

    action = ("drop", piece, (x, y), None)

    nb, nh = simulate(board, hands, action, turn)

    if nb is None:
        return False

    #打ち歩詰　重い処理（必要なら軽量化する）
    if piece == "p" and is_checkmate(nb, nh, not turn):
        return False

    #自玉が王手になる手の禁止
    if is_check(nb, turn):
        return False

    board[:] = [row[:] for row in nb]
    hands[True] = nh[True]
    hands[False] = nh[False]

    return True

# 指定側の王の位置取得
def find_king(board, turn):
    king = "k" if turn else "K"
    for x in range(9):
        for y in range(9):
            if board[x][y] == king:
                return x, y
    return None

# 指定駒の合法手をすべて生成
def get_legal_moves(board, hands, x, y, turn):
    piece = board[x][y]
    if not is_friend(piece, turn):
        return []

    legal = []

    for tx, ty in get_moves(board, x, y, turn):

        # 強制成りチェック
        if must_promote(piece, tx, turn):
            actions = [("move", x, y, tx, ty, True)]
        else:
            actions = [("move", x, y, tx, ty, False)]

            if can_promote(piece, x, tx, turn):
                actions.append(("move", x, y, tx, ty, True))

        for a in actions:
            res = simulate(board, hands, a, turn)
            if not res or res[0] is None:
                continue

            nb, nh = res            

            if nb is None:
                continue

            # 自玉が王手になる手は除外
            if is_check(nb, turn):
                continue

            legal.append(a)

    return legal    # [("move", fx, fy, tx, ty, promote_flag), ...]

# 駒の移動可能マスを生成
def get_moves(board, x, y, owner_turn):
    """
    ※以下は考慮しない
    ・自玉が王手になるか
    ・ピン
    ・王を取る手
    """
    piece = board[x][y]
    p = piece.lower()
    moves = []

    owner_turn = owner_turn 
    forward = -1 if owner_turn else 1

    def add_move(dx, dy, repeat=False):
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
        add_move(forward, 0)

    elif p == "l":
        add_move(forward, 0, True)

    elif p == "n":
        for dy in [-1, 1]:
            nx, ny = x + 2 * forward, y + dy
            if is_inside(nx, ny):
                moves.append((nx, ny))

    elif p == "s":
        dirs = [(forward,0),(forward,-1),(forward,1),(-forward,-1),(-forward,1)]
        for dx, dy in dirs:
            add_move(dx, dy)

    elif p in ["g", "+p", "+l", "+n", "+s"]:
        dirs = [(forward,0),(0,-1),(0,1),(-forward,0),(forward,-1),(forward,1)]
        for dx, dy in dirs:
            add_move(dx, dy)

    elif p == "k":
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx or dy:
                    add_move(dx, dy)

    elif p == "b":
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            add_move(dx, dy, True)

    elif p == "r":
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            add_move(dx, dy, True)

    elif p == "+b":
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            add_move(dx, dy, True)
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            add_move(dx, dy)

    elif p == "+r":
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            add_move(dx, dy, True)
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            add_move(dx, dy)

    return moves

# 初期配置
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

# 成れる条件
def in_promo_zone(x, turn):
    return (turn and x <= 2) or ((not turn) and x >= 6)

# 指定側が王手されているか判定
def is_check(board, turn):
    """
    指定側の玉が王手されているか判定

    ※擬似合法手ベースで判定する
    （ピン・自玉王手は考慮しない）
    """
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

# 詰み判定(現在王手、合法手での回避不可(移動+打ち駒))
def is_checkmate(board, hands, turn):
    if not is_check(board, turn):
        return False

    # move
    for x in range(9):
        for y in range(9):
            piece = board[x][y]
            if is_friend(piece, turn):
                for action in get_legal_moves(board, hands, x, y, turn):
                    nb, nh = simulate(board, hands, action, turn)
                    if not is_check(nb, turn):
                        return False

    # drop
    for piece in hands[turn]:
        for x in range(9):
            for y in range(9):
                if board[x][y] != EMPTY:
                    continue

                # 合法な打ちかチェック
                if not can_drop(board, hands, piece, x, y, turn):
                    continue

                action = ("drop", piece, (x, y), None)
                nb, nh = simulate(board, hands, action, turn)

                if nb is None:
                    continue

                # 打ち歩詰め禁止　重い処理（必要なら軽量化する）
                if piece == "p" and is_checkmate(nb, nh, not turn):
                    continue

                if not is_check(nb, turn):
                    return False

    return True

# 相手の駒か判定
def is_enemy(piece, turn):
    return piece != EMPTY and owner(piece) != turn

# 自分の駒か判定
def is_friend(piece, turn):
    return piece != EMPTY and owner(piece) == turn

# 盤面座標か判定
def is_inside(x,y):
    return 0 <= x < 9 and 0 <= y < 9

# 二歩
def is_nifu(board, y, turn):
    pawn = "p" if turn else "P"
    for x in range(9):
        if board[x][y] == pawn:
            return True
    return False

# 実際に駒を動かす(simulateで検証)
def move_piece(board, hands, action, turn):
    nb, nh = simulate(board, hands, action, turn)

    if nb is None:
        return False

    if is_check(nb, turn):
        return False

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

# 駒の所有者を返す
def owner(piece):
    if piece == EMPTY:
        return None
    return piece.islower()  # True=先手, False=後手

# cui用の盤面表示
def print_board(board, hands):
    # ヘッダー（列番号）
    print(" | " + "".join(f"{i:>3} " for i in range(1,10)))
    print(" +" + "ーー"*9)

    for i, row in enumerate(board):
        row_label = chr(ord('a') + i)
        line = []
        for piece in row:
            text = display_piece(piece)
            line.append(f"{text:>3}")
        print(f"{row_label}|"+ "".join(line))

    print(" +" + "ーー"*9)
    print("先手持ち駒:", hands[True])
    print("後手持ち駒:", hands[False])
    print()
    
# 一手仮適用して、新しい盤面と持ち駒を返す
def simulate(board, hands, action, turn):
    nb = [row[:] for row in board]
    nh = {True: hands[True][:], False: hands[False][:]}

    kind = action[0]

    if kind == "move":
        fx, fy, tx, ty, promote = action[1], action[2], action[3], action[4], action[5]

        piece = nb[fx][fy]
        target = nb[tx][ty]

        if piece == EMPTY:
            return None, None

        if target != EMPTY:
            base = target.lower()
            base = UNPROMOTE_MAP.get(base, base) 
            nh[turn].append(base)          

        nb[fx][fy] = EMPTY

        if promote:
            piece = PROMOTE_MAP[piece.lower()]
            piece = piece if turn else piece.upper()

        nb[tx][ty] = piece

    elif kind == "drop":
        piece = action[1]
        x, y = action[2]

        if nb[x][y] != EMPTY:
            return None, None

        nb[x][y] = piece if turn else piece.upper()
        nh[turn].remove(piece)

    return nb, nh   # (new_board, new_hands)または(None, None)(不正時)

#座標変換
def parse_pos(pos):
    """
    '6a' → (x, y) に変換
    """
    col = int(pos[0]) - 1          # 1-9 → 0-8
    row = ord(pos[1].lower()) - ord('a')  # a-i → 0-8
    return row, col

#表示の逆変換
def format_pos(x, y):
    """
    (x, y) → '6a'
    """
    return f"{y+1}{chr(ord('a') + x)}"

#座標入力の分割
def input_pos():
    col = input("列 (1-9): ")
    row = input("行 (a-i): ").lower()
    

    if row < 'a' or row > 'i':
        return None

    if not col.isdigit() or not (1 <= int(col) <= 9):
        return None

    x = ord(row) - ord('a')
    y = int(col) - 1
    return x, y

#cuiモード
def main():
    board = init_board()
    hands = {True: [], False: []}
    turn = True

    while True:
        print_board(board, hands)
        print("先手" if turn else "後手", "の番")
        mode = input("move or drop? ")

        if mode == "move":
            print("移動元を選択")
            pos = input_pos()
            if pos is None:
                print("入力エラー")
                continue

            fx, fy = pos

            legal_actions = get_legal_moves(board, hands, fx, fy, turn)

            if not legal_actions:
                print("合法手がありません")
                continue

            print("移動可能なマス:")
            for i, act in enumerate(legal_actions):
                _, fx, fy, tx, ty, promote = act
                p = "成" if promote else "不成"
                print(f"{i}: {format_pos(tx, ty)} {p}")

            idx = int(input("番号を選択: "))
            if idx < 0 or idx >= len(legal_actions):
                print("無効な選択")
                continue

            action = legal_actions[idx]
            success = move_piece(board, hands, action, turn)
            
        elif mode == "drop":
            piece = input("駒(p,l,n,s,g,b,r): ")

            print("打つ位置を選択")
            pos = input_pos()
            if pos is None:
                print("入力エラー")
                continue

            x, y = pos

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

#guiモード
def run_gui():
    root = tk.Tk()
    app = ShogiGUI(root)
    root.mainloop()

if __name__ == "__main__":
    mode = input("cui or gui? ")

    if mode == "cui":
        main()
    else:
        run_gui()

