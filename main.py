"""Rock / Paper / Scissors — a dark, animated Tkinter desktop game."""
import math
import os
import sys
import time
import tkinter as tk
from tkinter import font as tkfont

from game_logic import CHOICES, DRAW, LOSE, WIN, Game, computer_choice

# Palette: graphite, off-white, muted lime, and restrained red.
BG = "#101010"
PANEL = "#191919"
PANEL_HOVER = "#202020"
INSET = "#141414"
BORDER = "#2b2b2b"
BORDER_STRONG = "#4a4a46"
LIME = "#C4F06A"
TEXT = "#EDEDE6"
ICON_IDLE = "#A9A9A3"
MUTED = "#7C7C76"
FAINT = "#464642"
RED = "#D4574B"
FRAME_MS = 16
SCALE = 1.0

def px(n):
    return max(1, int(round(n * SCALE)))

def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))

def ease_out(t):
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def ease_out_back(t):
    c1 = 1.70158
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2

def approach(value, goal, step):
    if value < goal:
        return min(goal, value + step)
    return max(goal, value - step)

def round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
        x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
        x1,y2, x1,y2-r, x1,y1+r, x1,y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def prefers_reduced_motion():
    if os.environ.get("RPS_REDUCE_MOTION") == "1" or "--reduce-motion" in sys.argv:
        return True
    if sys.platform == "win32":
        try:
            import ctypes
            enabled = ctypes.c_int(1)
            if ctypes.windll.user32.SystemParametersInfoW(
                0x1042, 0, ctypes.byref(enabled), 0
            ):
                return not bool(enabled.value)
        except Exception:
            pass
    return False

REDUCED = prefers_reduced_motion()

def enable_dpi_awareness():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

def use_dark_title_bar(window):
    if sys.platform != "win32":
        return
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1)
        for attribute in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            )
    except Exception:
        pass

def pick_font_family():
    available = set(tkfont.families())
    for name in ("Segoe UI Variable Text", "Segoe UI", "Inter", "Helvetica Neue", "Helvetica", "DejaVu Sans"):
        if name in available:
            return name
    return "TkDefaultFont"

class Animator:
    """Time-based animation helper that schedules frames without blocking Tk."""

    def __init__(self, root):
        self.root = root
        self.jobs = {}
        self.counter = 0

    def run(self, duration_ms, step, done=None, ease=ease_out):
        if REDUCED or duration_ms <= 0:
            step(1.0)
            if done:
                done()
            return
        self.counter += 1
        key = self.counter
        start = time.perf_counter()

        def tick():
            t = min(1.0, (time.perf_counter() - start) * 1000 / duration_ms)
            step(ease(t) if ease else t)
            if t >= 1:
                self.jobs.pop(key, None)
                if done:
                    done()
            else:
                self.jobs[key] = self.root.after(FRAME_MS, tick)

        tick()

    def cancel_all(self):
        for job in list(self.jobs.values()):
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
        self.jobs.clear()

# Simple custom vector illustrations.
ROCK_BODY = [(-.85,.25),(-.72,-.35),(-.25,-.78),(.35,-.72),(.8,-.28),(.86,.35),(.42,.78),(-.3,.76)]
PAPER_BODY = [(-.58,-.85),(.2,-.85),(.6,-.45),(.6,.85),(-.58,.85)]
PAPER_FOLD = [(.2,-.85),(.2,-.45),(.6,-.45)]
PAPER_LINES = [[(-.32,0),(.34,0)],[(-.32,.3),(.34,.3)],[(-.32,.6),(.08,.6)]]
SCISSOR_BLADE = [(-.09,0),(.09,0),(.03,-.98),(-.03,-.98)]
SCISSOR_HANDLE = [(.2*math.cos(a),.66+.26*math.sin(a)) for a in [i*math.pi/10 for i in range(20)]]

def transform(points, cx, cy, size, rot=0):
    c, s = math.cos(rot), math.sin(rot)
    flat = []
    for x, y in points:
        flat.extend([cx + (x*c-y*s)*size, cy + (x*s+y*c)*size])
    return flat

