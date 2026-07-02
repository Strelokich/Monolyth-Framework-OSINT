import tkinter as tk
from tkinter import ttk, simpledialog, colorchooser, filedialog, messagebox
import json
import math
import time
import uuid

#краска
BG          = "#0a0a14"
BG2         = "#0f0f1e"
PANEL       = "#12122a"
BORDER      = "#1e1e4a"
ACCENT1     = "#4040ff"
ACCENT2     = "#8800ff"
ACCENT3     = "#00cfff"
TEXT        = "#c8c8ff"
TEXT_DIM    = "#5555aa"
TEXT_BRIGHT = "#ffffff"
SUCCESS     = "#00ff99"
DANGER      = "#ff3366"
WARN        = "#ffaa00"

NODE_TYPES = {
    "PERSON":    {"color": "#4040ff", "border": "#6666ff", "body": "#0d0d2e", "strip": "#1a1a44", "icon": "⬡"},
    "DOMAIN":    {"color": "#8800ff", "border": "#aa44ff", "body": "#110022", "strip": "#220044", "icon": "◈"},
    "IP":        {"color": "#00cfff", "border": "#44ddff", "body": "#002233", "strip": "#003344", "icon": "◉"},
    "EMAIL":     {"color": "#00ff99", "border": "#44ffbb", "body": "#002211", "strip": "#003322", "icon": "▣"},
    "PHONE":     {"color": "#ffaa00", "border": "#ffcc44", "body": "#221500", "strip": "#332200", "icon": "◆"},
    "ORG":       {"color": "#ff3366", "border": "#ff6688", "body": "#220011", "strip": "#330022", "icon": "▲"},
    "LOCATION":  {"color": "#aa44ff", "border": "#cc66ff", "body": "#150022", "strip": "#220033", "icon": "◍"},
    "USERNAME":  {"color": "#00cfff", "border": "#44eeff", "body": "#002233", "strip": "#003344", "icon": "▷"},
    "FILE":      {"color": "#5555aa", "border": "#7777cc", "body": "#0d0d22", "strip": "#1a1a33", "icon": "▪"},
    "NOTE":      {"color": "#555577", "border": "#777799", "body": "#0d0d18", "strip": "#1a1a28", "icon": "▫"},
}

W, H = 1400, 860
CANVAS_W, CANVAS_H = 6000, 6000
NODE_W, NODE_H = 130, 44

