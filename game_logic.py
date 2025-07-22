import random
import math

# ゲームの定数 (Python側で管理)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BALL_RADIUS = 5 # 玉の半径 (表示サイズと合わせる)
PIN_RADIUS = 4 # 釘の半径 (表示サイズと合わせる)
POCKET_WIDTH = 80
POCKET_HEIGHT = 20
GRAVITY_Y = 0.5
ELASTICITY = 0.7 # 弾性係数

# ゲームの状態
game_state = {
    "score": 0,
    "balls": [], # 各ボールの [x, y, vx, vy] を格納
    "pins": [],  # 各釘の [x, y] を格納
    "pockets": [], # 各ポケットの [x, y, width, height, is_big_win_pocket] を格納
    "game_status": "NORMAL", # "NORMAL", "BIG_WIN"
    "big_win_start_time": 0,
    "current_big_win_message": "",
    "rainbow_hue": 0.0 # 虹色背景の色相
}

BIG_WIN_DURATION = 7000 # 7秒
BIG_WIN_MESSAGES = [
    "yuki die",
    "sukisoudana",
    "nanisitennno",
    "LOSER",
    "CSC die",
]

def init_game_logic():
    """ゲームの初期状態を設定する"""
    game_state["score"] = 0
    game_state["balls"] = []
    game_state["game_status"] = "NORMAL"
    game_state["big_win_start_time"] = 0
    game_state["current_big_win_message"] = ""
    game_state["rainbow_hue"] = 0.0

    # ピンの配置
    game_state["pins"] = []
    for row in range(15):
        for col in range(15):
            x = 50 + col * 45 + (row % 2) * 22.5
            y = 50 + row * 30
            game_state["pins"].append([x, y])

    # 入賞口の配置
    game_state["pockets"] = []
    num_pockets = 5
    pocket_spacing = (SCREEN_WIDTH - POCKET_WIDTH * num_pockets) // (num_pockets + 1)
    big_win_pocket_index = random.randint(0, num_pockets - 1)

    for i in range(num_pockets):
        x = pocket_spacing * (i + 1) + POCKET_WIDTH * i
        is_big_win = (i == big_win_pocket_index)
        game_state["pockets"].append([x, SCREEN_HEIGHT - 50, POCKET_WIDTH, POCKET_HEIGHT, is_big_win])

    return game_state # 初期状態をJavaScriptに返す

def add_ball():
    """新しい玉を追加する"""
    start_x = SCREEN_WIDTH // 2
    start_y = 0
    # 初速に左右へのランダムな成分を追加
    vx = random.uniform(-3, 3)
    vy = 0 # 初期はY速度0
    game_state["balls"].append([start_x, start_y, vx, vy])

def update_game_state(delta_time, current_js_time):
    """ゲームの状態を更新する (JavaScriptから呼ばれる)"""
    # 玉の更新
    for i, ball in enumerate(game_state["balls"]):
        x, y, vx, vy = ball

        # 重力
        vy += GRAVITY_Y
        # 位置更新
        x += vx
        y += vy

        # 画面端での跳ね返り (壁)
        if x - BALL_RADIUS < 0:
            x = BALL_RADIUS
            vx *= -1 * ELASTICITY
        elif x + BALL_RADIUS > SCREEN_WIDTH:
            x = SCREEN_WIDTH - BALL_RADIUS
            vx *= -1 * ELASTICITY

        # 画面下部に到達したら削除
        if y - BALL_RADIUS > SCREEN_HEIGHT:
            game_state["balls"][i] = None # 後でまとめて削除

        game_state["balls"][i] = [x, y, vx, vy]

    game_state["balls"] = [ball for ball in game_state["balls"] if ball is not None]

    # 玉と釘の衝突判定
    balls_to_remove = set()
    for i, ball in enumerate(game_state["balls"]):
        if ball is None: continue # 削除済みのボールはスキップ
        ball_x, ball_y, ball_vx, ball_vy = ball

        for pin_x, pin_y in game_state["pins"]:
            # 中心点間のベクトル
            dx = ball_x - pin_x
            dy = ball_y - pin_y
            distance = math.sqrt(dx**2 + dy**2)

            # 衝突しているか判定
            if distance < BALL_RADIUS + PIN_RADIUS:
                # めり込み解消
                overlap = (BALL_RADIUS + PIN_RADIUS) - distance
                if distance != 0:
                    x += dx / distance * overlap
                    y += dy / distance * overlap

                # 法線ベクトル
                normal_x = dx / distance if distance != 0 else 0
                normal_y = dy / distance if distance != 0 else 0

                # 入射ベクトルと法線ベクトルの内積 (V ドット N)
                dot_product = ball_vx * normal_x + ball_vy * normal_y

                # 反射ベクトル R = V - 2 * (V ドット N) * N
                reflected_vx = ball_vx - 2 * dot_product * normal_x
                reflected_vy = ball_vy - 2 * dot_product * normal_y

                # 速度を更新し、減衰を適用
                ball_vx = reflected_vx * ELASTICITY
                ball_vy = reflected_vy * ELASTICITY

                game_state["balls"][i] = [x, y, ball_vx, ball_vy] # 更新されたボール情報をリストに反映

    # 入賞口との衝突判定
    for i, ball in enumerate(game_state["balls"]):
        if ball is None: continue # 削除済みのボールはスキップ
        ball_x, ball_y, _, _ = ball
        ball_rect_left = ball_x - BALL_RADIUS
        ball_rect_right = ball_x + BALL_RADIUS
        ball_rect_top = ball_y - BALL_RADIUS
        ball_rect_bottom = ball_y + BALL_RADIUS

        for j, pocket in enumerate(game_state["pockets"]):
            pocket_x, pocket_y, pocket_w, pocket_h, is_big_win_pocket = pocket
            pocket_rect_left = pocket_x
            pocket_rect_right = pocket_x + pocket_w
            pocket_rect_top = pocket_y
            pocket_rect_bottom = pocket_y + pocket_h

            # AABB衝突判定 (矩形と矩形)
            if (ball_rect_left < pocket_rect_right and
                ball_rect_right > pocket_rect_left and
                ball_rect_top < pocket_rect_bottom and
                ball_rect_bottom > pocket_rect_top):

                game_state["score"] += 1
                balls_to_remove.add(i) # 削除対象としてマーク

                if is_big_win_pocket and game_state["game_status"] == "NORMAL":
                    game_state["game_status"] = "BIG_WIN"
                    game_state["big_win_start_time"] = current_js_time # JavaScriptの時間を渡す
                    game_state["current_big_win_message"] = random.choice(BIG_WIN_MESSAGES)

    # 削除対象のボールを実際に削除
    game_state["balls"] = [ball for k, ball in enumerate(game_state["balls"]) if k not in balls_to_remove]

    # 大当たり中の処理
    if game_state["game_status"] == "BIG_WIN":
        # 虹色背景の色相を更新 (JavaScript側でも同期)
        # JavaScript側で描画のため、Python側では状態管理のみ
        game_state["rainbow_hue"] = (current_js_time / 1000.0 * 0.1) % 1.0

        if current_js_time - game_state["big_win_start_time"] > BIG_WIN_DURATION:
            game_state["game_status"] = "NORMAL"

    return game_state # 更新されたゲーム状態をJavaScriptに返す