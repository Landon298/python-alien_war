import pygame
import sys
import random
import sqlite3
import os
import traceback
from datetime import datetime

# ===================== 全局初始化 =====================
pygame.init()

# 游戏窗口设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('外星人大战 - 排行榜优化版')

# 路径配置（账号/数据存桌面，易查找）
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
USER_FILE = os.path.join(DESKTOP_PATH, "alien_war_users.txt")  # 玩家数据文件
DB_FILE = os.path.join(DESKTOP_PATH, "alien_war_weapons.db")  # 武器数据库

# 游戏参数
FPS = 60
SHIP_WIDTH = 50
SHIP_HEIGHT = 50
SHIP_SPEED = 5
ALIEN_WIDTH = 50
ALIEN_HEIGHT = 50
ALIEN_SPEED_BASE = 2
BULLET_WIDTH = 5
BULLET_HEIGHT = 15
BULLET_SPEED_BASE = 10

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
LIGHT_BLUE = (100, 180, 255)


# ===================== 资源加载函数（修复核心） =====================
def get_font(size):
    """加载自定义字体（路径对应：外星人大战/fonts/font.ttf）"""
    try:
        # 相对路径（推荐）：fonts文件夹和游戏脚本同目录，适配所有电脑
        font_path = "fonts/font.ttf"
        return pygame.font.Font(font_path, size)
    except FileNotFoundError:
        # 备用：绝对路径（精准指向你的字体文件，防止相对路径出错）
        font_path = "C:/Users/白龙飞/Desktop/外星人大战/fonts/font.ttf"
        try:
            return pygame.font.Font(font_path, size)
        except:
            # 终极兜底：系统字体（防止字体文件丢失）
            print("提示：自定义字体加载失败，使用系统字体")
            return pygame.font.SysFont(['SimHei', 'Microsoft YaHei'], size)
    except:
        return pygame.font.Font(None, size)


