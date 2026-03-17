import tkinter as tk
import random
import math
from PIL import Image, ImageTk
import os
import sys

# =====================
# PyInstaller用パス解決関数
# =====================
def resource_path(relative_path):
    """ リソースファイルへの絶対パスを取得する """
    try:
        # PyInstallerの一時フォルダパス
        base_path = sys._MEIPASS
    except Exception:
        # 通常実行時のパス
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =====================
# 基本設定と画像読み込み
# =====================
WIDTH, HEIGHT = 600, 400
FPS_MS = 10 

# 画像ファイル名の設定
IMAGE_FILENAME = "210ebb27-a2bc-4a2e-92fb-7939b53e40ea.jpg"
IMAGE_PATH = resource_path(IMAGE_FILENAME)

root = tk.Tk()
root.title("ROGUE-BRICK: FOREST SURVIVOR")
root.resizable(False, False)

# キャンバス作成
container = tk.Frame(root, width=WIDTH, height=HEIGHT, bg="black")
container.pack()
canvas = tk.Canvas(container, width=WIDTH, height=HEIGHT, bg="#050510", highlightthickness=0)
canvas.place(x=0, y=0)

# 背景画像の読み込み（エラーハンドリング付き）
bg_image = None
if os.path.exists(IMAGE_PATH):
    try:
        bg_pil = Image.open(IMAGE_PATH)
        bg_pil = bg_pil.resize((WIDTH, HEIGHT), Image.NEAREST)
        bg_image = ImageTk.PhotoImage(bg_pil)
    except Exception as e:
        print(f"画像読み込みエラー: {e}")
else:
    print(f"警告: 画像ファイルが見つかりません: {IMAGE_PATH}")

# =====================
# ゲームステータス (初期化)
# =====================
current_stage = 1
score = 0
lives = 3
paddle_width = 100
fixed_speed = 6.5
BLOCK_MAGNET_RANGE = 150

max_penetration = 0
split_chance = 0.0
magnetic_ball = False
bullet_time_enabled = False
safety_net_enabled = False
safety_net_active = False
safety_net_count = 0

balls_data = [] 
blocks = []
particles = [] 
paddle = None
running = False

upgrade_counts = {"penetration": 0, "magnetic": 0, "paddle_width": 0, "split": 0, "safety_net": 0}
LIMITS = {"penetration": 5, "magnetic": 1, "paddle_width": 5, "split": 5, "safety_net": 2}

# =====================
# 共通描画関数
# =====================
def draw_bg():
    canvas.delete("bg_tag")
    if bg_image:
        canvas.create_image(0, 0, image=bg_image, anchor="nw", tags="bg_tag")
        canvas.tag_lower("bg_tag")