def draw_icon(canvas, name, cx, cy, size, color, rot=0, spread=0):
    width = max(2, round(size / 15))
    poly = dict(fill="", outline=color, width=width, joinstyle="round")
    line = dict(fill=color, width=width, capstyle="round", joinstyle="round")
    if name == "rock":
        canvas.create_polygon(transform(ROCK_BODY,cx,cy,size,rot), smooth=True, **poly)
        canvas.create_line(transform([(-.55,-.2),(.05,.02),(.4,-.55)],cx,cy,size,rot), **line)
        canvas.create_line(transform([(-.05,.02),(.06,.55)],cx,cy,size,rot), **line)
    elif name == "paper":
        canvas.create_polygon(transform(PAPER_BODY,cx,cy,size,rot), **poly)
        canvas.create_line(transform(PAPER_FOLD,cx,cy,size,rot), **line)
        for points in PAPER_LINES:
            canvas.create_line(transform(points,cx,cy,size,rot), **line)
    else:
        for sign in (1,-1):
            angle = rot + sign*(.14+spread)
            canvas.create_polygon(transform(SCISSOR_BLADE,cx,cy,size,angle), **poly)
            canvas.create_polygon(transform(SCISSOR_HANDLE,cx,cy,size,angle), **poly)
        dot = size*.07
        canvas.create_oval(cx-dot,cy-dot,cx+dot,cy+dot,fill=color,outline=color)

class ChoiceCard(tk.Canvas):
    """Animated choice card with hover lift, icon motion, and press response."""
    def __init__(self, master, name, key_hint, fonts, on_pick):
        super().__init__(master, height=px(166), bg=BG, highlightthickness=0, cursor="hand2")
        self.name, self.key_hint, self.fonts, self.on_pick = name, key_hint, fonts, on_pick
        self.hover = self.hover_goal = 0.0
        self.press = self.press_goal = 0.0
        self.phase = 0.0
        self.selected = False
        self.enabled = True
        self.ticking = False
        self.last_time = time.perf_counter()
        self.bind("<Configure>", lambda _e: self.draw())
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_enter(self, _event):
        if self.enabled:
            self.hover_goal = 1
            self.start()

    def on_leave(self, _event):
        self.hover_goal = 0
        self.press_goal = 0
        self.start()

    def on_press(self, _event):
        if self.enabled:
            self.press_goal = 1
            self.start()

    def on_release(self, event):
        was_pressed = self.press_goal > 0
        self.press_goal = 0
        self.start()
        inside = 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        if self.enabled and was_pressed and inside:
            self.on_pick(self.name)

    def nudge(self):
        self.press = 1
        self.press_goal = 0
        self.start()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        if enabled:
            try:
                under = self.winfo_containing(*self.winfo_pointerxy()) is self
            except tk.TclError:
                under = False
            self.hover_goal = 1 if under else 0
        else:
            self.hover_goal = self.press_goal = 0
        self.start()

    def start(self):
        if not self.ticking:
            self.ticking = True
            self.last_time = time.perf_counter()
            self.tick()

    def tick(self):
        now = time.perf_counter()
        dt = min(now - self.last_time, .05)
        self.last_time = now
        if REDUCED:
            self.hover, self.press = self.hover_goal, self.press_goal
        else:
            self.hover = approach(self.hover, self.hover_goal, dt/.18)
            self.press = approach(self.press, self.press_goal, dt/.07)
            self.phase = self.phase + dt*5 if self.hover > 0 else 0
        self.draw()
        at_goal = self.hover == self.hover_goal and self.press == self.press_goal
        if at_goal and (REDUCED or self.hover_goal == 0):
            self.ticking = False
        else:
            self.after(FRAME_MS, self.tick)

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 40 or h < 40:
            return
        hv, pr = ease_in_out(self.hover), self.press
        lift = 0 if REDUCED else px(5)*hv
        drop = px(3)*pr
        x1, x2 = px(2), w-px(2)
        y1, y2 = px(8)-lift+drop, h-px(10)-lift+drop
        radius = px(14)
        dim = 0 if (self.enabled or self.selected) else .5
        round_rect(self,x1,y1+px(7),x2,y2+px(7),radius,fill="#080808",outline="")
        fill = mix(PANEL,PANEL_HOVER,hv)
        fill = mix(fill,INSET,pr)
        if self.selected:
            fill = mix(fill,LIME,.04)
        border = LIME if self.selected else mix(BORDER,LIME,max(hv*.85,pr))
        round_rect(self,x1,y1,x2,y2,radius,fill=fill,outline=border)
        self.create_text(x1+px(17),y1+px(15),text=self.key_hint,anchor="w",
                         fill=mix(FAINT,LIME,hv),font=self.fonts["tiny"])
        size = (y2-y1)*.26*(1-.07*pr)
        amp = 0 if REDUCED else hv
        s = math.sin(self.phase)
        rot = spread = dy = 0
        if self.name == "rock":
            dy = -abs(s)*.16*size*amp
            rot = .1*math.sin(self.phase*2)*amp
        elif self.name == "paper":
            rot = .16*s*amp
            dy = -.05*size*amp
        else:
            spread = .2*(.5+.5*math.sin(self.phase*2-math.pi/2))*amp
        icon_color = LIME if self.selected else mix(ICON_IDLE,LIME,hv)
        icon_color = mix(icon_color,fill,dim)
        draw_icon(self,self.name,w/2,(y1+y2)/2-px(11)+dy,size,icon_color,rot,spread)
        label_color = LIME if self.selected else mix(MUTED,TEXT,hv)
        self.create_text(w/2,y2-px(28),text=self.name.upper(),fill=mix(label_color,fill,dim),font=self.fonts["label"])
        half = px(14)*(1 if self.selected else hv)
        self.create_line(w/2-half,y2-px(14),w/2+half,y2-px(14),fill=LIME,width=2,capstyle="round")