def load_image(path, width=None, height=None):
    """加载图片（强化日志+绝对路径备选+强制缩放）"""
    # 1. 先尝试相对路径
    rel_path = path
    # 2. 备选绝对路径（适配桌面目录）
    abs_path = os.path.join(DESKTOP_PATH, "外星人大战", path)

    # 调试日志：输出尝试的路径
    print(f"尝试加载图片：相对路径={rel_path} | 绝对路径={abs_path}")

    for img_path in [rel_path, abs_path]:
        try:
            # 加载图片并保留透明通道
            img = pygame.image.load(img_path).convert_alpha()
            # 强制缩放（确保尺寸匹配）
            if width and height:
                img = pygame.transform.scale(img, (width, height))
            print(f"成功加载图片：{img_path}")
            return img
        except (FileNotFoundError, pygame.error) as e:
            print(f"加载失败：{img_path} | 错误：{e}")

    # 兜底：创建纯色矩形（带调试标记）
    print(f"所有路径加载失败，使用兜底图形：{path}")
    img = pygame.Surface((width or 50, height or 50), pygame.SRCALPHA)
    if "ship" in path:
        img.fill((0, 255, 255))  # 青色飞船（方便识别）
        # 绘制十字标记
        pygame.draw.line(img, RED, (0, height // 2), (width, height // 2), 2)
        pygame.draw.line(img, RED, (width // 2, 0), (width // 2, height), 2)
    elif "alien" in path:
        img.fill((255, 165, 0))  # 橙色外星人（方便识别）
        pygame.draw.circle(img, RED, (width // 2, height // 2), width // 4, 2)
    elif "background" in path:
        img.fill((0, 0, 50))  # 深蓝色背景（方便识别）
        # 绘制网格标记
        for x in range(0, width or SCREEN_WIDTH, 50):
            pygame.draw.line(img, (50, 50, 50), (x, 0), (x, height or SCREEN_HEIGHT), 1)
        for y in range(0, height or SCREEN_HEIGHT, 50):
            pygame.draw.line(img, (50, 50, 50), (0, y), (width or SCREEN_WIDTH, y), 1)
    elif "icon" in path:
        img.fill((128, 0, 128))  # 紫色图标
    return img


def load_sound(filename, volume=0.5):
    """加载音效（兼容文件缺失，设置音量）"""
    sound_path = f"sounds/{filename}"
    abs_sound_path = os.path.join(DESKTOP_PATH, "外星人大战", sound_path)

    try:
        sound = pygame.mixer.Sound(sound_path)
        sound.set_volume(volume)
        return sound
    except (FileNotFoundError, pygame.error):
        try:
            sound = pygame.mixer.Sound(abs_sound_path)
            sound.set_volume(volume)
            return sound
        except:
            print(f"警告：未找到音效 {sound_path} / {abs_sound_path}，使用空音效替代")

            # 兜底：空音效类
            class EmptySound:
                def play(self): pass

            return EmptySound()


# ---------------------- 强制加载所有图片资源（修复核心） ----------------------
# 背景图（强制800x600）
BACKGROUND_IMG = load_image("images/background/bg_star.png", SCREEN_WIDTH, SCREEN_HEIGHT)
# 飞船图（强制50x50）
SHIP_IMG = load_image("images/ship/ship_white.png", SHIP_WIDTH, SHIP_HEIGHT)
# 外星人图（强制50x50）
ALIEN_IMG = load_image("images/alien/alien_red.png", ALIEN_WIDTH, ALIEN_HEIGHT)
# 游戏图标（强制64x64）
GAME_ICON = load_image("images/icon/game_icon.png", 64, 64)
pygame.display.set_icon(GAME_ICON)  # 设置窗口图标

# ---------------------- 加载所有音效资源 ----------------------
BGM_SOUND = load_sound("bgm.wav", 0.4)  # 背景音乐（音量40%）
SHOOT_SOUND = load_sound("shoot.wav", 0.6)  # 射击音效（音量60%）
HIT_SOUND = load_sound("hit.wav", 0.7)  # 击中音效（音量70%）
HURT_SOUND = load_sound("hurt.wav", 0.8)  # 受伤音效（音量80%）
GAME_OVER_SOUND = load_sound("game_over.wav", 0.7)  # 游戏结束音效
LEVEL_UP_SOUND = load_sound("level_up.wav", 0.7)  # 升级音效（可选）


# ===================== 工具函数（无修改） =====================
def save_user(username, password):
    """注册新用户（初始化所有字段）"""
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            f.write("username,password,best_score,points,owned_weapons,current_weapon,last_level\n")

    with open(USER_FILE, "r+", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[1:]:
            if line.strip().split(",")[0] == username:
                return False
        f.write(f"{username},{password},0,0,普通子弹,普通子弹,1\n")
        return True


def check_user(username, password):
    """验证登录"""
    if not os.path.exists(USER_FILE):
        return False
    with open(USER_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 2:
                continue
            u = parts[0]
            p = parts[1]
            if u == username and p == password:
                return True
    return False


def get_user_data(username):
    """获取玩家核心数据"""
    if not os.path.exists(USER_FILE):
        return 0, 0, 1
    with open(USER_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 1 or parts[0] != username:
                continue
            best = int(parts[2]) if (len(parts) >= 3 and parts[2].isdigit()) else 0
            points = int(parts[3]) if (len(parts) >= 4 and parts[3].isdigit()) else 0
            last_level = int(parts[6]) if (len(parts) >= 7 and parts[6].isdigit()) else 1
            return best, points, last_level
    return 0, 0, 1


def get_owned_weapons(username):
    """获取已购武器列表"""
    if not os.path.exists(USER_FILE):
        return ['普通子弹']
    with open(USER_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 1 or parts[0] != username:
                continue
            owned = parts[4] if len(parts) >= 5 else '普通子弹'
            return owned.split(",") if owned else ['普通子弹']
    return ['普通子弹']


def get_current_weapon(username):
    """获取上次使用的武器"""
    if not os.path.exists(USER_FILE):
        return '普通子弹'
    with open(USER_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 1 or parts[0] != username:
                continue
            return parts[5] if (len(parts) >= 6 and parts[5]) else '普通子弹'
    return '普通子弹'


def update_user_data(username, best_score=0, points=0, current_weapon="", last_level=0):
    """更新玩家数据"""
    if not os.path.exists(USER_FILE):
        return
    lines = []
    with open(USER_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) < 1 or parts[0] != username:
            continue

        pwd = parts[1] if len(parts) >= 2 else ""
        old_best = int(parts[2]) if (len(parts) >= 3 and parts[2].isdigit()) else 0
        old_points = int(parts[3]) if (len(parts) >= 4 and parts[3].isdigit()) else 0
        old_owned = parts[4] if len(parts) >= 5 else "普通子弹"
        old_weapon = parts[5] if len(parts) >= 6 else "普通子弹"
        old_level = int(parts[6]) if (len(parts) >= 7 and parts[6].isdigit()) else 1

        new_best = max(old_best, best_score) if best_score != 0 else old_best
        new_points = old_points + points if points != 0 else old_points
        new_weapon = current_weapon if current_weapon else old_weapon
        new_level = last_level if last_level != 0 else old_level

        lines[i] = f"{username},{pwd},{new_best},{new_points},{old_owned},{new_weapon},{new_level}\n"
        break

    with open(USER_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


def save_owned_weapons(username, owned_weapons):
    """保存已购武器列表"""
    if not os.path.exists(USER_FILE):
        return
    lines = []
    with open(USER_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) < 1 or parts[0] != username:
            continue

        pwd = parts[1] if len(parts) >= 2 else ""
        best = parts[2] if len(parts) >= 3 else "0"
        points = parts[3] if len(parts) >= 4 else "0"
        weapon = parts[5] if len(parts) >= 6 else "普通子弹"
        level = parts[6] if len(parts) >= 7 else "1"
        owned_str = ",".join(owned_weapons)

        lines[i] = f"{username},{pwd},{best},{points},{owned_str},{weapon},{level}\n"
        break

    with open(USER_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_all_users_ranking():
    """获取所有用户排行榜数据（按最佳分数降序）"""
    if not os.path.exists(USER_FILE):
        return []

    ranking = []
    with open(USER_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue

            username = parts[0]
            best_score = int(parts[2]) if (parts[2].isdigit()) else 0
            points = int(parts[3]) if (len(parts) >= 4 and parts[3].isdigit()) else 0
            last_level = int(parts[6]) if (len(parts) >= 7 and parts[6].isdigit()) else 1

            ranking.append({
                "username": username,
                "best_score": best_score,
                "points": points,
                "last_level": last_level
            })

    # 按最佳分数降序排序
    ranking.sort(key=lambda x: x["best_score"], reverse=True)
    return ranking


def export_full_ranking_data():
    """导出完整排行榜数据到桌面"""
    ranking = get_all_users_ranking()
    if not ranking:
        return False, "暂无用户数据可导出"

    # 生成导出文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_filename = f"alien_war_full_ranking_{timestamp}.txt"
    export_path = os.path.join(DESKTOP_PATH, export_filename)

    try:
        with open(export_path, "w", encoding="utf-8") as f:
            f.write("===== 外星人大战完整排行榜数据 =====\n")
            f.write(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("排名\t用户名\t最佳分数\t当前积分\t最高关卡\n")
            f.write("-" * 60 + "\n")

            for idx, user in enumerate(ranking, 1):
                f.write(f"{idx}\t{user['username']}\t{user['best_score']}\t{user['points']}\t{user['last_level']}\n")

            f.write("=" * 60 + "\n")
        return True, f"完整排行榜已导出到桌面"
    except Exception as e:
        return False, f"导出失败：{str(e)}"


def draw_ranking_style(surface, x, y, width, height):
    """绘制排行榜美化背景"""
    # 外边框
    pygame.draw.rect(surface, LIGHT_BLUE, (x - 2, y - 2, width + 4, height + 4), 2)
    # 内背景（半透明）
    bg_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    bg_surface.fill((0, 20, 50, 180))
    surface.blit(bg_surface, (x, y))


def ranking_interface():
    """优化版排行榜界面（滚动/实时更新/适配窗口）"""
    clock = pygame.time.Clock()
    current_page = 1
    RANK_PER_PAGE = 6  # 每页显示6条，适配600窗口
    selected_menu = 0
    menu_options = ["导出完整数据", "刷新排行榜", "返回主菜单"]
    tip_msg = ""
    tip_color = WHITE

    while running := True:
        clock.tick(FPS)

        # ========== 强制绘制背景图（修复核心） ==========
        # 第一步：清空屏幕（必须）
        SCREEN.fill(BLACK)
        # 第二步：绘制背景图（确保在最底层）
        SCREEN.blit(BACKGROUND_IMG, (0, 0))

        # 实时获取最新排行榜数据
        ranking = get_all_users_ranking()
        total_users = len(ranking)
        total_pages = max(1, (total_users + RANK_PER_PAGE - 1) // RANK_PER_PAGE)

        # 绘制排行榜背景和标题
        rank_x, rank_y = 30, 20
        rank_width, rank_height = 740, 380
        draw_ranking_style(SCREEN, rank_x, rank_y, rank_width, rank_height)

        # 排行榜标题
        title_text = get_font(40).render("玩家排行榜", True, YELLOW)
        SCREEN.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, rank_y + 10))

        # 绘制表头
        header_font = get_font(24)
        headers = ["排名", "用户名", "最佳分数", "当前积分", "最高关卡"]
        header_xs = [rank_x + 40, rank_x + 160, rank_x + 320, rank_x + 450, rank_x + 580]
        for i, header in enumerate(headers):
            header_text = header_font.render(header, True, LIGHT_BLUE)
            SCREEN.blit(header_text, (header_xs[i], rank_y + 60))
        pygame.draw.line(SCREEN, GRAY, (rank_x + 20, rank_y + 90), (rank_x + 720, rank_y + 90), 1)

        # 绘制当前页排名数据
        start_idx = (current_page - 1) * RANK_PER_PAGE
        end_idx = min(start_idx + RANK_PER_PAGE, total_users)
        current_data = ranking[start_idx:end_idx]

        y_pos = rank_y + 105
        for idx, user in enumerate(current_data):
            global_rank = start_idx + idx + 1
            # 前3名特殊颜色
            if global_rank == 1:
                rank_color = (255, 215, 0)  # 金色
            elif global_rank == 2:
                rank_color = (192, 192, 192)  # 银色
            elif global_rank == 3:
                rank_color = (205, 127, 50)  # 铜色
            else:
                rank_color = WHITE

            # 绘制排名数据
            rank_text = get_font(22).render(f"{global_rank}", True, rank_color)
            name_text = get_font(22).render(user['username'], True, WHITE)
            score_text = get_font(22).render(f"{user['best_score']}", True, YELLOW)
            points_text = get_font(22).render(f"{user['points']}", True, GREEN)
            level_text = get_font(22).render(f"{user['last_level']}", True, BLUE)

            SCREEN.blit(rank_text, (header_xs[0], y_pos))
            SCREEN.blit(name_text, (header_xs[1], y_pos))
            SCREEN.blit(score_text, (header_xs[2], y_pos))
            SCREEN.blit(points_text, (header_xs[3], y_pos))
            SCREEN.blit(level_text, (header_xs[4], y_pos))

            pygame.draw.line(SCREEN, (50, 50, 50), (rank_x + 20, y_pos + 30), (rank_x + 720, y_pos + 30), 1)
            y_pos += 35

        # 绘制页码信息
        page_text = get_font(20).render(f"第 {current_page}/{total_pages} 页 (共{total_users}名玩家)", True, LIGHT_BLUE)
        SCREEN.blit(page_text, (SCREEN_WIDTH // 2 - page_text.get_width() // 2, rank_y + rank_height - 25))

        # 绘制操作菜单（适配窗口，不超出）
        menu_y = rank_y + rank_height + 15
        for i, opt in enumerate(menu_options):
            color = RED if i == selected_menu else WHITE
            opt_text = get_font(28).render(opt, True, color)
            menu_pos_y = menu_y + i * 45
            SCREEN.blit(opt_text, (SCREEN_WIDTH // 2 - opt_text.get_width() // 2, menu_pos_y))

        # 绘制提示信息
        if tip_msg:
            tip_text = get_font(24).render(tip_msg, True, tip_color)
            SCREEN.blit(tip_text, (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, rank_y + rank_height - 50))

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                tip_msg = ""
                tip_color = WHITE
                # 排行榜翻页
                if event.key == pygame.K_PAGEUP:
                    if current_page > 1:
                        current_page -= 1
                elif event.key == pygame.K_PAGEDOWN:
                    if current_page < total_pages:
                        current_page += 1
                # 菜单选择
                elif event.key == pygame.K_UP:
                    selected_menu = (selected_menu - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_menu = (selected_menu + 1) % len(menu_options)
                # ESC直接返回主菜单
                elif event.key == pygame.K_ESCAPE:
                    return
                # 执行菜单操作
                elif event.key == pygame.K_RETURN:
                    if selected_menu == 0:
                        # 导出完整数据
                        success, msg = export_full_ranking_data()
                        tip_msg = msg
                        tip_color = GREEN if success else RED
                    elif selected_menu == 1:
                        # 刷新排行榜（实时更新）
                        tip_msg = "排行榜已实时更新！"
                        tip_color = LIGHT_BLUE
                    elif selected_menu == 2:
                        # 返回主菜单
                        return

        pygame.display.flip()


def init_weapon_db():
    """初始化武器数据库"""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS weapons')
        c.execute('CREATE TABLE weapons (name TEXT PRIMARY KEY, price INTEGER, damage INTEGER, bullet_type TEXT)')
        weapons_data = [
            ('普通子弹', 0, 10, 'normal'),
            ('激光', 500, 20, 'laser'),
            ('导弹', 1000, 30, 'missile'),
            ('超级激光', 2000, 25, 'super_laser')
        ]
        c.executemany('INSERT INTO weapons VALUES (?,?,?,?)', weapons_data)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"武器数据库初始化失败：{e}")
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        init_weapon_db()


# ===================== 核心类定义（修复绘制逻辑） =====================
class Player:
    def __init__(self, username):
        self.username = username
        self.best_score, self.points, self.level = get_user_data(username)
        self.current_score = 0
        self.kill_count = 0
        self.level_kill_target = 10 * self.level
        self.owned_weapons = get_owned_weapons(username)
        self.current_weapon = get_current_weapon(username)
        self.last_failed_level = self.level

    def update_score(self, add_score):
        self.current_score += add_score
        self.best_score = max(self.best_score, self.current_score)

    def update_points(self, points):
        self.points += points
        update_user_data(self.username, points=points)

    def level_up(self):
        self.level += 1
        self.kill_count = 0
        self.level_kill_target = 10 * self.level
        update_user_data(self.username, last_level=self.level)
        LEVEL_UP_SOUND.play()  # 新增：播放升级音效
        tip_text = get_font(48).render(f'恭喜！升级到第{self.level}关', True, YELLOW)
        SCREEN.blit(tip_text, (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)

    def buy_weapon(self, weapon_name):
        try:
            conn = sqlite3.connect(DB_FILE, timeout=10)
            c = conn.cursor()
            c.execute('SELECT price FROM weapons WHERE name=?', (weapon_name,))
            price_data = c.fetchone()
            if not price_data:
                conn.close()
                return False

            price = price_data[0]
            if self.points >= price:
                self.points -= price
                update_user_data(self.username, points=-price)
                self.current_weapon = weapon_name
                if weapon_name not in self.owned_weapons:
                    self.owned_weapons.append(weapon_name)
                    save_owned_weapons(self.username, self.owned_weapons)
                update_user_data(self.username, current_weapon=weapon_name)
                conn.close()
                return True
            conn.close()
            return False
        except Exception as e:
            print(f"购买武器失败：{e}")
            conn.close()
            return False

    def save_failed_level(self):
        update_user_data(self.username, last_level=self.level)
        self.last_failed_level = self.level
        print(f"保存失败关卡：{self.level}，用户：{self.username}")

    def save_current_progress(self):
        update_user_data(
            self.username,
            best_score=self.best_score,
            current_weapon=self.current_weapon,
            last_level=self.level
        )
        print(f"保存当前进度：关卡{self.level}，武器{self.current_weapon}，用户{self.username}")


class Spaceship:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2 - SHIP_WIDTH // 2
        self.y = SCREEN_HEIGHT - SHIP_HEIGHT - 20
        self.width = SHIP_WIDTH
        self.height = SHIP_HEIGHT
        self.bullets = []
        # 调试：输出飞船初始位置
        print(f"飞船初始化：x={self.x}, y={self.y}, 尺寸={self.width}x{self.height}")

    def move(self, direction):
        if direction == 'left' and self.x > 0:
            self.x -= SHIP_SPEED
        if direction == 'right' and self.x < SCREEN_WIDTH - self.width:
            self.x += SHIP_SPEED

    def shoot(self, bullet_type):
        bullet_x = self.x + self.width // 2 - BULLET_WIDTH // 2
        bullet_y = self.y - BULLET_HEIGHT
        self.bullets.append(Bullet(bullet_x, bullet_y, bullet_type))
        SHOOT_SOUND.play()  # 新增：播放射击音效

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.y < 0:
                self.bullets.remove(bullet)

    def draw(self):
        # ========== 修复：强制绘制飞船图片 ==========
        # 调试：输出绘制位置
        print(f"绘制飞船：x={self.x}, y={self.y}")
        # 直接绘制图片（覆盖原矩形）
        SCREEN.blit(SHIP_IMG, (self.x, self.y))
        # 可选：绘制碰撞框（调试用）
        # pygame.draw.rect(SCREEN, (0,255,0), (self.x, self.y, self.width, self.height), 1)


class Alien:
    def __init__(self, level):
        self.x = random.randint(0, SCREEN_WIDTH - ALIEN_WIDTH)
        self.y = random.randint(-100, -50)
        self.width = ALIEN_WIDTH
        self.height = ALIEN_HEIGHT
        self.speed = ALIEN_SPEED_BASE + (level - 1) * 0.5
        self.health = 10 + (level - 1) * 5
        # 调试：输出外星人初始位置
        print(f"外星人初始化：x={self.x}, y={self.y}, 尺寸={self.width}x{self.height}")

    def move(self):
        self.y += self.speed

    def draw(self):
        # ========== 修复：强制绘制外星人图片 ==========
        # 调试：输出绘制位置
        print(f"绘制外星人：x={self.x}, y={self.y}")
        # 直接绘制图片（覆盖原矩形）
        SCREEN.blit(ALIEN_IMG, (self.x, self.y))
        # 可选：绘制碰撞框（调试用）
        # pygame.draw.rect(SCREEN, (255,0,0), (self.x, self.y, self.width, self.height), 1)


class Bullet:
    def __init__(self, x, y, bullet_type):
        self.x = x
        self.y = y
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT
        self.type = bullet_type
        if bullet_type == 'laser':
            self.speed = 15
            self.damage = 20
            self.color = RED
            self.width = 8
        elif bullet_type == 'missile':
            self.speed = 8
            self.damage = 30
            self.color = GREEN
            self.width = 10
            self.height = 20
        elif bullet_type == 'super_laser':
            self.speed = 20
            self.damage = 25
            self.color = BLUE
            self.width = 8
        else:
            self.speed = 10
            self.damage = 10
            self.color = YELLOW

    def move(self):
        self.y -= self.speed

    def draw(self):
        # 保留原矩形（子弹图片可选，若需要可新增）
        pygame.draw.rect(SCREEN, self.color, (self.x, self.y, self.width, self.height))


class Background:
    def __init__(self, level):
        self.stars = []
        self.generate_stars(level)

    def generate_stars(self, level):
        star_count = 100 + level * 10
        for _ in range(star_count):
            self.stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'color': (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
                'speed': random.randint(1, 3) + (level - 1) * 0.2
            })

    def update(self):
        for star in self.stars:
            star['y'] += star['speed']
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = -star['size']
                star['x'] = random.randint(0, SCREEN_WIDTH)

    def draw(self):
        # ========== 修复：强制绘制背景图 ==========
        # 第一步：清空屏幕（必须）
        SCREEN.fill(BLACK)
        # 第二步：绘制背景图（确保在最底层）
        SCREEN.blit(BACKGROUND_IMG, (0, 0))
        # 第三步：绘制星星（叠加在背景图上）
        for star in self.stars:
            pygame.draw.circle(SCREEN, star['color'], (star['x'], star['y']), star['size'])


# ===================== 界面函数（修复背景绘制） =====================
def login_register_interface():
    """登录/注册界面（强制绘制背景图）"""
    clock = pygame.time.Clock()
    mode = 'login'
    username_input = ''
    password_input = ''
    error_msg = ''
    tip_msg = ''
    active_input = 'username'

    while running := True:
        clock.tick(FPS)

        # ========== 强制绘制背景图（修复核心） ==========
        SCREEN.fill(BLACK)  # 先清空
        SCREEN.blit(BACKGROUND_IMG, (0, 0))  # 再绘制背景

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    mode = 'register' if mode == 'login' else 'login'
                    error_msg = ''
                    tip_msg = ''
                elif event.key == pygame.K_RETURN:
                    if len(username_input) < 3 or len(password_input) < 3:
                        error_msg = '用户名/密码至少3位'
                    else:
                        if mode == 'login':
                            if check_user(username_input, password_input):
                                shop_or_game(username_input)
                            else:
                                error_msg = '用户名或密码错误'
                        else:
                            if save_user(username_input, password_input):
                                tip_msg = '注册成功！请登录'
                                mode = 'login'
                                username_input = ''
                                password_input = ''
                            else:
                                error_msg = '用户名已存在'
                elif event.key == pygame.K_BACKSPACE:
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        username_input = ''
                        password_input = ''
                    else:
                        if active_input == 'username':
                            username_input = username_input[:-1]
                        else:
                            password_input = password_input[:-1]
                else:
                    if event.unicode.isalnum() or event.unicode == '_':
                        if active_input == 'username' and len(username_input) < 20:
                            username_input += event.unicode
                        elif active_input == 'password' and len(password_input) < 20:
                            password_input += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if 350 <= mouse_pos[0] <= 650 and 250 <= mouse_pos[1] <= 300:
                    active_input = 'username'
                elif 350 <= mouse_pos[0] <= 650 and 350 <= mouse_pos[1] <= 400:
                    active_input = 'password'
                elif 350 <= mouse_pos[0] <= 450 and 450 <= mouse_pos[1] <= 500:
                    mode = 'login'
                    error_msg = ''
                    tip_msg = ''
                elif 450 <= mouse_pos[0] <= 550 and 450 <= mouse_pos[1] <= 500:
                    mode = 'register'
                    error_msg = ''
                    tip_msg = ''

        # 绘制界面
        title_text = get_font(60).render('外星人大战', True, WHITE)
        SCREEN.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 80))

        mode_text = get_font(36).render(f'当前模式：{mode}', True, YELLOW)
        SCREEN.blit(mode_text, (SCREEN_WIDTH // 2 - mode_text.get_width() // 2, 160))

        # 用户名输入框
        pygame.draw.rect(SCREEN, (80, 80, 80) if active_input == 'username' else (50, 50, 50), (350, 250, 300, 50), 0,
                         5)
        pygame.draw.rect(SCREEN, WHITE, (350, 250, 300, 50), 2, 5)
        username_label = get_font(36).render('用户名：', True, WHITE)
        SCREEN.blit(username_label, (220, 255))
        username_text = get_font(36).render(username_input, True, WHITE)
        SCREEN.blit(username_text, (360, 255))

        # 密码输入框
        pygame.draw.rect(SCREEN, (80, 80, 80) if active_input == 'password' else (50, 50, 50), (350, 350, 300, 50), 0,
                         5)
        pygame.draw.rect(SCREEN, WHITE, (350, 350, 300, 50), 2, 5)
        password_label = get_font(36).render('密码：', True, WHITE)
        SCREEN.blit(password_label, (240, 355))
        password_hide = '*' * len(password_input)
        password_text = get_font(36).render(password_hide, True, WHITE)
        SCREEN.blit(password_text, (360, 355))

        # 切换按钮
        pygame.draw.rect(SCREEN, BLUE if mode == 'login' else (30, 30, 30), (350, 450, 100, 50), 0, 5)
        login_btn = get_font(30).render('登录', True, WHITE)
        SCREEN.blit(login_btn, (370, 460))

        pygame.draw.rect(SCREEN, BLUE if mode == 'register' else (30, 30, 30), (450, 450, 100, 50), 0, 5)
        reg_btn = get_font(30).render('注册', True, WHITE)
        SCREEN.blit(reg_btn, (470, 460))

        # 提示信息
        if error_msg:
            error_text = get_font(24).render(error_msg, True, RED)
            SCREEN.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 560))
        if tip_msg:
            tip_text = get_font(24).render(tip_msg, True, GREEN)
            SCREEN.blit(tip_text, (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, 560))

        pygame.display.flip()


def shop_interface(player):
    """武器商店界面（强制绘制背景图）"""
    clock = pygame.time.Clock()
    selected_weapon = 0
    weapons = ['普通子弹', '激光', '导弹', '超级激光']
    tip_msg = ''

    while running := True:
        clock.tick(FPS)

        # ========== 强制绘制背景图（修复核心） ==========
        SCREEN.fill(BLACK)  # 先清空
        SCREEN.blit(BACKGROUND_IMG, (0, 0))  # 再绘制背景

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_weapon = (selected_weapon - 1) % len(weapons)
                    tip_msg = ''
                elif event.key == pygame.K_DOWN:
                    selected_weapon = (selected_weapon + 1) % len(weapons)
                    tip_msg = ''
                elif event.key == pygame.K_RETURN:
                    weapon_name = weapons[selected_weapon]
                    if weapon_name == '普通子弹':
                        tip_msg = '默认拥有普通子弹！'
                    else:
                        if player.buy_weapon(weapon_name):
                            tip_msg = f'购买{weapon_name}成功！'
                            player.save_current_progress()
                        else:
                            tip_msg = '积分不足，无法购买！'
                elif event.key == pygame.K_ESCAPE:
                    player.save_current_progress()
                    return

        # 绘制界面
        title = get_font(48).render('武器商店', True, WHITE)
        SCREEN.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        points_text = get_font(36).render(f'当前积分：{player.points}', True, YELLOW)
        SCREEN.blit(points_text, (SCREEN_WIDTH // 2 - points_text.get_width() // 2, 120))

        y_offset = 200
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for i, weapon in enumerate(weapons):
            c.execute('SELECT price, damage FROM weapons WHERE name=?', (weapon,))
            data = c.fetchone()
            price, damage = data if data else (0, 0)
            color = RED if i == selected_weapon else WHITE
            text = get_font(36).render(f'{weapon} - 价格：{price} 积分 | 伤害：{damage}', True, color)
            SCREEN.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_offset + i * 60))
        conn.close()

        curr_weapon = get_font(36).render(f'当前武器：{player.current_weapon}', True, GREEN)
        SCREEN.blit(curr_weapon, (SCREEN_WIDTH // 2 - curr_weapon.get_width() // 2, 480))

        if tip_msg:
            tip_text = get_font(36).render(tip_msg, True, RED if '不足' in tip_msg else GREEN)
            SCREEN.blit(tip_text, (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, 540))

        exit_text = get_font(24).render('按ESC返回主菜单', True, WHITE)
        SCREEN.blit(exit_text, (20, 20))

        pygame.display.flip()


def shop_or_game(username):
    """主菜单界面（强制绘制背景图）"""
    clock = pygame.time.Clock()
    player = Player(username)
    selected = 0
    # 移除“导出数据”，新增“排行榜”
    options = ['开始游戏', '武器商店', '排行榜', '重置数据', '退出游戏']
    tip_msg = ''

    while running := True:
        clock.tick(FPS)

        # ========== 强制绘制背景图（修复核心） ==========
        SCREEN.fill(BLACK)  # 先清空
        SCREEN.blit(BACKGROUND_IMG, (0, 0))  # 再绘制背景

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                player.save_current_progress()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                    tip_msg = ''
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                    tip_msg = ''
                elif event.key == pygame.K_RETURN:
                    if selected == 0:
                        main_game(username)
                    elif selected == 1:
                        shop_interface(player)
                    elif selected == 2:
                        # 进入排行榜界面
                        ranking_interface()
                    elif selected == 3:
                        if os.path.exists(USER_FILE):
                            os.remove(USER_FILE)
                        init_weapon_db()
                        tip_msg = '数据已重置！请重新登录'
                        pygame.display.flip()
                        pygame.time.wait(2000)
                        login_register_interface()
                    elif selected == 4:
                        player.save_current_progress()
                        login_register_interface()

        # 绘制界面
        welcome = get_font(36).render(f'欢迎 {username} | 最后关卡：{player.level} | 积分：{player.points}', True, WHITE)
        SCREEN.blit(welcome, (SCREEN_WIDTH // 2 - welcome.get_width() // 2, 50))

        y_offset = 200
        for i, opt in enumerate(options):
            color = RED if i == selected else WHITE
            text = get_font(48).render(opt, True, color)
            SCREEN.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_offset + i * 80))

        if tip_msg:
            tip_color = GREEN if '成功' in tip_msg else RED
            tip_text = get_font(36).render(tip_msg, True, tip_color)
            SCREEN.blit(tip_text, (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, 500))

        pygame.display.flip()


def main_game(username):
    """核心游戏逻辑（优化音效播放+强制绘制图片+新增ESC暂停功能）"""
    clock = pygame.time.Clock()
    player = Player(username)
    print(f"加载用户 {username} 的关卡：{player.level}")

    spaceship = Spaceship()
    background = Background(player.level)
    aliens = [Alien(player.level) for _ in range(5 + player.level * 2)]

    # 替换为加载的音效（新增）
    hit_sound = HIT_SOUND
    hurt_sound = HURT_SOUND
    game_over_sound = GAME_OVER_SOUND

    bgm_playing = True
    try:
        # 播放背景音乐（新增）
        BGM_SOUND.play(-1)  # -1表示循环播放
    except:
        bgm_playing = False

    invulnerable = False
    invulnerable_time = 2000
    last_hurt_time = 0
    lives_exhausted = False
    max_lives = 3
    current_lives = max_lives

    auto_attack = True
    weapon_interval = {'normal': 300, 'laser': 500, 'missile': 800, 'super_laser': 400}
    last_attack_time = 0

    # ========== 新增：暂停功能核心变量 ==========
    paused = False  # 暂停状态
    pause_menu_options = ["继续游戏", "退出游戏"]  # 暂停菜单选项
    pause_selected = 0  # 当前选中的菜单项（0=继续，1=退出）
    resume_countdown = 0  # 继续游戏倒计时计时器
    resume_seconds = 3  # 继续游戏倒计时秒数
    countdown_active = False  # 是否处于倒计时阶段

    while running := True:
        current_time = pygame.time.get_ticks()
        clock.tick(FPS)

        # ========== 新增：暂停/倒计时逻辑（优先级最高） ==========
        if paused or countdown_active:
            # 绘制半透明遮罩（暂停背景）
            pause_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pause_mask.fill((0, 0, 0, 180))  # 黑色半透明（透明度180）
            SCREEN.blit(pause_mask, (0, 0))

            if countdown_active:
                # 倒计时逻辑：每秒减1
                if current_time - resume_countdown >= 1000:
                    resume_seconds -= 1
                    resume_countdown = current_time
                    # 倒计时结束，恢复游戏
                    if resume_seconds <= 0:
                        countdown_active = False
                        paused = False
                        resume_seconds = 3  # 重置倒计时

                # 绘制倒计时文字
                countdown_text = get_font(80).render(f"{resume_seconds}", True, YELLOW)
                countdown_tip = get_font(40).render("即将继续游戏...", True, WHITE)
                SCREEN.blit(countdown_text, (SCREEN_WIDTH//2 - countdown_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
                SCREEN.blit(countdown_tip, (SCREEN_WIDTH//2 - countdown_tip.get_width()//2, SCREEN_HEIGHT//2 + 40))
            else:
                # 绘制暂停菜单
                pause_title = get_font(60).render("游戏暂停", True, RED)
                SCREEN.blit(pause_title, (SCREEN_WIDTH//2 - pause_title.get_width()//2, SCREEN_HEIGHT//2 - 120))

                # 绘制菜单选项（选中项黄色高亮）
                for i, opt in enumerate(pause_menu_options):
                    color = YELLOW if i == pause_selected else WHITE
                    opt_text = get_font(48).render(opt, True, color)
                    SCREEN.blit(opt_text, (SCREEN_WIDTH//2 - opt_text.get_width()//2, SCREEN_HEIGHT//2 + i*80))

            # 暂停状态事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    player.save_current_progress()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if not countdown_active:  # 倒计时期间不响应菜单操作
                        # ESC再次按下取消暂停
                        if event.key == pygame.K_ESCAPE:
                            paused = False
                        # 上下键切换菜单
                        elif event.key == pygame.K_UP:
                            pause_selected = (pause_selected - 1) % len(pause_menu_options)
                        elif event.key == pygame.K_DOWN:
                            pause_selected = (pause_selected + 1) % len(pause_menu_options)
                        # 回车键确认选择
                        elif event.key == pygame.K_RETURN:
                            if pause_selected == 0:
                                # 选择继续游戏：启动3秒倒计时
                                countdown_active = True
                                resume_countdown = current_time
                            elif pause_selected == 1:
                                # 选择退出游戏：保存进度并返回主菜单
                                player.save_current_progress()
                                if bgm_playing:
                                    BGM_SOUND.stop()
                                shop_or_game(username)
                                return  # 退出游戏循环

            pygame.display.flip()
            continue  # 暂停时跳过后续游戏逻辑

        # ========== 原有游戏结束逻辑（无修改） ==========
        if lives_exhausted:
            player.save_failed_level()
            update_user_data(username, best_score=player.best_score, current_weapon=player.current_weapon)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if bgm_playing:
                            BGM_SOUND.stop()  # 停止背景音乐
                        shop_or_game(username)
                    elif event.key == pygame.K_r:
                        if bgm_playing:
                            BGM_SOUND.stop()  # 停止背景音乐
                        main_game(username)

            # ========== 游戏结束界面强制绘制背景 ==========
            SCREEN.fill(BLACK)
            SCREEN.blit(BACKGROUND_IMG, (0, 0))

            game_over = get_font(72).render('游戏结束！', True, RED)
            SCREEN.blit(game_over, (SCREEN_WIDTH // 2 - game_over.get_width() // 2, 150))

            final_score = get_font(48).render(f'最终分数：{player.current_score}', True, YELLOW)
            best_score = get_font(48).render(f'最佳分数：{player.best_score}', True, GREEN)
            level = get_font(48).render(f'失败关卡：{player.level}', True, BLUE)
            weapon = get_font(48).render(f'当前武器：{player.current_weapon}', True, WHITE)

            SCREEN.blit(final_score, (SCREEN_WIDTH // 2 - final_score.get_width() // 2, 280))
            SCREEN.blit(best_score, (SCREEN_WIDTH // 2 - best_score.get_width() // 2, 340))
            SCREEN.blit(level, (SCREEN_WIDTH // 2 - level.get_width() // 2, 400))
            SCREEN.blit(weapon, (SCREEN_WIDTH // 2 - weapon.get_width() // 2, 460))

            tip = get_font(36).render('按ESC返回主菜单 | 按R重新开始（继续当前关卡）', True, WHITE)
            SCREEN.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 520))

            pygame.display.flip()
            continue

        # ========== 原有事件处理（新增ESC暂停触发） ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                player.save_current_progress()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # 新增：ESC键触发暂停
                if event.key == pygame.K_ESCAPE and not lives_exhausted:
                    paused = True
                elif event.key == pygame.K_SPACE:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute('SELECT bullet_type FROM weapons WHERE name=?', (player.current_weapon,))
                    res = c.fetchone()
                    bullet_type = res[0] if res else 'normal'
                    conn.close()
                    spaceship.shoot(bullet_type)
                    last_attack_time = current_time
                elif event.key == pygame.K_q:
                    if len(player.owned_weapons) > 1:
                        idx = player.owned_weapons.index(player.current_weapon)
                        player.current_weapon = player.owned_weapons[(idx - 1) % len(player.owned_weapons)]
                        player.save_current_progress()
                elif event.key == pygame.K_e:
                    if len(player.owned_weapons) > 1:
                        idx = player.owned_weapons.index(player.current_weapon)
                        player.current_weapon = player.owned_weapons[(idx + 1) % len(player.owned_weapons)]
                        player.save_current_progress()
                elif event.key == pygame.K_ESCAPE:
                    player.save_current_progress()
                    if bgm_playing:
                        BGM_SOUND.stop()  # 停止背景音乐
                    shop_or_game(username)

        # ========== 原有游戏逻辑（无修改） ==========
        # 飞船移动
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            spaceship.move('left')
        if keys[pygame.K_RIGHT]:
            spaceship.move('right')

        # 自动发射
        if auto_attack:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT bullet_type FROM weapons WHERE name=?', (player.current_weapon,))
            res = c.fetchone()
            bullet_type = res[0] if res else 'normal'
            conn.close()
            interval = weapon_interval.get(bullet_type, 300)
            if current_time - last_attack_time >= interval:
                spaceship.shoot(bullet_type)
                last_attack_time = current_time

        # 无敌时间
        if invulnerable and current_time - last_hurt_time >= invulnerable_time:
            invulnerable = False

        # 更新元素
        background.update()
        spaceship.update_bullets()

        # 敌人逻辑
        for alien in aliens[:]:
            alien.move()
            if alien.y > SCREEN_HEIGHT:
                aliens.remove(alien)
                aliens.append(Alien(player.level))

            ship_rect = pygame.Rect(spaceship.x, spaceship.y, spaceship.width, spaceship.height)
            alien_rect = pygame.Rect(alien.x, alien.y, alien.width, alien.height)
            if not invulnerable and ship_rect.colliderect(alien_rect):
                current_lives -= 1
                hurt_sound.play()  # 播放受伤音效
                invulnerable = True
                last_hurt_time = current_time
                aliens.remove(alien)
                aliens.append(Alien(player.level))
                if current_lives <= 0:
                    lives_exhausted = True
                    game_over_sound.play()  # 播放游戏结束音效
                    if bgm_playing:
                        BGM_SOUND.stop()  # 停止背景音乐
                    player.save_failed_level()

        # 子弹碰撞
        for bullet in spaceship.bullets[:]:
            bullet_rect = pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height)
            for alien in aliens[:]:
                alien_rect = pygame.Rect(alien.x, alien.y, alien.width, alien.height)
                if bullet_rect.colliderect(alien_rect):
                    hit_sound.play()  # 播放击中音效
                    alien.health -= bullet.damage
                    if bullet.type != 'super_laser':
                        spaceship.bullets.remove(bullet)
                    if alien.health <= 0:
                        aliens.remove(alien)
                        aliens.append(Alien(player.level))
                        player.update_score(10 * player.level)
                        player.update_points(5 * player.level)
                        player.kill_count += 1
                        if player.kill_count >= player.level_kill_target:
                            player.level_up()
                            aliens = [Alien(player.level) for _ in range(5 + player.level * 2)]
                            background = Background(player.level)
                            player.save_current_progress()
                    break

        # ========== 强制绘制所有元素（确保层级正确） ==========
        background.draw()  # 1. 背景图（最底层）
        spaceship.draw()  # 2. 飞船
        for alien in aliens:  # 3. 外星人
            alien.draw()
        for bullet in spaceship.bullets:  # 4. 子弹
            bullet.draw()

        # 绘制信息面板（红圈生命值）
        # 生命标题
        life_title = get_font(30).render('生命：', True, RED)
        SCREEN.blit(life_title, (20, 10))
        # 红圈绘制
        circle_radius = 8
        circle_spacing = 20
        start_x = 90
        start_y = 25
        # 实心红圈（当前生命）
        for i in range(current_lives):
            pygame.draw.circle(SCREEN, RED, (start_x + i * circle_spacing, start_y), circle_radius)
        # 空心灰圈（剩余生命）
        for i in range(current_lives, max_lives):
            pygame.draw.circle(SCREEN, GRAY, (start_x + i * circle_spacing, start_y), circle_radius, 2)

        # 其他信息
        weapon_text = get_font(30).render(f'武器：{player.current_weapon}', True, WHITE)
        SCREEN.blit(weapon_text, (20, 50))

        score_text = get_font(30).render(f'分数：{player.current_score}', True, YELLOW)
        SCREEN.blit(score_text, (200, 10))

        level_text = get_font(30).render(f'关卡：{player.level}', True, BLUE)
        SCREEN.blit(level_text, (380, 10))

        kill_text = get_font(30).render(f'击杀：{player.kill_count}/{player.level_kill_target}', True, GREEN)
        SCREEN.blit(kill_text, (550, 10))

        # 无敌提示
        if invulnerable and (current_time // 100) % 2 == 0:
            inv_text = get_font(30).render('无敌中...', True, WHITE)
            SCREEN.blit(inv_text, (20, 90))

        pygame.display.flip()


# ===================== 程序入口 =====================
if __name__ == '__main__':
    # 调试：输出当前工作目录
    print(f"当前工作目录：{os.getcwd()}")
    print(f"桌面路径：{DESKTOP_PATH}")

    try:
        init_weapon_db()
        login_register_interface()
    except Exception as e:
        print(f"程序异常：{e}")
        traceback.print_exc()
        pygame.quit()
        sys.exit()