def update_ui():
    canvas.delete("ui")
    canvas.create_text(62, 22, text=f"LIFE: {lives}", fill="black", font=("Courier", 14, "bold"), tags="ui")
    canvas.create_text(60, 20, text=f"LIFE: {lives}", fill="#FF4444", font=("Courier", 14, "bold"), tags="ui")
    canvas.create_text(WIDTH//2, 20, text=f"SCORE: {score}", fill="white", font=("Courier", 12, "bold"), tags="ui")
    canvas.create_text(WIDTH-68, 22, text=f"STAGE: {current_stage}", fill="black", font=("Courier", 14, "bold"), tags="ui")
    canvas.create_text(WIDTH-70, 20, text=f"STAGE: {current_stage}", fill="#FFFF44", font=("Courier", 14, "bold"), tags="ui")

# =====================
# VFX 関数
# =====================
def create_particles(x, y, color):
    for _ in range(8):
        p = canvas.create_rectangle(x-2, y-2, x+2, y+2, fill=color, outline="")
        particles.append({
            "id": p,
            "dx": random.uniform(-4, 4),
            "dy": random.uniform(-4, 4),
            "life": 25
        })

def update_particles_logic():
    for p_info in particles[:]:
        canvas.move(p_info["id"], p_info["dx"], p_info["dy"])
        p_info["dy"] += 0.15 
        p_info["life"] -= 1
        if p_info["life"] <= 0:
            canvas.delete(p_info["id"])
            particles.remove(p_info)

def screen_shake(intensity=15, duration=15):
    if duration <= 0:
        canvas.place(x=0, y=0)
        return
    dx = random.randint(-intensity, intensity)
    dy = random.randint(-intensity, intensity)
    canvas.place(x=dx, y=dy)
    root.after(20, lambda: screen_shake(max(0, intensity - 1), duration - 1))

# =====================
# ボール管理
# =====================
def create_ball_object(x, y, v_dx, v_dy, pen_count):
    new_ball = canvas.create_oval(x-7, y-7, x+7, y+7, fill="cyan", outline="white", width=1)
    ball_info = {
        "id": new_ball, 
        "x": float(x), 
        "y": float(y), 
        "dx": float(v_dx), 
        "dy": float(v_dy), 
        "pen": pen_count,
        "trail_ids": []
    }
    balls_data.append(ball_info)
    update_ball_visual(ball_info)

def update_ball_visual(b_info):
    color = "#FFD700" if b_info["pen"] > 0 else "#00FFFF"
    canvas.itemconfig(b_info["id"], fill=color)

# =====================
# ゲーム進行
# =====================
def show_start_screen():
    global running, current_stage, score, lives, paddle_width, magnetic_ball, max_penetration, split_chance, bullet_time_enabled, safety_net_enabled, upgrade_counts, balls_data, safety_net_count, particles
    safety_net_count = 0
    running = False
    current_stage, score, lives, paddle_width = 1, 0, 3, 100
    magnetic_ball, bullet_time_enabled, safety_net_enabled = False, False, False
    max_penetration, split_chance = 0, 0.0
    upgrade_counts = {k: 0 for k in upgrade_counts}
    balls_data, particles = [], []
    
    canvas.delete("all")
    draw_bg()
    
    canvas.create_text(WIDTH//2, HEIGHT//2 - 40, text="ROGUE-BRICK", fill="#00FFFF", font=("Courier", 40, "bold"))
    canvas.create_text(WIDTH//2, HEIGHT//2 + 20, text="CLICK TO START", fill="white", font=("Courier", 16, "bold"))
    canvas.bind("<Button-1>", lambda e: start_stage())

def start_stage():
    global paddle, running, blocks, safety_net_active, balls_data, safety_net_count
    canvas.delete("all")
    draw_bg()
    
    blocks, balls_data = [], []
    update_ui()
    
    paddle = canvas.create_rectangle((WIDTH-paddle_width)/2, 360, (WIDTH+paddle_width)/2, 372, fill="#00FF00", outline="white", width=2)
    
    angle = random.uniform(-0.5, 0.5)
    create_ball_object(WIDTH/2, HEIGHT-80, math.sin(angle)*fixed_speed, -math.cos(angle)*fixed_speed, max_penetration)
    
    if safety_net_enabled and safety_net_count > 0:
        safety_net_active = True
        draw_safety_net()
    
    create_stage(current_stage)
    canvas.bind("<Motion>", move_paddle)
    canvas.unbind("<Button-1>")
    running = True
    move_ball_loop()

def move_paddle(event):
    if paddle is None: return
    x = max(paddle_width // 2, min(WIDTH - paddle_width // 2, event.x))
    canvas.coords(paddle, x - paddle_width // 2, 360, x + paddle_width // 2, 372)

def create_stage(stage):
    colors = ["#FF5555", "#55FF55", "#5555FF", "#FFFF55", "#FF55FF"]
    total_blocks = 10 + stage * 5
    rows, cols = min(stage + 2, 8), 8
    b_w, b_h = (WIDTH - 50) / cols, 20
    count = 0
    for r in range(rows):
        for c in range(cols):
            if count >= total_blocks: break
            x1, y1 = c * b_w + 25, r * b_h + 50
            block = canvas.create_rectangle(x1, y1, x1+b_w-6, y1+b_h-6, fill=colors[r % len(colors)], outline="white", tags="block")
            blocks.append(block)
            count += 1

# =====================
# メインループ
# =====================
def move_ball_loop():
    global lives, running, safety_net_active, safety_net_count, score
    if not running: return

    update_particles_logic()
    p_pos = canvas.coords(paddle)
    
    current_wait = FPS_MS 
    if bullet_time_enabled and p_pos:
        for b in balls_data:
            if math.hypot(b["x"] - (p_pos[0]+p_pos[2])/2, b["y"] - 360) < 100:
                current_wait = 25
                break

    sub_steps = 2 
    for _ in range(sub_steps):
        for b_info in balls_data[:]:
            move_dy = (b_info["dy"] + 1.0) if b_info["dy"] > 0 else b_info["dy"]
            b_info["x"] += b_info["dx"] / sub_steps
            b_info["y"] += move_dy / sub_steps

            if b_info["x"] <= 7: b_info["dx"] = abs(b_info["dx"])
            elif b_info["x"] >= WIDTH - 7: b_info["dx"] = -abs(b_info["dx"])
            if b_info["y"] <= 47: b_info["dy"] = abs(b_info["dy"])

            if safety_net_active and b_info["y"] >= 390:
                b_info["dy"] = -abs(b_info["dy"])
                safety_net_count -= 1
                if safety_net_count <= 0:
                    safety_net_active = False
                    canvas.delete("safety_net_tag")
                else:
                    draw_safety_net()

            bx1, by1, bx2, by2 = b_info["x"]-7, b_info["y"]-7, b_info["x"]+7, b_info["y"]+7
            if p_pos and bx2 >= p_pos[0] and bx1 <= p_pos[2] and by2 >= p_pos[1] and by1 <= p_pos[1] + 12:
                b_info["y"] = p_pos[1] - 8
                b_info["pen"] = max_penetration
                update_ball_visual(b_info)
                
                if random.random() < split_chance and len(balls_data) < 3:
                    create_ball_object(b_info["x"], b_info["y"], -b_info["dx"], -abs(b_info["dy"]), b_info["pen"])
                
                offset = (b_info["x"] - (p_pos[0]+p_pos[2])/2) / (paddle_width/2)
                angle = max(-0.9, min(0.9, offset)) * (math.pi/3)
                b_info["dx"], b_info["dy"] = math.sin(angle) * fixed_speed, -math.cos(angle) * fixed_speed

            hit_blocks = [i for i in canvas.find_overlapping(bx1, by1, bx2, by2) if "block" in canvas.gettags(i)]
            for block in hit_blocks:
                bl_pos = canvas.coords(block)
                if not bl_pos: continue
                score += 10
                update_ui()
                create_particles((bl_pos[0]+bl_pos[2])/2, (bl_pos[1]+bl_pos[3])/2, canvas.itemcget(block, "fill"))
                if b_info["pen"] > 0:
                    b_info["pen"] -= 1
                    update_ball_visual(b_info)
                else:
                    if b_info["dx"] > 0 and bx2 > bl_pos[0] and b_info["x"] < bl_pos[0]: b_info["dx"] *= -1
                    elif b_info["dx"] < 0 and bx1 < bl_pos[2] and b_info["x"] > bl_pos[2]: b_info["dx"] *= -1
                    else: b_info["dy"] *= -1
                canvas.delete(block)
                if block in blocks: blocks.remove(block)
                break 

            if magnetic_ball: apply_magnet_logic(b_info)

    for b_info in balls_data[:]:
        canvas.coords(b_info["id"], b_info["x"]-7, b_info["y"]-7, b_info["x"]+7, b_info["y"]+7)
        if b_info["y"] > HEIGHT + 20:
            canvas.delete(b_info["id"])
            balls_data.remove(b_info)
            if not balls_data:
                lose_life()
                return

    if not blocks:
        running = False
        root.after(500, show_upgrade_choices)
        return
    root.after(current_wait, move_ball_loop)

def apply_magnet_logic(b_info):
    target_coords = None
    if b_info["dy"] < 0:
        min_d = float("inf")
        for b in blocks:
            coords = canvas.coords(b)
            if coords:
                x, y = (coords[0]+coords[2])/2, (coords[1]+coords[3])/2
                d = math.hypot(x-b_info["x"], y-b_info["y"])
                if d < min_d and d < BLOCK_MAGNET_RANGE:
                    min_d, target_coords = d, (x, y)
    else:
        p_pos = canvas.coords(paddle)
        if p_pos:
            target_coords = ((p_pos[0] + p_pos[2]) / 2, p_pos[1])
    if target_coords:
        tx, ty = target_coords
        dx, dy = tx - b_info["x"], ty - b_info["y"]
        dist = math.hypot(dx, dy)
        if dist > 0:
            power = 0.2 if b_info["dy"] < 0 else 0.05
            b_info["dx"] = (b_info["dx"] * 0.95) + (dx / dist * power)
            b_info["dy"] = (b_info["dy"] * 0.95) + (dy / dist * power)
            mag = math.hypot(b_info["dx"], b_info["dy"])
            b_info["dx"], b_info["dy"] = (b_info["dx"]/mag)*fixed_speed, (b_info["dy"]/mag)*fixed_speed

# =====================
# アップグレード
# =====================
def show_upgrade_choices():
    canvas.delete("all")
    draw_bg()
    canvas.create_text(WIDTH//2, 80, text=f"STAGE {current_stage} CLEAR", fill="#00FF00", font=("Courier", 24, "bold"))
    available = []
    if upgrade_counts["penetration"] < LIMITS["penetration"]: available.append(("貫通力 (PEN +1)", upgrade_p))
    if upgrade_counts["split"] < LIMITS["split"]: available.append(("分裂 (SPLIT 20%)", upgrade_split))
    if not magnetic_ball: available.append(("磁力 (MAGNET BALL)", upgrade_m))
    if upgrade_counts["paddle_width"] < LIMITS["paddle_width"]: available.append(("拡張 (PADDLE +30)", upgrade_w))
    if not bullet_time_enabled: available.append(("集中 (SLOW MOTION)", upgrade_bt))
    if upgrade_counts["safety_net"] < LIMITS["safety_net"]: available.append(("保護 (SAFETY NET)", upgrade_sn))
    available.append(("修理 (LIFE +1)", upgrade_l))
    choices = random.sample(available, min(len(available), 3))
    for i, (name, func) in enumerate(choices):
        y = 180 + i*65
        group_tag = f"group_{i}"
        canvas.create_rectangle(150, y-25, 450, y+25, fill="#222", outline="#00FFFF", width=2, tags=group_tag)
        canvas.create_text(300, y, text=name, fill="white", font=("Courier", 14, "bold"), tags=group_tag)
        canvas.tag_bind(group_tag, "<Button-1>", lambda e, f=func: f())

def upgrade_p(): global max_penetration; max_penetration += 1; upgrade_counts["penetration"] += 1; next_floor()
def upgrade_split(): global split_chance; split_chance += 0.2; upgrade_counts["split"] += 1; next_floor()
def upgrade_m(): global magnetic_ball; magnetic_ball = True; next_floor()
def upgrade_w(): global paddle_width; paddle_width += 30; upgrade_counts["paddle_width"] += 1; next_floor()
def upgrade_bt(): global bullet_time_enabled; bullet_time_enabled = True; next_floor()
def upgrade_sn(): 
    global safety_net_enabled, safety_net_count
    safety_net_enabled = True
    safety_net_count += 1
    upgrade_counts["safety_net"] += 1
    next_floor()
def upgrade_l(): global lives; lives += 1; next_floor()

def next_floor(): 
    global current_stage
    current_stage += 1
    start_stage()

def lose_life():
    global lives, running
    running = False
    lives -= 1
    update_ui()
    if lives <= 0:
        screen_shake(25, 20)
        root.after(1000, show_gameover_screen)
    else:
        screen_shake(12, 10)
        root.after(1000, start_stage)

def show_gameover_screen():
    canvas.delete("all")
    draw_bg()
    canvas.create_text(WIDTH//2, HEIGHT//2-40, text="GAME OVER", fill="#FF0000", font=("Courier", 40, "bold"))
    canvas.create_text(WIDTH//2, HEIGHT//2+10, text=f"FINAL SCORE: {score}", fill="white", font=("Courier", 16, "bold"))
    canvas.create_rectangle(WIDTH//2-80, HEIGHT//2+40, WIDTH//2+80, HEIGHT//2+80, fill="#333", outline="white", tags="restart")
    canvas.create_text(WIDTH//2, HEIGHT//2+60, text="RETRY", fill="white", font=("Courier", 14, "bold"), tags="restart")
    canvas.tag_bind("restart", "<Button-1>", lambda e: show_start_screen())

def draw_safety_net():
    canvas.delete("safety_net_tag")
    if safety_net_count >= 1:
        canvas.create_line(0, 398, WIDTH, 398, fill="#005555", width=3, dash=(10, 10), tags="safety_net_tag")
    if safety_net_count >= 2:
        canvas.create_line(0, 392, WIDTH, 392, fill="#00AAAA", width=3, dash=(10, 10), tags="safety_net_tag")

show_start_screen()
root.mainloop()