class Arena(tk.Canvas):
    """Battle area showing the player's move, computer move, and result."""
    def __init__(self, master, fonts):
        super().__init__(master,height=px(220),bg=BG,highlightthickness=0)
        self.fonts = fonts
        self.bind("<Configure>",lambda _e:self.draw())
        self.clear()

    def clear(self):
        self.player = self.cpu = None
        self.player_scale = self.cpu_scale = 1
        self.cpu_dx = 0
        self.cpu_revealed = False
        self.outcome = None
        self.detail = ""
        self.border_to = {"player":BORDER,"cpu":BORDER}
        self.icon_to = {"player":ICON_IDLE,"cpu":ICON_IDLE}
        self.highlight = self.result = 0
        self.draw()

    def start_round(self, player_move):
        self.clear()
        self.player = player_move
        self.player_scale = .55
        self.draw()

    def show_outcome(self, result):
        self.outcome, self.detail = result.outcome, result.explanation
        if result.outcome == WIN:
            self.border_to = {"player":LIME,"cpu":BORDER}
            self.icon_to = {"player":LIME,"cpu":FAINT}
        elif result.outcome == LOSE:
            self.border_to = {"player":BORDER,"cpu":RED}
            self.icon_to = {"player":FAINT,"cpu":RED}
        else:
            self.border_to = {"player":BORDER_STRONG,"cpu":BORDER_STRONG}
            self.icon_to = {"player":TEXT,"cpu":TEXT}
        self.highlight = self.result = 0

    def draw(self):
        self.delete("all")
        w,h = self.winfo_width(),self.winfo_height()
        if w < 80 or h < 80:
            return
        round_rect(self,1,1,w-1,h-1,px(16),fill=PANEL,outline=BORDER)
        slot = max(px(64),min(px(116),h-px(104),w*.23))
        block = px(18)+slot+px(26)
        top = (h-block)/2
        y1,y2 = top+px(18),top+px(18)+slot
        mid_y = (y1+y2)/2
        left = max(slot/2+px(38),w*.2)
        right = w-left
        sides = (("player",left,"YOU",self.player,self.player_scale,True),
                 ("cpu",right,"COMPUTER",self.cpu,self.cpu_scale,self.cpu_revealed))
        for who,cx,title,move,scale,show_name in sides:
            cx += self.cpu_dx if who == "cpu" else 0
            border = mix(BORDER,self.border_to[who],self.highlight)
            self.create_text(cx,top+px(4),text=title,fill=MUTED,font=self.fonts["tiny"])
            round_rect(self,cx-slot/2,y1,cx+slot/2,y2,px(13),fill=INSET,outline=border)
            if move:
                color = mix(ICON_IDLE,self.icon_to[who],self.highlight)
                draw_icon(self,move,cx,mid_y,slot*.27*scale,color)
                if show_name:
                    self.create_text(cx,y2+px(17),text=move.upper(),fill=MUTED,font=self.fonts["tiny"])
            else:
                self.create_line(cx-px(7),mid_y,cx+px(7),mid_y,fill=FAINT,width=2)
        if self.outcome:
            t = self.result
            color = {WIN:LIME,LOSE:RED,DRAW:TEXT}[self.outcome]
            words = {WIN:"YOU WIN",LOSE:"YOU LOSE",DRAW:"DRAW"}
            rise = (1-t)*px(12)
            self.create_text(w/2,mid_y-px(7)+rise,text=words[self.outcome],
                             fill=mix(PANEL,color,t),font=self.fonts["result"])
            self.create_text(w/2,mid_y+px(27)+rise,text=self.detail,
                             fill=mix(PANEL,MUTED,t),font=self.fonts["small"])
        else:
            self.create_text(w/2,mid_y,text="VS",fill=FAINT,font=self.fonts["vs"])

