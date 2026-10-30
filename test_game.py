# -*- coding: utf-8 -*-
"""
اختبار سريع (Smoke Test) للعبة knockout_legends.py
- لو pygame مثبّت: يشتغل بدون نافذة (SDL dummy) على pygame الحقيقي.
- لو مش مثبّت: يستخدم نسخة وهمية صغيرة من pygame لفحص المنطق فقط.

التشغيل:  python test_knockout_legends.py
(حطه في نفس فولدر knockout_legends.py)
"""
import os, sys, types, random, itertools

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pygame
    USING_STUB = False
except ImportError:
    USING_STUB = True
    _c = itertools.count(1)
    _consts = {}

    class _Mod(types.ModuleType):
        def __getattr__(self, name):          # أي ثابت K_* / MOUSE* ... إلخ
            if name.isupper() or name.startswith("K_"):
                return _consts.setdefault(name, next(_c))
            raise AttributeError(name)

    pygame = _Mod("pygame")

    class Rect:
        def __init__(s, *a):
            if len(a) == 1:
                a = tuple(a[0])
            s.x, s.y, s.w, s.h = [float(v) for v in a]
        width = property(lambda s: s.w)
        height = property(lambda s: s.h)
        size = property(lambda s: (s.w, s.h))
        center = property(lambda s: (s.x + s.w / 2, s.y + s.h / 2))
        centerx = property(lambda s: s.x + s.w / 2)
        centery = property(lambda s: s.y + s.h / 2)
        bottom = property(lambda s: s.y + s.h)
        def collidepoint(s, p, *a): return s.x <= p[0] <= s.x + s.w and s.y <= p[1] <= s.y + s.h
        def move(s, dx, dy): return Rect(s.x + dx, s.y + dy, s.w, s.h)
        def inflate(s, dx, dy): return Rect(s.x - dx / 2, s.y - dy / 2, s.w + dx, s.h + dy)

    class Surface:
        def __init__(s, size=(1, 1), flags=0): s.size = size
        def get_rect(s, **k): return Rect(0, 0, *s.size)
        def blit(s, *a, **k): pass
        def fill(s, *a): pass
        def convert(s): return s
        def set_clip(s, *a): pass

    class _Font:
        def render(s, t, aa, c): return Surface((len(str(t)) * 10, 20))

    class _Draw:
        def __getattr__(s, n):
            def f(surf, color, *a, **k):
                for v in a:                      # يتأكد إن الإحداثيات أرقام صحيحة
                    if isinstance(v, (tuple, list)) and v:
                        for q in (v if isinstance(v[0], (tuple, list)) else [v]):
                            [float(x) for x in q]
            return f

    class _Snd:
        def __init__(s, buffer=None): assert buffer and len(buffer) > 0
        def play(s): pass

    pygame.error = Exception
    pygame.Rect, pygame.Surface = Rect, Surface
    pygame.font = types.SimpleNamespace(SysFont=lambda *a, **k: _Font())
    pygame.draw = _Draw()
    pygame.transform = types.SimpleNamespace(rotozoom=lambda s, a, z: Surface(s.size))
    pygame.mixer = types.SimpleNamespace(init=lambda *a, **k: None, quit=lambda: None,
                                         get_init=lambda: True, Sound=_Snd)
    pygame.key = types.SimpleNamespace(get_pressed=lambda: {})
    pygame.mouse = types.SimpleNamespace(get_pos=lambda: (100, 100))
    pygame.display = types.SimpleNamespace(set_mode=lambda s: Surface(s), set_caption=lambda t: None,
                                           flip=lambda: None)
    pygame.time = types.SimpleNamespace(Clock=lambda: types.SimpleNamespace(tick=lambda f: 16))
    pygame.event = types.SimpleNamespace(get=lambda: [],
                                         Event=lambda t, **k: types.SimpleNamespace(type=t, **k))
    pygame.init = lambda: None
    pygame.quit = lambda: None
    sys.modules["pygame"] = pygame