#main app
class Board:
    def __init__(self, root):
        self.root = root
        self.root.title("MONOLYTH :: Investigation Board")
        self.root.configure(bg=BG)
        self.root.geometry(f"{W}x{H}")
        self.root.minsize(900, 600)

        self.nodes = {}       # id - node dict
        self.edges = {}       # id - edge dict
        self.selected = set() # selected node ids
        self.drag_data = {}
        self.connect_mode = False
        self.connect_src  = None
        self.pan_data     = {}
        self.edge_draw_id = None
        self.search_highlights = set()
        self.canvas_offset = [CANVAS_W//2 - W//2, CANVAS_H//2 - H//2]

        self._build_ui()
        self._bind_events()
        self._draw_grid()
        self._status("Board ready — right-click canvas to add node")

    #UI
    def _build_ui(self):
        #top toolbar
        tb = tk.Frame(self.root, bg=PANEL, height=44)
        tb.pack(fill="x", side="top")
        tb.pack_propagate(False)

        self._btn(tb, "＋ ADD NODE",    self._menu_add_node,  ACCENT1)
        self._btn(tb, "⟶ CONNECT",     self._toggle_connect, ACCENT2, key="connect_btn")
        self._btn(tb, "✕ DELETE",      self._delete_selected,DANGER)
        self._btn(tb, "⊞ AUTO LAYOUT", self._auto_layout,    "#334")
        self._btn(tb, "⌖ CENTER",      self._center_view,    "#334")
        self._btn(tb, "▣ CLEAR ALL",   self._clear_all,      "#334")

        tk.Frame(tb, bg=PANEL, width=20).pack(side="left")

        #search
        tk.Label(tb, text="SEARCH:", bg=PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8, "bold")).pack(side="left", padx=(8,2))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        se = tk.Entry(tb, textvariable=self.search_var, bg=BG2, fg=TEXT_BRIGHT,
                      insertbackground=ACCENT3, relief="flat",
                      font=("Courier New", 9), width=18)
        se.pack(side="left", padx=2, ipady=3)

        tk.Frame(tb, bg=PANEL).pack(side="left", expand=True, fill="x")

        #save/load
        self._btn(tb, "💾 SAVE", self._save, SUCCESS)
        self._btn(tb, "📂 LOAD", self._load, WARN)

        # zoom
        tk.Label(tb, text="ZOOM:", bg=PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8)).pack(side="left", padx=(12,2))
        self.zoom_var = tk.DoubleVar(value=1.0)
        self.zoom_label = tk.Label(tb, text="100%", bg=PANEL, fg=ACCENT3,
                                   font=("Courier New", 8, "bold"), width=5)
        self.zoom_label.pack(side="left")

        #main area
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        #left sidebar
        sidebar = tk.Frame(main, bg=PANEL, width=130)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="◈ ENTITIES", bg=PANEL, fg=ACCENT2,
                 font=("Courier New", 8, "bold"), pady=8).pack()

        for ntype, cfg in NODE_TYPES.items():
            f = tk.Frame(sidebar, bg=PANEL, cursor="hand2")
            f.pack(fill="x", padx=4, pady=1)
            tk.Label(f, text=f" {cfg['icon']} {ntype}", bg=PANEL,
                     fg=cfg["color"], font=("Courier New", 8, "bold"),
                     anchor="w").pack(fill="x", padx=4, pady=2)
            f.bind("<Button-1>", lambda e, t=ntype: self._quick_add(t))
            f.winfo_children()[0].bind("<Button-1>", lambda e, t=ntype: self._quick_add(t))

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=4, pady=8)

        #properties panel
        tk.Label(sidebar, text="◈ PROPERTIES", bg=PANEL, fg=ACCENT2,
                 font=("Courier New", 8, "bold"), pady=4).pack()
        self.prop_frame = tk.Frame(sidebar, bg=PANEL)
        self.prop_frame.pack(fill="both", padx=4)

        #canvas
        canvas_frame = tk.Frame(main, bg=BG)
        canvas_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=BG, highlightthickness=0,
                                scrollregion=(0, 0, CANVAS_W, CANVAS_H),
                                cursor="crosshair")
        hbar = tk.Scrollbar(canvas_frame, orient="horizontal",
                            command=self.canvas.xview, bg=BG2)
        vbar = tk.Scrollbar(canvas_frame, orient="vertical",
                            command=self.canvas.yview, bg=BG2)
        hbar.pack(side="bottom", fill="x")
        vbar.pack(side="right",  fill="y")
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.xview_moveto(self.canvas_offset[0] / CANVAS_W)
        self.canvas.yview_moveto(self.canvas_offset[1] / CANVAS_H)

        #status bar
        self.status_var = tk.StringVar(value="")
        sb = tk.Label(self.root, textvariable=self.status_var, bg=BG2,
                      fg=TEXT_DIM, font=("Courier New", 8), anchor="w",
                      padx=8, pady=2)
        sb.pack(fill="x", side="bottom")

        #right-click context menu
        self.ctx_menu = tk.Menu(self.root, tearoff=0, bg=PANEL, fg=TEXT,
                                activebackground=ACCENT1, activeforeground=TEXT_BRIGHT,
                                font=("Courier New", 9), bd=0)
        self.ctx_menu.add_command(label="＋ Add node here", command=self._ctx_add)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="⟶ Connect to...", command=self._toggle_connect)
        self.ctx_menu.add_command(label="✎ Rename", command=self._rename_selected)
        self.ctx_menu.add_command(label="✕ Delete selected", command=self._delete_selected)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="⊞ Auto layout", command=self._auto_layout)

        self._ctx_x = self._ctx_y = 0

    def _btn(self, parent, text, cmd, color, key=None):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=color, fg=TEXT_BRIGHT, relief="flat",
                      font=("Courier New", 8, "bold"), padx=10, pady=6,
                      cursor="hand2", activebackground=BG2,
                      activeforeground=TEXT_BRIGHT, bd=0)
        b.pack(side="left", padx=2, pady=4)
        if key:
            setattr(self, key, b)
        return b

    #events
    def _bind_events(self):
        c = self.canvas
        c.bind("<ButtonPress-1>",   self._on_lclick)
        c.bind("<B1-Motion>",       self._on_drag)
        c.bind("<ButtonRelease-1>", self._on_release)
        c.bind("<ButtonPress-3>",   self._on_rclick)
        c.bind("<Double-Button-1>", self._on_dblclick)
        c.bind("<MouseWheel>",      self._on_zoom)
        c.bind("<Button-4>",        self._on_zoom)
        c.bind("<Button-5>",        self._on_zoom)
        c.bind("<ButtonPress-2>",   self._pan_start)
        c.bind("<B2-Motion>",       self._pan_move)
        c.bind("<Delete>",          lambda e: self._delete_selected())
        c.bind("<Escape>",          self._cancel_connect)
        self.root.bind("<Control-z>", lambda e: None)
        self.root.bind("<Control-a>", lambda e: self._select_all())
        c.focus_set()

    def _canvas_coords(self, event):
        return (self.canvas.canvasx(event.x),
                self.canvas.canvasy(event.y))

    def _on_lclick(self, event):
        cx, cy = self._canvas_coords(event)
        nid = self._node_at(cx, cy)

        if self.connect_mode:
            if nid:
                if self.connect_src is None:
                    self.connect_src = nid
                    self._status(f"Connect: source = {self.nodes[nid]['label']} — click target")
                elif nid != self.connect_src:
                    self._add_edge(self.connect_src, nid)
                    self.connect_src = None
                    self._status("Edge added — click next source or press Esc")
            return

        if nid:
            if event.state & 0x0004:  #Ctrl
                if nid in self.selected:
                    self.selected.discard(nid)
                else:
                    self.selected.add(nid)
            else:
                if nid not in self.selected:
                    self.selected = {nid}
            self.drag_data = {"x": cx, "y": cy, "moved": False}
            self._show_props(nid)
        else:
            self.selected = set()
            self._hide_props()
            self.drag_data = {"x": cx, "y": cy, "sel_start": (cx, cy), "sel_rect": None}

        self._redraw()

    def _on_drag(self, event):
        if not self.drag_data:
            return
        cx, cy = self._canvas_coords(event)
        dx = cx - self.drag_data["x"]
        dy = cy - self.drag_data["y"]
        self.drag_data["x"] = cx
        self.drag_data["y"] = cy

        if self.selected and "sel_start" not in self.drag_data:
            self.drag_data["moved"] = True
            z = self.zoom_var.get()
            for nid in self.selected:
                self.nodes[nid]["x"] += dx / z
                self.nodes[nid]["y"] += dy / z
            self._redraw()
        elif "sel_start" in self.drag_data:
            sx, sy = self.drag_data["sel_start"]
            if self.drag_data.get("sel_rect"):
                self.canvas.delete(self.drag_data["sel_rect"])
            self.drag_data["sel_rect"] = self.canvas.create_rectangle(
                sx, sy, cx, cy,
                outline=ACCENT3, dash=(4,4), width=1, fill="")
            # highlight nodes inside rect
            x0,y0,x1,y1 = min(sx,cx), min(sy,cy), max(sx,cx), max(sy,cy)
            z = self.zoom_var.get()
            self.selected = set()
            for nid, n in self.nodes.items():
                nx = n["x"]*z; ny = n["y"]*z
                if x0 <= nx <= x1 and y0 <= ny <= y1:
                    self.selected.add(nid)
            self._redraw()
            if self.drag_data.get("sel_rect"):
                self.canvas.create_rectangle(
                    sx, sy, cx, cy,
                    outline=ACCENT3, dash=(4,4), width=1, fill="",
                    tags="selrect")

        if self.connect_mode and self.connect_src:
            if self.edge_draw_id:
                self.canvas.delete(self.edge_draw_id)
            n = self.nodes[self.connect_src]
            z = self.zoom_var.get()
            sx, sy = n["x"]*z, n["y"]*z
            self.edge_draw_id = self.canvas.create_line(
                sx, sy, cx, cy,
                fill=ACCENT2, width=1, dash=(6,3), tags="tmp")
    def _on_release(self, event):
        if "sel_rect" in self.drag_data:
            self.canvas.delete("selrect")
            if self.drag_data.get("sel_rect"):
                self.canvas.delete(self.drag_data["sel_rect"])
        self.drag_data = {}
    def _on_rclick(self, event):
        cx, cy = self._canvas_coords(event)
        self._ctx_x, self._ctx_y = cx, cy
        nid = self._node_at(cx, cy)
        if nid and nid not in self.selected:
            self.selected = {nid}
            self._redraw()
        self.ctx_menu.tk_popup(event.x_root, event.y_root)
    def _on_dblclick(self, event):
        cx, cy = self._canvas_coords(event)
        nid = self._node_at(cx, cy)
        if nid:
            self._rename_node(nid)
    def _on_zoom(self, event):
        if hasattr(event, "delta") and event.delta:
            factor = 1.1 if event.delta > 0 else 0.9
        else:
            factor = 1.1 if event.num == 4 else 0.9
        z = max(0.2, min(3.0, self.zoom_var.get() * factor))
        self.zoom_var.set(z)
        self.zoom_label.config(text=f"{int(z*100)}%")
        self._redraw()
    def _pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
    def _pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    def _cancel_connect(self, event=None):
        self.connect_mode = False
        self.connect_src  = None
        if self.edge_draw_id:
            self.canvas.delete(self.edge_draw_id)
        self.connect_btn.config(bg=ACCENT2)
        self._status("Connect mode off")
        self._redraw()
    def _on_search(self, *_):
        q = self.search_var.get().lower().strip()
        if q:
            self.search_highlights = {
                nid for nid, n in self.nodes.items()
                if q in n["label"].lower() or q in n.get("notes","").lower()
            }
        else:
            self.search_highlights = set()
        self._redraw()

    #operation
    def _node_at(self, cx, cy):
        z = self.zoom_var.get()
        hw, hh = NODE_W*z/2, NODE_H*z/2
        for nid, n in self.nodes.items():
            nx, ny = n["x"]*z, n["y"]*z
            if abs(cx-nx) <= hw and abs(cy-ny) <= hh:
                return nid
        return None

    def _add_node(self, ntype, label, x, y, notes=""):
        nid = str(uuid.uuid4())[:8]
        self.nodes[nid] = {
            "id": nid, "type": ntype, "label": label,
            "x": x, "y": y, "notes": notes,
        }
        self._redraw()
        return nid

    def _add_edge(self, src, dst, label=""):
        eid = str(uuid.uuid4())[:8]
        self.edges[eid] = {"id": eid, "src": src, "dst": dst, "label": label}
        self._redraw()

    def _delete_selected(self):
        if not self.selected:
            return
        for nid in list(self.selected):
            del self.nodes[nid]
            for eid in [e for e,v in self.edges.items()
                        if v["src"]==nid or v["dst"]==nid]:
                del self.edges[eid]
        self.selected = set()
        self._hide_props()
        self._redraw()

    def _rename_node(self, nid):
        n = self.nodes[nid]
        new = simpledialog.askstring("Rename", "Label:",
                                     initialvalue=n["label"], parent=self.root)
        if new:
            n["label"] = new
            self._redraw()
            self._show_props(nid)

    def _rename_selected(self):
        if len(self.selected) == 1:
            self._rename_node(next(iter(self.selected)))

    def _select_all(self):
        self.selected = set(self.nodes.keys())
        self._redraw()

    #node dialog
    def _ctx_add(self):
        self._open_add_dialog(self._ctx_x, self._ctx_y)

    def _menu_add_node(self):
        z = self.zoom_var.get()
        cx = self.canvas.canvasx(self.canvas.winfo_width()//2)
        cy = self.canvas.canvasy(self.canvas.winfo_height()//2)
        self._open_add_dialog(cx, cy)

    def _quick_add(self, ntype):
        z = self.zoom_var.get()
        cx = self.canvas.canvasx(self.canvas.winfo_width()//2)
        cy = self.canvas.canvasy(self.canvas.winfo_height()//2)
        import random
        cx += random.randint(-120,120)
        cy += random.randint(-80,80)
        label = simpledialog.askstring(f"Add {ntype}", f"{ntype} value:",
                                       parent=self.root)
        if label:
            self._add_node(ntype, label, cx/z, cy/z)

    def _open_add_dialog(self, cx, cy):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Node")
        dlg.configure(bg=PANEL)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="◈ ADD ENTITY", bg=PANEL, fg=ACCENT2,
                 font=("Courier New", 10, "bold"), pady=8).pack()

        frm = tk.Frame(dlg, bg=PANEL)
        frm.pack(padx=16, pady=4)

        tk.Label(frm, text="TYPE:", bg=PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8, "bold"), anchor="w").grid(
                     row=0, column=0, sticky="w", pady=3)
        type_var = tk.StringVar(value="PERSON")
        cb = ttk.Combobox(frm, textvariable=type_var,
                          values=list(NODE_TYPES.keys()),
                          font=("Courier New", 9), width=14, state="readonly")
        cb.grid(row=0, column=1, padx=8, pady=3)

        tk.Label(frm, text="LABEL:", bg=PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8, "bold"), anchor="w").grid(
                     row=1, column=0, sticky="w", pady=3)
        label_var = tk.StringVar()
        le = tk.Entry(frm, textvariable=label_var, bg=BG2, fg=TEXT_BRIGHT,
                      insertbackground=ACCENT3, relief="flat",
                      font=("Courier New", 9), width=20)
        le.grid(row=1, column=1, padx=8, pady=3, ipady=3)
        le.focus_set()

        tk.Label(frm, text="NOTES:", bg=PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8, "bold"), anchor="w").grid(
                     row=2, column=0, sticky="nw", pady=3)
        notes_txt = tk.Text(frm, bg=BG2, fg=TEXT_BRIGHT,
                            insertbackground=ACCENT3, relief="flat",
                            font=("Courier New", 8), width=20, height=3)
        notes_txt.grid(row=2, column=1, padx=8, pady=3)

        def _ok(e=None):
            lbl = label_var.get().strip()
            if not lbl:
                return
            z = self.zoom_var.get()
            self._add_node(type_var.get(), lbl,
                           cx/z, cy/z,
                           notes_txt.get("1.0","end").strip())
            dlg.destroy()

        le.bind("<Return>", _ok)

        tk.Button(dlg, text="  ADD  ", command=_ok,
                  bg=ACCENT1, fg=TEXT_BRIGHT, relief="flat",
                  font=("Courier New", 9, "bold"), padx=14, pady=4,
                  cursor="hand2").pack(pady=10)

    #connecte mode
    def _toggle_connect(self):
        self.connect_mode = not self.connect_mode
        self.connect_src  = None
        if self.connect_mode:
            self.connect_btn.config(bg=DANGER)
            self._status("Connect mode ON — click source node, then target node  (Esc to cancel)")
        else:
            self.connect_btn.config(bg=ACCENT2)
            self._status("Connect mode OFF")
        if self.edge_draw_id:
            self.canvas.delete(self.edge_draw_id)

    #properties panel
    def _show_props(self, nid):
        for w in self.prop_frame.winfo_children():
            w.destroy()
        n = self.nodes.get(nid)
        if not n:
            return

        cfg = NODE_TYPES[n["type"]]
        tk.Label(self.prop_frame, text=f"{cfg['icon']} {n['type']}",
                 bg=PANEL, fg=cfg["color"],
                 font=("Courier New", 8, "bold")).pack(anchor="w")

        tk.Label(self.prop_frame, text=n["label"], bg=PANEL,
                 fg=TEXT_BRIGHT, font=("Courier New", 9),
                 wraplength=110, anchor="w").pack(anchor="w", pady=2)

        if n.get("notes"):
            tk.Frame(self.prop_frame, bg=BORDER, height=1).pack(fill="x", pady=4)
            tk.Label(self.prop_frame, text=n["notes"], bg=PANEL,
                     fg=TEXT_DIM, font=("Courier New", 7),
                     wraplength=110, anchor="w", justify="left").pack(anchor="w")

        tk.Frame(self.prop_frame, bg=BORDER, height=1).pack(fill="x", pady=4)

        edges_from = [e for e in self.edges.values() if e["src"]==nid]
        edges_to   = [e for e in self.edges.values() if e["dst"]==nid]
        tk.Label(self.prop_frame,
                 text=f"Out: {len(edges_from)}  In: {len(edges_to)}",
                 bg=PANEL, fg=TEXT_DIM, font=("Courier New", 7)).pack(anchor="w")

        def _edit():
            self._rename_node(nid)
        tk.Button(self.prop_frame, text="✎ RENAME", command=_edit,
                  bg=BG2, fg=ACCENT3, relief="flat",
                  font=("Courier New", 7, "bold"), pady=2).pack(fill="x", pady=2)

        def _del():
            self.selected = {nid}
            self._delete_selected()
        tk.Button(self.prop_frame, text="✕ DELETE", command=_del,
                  bg=BG2, fg=DANGER, relief="flat",
                  font=("Courier New", 7, "bold"), pady=2).pack(fill="x")

    def _hide_props(self):
        for w in self.prop_frame.winfo_children():
            w.destroy()

    #draw
    def _draw_grid(self):
        step = 50
        for x in range(0, CANVAS_W, step):
            c = "#0d0d20" if x % 200 == 0 else "#0b0b18"
            self.canvas.create_line(x, 0, x, CANVAS_H, fill=c, tags="grid")
        for y in range(0, CANVAS_H, step):
            c = "#0d0d20" if y % 200 == 0 else "#0b0b18"
            self.canvas.create_line(0, y, CANVAS_W, y, fill=c, tags="grid")

    def _redraw(self):
        self.canvas.delete("node", "edge", "tmp", "selrect")
        z = self.zoom_var.get()

        #edges first
        for eid, e in self.edges.items():
            src = self.nodes.get(e["src"])
            dst = self.nodes.get(e["dst"])
            if not src or not dst:
                continue
            sx, sy = src["x"]*z, src["y"]*z
            dx, dy = dst["x"]*z, dst["y"]*z

            #curved line
            mx = (sx+dx)/2 + (dy-sy)*0.15
            my = (sy+dy)/2 + (sx-dx)*0.15

            self.canvas.create_line(
                sx, sy, mx, my, dx, dy,
                smooth=True, fill=BORDER, width=max(1, int(1.5*z)),
                arrow="last", arrowshape=(8*z, 10*z, 3*z),
                tags="edge")

            if e.get("label"):
                self.canvas.create_text(
                    (sx+dx)/2, (sy+dy)/2,
                    text=e["label"], fill=TEXT_DIM,
                    font=("Courier New", max(7, int(7*z))), tags="edge")

        #nodes
        hw = NODE_W*z/2
        hh = NODE_H*z/2

        for nid, n in self.nodes.items():
            nx, ny = n["x"]*z, n["y"]*z
            cfg = NODE_TYPES.get(n["type"], NODE_TYPES["NOTE"])

            is_sel = nid in self.selected
            is_hit = nid in self.search_highlights
            is_src = nid == self.connect_src

            #outer glow ring
            if is_sel or is_src:
                ring_color = WARN if is_src else ACCENT3
                self.canvas.create_rectangle(
                    nx-hw-3, ny-hh-3, nx+hw+3, ny+hh+3,
                    outline=ring_color, width=max(1,int(2*z)),
                    fill="", tags="node")
            if is_hit:
                self.canvas.create_rectangle(
                    nx-hw-5, ny-hh-5, nx+hw+5, ny+hh+5,
                    outline=WARN, width=1, fill="", dash=(4,3), tags="node")

            #node body
            self.canvas.create_rectangle(
                nx-hw, ny-hh, nx+hw, ny+hh,
                fill=cfg["body"],
                outline=cfg["border"],
                width=max(1, int(1.5*z)),
                tags="node")

            #type icon + strip
            icon_w = max(18, int(22*z))
            self.canvas.create_rectangle(
                nx-hw, ny-hh, nx-hw+icon_w, ny+hh,
                fill=cfg["strip"], outline="", tags="node")
            self.canvas.create_text(
                nx-hw+icon_w//2, ny,
                text=cfg["icon"],
                fill=cfg["border"],
                font=("Courier New", max(8, int(9*z)), "bold"),
                tags="node")

            #label
            max_chars = max(8, int(14 / max(0.5, z)))
            lbl = n["label"]
            if len(lbl) > max_chars:
                lbl = lbl[:max_chars-1] + "…"
            self.canvas.create_text(
                nx - hw + icon_w + 4, ny,
                text=lbl, anchor="w",
                fill=TEXT_BRIGHT,
                font=("Courier New", max(7, int(9*z)), "bold"),
                tags="node")

    #layout
    def _auto_layout(self):
        if not self.nodes:
            return
        ids = list(self.nodes.keys())
        n = len(ids)
        cx = CANVAS_W / 2
        cy = CANVAS_H / 2

        #force-directed quick pass
        pos = {nid: [self.nodes[nid]["x"], self.nodes[nid]["y"]] for nid in ids}

        for _ in range(80):
            force = {nid: [0.0, 0.0] for nid in ids}
            #repulsion
            for i in range(n):
                for j in range(i+1, n):
                    a, b = ids[i], ids[j]
                    dx = pos[a][0] - pos[b][0]
                    dy = pos[a][1] - pos[b][1]
                    dist = max(1, math.hypot(dx, dy))
                    rep = 18000 / dist**2
                    fx, fy = dx/dist*rep, dy/dist*rep
                    force[a][0] += fx; force[a][1] += fy
                    force[b][0] -= fx; force[b][1] -= fy
            #attraction along edges
            for e in self.edges.values():
                if e["src"] in pos and e["dst"] in pos:
                    dx = pos[e["src"]][0] - pos[e["dst"]][0]
                    dy = pos[e["src"]][1] - pos[e["dst"]][1]
                    dist = max(1, math.hypot(dx, dy))
                    att = dist / 200
                    fx, fy = dx/dist*att, dy/dist*att
                    force[e["src"]][0] -= fx*40; force[e["src"]][1] -= fy*40
                    force[e["dst"]][0] += fx*40; force[e["dst"]][1] += fy*40
            #center pull
            for nid in ids:
                force[nid][0] += (cx - pos[nid][0]) * 0.002
                force[nid][1] += (cy - pos[nid][1]) * 0.002
            #apply
            for nid in ids:
                pos[nid][0] += max(-30, min(30, force[nid][0]))
                pos[nid][1] += max(-30, min(30, force[nid][1]))

        for nid in ids:
            self.nodes[nid]["x"] = pos[nid][0]
            self.nodes[nid]["y"] = pos[nid][1]

        self._center_view()
        self._redraw()
        self._status("Auto layout complete")

    def _center_view(self):
        if not self.nodes:
            return
        xs = [n["x"] for n in self.nodes.values()]
        ys = [n["y"] for n in self.nodes.values()]
        cx = (min(xs)+max(xs))/2
        cy = (min(ys)+max(ys))/2
        z  = self.zoom_var.get()
        self.canvas.xview_moveto(max(0, (cx*z - self.canvas.winfo_width()/2) / CANVAS_W))
        self.canvas.yview_moveto(max(0, (cy*z - self.canvas.winfo_height()/2) / CANVAS_H))

    #clear all
    def _clear_all(self):
        if not messagebox.askyesno("Clear board",
                                   "Delete ALL nodes and edges?",
                                   parent=self.root):
            return
        self.nodes.clear()
        self.edges.clear()
        self.selected.clear()
        self._hide_props()
        self._redraw()
        self._status("Board cleared")

    #save/load
    def _save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            title="Save Board")
        if not path:
            return
        data = {"nodes": self.nodes, "edges": self.edges}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self._status(f"Saved → {path}")

    def _load(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            title="Load Board")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.nodes = data.get("nodes", {})
        self.edges = data.get("edges", {})
        self.selected.clear()
        self._redraw()
        self._center_view()
        self._status(f"Loaded {len(self.nodes)} nodes, {len(self.edges)} edges from {path}")

    #staus
    def _status(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.status_var.set(f"[{ts}]  {msg}   |   nodes: {len(self.nodes)}  edges: {len(self.edges)}")


#entry
if __name__ == "__main__":
    root = tk.Tk()
    app = Board(root)
    root.mainloop()