class Scoreboard(tk.Canvas):
    TILES = (("player","PLAYER"),("computer","COMPUTER"),("draws","DRAWS"))
    def __init__(self,master,fonts,animator):
        super().__init__(master,height=px(78),bg=BG,highlightthickness=0)
        self.fonts,self.animator = fonts,animator
        self.bind("<Configure>",lambda _e:self.draw())
        self.reset()

    def reset(self):
        self.values = {"player":0,"computer":0,"draws":0}
        self.settle = {key:1.0 for key,_ in self.TILES}
        self.accent = {key:TEXT for key,_ in self.TILES}
        self.draw()

    def update_scores(self,game,outcome):
        self.values = {"player":game.player_score,"computer":game.computer_score,"draws":game.draws}
        key = {WIN:"player",LOSE:"computer",DRAW:"draws"}[outcome]
        self.accent[key] = {WIN:LIME,LOSE:RED,DRAW:TEXT}[outcome]
        self.animator.run(500,lambda t:self._settle(key,t))

    def _settle(self,key,t):
        self.settle[key] = t
        self.draw()

    def draw(self):
        self.delete("all")
        w,h = self.winfo_width(),self.winfo_height()
        if w < 80:
            return
        gap = px(10)
        tile_w = (w-2*gap)/3
        for i,(key,label) in enumerate(self.TILES):
            x1 = i*(tile_w+gap)
            t = self.settle[key]
            round_rect(self,x1+1,1,x1+tile_w-1,h-1,px(13),fill=PANEL,
                       outline=mix(self.accent[key],BORDER,t))
            self.create_text(x1+px(16),px(18),text=label,anchor="w",fill=MUTED,font=self.fonts["tiny"])
            self.create_text(x1+px(16),h-px(8)+(1-t)*px(8),text=str(self.values[key]),
                             anchor="sw",fill=mix(self.accent[key],TEXT,t),font=self.fonts["score"])

class ScanLine(tk.Canvas):
    """A subtle moving lime detail along the top edge."""
    def __init__(self,master):
        super().__init__(master,height=px(2),bg=BG,highlightthickness=0)
        self.bind("<Configure>",lambda _e:self.draw())
        self.after(33,self.tick)

    def tick(self):
        if not REDUCED and self.winfo_exists():
            self.draw()
            self.after(33,self.tick)

    def draw(self):
        self.delete("all")
        w = self.winfo_width()
        self.create_rectangle(0,0,w,px(2),fill=mix(BG,BORDER,.6),outline="")
        if REDUCED or w <= 0:
            return
        head = (time.perf_counter()%14)/14
        beam = w*.25
        start = head*(w+beam)-beam
        seg = beam/28
        for i in range(28):
            strength = math.sin(math.pi*i/27)**2
            self.create_rectangle(start+i*seg,0,start+(i+1)*seg+1,px(2),
                                  fill=mix(mix(BG,BORDER,.6),LIME,strength*.5),outline="")