import knockout_legends as K

# ---- لوحة مفاتيح وهمية نتحكم فيها من الاختبار (تعمل مع pygame الحقيقي والوهمي) ----
class FakeKeys(dict):
    def __getitem__(self, k): return self.get(k, False)
KEYS = FakeKeys()
pygame.key.get_pressed = lambda: KEYS

E = pygame.event.Event
g = K.Game()


def frames(n):
    for _ in range(n):
        g.update(1 / 60)
        g.draw()


def click(pos):
    g.handle_event(E(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


print("pygame:", "STUB (منطق فقط)" if USING_STUB else pygame.version.ver)

# 1) القائمة -> المتجر -> الشراء
frames(5)
g.set_state("shop"); frames(3)
tyson_card = (30 + 310 * 1 + 50, 125 + 230)
click(tyson_card); frames(2)                       # فلوس مش كفاية
assert 1 not in g.owned, "اشترى بدون فلوس!"
g.money = 10000
click(tyson_card); frames(2)
assert 1 in g.owned and g.selected == 1 and g.money == 10000 - 2500
print("OK: المتجر (رفض الشراء بدون فلوس + شراء ناجح)")

# 2) المستويات: المغلق ما يفتحش، والأول يفتح
g.set_state("levels"); frames(3)
click((67 + 6 * 166 + 20, 170 + 2 * 142 + 20)); assert g.state == "levels"   # مستوى 21 مقفول
click((100, 200)); assert g.state == "fight"
print("OK: شاشة المستويات")

# 3) قتال كامل بمدخلات عشوائية على مستويات 1 و10 و21
random.seed(3)
for lvl in (1, 10, 21):
    g.start_fight(lvl)
    f = g.fight
    for i in range(60 * 40):
        KEYS.clear()
        if i % 90 < 40:
            KEYS[pygame.K_a if (i // 90) % 2 else pygame.K_d] = True
        if i % 200 > 150:
            KEYS[pygame.K_s] = True
        if i % 25 == 0:
            f.handle_event(E(pygame.KEYDOWN, key=random.choice([pygame.K_j, pygame.K_k])))
        if i % 300 == 0:
            f.handle_event(E(pygame.MOUSEWHEEL, y=random.choice([-1, 1])))
        g.update(1 / 60); g.draw()
        if g.state != "fight":
            break
    KEYS.clear()
    print(f"OK: مستوى {lvl} -> {g.state} (فوز={g.result and g.result['win']})")

# 4) الفوز: +1000 وفتح المستوى التالي، والخسارة: نفس المستوى
g.money, g.progress = 0, 1
g.start_fight(1); g.fight.opp.hp = 0; g.fight.opp.state = "ko"
g.fight.end_fight(True, "K.O.!"); frames(60 * 4)
assert g.state == "result" and g.money == K.WIN_REWARD and g.progress == 2 and g.next_level == 2
g.start_fight(2); g.fight.player.hp = 0; g.fight.player.state = "ko"
g.fight.end_fight(False, "K.O.!"); frames(60 * 4)
assert g.state == "result" and g.money == K.WIN_REWARD and g.next_level == 2 and g.result["win"] is False
print("OK: مكافأة 1000 + تقدم للمستوى التالي، والخسارة تعيد نفس المستوى")

# 5) التقدم التلقائي بعد انتهاء العدّاد + الإيقاف المؤقت
g.result["timer"] = 0.01; frames(3)
assert g.state == "fight" and g.fight.level == 2
g.fight.paused = True; frames(2)
print("OK: التقدم التلقائي + Pause")

# 6) كل الخلفيات الـ 21 تترسم بدون أخطاء
for i in range(K.NUM_LEVELS):
    g.start_fight(i + 1); frames(3)
print("OK: الخلفيات الـ 21")
print("\nALL TESTS PASSED")