import sqlite3
import csv
import pygame
# 导入所有需要的常量
from config import (
    DB_FILE, SOUND_DIR, IMAGE_DIR,
    BLACK, GREEN, RED, BLUE, YELLOW, WHITE, GRAY
)


# ===================== 数据库工具 =====================
def init_db():
    """初始化数据库（创建表+默认武器）"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 玩家表
    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  best_score INTEGER DEFAULT 0,
                  total_points INTEGER DEFAULT 0)''')

    # 武器商店表
    c.execute('''CREATE TABLE IF NOT EXISTS weapons
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  damage INTEGER NOT NULL,
                  price INTEGER NOT NULL,
                  bullet_type TEXT NOT NULL)''')

    # 初始化默认武器
    c.execute('SELECT COUNT(*) FROM weapons')
    if c.fetchone()[0] == 0:
        default_weapons = [
            ('普通子弹', 10, 0, 'normal'),
            ('激光炮', 30, 50, 'laser'),
            ('导弹', 50, 100, 'missile')
        ]
        c.executemany('INSERT INTO weapons VALUES (NULL,?,?,?,?)', default_weapons)

    conn.commit()
    conn.close()


def export_data(filename_prefix):
    """导出玩家/武器数据到CSV"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 导出玩家数据
    c.execute('SELECT * FROM players')
    players = c.fetchall()
    with open(f'{filename_prefix}_players.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', '用户名', '密码', '最佳成绩', '总积分'])
        writer.writerows(players)

    # 导出武器数据
    c.execute('SELECT * FROM weapons')
    weapons = c.fetchall()
    with open(f'{filename_prefix}_weapons.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', '名称', '伤害', '价格', '子弹类型'])
        writer.writerows(weapons)

    conn.close()
    return True


def import_data(player_file, weapon_file):
    """从CSV导入玩家/武器数据"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        # 导入玩家数据
        with open(player_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            c.executemany('REPLACE INTO players VALUES (?,?,?,?,?)', reader)

        # 导入武器数据
        with open(weapon_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            c.executemany('REPLACE INTO weapons VALUES (?,?,?,?,?)', reader)

        conn.commit()
        return True
    except Exception as e:
        print(f"导入数据失败: {e}")
        return False
    finally:
        conn.close()


def manage_weapon(action, name, damage=None, price=None, bullet_type=None):
    """管理武器（增/删/改）"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        if action == 'add':
            c.execute('INSERT INTO weapons (name, damage, price, bullet_type) VALUES (?,?,?,?)',
                      (name, damage, price, bullet_type))
        elif action == 'delete':
            c.execute('DELETE FROM weapons WHERE name=?', (name,))
        elif action == 'update':
            c.execute('UPDATE weapons SET damage=?, price=?, bullet_type=? WHERE name=?',
                      (damage, price, bullet_type, name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"武器名称 {name} 已存在（添加失败）")
        return False
    except Exception as e:
        print(f"武器管理失败: {e}")
        return False
    finally:
        conn.close()


# ===================== 资源加载工具 =====================
def load_sound(filename):
    """加载音效（兼容文件缺失）"""
    try:
        return pygame.mixer.Sound(f"{SOUND_DIR}{filename}")
    except:
        # 音效文件缺失时返回空函数（静音）
        class DummySound:
            def play(self): pass

        return DummySound()


def load_image(filename, width, height):
    """加载图片（兼容文件缺失，用纯色矩形替代）"""
    try:
        img = pygame.image.load(f"{IMAGE_DIR}{filename}").convert_alpha()
        return pygame.transform.scale(img, (width, height))
    except Exception as e:
        # 捕获所有异常（文件缺失/路径错误等），确保兼容逻辑生效
        print(f"加载图片 {filename} 失败: {e}，使用纯色矩形替代")
        # 图片缺失时用纯色矩形替代
        surf = pygame.Surface((width, height))
        surf.set_colorkey(BLACK)  # 透明背景
        if "ship" in filename:
            surf.fill(GREEN)
        elif "alien" in filename:
            surf.fill(RED)
        elif "normal" in filename:
            surf.fill(WHITE)
        elif "laser" in filename:
            surf.fill(BLUE)
        elif "missile" in filename:
            surf.fill(YELLOW)
        else:
            surf.fill(GRAY)
        return surf


# ===================== 验证工具 =====================
def login(username, password):
    """玩家登录验证"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE username=? AND password=?', (username, password))
    result = c.fetchone()
    conn.close()
    return result is not None


def register(username, password):
    """玩家注册"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO players (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()