class TextButton(tk.Label):
    def __init__(self,master,text,command,font):
        super().__init__(master,text=text,font=font,fg=MUTED,bg=BG,cursor="hand2",
                         padx=px(12),pady=px(6),highlightthickness=1,
                         highlightbackground=BORDER,highlightcolor=BORDER)
        self.command = command
        self.bind("<Enter>",lambda _e:self.paint(LIME,LIME,BG))
        self.bind("<Leave>",lambda _e:self.paint(MUTED,BORDER,BG))
        self.bind("<ButtonPress-1>",lambda _e:self.paint(TEXT,LIME,PANEL))
        self.bind("<ButtonRelease-1>",self.on_release)

    def paint(self,fg,border,bg):
        self.configure(fg=fg,bg=bg,highlightbackground=border,highlightcolor=border)

    def on_release(self,event):
        inside = 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        self.paint(LIME if inside else MUTED,LIME if inside else BORDER,BG)
        if inside:
            self.command()

class App(tk.Tk):
    KEYMAP = {"r":"rock","p":"paper","s":"scissors","1":"rock","2":"paper","3":"scissors"}
    INTRO = "Choose your move. R, P and S keys work too."

    def __init__(self):
        enable_dpi_awareness()
        super().__init__()
        global SCALE
        SCALE = self.winfo_fpixels("1i")/96
        self.title("Rock / Paper / Scissors")
        self.configure(bg=BG)
        self.minsize(px(620),px(650))
        self.place_window(px(760),px(730))
        use_dark_title_bar(self)
        family = pick_font_family()
        self.fonts = {
            "title":(family,11,"bold"),"small":(family,10),"tiny":(family,8,"bold"),
            "label":(family,10,"bold"),"score":(family,26,"bold"),
            "result":(family,22,"bold"),"vs":(family,13,"bold")
        }
        self.game = Game()
        self.animator = Animator(self)
        self.busy = False
        self.round_token = 0
        self.build()
        self.bind("<Key>",self.on_key)
        self.bind("<Control-r>",lambda _e:self.reset())
        self.set_status(self.INTRO)
        self.protocol("WM_DELETE_WINDOW",self.close)

    def place_window(self,width,height):
        width = min(width,self.winfo_screenwidth()-30)
        height = min(height,self.winfo_screenheight()-60)
        x = max(0,(self.winfo_screenwidth()-width)//2)
        y = max(0,(self.winfo_screenheight()-height)//3)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def build(self):
        ScanLine(self).pack(fill="x")
        body = tk.Frame(self,bg=BG)
        body.pack(fill="both",expand=True,padx=px(25),pady=(px(20),px(14)))
        body.columnconfigure(0,weight=1)
        body.rowconfigure(2,weight=1)
        header = tk.Frame(body,bg=BG)
        header.grid(row=0,column=0,sticky="ew")
        header.columnconfigure(0,weight=1)
        title = tk.Frame(header,bg=BG)
        title.grid(row=0,column=0,sticky="w")
        for word,color in (("ROCK",TEXT),(" / ",LIME),("PAPER",TEXT),(" / ",LIME),("SCISSORS",TEXT)):
            tk.Label(title,text=word,font=self.fonts["title"],fg=color,bg=BG,padx=0).pack(side="left")
        tk.Label(header,text="A game of chance.",font=self.fonts["small"],fg=MUTED,bg=BG).grid(
            row=1,column=0,sticky="w",pady=(px(3),0))
        right = tk.Frame(header,bg=BG)
        right.grid(row=0,column=1,rowspan=2,sticky="e")
        tk.Label(right,text="ROUNDS",font=self.fonts["tiny"],fg=MUTED,bg=BG).pack(side="left")
        self.rounds_label = tk.Label(right,text="00",font=self.fonts["label"],fg=TEXT,bg=BG,width=3)
        self.rounds_label.pack(side="left",padx=(px(4),px(12)))
        TextButton(right,"RESET",self.reset,self.fonts["tiny"]).pack(side="left")
        self.scoreboard = Scoreboard(body,self.fonts,self.animator)
        self.scoreboard.grid(row=1,column=0,sticky="ew",pady=(px(20),0))
        self.arena = Arena(body,self.fonts)
        self.arena.grid(row=2,column=0,sticky="nsew",pady=(px(13),0))
        cards = tk.Frame(body,bg=BG)
        cards.grid(row=3,column=0,sticky="ew",pady=(px(13),0))
        self.cards = {}
        for i,(name,hint) in enumerate(zip(CHOICES,("R","P","S"))):
            cards.columnconfigure(i,weight=1,uniform="cards")
            card = ChoiceCard(cards,name,hint,self.fonts,self.pick)
            card.grid(row=0,column=i,sticky="ew",padx=(0 if i==0 else px(10),0))
            self.cards[name] = card
        self.status = tk.Label(body,text="",font=self.fonts["small"],fg=MUTED,bg=BG)
        self.status.grid(row=4,column=0,pady=(px(10),0))

    def set_status(self,message):
        self.status.configure(text=message,fg=MUTED)

    def set_rounds(self,number):
        self.rounds_label.configure(text=f"{number:02d}",fg=LIME)
        self.animator.run(500,lambda t:self.rounds_label.configure(fg=mix(LIME,TEXT,t)))

    def on_key(self,event):
        if event.state & 0x4:
            return
        name = self.KEYMAP.get(event.keysym.lower())
        if name and not self.busy:
            self.cards[name].nudge()
            self.pick(name)

    def pick(self,name):
        if self.busy or name not in CHOICES:
            return
        self.busy = True
        self.round_token += 1
        token = self.round_token
        for card in self.cards.values():
            card.selected = card.name == name
            card.set_enabled(False)
        self.set_status("The computer is choosing...")
        self.arena.start_round(name)
        computer = computer_choice()

        def pop(t):
            if token != self.round_token:
                return
            self.arena.player_scale = .55+.45*t
            self.arena.draw()
        self.animator.run(220,pop,done=lambda:self.shuffle(name,computer,token),ease=ease_out_back)

    def shuffle(self,player,computer,token):
        if token != self.round_token:
            return
        first = CHOICES.index(computer)
        def step(t):
            if token != self.round_token:
                return
            self.arena.cpu = CHOICES[(first+int(t*9))%3]
            self.arena.cpu_scale = .92
            self.arena.cpu_dx = math.sin(t*48)*px(4)*(1-t)
            self.arena.draw()
        self.animator.run(650,step,ease=None,done=lambda:self.reveal(player,computer,token))

    def reveal(self,player,computer,token):
        if token != self.round_token:
            return
        self.arena.cpu = computer
        self.arena.cpu_dx = 0
        self.arena.cpu_revealed = True
        def pop(t):
            if token != self.round_token:
                return
            self.arena.cpu_scale = .6+.4*t
            self.arena.draw()
        self.animator.run(240,pop,done=lambda:self.finish(player,computer,token),ease=ease_out_back)

    def finish(self,player,computer,token):
        if token != self.round_token:
            return
        result = self.game.play(player,computer)
        self.arena.show_outcome(result)
        self.scoreboard.update_scores(self.game,result.outcome)
        self.set_rounds(self.game.rounds)
        messages = {
            WIN:f"Round {result.number} goes to you. Choose your next move.",
            LOSE:f"Round {result.number} goes to the computer. Try again.",
            DRAW:f"Round {result.number} is a draw. Go again."
        }
        self.set_status(messages[result.outcome])
        def show(t):
            if token == self.round_token:
                self.arena.highlight = self.arena.result = t
                self.arena.draw()
        self.animator.run(320,show,done=lambda:self.round_over(token))

    def round_over(self,token):
        if token != self.round_token:
            return
        self.busy = False
        for card in self.cards.values():
            card.set_enabled(True)

    def reset(self):
        self.round_token += 1
        self.animator.cancel_all()
        self.game.reset()
        self.busy = False
        self.arena.clear()
        self.scoreboard.reset()
        self.rounds_label.configure(text="00",fg=TEXT)
        for card in self.cards.values():
            card.selected = False
            card.set_enabled(True)
        self.set_status(self.INTRO)

    def close(self):
        self.round_token += 1
        self.animator.cancel_all()
        self.destroy()

if __name__ == "__main__":
    App().mainloop()
