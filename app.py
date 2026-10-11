#!/usr/bin/env python3
"""8-Bit CPU Emulator — PySide6 — Ultimate Edition"""

import sys, re
from collections import deque
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QLabel, QPushButton, QSlider, QTableWidget,
    QTableWidgetItem, QSplitter, QFrame, QComboBox, QTextEdit,
    QHeaderView, QTabWidget, QLineEdit, QFileDialog, QInputDialog,
    QAbstractItemView, QSizePolicy, QMenu, QMenuBar, QToolTip
)
from PySide6.QtCore import Qt, QTimer, QSize, QRect, QPoint
from PySide6.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat,
    QTextCursor, QTextFormat, QPainter, QKeySequence, QAction
)

# ═══════════════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════════════
C = dict(
    bg='#0b0f15', panel='#111820', editor='#0d1218', border='#1c2633',
    text='#c8d0dc', dim='#4a5568', green='#00e88f', amber='#ffa830',
    cyan='#38c8e8', red='#ff4455', purple='#b888ff', cur_line='#0a2018',
    err_line='#2a0a0a', mem_zero='#0e1319', mem_write='#1a3320',
    mem_read='#102030', sp_mark='#ff6644', bp='#ff4466',
)
FM = QFont("Consolas", 11); FMS = QFont("Consolas", 9)
FML = QFont("Consolas", 15, QFont.Bold); FUI = QFont("Segoe UI", 10)
FLB = QFont("Segoe UI", 9); FTI = QFont("Segoe UI", 10, QFont.Bold)

# ═══════════════════════════════════════════════════════════════════
#  EXAMPLES
# ═══════════════════════════════════════════════════════════════════
EXAMPLES = {
    "Counter": """\
; ── Counter: A counts 0 → 9 ──
MOV A, 0
MOV B, 10
LOOP:
  INC A
  CMP A, B
  JNZ LOOP
  HLT""",
    "User Snippet": """\
; ── From your example ──
MOV A, 5
ADD A, 2
; JMP LOOP
HLT""",
    "Fibonacci": """\
; ── Fibonacci in memory at 0x20 ──
MOV A, 1
MOV B, 0
MOV D, 0x20
STORE [D], B
INC D
STORE [D], A
INC D
MOV C, 6
LOOP:
  MOV [0xF0], A
  ADD A, B
  LOAD B, [0xF0]
  STORE [D], A
  INC D
  DEC C
  JNZ LOOP
  HLT""",
    "Subroutines": """\
; ── CALL / RET demo ──
MOV A, 3
CALL DOUBLE
CALL DOUBLE
CALL DOUBLE
HLT
DOUBLE:
  ADD A, A
  RET""",
    "Bitwise Logic": """\
; ── Bitwise operations ──
MOV A, 0xF0
MOV B, 0x0F
AND A, B
MOV C, A
MOV A, 0xF0
OR A, B
MOV D, A
MOV A, 0xFF
XOR A, C
HLT""",
    "I/O Demo": """\
; ── I/O: 7-seg + LEDs + terminal ──
; Port 0=7-seg, 1=LED bar, 2=ASCII, 3=matrix row, 4=matrix data
MOV A, 5
LOOP:
  OUT A, 0
  OUT A, 1
  MOV B, 0
  MLOOP:
    OUT B, 3
    OUT A, 4
    INC B
    CMP B, 8
    JNZ MLOOP
  MOV B, A
  ADD B, 0x30
  OUT B, 2
  MOV B, 0x20
  OUT B, 2
  CMP A, 0
  JZ DONE
  DEC A
  JMP LOOP
DONE:
  HLT""",
    "Memory Scan": """\
; ── Find first non-zero in 0x40-0x4F ──
MOV D, 0x40
MOV A, 0
STORE [0x40], A
STORE [0x41], A
STORE [0x42], 0xAB
MOV C, 16
LOOP:
  LOAD A, [D]
  CMP A, 0
  JNZ FOUND
  INC D
  DEC C
  JNZ LOOP
  MOV A, 0xFF
  HLT
FOUND:
  HLT""",
    "Stack Ops": """\
; ── Push / Pop ──
MOV A, 0xAA
MOV B, 0xBB
MOV C, 0xCC
PUSH A
PUSH B
PUSH C
MOV A, 0
MOV B, 0
MOV C, 0
POP C
POP B
POP A
HLT""",
}

# ═══════════════════════════════════════════════════════════════════
#  INSTRUCTION REFERENCE
# ═══════════════════════════════════════════════════════════════════
REF_HTML = """<style>
body{color:#c8d0dc;font-family:Consolas;font-size:11px}
h3{color:#38c8e8;margin:8px 0 4px}
table{border-collapse:collapse;width:100%;margin:4px 0}
th{color:#ffa830;text-align:left;padding:3px 6px;border-bottom:1px solid #1c2633;font-size:10px}
td{padding:2px 6px;border-bottom:1px solid #111820;font-size:10px}
</style>
<h3>Data Movement</h3>
<table><tr><th>Op</th><th>Operands</th><th>Description</th></tr>
<tr><td>MOV</td><td>dst, src</td><td>Copy src → dst (reg/imm/mem)</td></tr>
<tr><td>LOAD</td><td>reg, [addr]</td><td>Memory → register</td></tr>
<tr><td>STORE</td><td>[addr], reg</td><td>Register → memory</td></tr>
<tr><td>PUSH</td><td>reg</td><td>Push onto stack</td></tr>
<tr><td>POP</td><td>reg</td><td>Pop from stack</td></tr></table>
<h3>Arithmetic</h3>
<table><tr><th>Op</th><th>Operands</th><th>Description</th></tr>
<tr><td>ADD</td><td>dst, src</td><td>dst += src</td></tr>
<tr><td>SUB</td><td>dst, src</td><td>dst -= src</td></tr>
<tr><td>MUL</td><td>dst, src</td><td>dst *= src (low byte)</td></tr>
<tr><td>INC</td><td>dst</td><td>dst++</td></tr>
<tr><td>DEC</td><td>dst</td><td>dst--</td></tr>
<tr><td>CMP</td><td>a, b</td><td>Set flags: a-b (no store)</td></tr></table>
<h3>Logic</h3>
<table><tr><th>Op</th><th>Operands</th><th>Description</th></tr>
<tr><td>AND</td><td>dst, src</td><td>dst &= src</td></tr>
<tr><td>OR</td><td>dst, src</td><td>dst |= src</td></tr>
<tr><td>XOR</td><td>dst, src</td><td>dst ^= src</td></tr>
<tr><td>NOT</td><td>dst</td><td>dst = ~dst</td></tr>
<tr><td>SHL</td><td>dst, n</td><td>dst <<= n</td></tr>
<tr><td>SHR</td><td>dst, n</td><td>dst >>= n</td></tr></table>
<h3>Branch</h3>
<table><tr><th>Op</th><th>Cond</th><th>Description</th></tr>
<tr><td>JMP</td><td>always</td><td>Unconditional jump</td></tr>
<tr><td>JZ</td><td>Z=1</td><td>Jump if zero</td></tr>
<tr><td>JNZ</td><td>Z=0</td><td>Jump if not zero</td></tr>
<tr><td>JC</td><td>C=1</td><td>Jump if carry</td></tr>
<tr><td>JNC</td><td>C=0</td><td>Jump if no carry</td></tr>
<tr><td>JN</td><td>N=1</td><td>Jump if negative</td></tr></table>
<h3>Subroutine</h3>
<table><tr><td>CALL</td><td>label</td><td>Push PC, jump</td></tr>
<tr><td>RET</td><td></td><td>Pop PC (return)</td></tr></table>
<h3>I/O</h3>
<table><tr><td>IN</td><td>reg, port</td><td>Read port → reg</td></tr>
<tr><td>OUT</td><td>reg, port</td><td>Write reg → port</td></tr></table>
<p style='color:#4a5568;font-size:10px;margin-top:6px'>
Port 0: 7-Seg &nbsp; 1: LED Bar &nbsp; 2: ASCII &nbsp; 3: Matrix Row &nbsp; 4: Matrix Data</p>
<h3>Control</h3>
<table><tr><td>NOP</td><td></td><td>No operation</td></tr>
<tr><td>HLT</td><td></td><td>Halt CPU</td></tr></table>
<h3>Debug Console Commands</h3>
<table><tr><th>Cmd</th><th>Example</th><th>Description</th></tr>
<tr><td>?reg</td><td>? A</td><td>Show register (hex/dec/bin)</td></tr>
<tr><td>?addr</td><td>? 0x20</td><td>Show memory at address</td></tr>
<tr><td>!instr</td><td>! MOV A,5</td><td>Execute instruction now</td></tr>
<tr><td>.fill</td><td>.fill 20 30 FF</td><td>Fill memory range</td></tr>
<tr><td>.set</td><td>.set A 42</td><td>Set register value</td></tr>
<tr><td>.clear</td><td>.clear</td><td>Clear console</td></tr>
<tr><td>.help</td><td>.help</td><td>Show commands</td></tr></table>"""

# ═══════════════════════════════════════════════════════════════════
#  CPU + STATE SNAPSHOT
# ═══════════════════════════════════════════════════════════════════
class CPUState:
    __slots__ = ['reg', 'flg', 'mem', 'ports', 'halted', 'cycles']
    def __init__(self, cpu):
        self.reg = dict(cpu.reg); self.flg = dict(cpu.flg)
        self.mem = list(cpu.mem); self.ports = dict(cpu.ports)
        self.halted = cpu.halted; self.cycles = cpu.cycles
    def restore(self, cpu):
        cpu.reg = dict(self.reg); cpu.flg = dict(self.flg)
        cpu.mem = list(self.mem); cpu.ports = dict(self.ports)
        cpu.halted = self.halted; cpu.cycles = self.cycles

class CPU:
    REGS = ['A','B','C','D','PC','SP']; FLAGS = ['Z','C','N','V']; MEM = 256
    def __init__(self): self.reset()
    def reset(self):
        self.reg = {r: 0 for r in self.REGS}; self.reg['SP'] = self.MEM - 1
        self.flg = {f: False for f in self.FLAGS}; self.mem = [0] * self.MEM
        self.ports = {i: 0 for i in range(8)}; self.prog = []; self.labels = {}
        self.halted = False; self.changed_reg = set(); self.changed_mem = {}
        self.changed_port = set(); self.cycles = 0; self.error = None
    def load(self, prog, labels): self.prog, self.labels = prog, labels
    def _get(self, op):
        t, v = op
        if t == 'reg':  return self.reg[v]
        if t == 'imm':  return v & 0xFF
        if t == 'mem':  a = v & 0xFF; self.changed_mem[a] = 'r'; return self.mem[a]
        if t == 'memr': a = self.reg[v] & 0xFF; self.changed_mem[a] = 'r'; return self.mem[a]
        return 0
    def _set(self, op, val):
        t, v = op; val &= 0xFF
        if t == 'reg':
            if self.reg[v] != val: self.changed_reg.add(v)
            self.reg[v] = val
        elif t == 'mem':   a = v & 0xFF; self.mem[a] = val; self.changed_mem[a] = 'w'
        elif t == 'memr':  a = self.reg[v] & 0xFF; self.mem[a] = val; self.changed_mem[a] = 'w'
    def _flags(self, res, a=None, b=None, sub=False):
        r8 = res & 0xFF; self.flg['Z'] = r8 == 0; self.flg['N'] = bool(r8 & 0x80)
        self.flg['C'] = res > 0xFF or res < 0
        if a is not None and b is not None:
            self.flg['V'] = bool(((a^b)&(a^r8)&0x80) if sub else ((a^r8)&(b^r8)&0x80))
    def step(self):
        if self.halted: return False
        self.changed_reg.clear(); self.changed_mem.clear()
        self.changed_port.clear(); self.error = None
        pc = self.reg['PC']
        if pc >= len(self.prog): self.halted = True; self.error = "PC out of bounds"; return False
        instr = self.prog[pc]; self.reg['PC'] = pc + 1; self.cycles += 1
        try: self._exec(instr['op'], instr['args'])
        except Exception as e: self.error = f"Addr {pc:02X}: {e}"; self.halted = True; return False
        return not self.halted
    def _exec(self, op, a):
        if op == 'NOP': pass
        elif op == 'HLT': self.halted = True
        elif op in ('MOV','LOAD','STORE'): self._set(a[0], self._get(a[1]))
        elif op == 'ADD':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1+v2,v1,v2); self._set(a[0],v1+v2)
        elif op == 'SUB':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1-v2,v1,v2,True); self._set(a[0],v1-v2)
        elif op == 'MUL':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1*v2); self._set(a[0],v1*v2)
        elif op == 'AND':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1&v2); self._set(a[0],v1&v2)
        elif op == 'OR':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1|v2); self._set(a[0],v1|v2)
        elif op == 'XOR':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1^v2); self._set(a[0],v1^v2)
        elif op == 'NOT':
            v = self._get(a[0]); self._flags(~v&0xFF); self._set(a[0],~v)
        elif op == 'SHL':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1<<v2); self._set(a[0],v1<<v2)
        elif op == 'SHR':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1>>v2); self._set(a[0],v1>>v2)
        elif op == 'INC':
            v = self._get(a[0]); self._flags(v+1,v,1); self._set(a[0],v+1)
        elif op == 'DEC':
            v = self._get(a[0]); self._flags(v-1,v,1,True); self._set(a[0],v-1)
        elif op == 'CMP':
            v1,v2 = self._get(a[0]),self._get(a[1]); self._flags(v1-v2,v1,v2,True)
        elif op == 'JMP':  self.reg['PC']=a[0][1]; self.changed_reg.add('PC')
        elif op == 'JZ'  and self.flg['Z']:  self.reg['PC']=a[0][1]; self.changed_reg.add('PC')
        elif op == 'JNZ' and not self.flg['Z']: self.reg['PC']=a[0][1]; self.changed_reg.add('PC')
        elif op == 'JC'  and self.flg['C']:  self.reg['PC']=a[0][1]; self.changed_reg.add('PC')
        elif op == 'JNC' and not self.flg['C']: self.reg['PC']=a[0][1]; self.changed_reg.add('PC')
        elif op == 'JN'  and self.flg['N']:  self.reg['PC']=a[0][1]; self.changed_reg.add('PC')
        elif op == 'PUSH':
            sp=self.reg['SP']; self.mem[sp]=self._get(a[0])
            self.changed_mem[sp]='w'; self.reg['SP']=(sp-1)&0xFF; self.changed_reg.add('SP')
        elif op == 'POP':
            sp=(self.reg['SP']+1)&0xFF; self.reg['SP']=sp; self.changed_reg.add('SP')
            self.changed_mem[sp]='r'; self._set(a[0],self.mem[sp])
        elif op == 'CALL':
            sp=self.reg['SP']; self.mem[sp]=self.reg['PC']&0xFF
            self.changed_mem[sp]='w'; self.reg['SP']=(sp-1)&0xFF; self.changed_reg.add('SP')
            self.reg['PC']=a[0][1]; self.changed_reg.add('PC')
        elif op == 'RET':
            sp=(self.reg['SP']+1)&0xFF; self.reg['SP']=sp; self.changed_reg.add('SP')
            self.changed_mem[sp]='r'; self.reg['PC']=self.mem[sp]; self.changed_reg.add('PC')
        elif op == 'IN':
            port=a[1][1]&7; self._set(a[0],self.ports.get(port,0)); self.changed_port.add(port)
        elif op == 'OUT':
            port=a[1][1]&7; val=self._get(a[0]); self.ports[port]=val; self.changed_port.add(port)
        else: raise ValueError(f"Unknown: {op}")

# ═══════════════════════════════════════════════════════════════════
#  ASSEMBLER
# ═══════════════════════════════════════════════════════════════════
class Assembler:
    OPS = {'NOP','HLT','MOV','LOAD','STORE','ADD','SUB','MUL','INC','DEC',
           'AND','OR','XOR','NOT','SHL','SHR','CMP','JMP','JZ','JNZ',
           'JC','JNC','JN','PUSH','POP','CALL','RET','IN','OUT'}
    def parse(self, text):
        labels, raw, addr = {}, [], 0
        for i, ln in enumerate(text.split('\n')):
            ci = ln.find(';')
            if ci >= 0: ln = ln[:ci]
            ln = ln.strip()
            if not ln: continue
            while ':' in ln:
                ci2 = ln.index(':'); lb = ln[:ci2].strip()
                if lb: labels[lb] = addr
                ln = ln[ci2+1:].strip()
            if not ln: continue
            parts = ln.split(None, 1); op = parts[0].upper()
            if op not in self.OPS: raise SyntaxError(f"Line {i+1}: unknown '{op}'")
            raw.append(dict(line=i, op=op, args=parts[1] if len(parts)>1 else '',
                            addr=addr, text=ln)); addr += 1
        prog = []
        for r in raw:
            prog.append(dict(line=r['line'], op=r['op'], args=self._pa(r['args'], labels),
                             addr=r['addr'], text=r['text']))
        return prog, labels
    def _pa(self, s, lb):
        if not s.strip(): return []
        out = []; depth = 0; cur = ''
        for ch in s:
            if ch == '[': depth += 1; cur += ch
            elif ch == ']': depth -= 1; cur += ch
            elif ch == ',' and depth == 0: out.append(cur); cur = ''
            else: cur += ch
        if cur.strip(): out.append(cur)
        args = []
        for p in out:
            p = p.strip()
            if p.startswith('[') and p.endswith(']'):
                inner = p[1:-1].strip()
                if inner.upper() in CPU.REGS: args.append(('memr', inner.upper()))
                elif inner in lb: args.append(('mem', lb[inner]))
                else: args.append(('mem', self._pn(inner)))
            elif p.upper() in CPU.REGS: args.append(('reg', p.upper()))
            elif p in lb: args.append(('label', lb[p]))
            else: args.append(('imm', self._pn(p)))
        return args
    @staticmethod
    def _pn(s):
        s = s.strip()
        try: return int(s,16) if s.lower().startswith('0x') else int(s,2) if s.lower().startswith('0b') else int(s)
        except ValueError: raise SyntaxError(f"Bad number: '{s}'")

# ═══════════════════════════════════════════════════════════════════
#  SYNTAX HIGHLIGHTER
# ═══════════════════════════════════════════════════════════════════
class Highlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc); self._f = {}
        def sf(c, b=False, i=False):
            f = QTextCharFormat(); f.setForeground(QColor(c))
            if b: f.setFontWeight(QFont.Bold)
            if i: f.setFontItalic(True)
            return f
        self._f = dict(op=sf(C['cyan'],True), num=sf(C['amber']), lbl=sf(C['purple']),
                       cmt=sf(C['dim'],i=True), reg=sf(C['green'],True), bkt=sf(C['text']))
        self._ops_re = re.compile(
            r'\b(NOP|HLT|MOV|LOAD|STORE|ADD|SUB|MUL|INC|DEC|AND|OR|XOR|NOT|'
            r'SHL|SHR|CMP|JMP|JZ|JNZ|JC|JNC|JN|PUSH|POP|CALL|RET|IN|OUT)\b', re.I)
    def highlightBlock(self, text):
        ci = text.find(';')
        if ci >= 0: self.setFormat(ci, len(text)-ci, self._f['cmt']); text = text[:ci]
        for m in re.finditer(r'(\w+)\s*:', text): self.setFormat(m.start(), m.end(), self._f['lbl'])
        for m in self._ops_re.finditer(text): self.setFormat(m.start(), m.end(), self._f['op'])
        for m in re.finditer(r'\b([ABCD])\b', text, re.I): self.setFormat(m.start(), m.end(), self._f['reg'])
        for m in re.finditer(r'\b(SP|PC)\b', text, re.I): self.setFormat(m.start(), m.end(), self._f['reg'])
        for m in re.finditer(r'\b(0x[0-9a-fA-F]+|0b[01]+|\d+)\b', text):
            self.setFormat(m.start(), m.end(), self._f['num'])
        for m in re.finditer(r'[\[\]]', text): self.setFormat(m.start(), 1, self._f['bkt'])

# ═══════════════════════════════════════════════════════════════════
#  BIT ROW WIDGET
# ═══════════════════════════════════════════════════════════════════
class BitRow(QWidget):
    def __init__(self):
        super().__init__(); self.setFixedHeight(12)
        self._bits = [False]*8; self._flash = [False]*8
        self._ft = QTimer(self); self._ft.setSingleShot(True)
        self._ft.timeout.connect(self._cf)
    def set_bits(self, val, changed=None):
        self._bits = [(val>>(7-i))&1 for i in range(8)]
        if changed:
            for i in changed: self._flash[i] = True
            self._ft.start(400)
        self.update()
    def _cf(self): self._flash = [False]*8; self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w = self.width()/8; r = min(w*0.3, 3.5)
        for i in range(8):
            cx = w*i+w/2; cy = self.height()/2; on = self._bits[i]
            if self._flash[i]: c = QColor(C['amber'])
            elif on: c = QColor(C['green'])
            else: c = QColor(C['border'])
            p.setPen(Qt.NoPen); p.setBrush(c)
            p.drawEllipse(int(cx-r), int(cy-r), int(r*2), int(r*2))
        p.end()

# ═══════════════════════════════════════════════════════════════════
#  LINE NUMBER AREA + CODE EDITOR
# ═══════════════════════════════════════════════════════════════════
class LineNumArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor); self.ed = editor
        self.breakpoints = set(); self.bp_conds = {}; self.setCursor(Qt.PointingHandCursor)
    def sizeHint(self): return QSize(self.ed.ln_width(), 0)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            blk = self.ed.firstVisibleBlock()
            top = int(self.ed.blockBoundingGeometry(blk).translated(self.ed.contentOffset()).top())
            while blk.isValid():
                bh = int(self.ed.blockBoundingRect(blk).height())
                if top <= e.position().y() < top + bh:
                    ln = blk.blockNumber(); self.breakpoints.symmetric_difference_update({ln})
                    if ln not in self.breakpoints: self.bp_conds.pop(ln, None)
                    self.update(); break
                blk = blk.next(); top += bh
    def contextMenuEvent(self, e):
        blk = self.ed.firstVisibleBlock()
        top = int(self.ed.blockBoundingGeometry(blk).translated(self.ed.contentOffset()).top())
        while blk.isValid():
            bh = int(self.ed.blockBoundingRect(blk).height())
            if top <= e.position().y() < top + bh:
                ln = blk.blockNumber(); break
            blk = blk.next(); top += bh
        else: return
        menu = QMenu(self); menu.setStyleSheet(f"QMenu{{background:{C['panel']};color:{C['text']};border:1px solid {C['border']}}}"
                                                f"QMenu::item:selected{{background:{C['border']};color:{C['green']}}}")
        act = menu.addAction("Set Condition..." if ln in self.breakpoints else "Add Breakpoint")
        if ln in self.breakpoints:
            menu.addAction("Remove Breakpoint")
            menu.addAction("Edit Condition...")
        res = menu.exec(e.globalPos())
        if res:
            txt = res.text()
            if "Add" in txt:
                self.breakpoints.add(ln)
                cond, ok = QInputDialog.getText(self, "Breakpoint Condition",
                    f"Condition for line {ln+1} (empty=always break):\n"
                    "e.g. A==5, A>10, [0x20]!=0, Z==1",
                    QLineEdit.Normal, self.bp_conds.get(ln, ""))
                if ok:
                    if cond.strip(): self.bp_conds[ln] = cond.strip()
                    elif ln in self.bp_conds: del self.bp_conds[ln]
                self.update()
            elif "Remove" in txt:
                self.breakpoints.discard(ln); self.bp_conds.pop(ln, None); self.update()
            elif "Edit" in txt:
                cond, ok = QInputDialog.getText(self, "Edit Condition",
                    f"Condition for line {ln+1}:",
                    QLineEdit.Normal, self.bp_conds.get(ln, ""))
                if ok:
                    if cond.strip(): self.bp_conds[ln] = cond.strip()
                    elif ln in self.bp_conds: del self.bp_conds[ln]
                self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.fillRect(e.rect(), QColor(C['editor']))
        blk = self.ed.firstVisibleBlock(); bn = blk.blockNumber()
        top = int(self.ed.blockBoundingGeometry(blk).translated(self.ed.contentOffset()).top())
        bot = top + int(self.ed.blockBoundingRect(blk).height())
        while blk.isValid() and top <= e.rect().bottom():
            if blk.isVisible() and bot >= e.rect().top():
                if bn in self.breakpoints:
                    p.setPen(Qt.NoPen); p.setBrush(QColor(C['bp']))
                    p.drawEllipse(QPoint(8, top+9), 5, 5)
                    if bn in self.bp_conds:
                        p.setPen(QColor(C['amber'])); p.setFont(FMS)
                        p.drawText(16, top+13, "⚡")
                elif bn == self.ed._pc_line:
                    p.setPen(Qt.NoPen); p.setBrush(QColor(C['green']))
                    p.drawPolygon(QPoint(4,top+9), QPoint(15,top+4), QPoint(15,top+14))
                elif bn == self.ed._err_line:
                    p.setPen(Qt.NoPen); p.setBrush(QColor(C['red']))
                    p.drawPolygon(QPoint(4,top+9), QPoint(15,top+4), QPoint(15,top+14))
                num = str(bn+1)
                col = C['green'] if bn==self.ed._pc_line else C['red'] if bn==self.ed._err_line else C['bp'] if bn in self.breakpoints else C['dim']
                p.setPen(QColor(col)); p.setFont(FMS)
                p.drawText(self.ed.ln_width()-22, top, 20, self.ed.fontMetrics().height(),
                           Qt.AlignRight|Qt.AlignVCenter, num)
            blk = blk.next(); top = bot
            bot = top + int(self.ed.blockBoundingRect(blk).height()); bn += 1
        p.end()

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__(); self.setFont(FM)
        self.setStyleSheet(f"background:{C['editor']};color:{C['text']};border:none;padding:4px;")
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.ln_area = LineNumArea(self); self._pc_line = -1; self._err_line = -1
        self.blockCountChanged.connect(self._um); self.updateRequest.connect(self._ur); self._um()
    def ln_width(self):
        n = max(1, self.blockCount()); d = 1
        while n >= 10: n //= 10; d += 1
        return 12 + FMS.horizontalAdvance('9')*d + 28
    def _um(self): self.setViewportMargins(self.ln_width(),0,0,0); self.ln_area.update()
    def _ur(self, r, dy):
        if dy: self.ln_area.scroll(0,dy)
        else: self.ln_area.update(0, r.y(), self.ln_area.width(), r.height())
    def resizeEvent(self, e):
        super().resizeEvent(e); self.ln_area.setGeometry(QRect(0,0,self.ln_width(),self.height()))
    def highlight_pc(self, line): self._pc_line=line; self._err_line=-1; self._sel(line, QColor(C['cur_line']))
    def highlight_err(self, line): self._err_line=line; self._sel(line, QColor(C['err_line']))
    def _sel(self, line, color):
        blk = self.document().findBlockByLineNumber(line) if line >= 0 else None
        sel = QTextEdit.ExtraSelection() if blk and blk.isValid() else None
        if sel:
            sel.cursor = QTextCursor(blk); sel.cursor.select(QTextCursor.LineUnderCursor)
            fmt = sel.cursor.charFormat(); fmt.setBackground(color)
            fmt.setProperty(QTextFormat.FullWidthSelection, True); sel.format = fmt
        self.setExtraSelections([sel] if sel else []); self.ln_area.update()

# ═══════════════════════════════════════════════════════════════════
#  REGISTER CARD WITH BITS
# ═══════════════════════════════════════════════════════════════════
class RegCard(QFrame):
    def __init__(self, name, accent=False):
        super().__init__(); self.name = name; self._val = 0; self._accent = accent
        self.setFixedSize(82, 60)
        self._ft = QTimer(self); self._ft.setSingleShot(True); self._ft.timeout.connect(self._uf)
        ly = QVBoxLayout(self); ly.setContentsMargins(4,1,4,1); ly.setSpacing(0)
        self.nm = QLabel(name); self.nm.setAlignment(Qt.AlignCenter); self.nm.setFont(FLB)
        self.nm.setStyleSheet(f"color:{C['dim']};")
        self.vl = QLabel("00"); self.vl.setAlignment(Qt.AlignCenter); self.vl.setFont(FML)
        ac = C['amber'] if accent else C['green']
        self.vl.setStyleSheet(f"color:{ac};"); self._ac = ac
        self.bits = BitRow(); ly.addWidget(self.nm); ly.addWidget(self.vl); ly.addWidget(self.bits)
        self._base()
    def _base(self):
        self.setStyleSheet(f"RegCard{{background:{C['panel']};border:1px solid {C['border']};border-radius:6px;}}")
    def set_val(self, v, changed_bits=None):
        self._val = v & 0xFF; self.vl.setText(f"{self._val:02X}")
        self.bits.set_bits(self._val, changed_bits)
        dec = self._val; b = f"{self._val:08b}"
        self.setToolTip(f"{self.name} = 0x{self._val:02X} = {dec} = {b}")
    def flash(self):
        self.setStyleSheet(f"RegCard{{background:#2a2010;border:1px solid {C['amber']};border-radius:6px;}}")
        self._ft.start(400)
    def _uf(self): self._base()

class FlagDot(QFrame):
    def __init__(self, name):
        super().__init__(); self.name = name; self.setFixedSize(52, 38)
        ly = QVBoxLayout(self); ly.setContentsMargins(2,0,2,0); ly.setSpacing(0)
        self.dot = QFrame(); self.dot.setFixedSize(14,14)
        self.dot.setStyleSheet(f"background:{C['border']};border-radius:7px;")
        self.nm = QLabel(name); self.nm.setAlignment(Qt.AlignCenter); self.nm.setFont(FLB)
        self.nm.setStyleSheet(f"color:{C['dim']};")
        ly.addStretch(); ly.addWidget(self.dot, alignment=Qt.AlignCenter); ly.addWidget(self.nm)
    def set_val(self, v):
        self.dot.setStyleSheet(f"background:{C['green'] if v else C['border']};border-radius:7px;")

# ═══════════════════════════════════════════════════════════════════
#  I/O WIDGETS
# ═══════════════════════════════════════════════════════════════════
class SevenSegment(QWidget):
    SEGS = {'a':(.18,0,.64,.09),'b':(.82,.09,.18,.38),'c':(.82,.53,.18,.38),
            'd':(.18,.91,.64,.09),'e':(0,.53,.18,.38),'f':(0,.09,.18,.38),'g':(.18,.455,.64,.09)}
    DIGS = {0:'abcdef',1:'bc',2:'abdeg',3:'abcdg',4:'bcfg',5:'acdfg',6:'acdefg',
            7:'abc',8:'abcdefg',9:'abcdfg',0xa:'abcefg',0xb:'cdefg',0xc:'adef',
            0xd:'bcdeg',0xe:'adefg',0xf:'aefg'}
    def __init__(self): super().__init__(); self.value=0; self.setFixedSize(48,76)
    def set_value(self, v): self.value=v&0xF; self.update()
    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.fillRect(self.rect(), QColor(C['bg']))
        active=self.DIGS.get(self.value,''); w,h=self.width(),self.height()
        for n,(sx,sy,sw,sh) in self.SEGS.items():
            on=n in active; p.setPen(Qt.NoPen)
            p.setBrush(QColor(C['green']) if on else QColor(C['border']))
            p.drawRoundedRect(int(sx*w),int(sy*h),max(int(sw*w),2),max(int(sh*h),2),2,2)
        p.end()

class LEDBar(QWidget):
    def __init__(self): super().__init__(); self.value=0; self.setFixedSize(190,26)
    def set_value(self, v): self.value=v&0xFF; self.update()
    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.fillRect(self.rect(), QColor(C['bg']))
        sp=self.width()/8; r=min(sp*.35,10); cy=self.height()/2
        for i in range(8):
            cx=sp*i+sp/2; on=(self.value>>(7-i))&1; p.setPen(Qt.NoPen)
            p.setBrush(QColor(C['green']) if on else QColor(C['border']))
            p.drawEllipse(int(cx-r),int(cy-r),int(r*2),int(r*2))
        p.end()

class LEDMatrix(QWidget):
    def __init__(self): super().__init__(); self.data=[0]*8; self.sel_row=-1; self.setFixedSize(130,130)
    def set_row(self, row, val): self.data[row&7]=val&0xFF; self.sel_row=row&7; self.update()
    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.fillRect(self.rect(), QColor(C['bg']))
        cell=self.width()/8; r=cell*.3
        for row in range(8):
            for col in range(8):
                on=(self.data[row]>>(7-col))&1; cx=col*cell+cell/2; cy=row*cell+cell/2
                c=QColor(C['cyan']) if on and row==self.sel_row else QColor(C['green']) if on else QColor(C['border'])
                p.setPen(Qt.NoPen); p.setBrush(c)
                p.drawEllipse(int(cx-r),int(cy-r),int(r*2),int(r*2))
        p.end()

class ASCIITerminal(QTextEdit):
    def __init__(self):
        super().__init__(); self.setReadOnly(True); self.setFont(FMS); self.setMaximumHeight(70)
        self.setStyleSheet(f"background:{C['editor']};color:{C['green']};border:1px solid {C['border']};border-radius:4px;")
    def put_char(self, ch):
        if ch==0x0A: self.append("")
        elif 0x20<=ch<0x7F: self.insertPlainText(chr(ch))
        sb=self.verticalScrollBar(); sb.setValue(sb.maximum())
    def clear_term(self): super().clear()

class PortMonitor(QWidget):
    def __init__(self):
        super().__init__(); ly=QHBoxLayout(self); ly.setContentsMargins(4,2,4,2); ly.setSpacing(4)
        self.labels = []
        for i in range(8):
            f = QFrame(); f.setFixedHeight(36); f.setFixedWidth(36)
            f.setStyleSheet(f"QFrame{{background:{C['bg']};border:1px solid {C['border']};border-radius:4px;}}")
            fl = QVBoxLayout(f); fl.setContentsMargins(1,1,1,1); fl.setSpacing(0)
            nm = QLabel(f"P{i}"); nm.setAlignment(Qt.AlignCenter); nm.setFont(QFont("Consolas",7))
            nm.setStyleSheet(f"color:{C['dim']};"); vl = QLabel("00"); vl.setAlignment(Qt.AlignCenter)
            vl.setFont(FMS); vl.setStyleSheet(f"color:{C['text']};")
            fl.addWidget(nm); fl.addWidget(vl); ly.addWidget(f); self.labels.append(vl)
    def update_ports(self, cpu, changed):
        for i in range(8):
            v = cpu.ports[i]; self.labels[i].setText(f"{v:02X}")
            if i in changed: self.labels[i].setStyleSheet(f"color:{C['green']};font-weight:bold;")
            else: self.labels[i].setStyleSheet(f"color:{C['text']};")

class IOPanel(QWidget):
    def __init__(self, cpu):
        super().__init__(); self.cpu=cpu
        ly=QVBoxLayout(self); ly.setContentsMargins(4,4,4,4); ly.setSpacing(6)
        r1=QHBoxLayout(); r1.setSpacing(8)
        for title, widget in [("7-SEG (P0)", SevenSegment()), ("LED BAR (P1)", LEDBar()),
                               ("MATRIX (P3-4)", LEDMatrix())]:
            f=QFrame(); f.setStyleSheet(f"QFrame{{border:1px solid {C['border']};border-radius:6px;background:{C['bg']};}}")
            l=QVBoxLayout(f); l.setContentsMargins(6,2,6,2)
            lb=QLabel(title); lb.setFont(FLB); lb.setStyleSheet(f"color:{C['dim']};")
            l.addWidget(lb); l.addWidget(widget, alignment=Qt.AlignCenter); r1.addWidget(f)
            if "7-SEG" in title: self.seg=widget
            elif "LED" in title: self.bar=widget
            elif "MATRIX" in title: self.matrix=widget
        ly.addLayout(r1)
        ly.addWidget(QLabel("PORTS"))
        self.port_mon = PortMonitor(); ly.addWidget(self.port_mon)
        ly.addWidget(QLabel("ASCII TERMINAL (P2)"))
        self.term = ASCIITerminal(); ly.addWidget(self.term)
        self._pr = 0
    def update_io(self):
        cp = self.cpu.changed_port
        if 0 in cp: self.seg.set_value(self.cpu.ports[0])
        if 1 in cp: self.bar.set_value(self.cpu.ports[1])
        if 2 in cp: self.term.put_char(self.cpu.ports[2])
        if 3 in cp: self._pr = self.cpu.ports[3]
        if 4 in cp: self.matrix.set_row(self._pr, self.cpu.ports[4])
        self.port_mon.update_ports(self.cpu, cp)
    def reset_io(self):
        self.seg.set_value(0); self.bar.set_value(0)
        self.matrix.data=[0]*8; self.matrix.sel_row=-1; self.matrix.update()
        self.term.clear_term(); self._pr=0

# ═══════════════════════════════════════════════════════════════════
#  STACK VIEW
# ═══════════════════════════════════════════════════════════════════
class StackView(QWidget):
    def __init__(self):
        super().__init__(); ly=QVBoxLayout(self); ly.setContentsMargins(4,4,4,4); ly.setSpacing(1)
        hdr=QHBoxLayout()
        for t,w in [("Addr",40),("Value",40,Qt.AlignRight),("",20),("",0)]:
            lb=QLabel(t); lb.setFixedWidth(w if isinstance(w,int) else 40)
            if len(t)==2: lb.setAlignment(Qt.AlignRight)
            lb.setFont(FLB); lb.setStyleSheet(f"color:{C['dim']};"); hdr.addWidget(lb)
        ly.addLayout(hdr)
        self.rows=[]
        for _ in range(14):
            r=QHBoxLayout(); r.setSpacing(2)
            al=QLabel(""); al.setFixedWidth(40); al.setFont(FMS); al.setAlignment(Qt.AlignRight)
            vl=QLabel(""); vl.setFixedWidth(40); vl.setFont(FMS); vl.setAlignment(Qt.AlignRight)
            sl=QLabel(""); sl.setFixedWidth(20); sl.setFont(FMS); sl.setAlignment(Qt.AlignCenter)
            r.addWidget(al); r.addWidget(vl); r.addStretch(); r.addWidget(sl)
            ly.addLayout(r); self.rows.append((al,vl,sl))
    def update_stack(self, cpu):
        sp=cpu.reg['SP']; cm=cpu.changed_mem
        for i,(al,vl,sl) in enumerate(self.rows):
            addr=sp+1+i
            if 0<=addr<256:
                v=cpu.mem[addr]; ch=addr in cm
                ac=C['green'] if ch else C['text']; bg=C['mem_write'] if ch and cm[addr]=='w' else C['mem_read'] if ch else 'transparent'
                al.setText(f"{addr:02X}"); vl.setText(f"{v:02X}")
                for lb in (al,vl): lb.setStyleSheet(f"color:{C['dim'] if lb is al else ac};background:{bg};border-radius:2px;")
                if i==0: sl.setText("◀SP"); sl.setStyleSheet(f"color:{C['amber']};background:transparent;")
                else: sl.setText(""); sl.setStyleSheet(f"background:transparent;")
            else:
                for lb in (al,vl,sl): lb.setText(""); lb.setStyleSheet(f"background:transparent;")

# ═══════════════════════════════════════════════════════════════════
#  MEMORY VIEW WITH TOOLS
# ═══════════════════════════════════════════════════════════════════
class MemView(QWidget):
    def __init__(self, cpu):
        super().__init__(); self.cpu=cpu
        self._ft=QTimer(self); self._ft.setSingleShot(True); self._ft.timeout.connect(self._cf); self._fl={}
        ly=QVBoxLayout(self); ly.setContentsMargins(0,0,0,0); ly.setSpacing(2)
        tr=QHBoxLayout(); tr.setSpacing(4)
        tr.addWidget(QLabel("MEM"))
        self.goto_inp=QLineEdit(); self.goto_inp.setPlaceholderText("Go addr"); self.goto_inp.setFixedWidth(65)
        self.goto_inp.setFont(FMS); self.goto_inp.returnPressed.connect(self._goto); tr.addWidget(self.goto_inp)
        gb=QPushButton("Go"); gb.setFixedWidth(26); gb.clicked.connect(self._goto); tr.addWidget(gb)
        self.search_inp=QLineEdit(); self.search_inp.setPlaceholderText("Search hex"); self.search_inp.setFixedWidth(65)
        self.search_inp.setFont(FMS); self.search_inp.returnPressed.connect(self._search); tr.addWidget(self.search_inp)
        sb=QPushButton("Find"); sb.setFixedWidth(30); sb.clicked.connect(self._search); tr.addWidget(sb)
        tr.addWidget(QLabel("Fill:"))
        self.fill_s=QLineEdit(); self.fill_s.setPlaceholderText("From"); self.fill_s.setFixedWidth(38)
        self.fill_s.setFont(FMS); tr.addWidget(self.fill_s)
        self.fill_e=QLineEdit(); self.fill_e.setPlaceholderText("To"); self.fill_e.setFixedWidth(38)
        self.fill_e.setFont(FMS); tr.addWidget(self.fill_e)
        self.fill_v=QLineEdit(); self.fill_v.setPlaceholderText="Val"; self.fill_v.setFixedWidth(34)
        self.fill_v.setFont(FMS); tr.addWidget(self.fill_v)
        fb=QPushButton("Fill"); fb.setFixedWidth(30); fb.clicked.connect(self._fill); tr.addWidget(fb)
        cb=QPushButton("Clr"); cb.setFixedWidth(26); cb.setToolTip("Clear all memory"); cb.clicked.connect(self._clear); tr.addWidget(cb)
        tr.addStretch(); ly.addLayout(tr)
        self.tb=QTableWidget(16,17); self.tb.verticalHeader().setVisible(False)
        self.tb.setHorizontalHeaderLabels(['Addr']+[f'{i:02X}' for i in range(16)])
        self.tb.setEditTriggers(QTableWidget.NoEditTriggers); self.tb.setSelectionMode(QTableWidget.NoSelection)
        self.tb.setFocusPolicy(Qt.NoFocus)
        self.tb.setStyleSheet(f"QTableWidget{{background:{C['panel']};gridline-color:{C['border']};border:1px solid {C['border']};color:{C['text']};font-family:Consolas;font-size:10px;}}QTableWidget::item{{padding:0;border:none;}}QHeaderView::section{{background:{C['bg']};color:{C['dim']};border:1px solid {C['border']};padding:2px;font-family:Consolas;font-size:9px;}}")
        self.tb.setColumnWidth(0,32)
        for i in range(1,17): self.tb.setColumnWidth(i,27)
        self.tb.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tb.verticalHeader().setDefaultSectionSize(19)
        self.cells={}
        for r in range(16):
            ai=QTableWidgetItem(f'{r*16:02X}'); ai.setTextAlignment(Qt.AlignCenter)
            ai.setForeground(QColor(C['dim'])); ai.setBackground(QColor(C['bg'])); self.tb.setItem(r,0,ai)
            for c2 in range(16):
                a=r*16+c2; it=QTableWidgetItem('00'); it.setTextAlignment(Qt.AlignCenter)
                it.setBackground(QColor(C['mem_zero'])); it.setForeground(QColor(C['border']))
                self.tb.setItem(r,c2+1,it); self.cells[a]=it
        self.tb.cellDoubleClicked.connect(self._edit_cell); ly.addWidget(self.tb); self._editor=None
    def _parse_hex(self, s):
        s=s.strip()
        return int(s,16) if s.lower().startswith('0x') else int(s,16) if s else 0
    def _goto(self):
        try:
            a=self._parse_hex(self.goto_inp.text())&0xFF; r,c=divmod(a,16)
            self.tb.scrollTo(self.tb.model().index(r,c+1))
            it=self.cells[a]; it.setBackground(QColor(C['amber']))
            QTimer.singleShot(800,lambda: it.setBackground(QColor(C['mem_write']) if self.cpu.mem[a] else QColor(C['mem_zero'])))
            self.goto_inp.clear()
        except: pass
    def _search(self):
        try:
            val=self._parse_hex(self.search_inp.text())&0xFF; found=False
            for a in range(256):
                if self.cpu.mem[a]==val:
                    r,c=divmod(a,16); self.tb.scrollTo(self.tb.model().index(r,c+1))
                    it=self.cells[a]; it.setBackground(QColor(C['purple']))
                    QTimer.singleShot(1200,lambda: it.setBackground(QColor(C['mem_zero'])))
                    found=True; break
            if not found: self.search_inp.setStyleSheet(f"color:{C['red']};border:1px solid {C['red']};")
            else: self.search_inp.setStyleSheet("")
        except: pass
    def _fill(self):
        try:
            s=self._parse_hex(self.fill_s.text())&0xFF; e=self._parse_hex(self.fill_e.text())&0xFF
            v=self._parse_hex(self.fill_v.text())&0xFF
            for a in range(min(s,e),max(s,e)+1): self.cpu.mem[a]=v
            self.update_view(self.cpu)
        except: pass
    def _clear(self):
        self.cpu.mem=[0]*256; self.update_view(self.cpu)
    def _edit_cell(self, row, col):
        if col==0: return
        a=row*16+(col-1); it=self.cells[a]; idx=self.tb.model().index(row,col)
        rect=self.tb.visualRect(idx); le=QLineEdit(self.tb.viewport()); le.setFont(FMS)
        le.setText(f"{self.cpu.mem[a]:02X}"); le.selectAll()
        le.setStyleSheet(f"background:{C['editor']};color:{C['green']};border:2px solid {C['green']};border-radius:3px;padding:1px;")
        le.setGeometry(rect); le.setFocus(); le.show()
        def commit():
            try: v=int(le.text(),16)&0xFF; self.cpu.mem[a]=v; self.update_view(self.cpu)
            except: pass
            le.deleteLater()
        le.returnPressed.connect(commit); le.editingFinished.connect(commit)
    def update_view(self, cpu):
        cm=cpu.changed_mem; sp=cpu.reg['SP']
        for a in range(256):
            v=cpu.mem[a]; it=self.cells[a]; it.setText(f'{v:02X}')
            if a in cm:
                if cm[a]=='w': it.setBackground(QColor(C['mem_write'])); it.setForeground(QColor(C['green']))
                else: it.setBackground(QColor(C['mem_read'])); it.setForeground(QColor(C['cyan']))
                it.setToolTip(f"0x{a:02X}={v} [{cm[a].upper()}]")
            elif v:
                f=v/255; it.setBackground(QColor(int(14+8*f),int(19+32*f),int(25+24*f)))
                it.setForeground(QColor(C['cyan'])); it.setToolTip(f"0x{a:02X} = {v} (0b{v:08b})")
            else:
                it.setBackground(QColor(C['mem_zero'])); it.setForeground(QColor(C['border']))
                it.setToolTip(f"0x{a:02X} = 0")
            if a==sp: it.setForeground(QColor(C['sp_mark']))
        if cm: self._fl=dict(cm); self._ft.start(300)
    def _cf(self): self._fl.clear()

# ═══════════════════════════════════════════════════════════════════
#  WATCH PANEL
# ═══════════════════════════════════════════════════════════════════
class WatchPanel(QWidget):
    def __init__(self, cpu):
        super().__init__(); self.cpu=cpu; self.watches=[]; self.prev={}
        ly=QVBoxLayout(self); ly.setContentsMargins(4,4,4,4); ly.setSpacing(4)
        row=QHBoxLayout()
        self.inp=QLineEdit(); self.inp.setPlaceholderText("Hex addr (e.g. 20)"); self.inp.setFont(FMS)
        self.inp.returnPressed.connect(self._add); row.addWidget(self.inp)
        b=QPushButton("+"); b.setFixedWidth(28); b.clicked.connect(self._add); row.addWidget(b)
        cb=QPushButton("Clear"); cb.setFixedWidth(40); cb.clicked.connect(self._clear); row.addWidget(cb)
        ly.addLayout(row)
        self.tbl=QTableWidget(0,5); self.tbl.setHorizontalHeaderLabels(['Addr','Hex','Dec','Bin',''])
        self.tbl.verticalHeader().setVisible(False); self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setStyleSheet(f"QTableWidget{{background:{C['panel']};gridline-color:{C['border']};border:1px solid {C['border']};color:{C['text']};font-family:Consolas;font-size:10px;}}QHeaderView::section{{background:{C['bg']};color:{C['dim']};border:1px solid {C['border']};padding:2px;font-family:Consolas;font-size:9px;}}")
        for i,w in enumerate([40,40,40,80,50]): self.tbl.setColumnWidth(i,w)
        self.tbl.doubleClicked.connect(self._remove); ly.addWidget(self.tbl)
    def _add(self):
        t=self.inp.text().strip()
        try:
            a=int(t,16) if not t.startswith('0x') else int(t,16)
            if 0<=a<256 and a not in self.watches: self.watches.append(a); self.prev[a]=self.cpu.mem[a]; self._rebuild()
        except: pass
        self.inp.clear()
    def _remove(self, idx):
        if idx.row()<len(self.watches): a=self.watches.pop(idx.row()); self.prev.pop(a,None); self._rebuild()
    def _clear(self): self.watches.clear(); self.prev.clear(); self._rebuild()
    def _rebuild(self):
        self.tbl.setRowCount(len(self.watches))
        for i,a in enumerate(sorted(self.watches)):
            v=self.cpu.mem[a]; pv=self.prev.get(a,0); ch=v!=pv
            col=C['green'] if ch else C['text']; bg=QColor(C['mem_write']) if ch else QColor(C['panel'])
            for j,txt in enumerate([f"{a:02X}",f"{v:02X}",str(v),f"{v:08b}","▲" if ch else ""]):
                it=QTableWidgetItem(txt); it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QColor(col if j else C['dim'])); it.setBackground(bg); self.tbl.setItem(i,j,it)
    def update_watches(self):
        for a in self.watches: self.prev[a]=self.cpu.mem[a]
        self._rebuild()

# ═══════════════════════════════════════════════════════════════════
#  DISASSEMBLY VIEW
# ═══════════════════════════════════════════════════════════════════
class DisasmView(QTableWidget):
    def __init__(self):
        super().__init__(0,4)
        self.setHorizontalHeaderLabels(['Addr','Label','Instruction','Src'])
        self.verticalHeader().setVisible(False); self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setStyleSheet(f"QTableWidget{{background:{C['panel']};gridline-color:{C['border']};border:1px solid {C['border']};color:{C['text']};font-family:Consolas;font-size:10px;}}QTableWidget::item{{padding:1px;border:none;}}QHeaderView::section{{background:{C['bg']};color:{C['dim']};border:1px solid {C['border']};padding:2px;font-family:Consolas;font-size:9px;}}")
        self.setColumnWidth(0,40); self.setColumnWidth(1,60); self.setColumnWidth(2,200); self.setColumnWidth(3,30)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.verticalHeader().setDefaultSectionSize(18)
        self.cellDoubleClicked.connect(self._jump_src)
    def load(self, prog, labels):
        self.setRowCount(len(prog))
        addr_to_label = {v:k for k,v in labels.items()}
        for i, instr in enumerate(prog):
            addr=instr['addr']; lbl=addr_to_label.get(addr,'')
            it_a=QTableWidgetItem(f"{addr:02X}"); it_a.setTextAlignment(Qt.AlignCenter)
            it_l=QTableWidgetItem(lbl); it_l.setForeground(QColor(C['purple']))
            it_i=QTableWidgetItem(instr['text'])
            it_s=QTableWidgetItem(f"{instr['line']+1}"); it_s.setTextAlignment(Qt.AlignCenter)
            it_s.setForeground(QColor(C['dim']))
            for j,it in enumerate([it_a,it_l,it_i,it_s]): self.setItem(i,j,it)
    def highlight_pc(self, pc):
        for i in range(self.rowCount()):
            item=self.item(i,0)
            addr=int(item.text(),16) if item else -1
            if addr==pc:
                for j in range(4): self.item(i,j).setBackground(QColor(C['cur_line']))
                self.scrollTo(self.model().index(i,0)); return
        for i in range(self.rowCount()):
            for j in range(4): self.item(i,j).setBackground(QColor(C['panel']))
    def _jump_src(self, row, col):
        it=self.item(row,3)
        if it:
            try:
                from PySide6.QtCore import QCoreApplication
                win=QCoreApplication.instance().activeWindow()
                if hasattr(win,'editor'):
                    ln=int(it.text())-1; win.editor.highlight_pc(ln)
                    cursor=win.editor.textCursor()
                    cursor.movePosition(QTextCursor.Start); cursor.movePosition(QTextCursor.Down,n=ln)
                    win.editor.setTextCursor(cursor); win.editor.ensureCursorVisible()
            except: pass

# ═══════════════════════════════════════════════════════════════════
#  REGISTER HISTORY CHART
# ═══════════════════════════════════════════════════════════════════
class HistoryChart(QWidget):
    COLORS = {'A':C['green'],'B':C['cyan'],'C':C['amber'],'D':C['purple']}
    def __init__(self):
        super().__init__(); self.data={r:deque(maxlen=300) for r in 'ABCD'}
        self.setMinimumHeight(180)
    def record(self, cpu):
        for r in 'ABCD': self.data[r].append(cpu.reg[r])
        self.update()
    def clear(self): self.data={r:deque(maxlen=300) for r in 'ABCD'}; self.update()
    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(C['panel']))
        w,h=self.width(),self.height(); ml,mr,mt,mb=35,10,10,20
        pw=w-ml-mr; ph=h-mt-mb
        # Grid
        p.setPen(QPen(QColor(C['border']),1,Qt.DotLine))
        for v in [0,64,128,192,255]:
            y=mt+ph-int(v/255*ph)
            p.drawLine(ml,y,ml+pw,y); p.setPen(QColor(C['dim'])); p.setFont(FMS)
            p.drawText(2,y-6,f"{v:03}"); p.setPen(QPen(QColor(C['border']),1,Qt.DotLine))
        # Lines
        for reg in 'ABCD':
            d=self.data[reg]; n=len(d)
            if n<2: continue
            p.setPen(QPen(QColor(self.COLORS[reg]),2))
            path=painter_path = None
            for i,v in enumerate(d):
                x=ml+int(i/(max(n-1,1))*pw); y=mt+ph-int(v/255*ph)
                if path is None: path = __import__('PySide6.QtGui',fromlist=['QPainterPath']).QPainterPath(QPoint(x,y))
                else: path.lineTo(x,y)
            if path: p.drawPath(path)
        # Legend
        lx=ml+5; ly2=mt+5
        for reg in 'ABCD':
            p.setPen(Qt.NoPen); p.setBrush(QColor(self.COLORS[reg]))
            p.drawEllipse(lx,ly2,8,8); lx+=12
            p.setPen(QColor(self.COLORS[reg])); p.setFont(FMS)
            p.drawText(lx,ly2+9,reg); lx+=20
        p.end()

# ═══════════════════════════════════════════════════════════════════
#  PROFILER WIDGET
# ═══════════════════════════════════════════════════════════════════
class ProfilerWidget(QWidget):
    CAT_COLORS = {'arithmetic':C['green'],'logic':C['cyan'],'branch':C['amber'],
                  'move':C['text'],'stack':C['purple'],'io':C['red'],'control':C['dim']}
    def __init__(self):
        super().__init__(); self.counts={}; self.setMinimumHeight(100)
    def record(self, op):
        self.counts[op]=self.counts.get(op,0)+1; self.update()
    def clear(self): self.counts={}; self.update()
    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(C['panel']))
        if not self.counts:
            p.setPen(QColor(C['dim'])); p.setFont(FUI)
            p.drawText(self.rect(), Qt.AlignCenter, "No data yet — run program to profile"); p.end(); return
        items=sorted(self.counts.items(), key=lambda x:-x[1])
        mx=items[0][1]; w=self.width(); h=self.height()
        bh=min(18, max(12, (h-10)//len(items)-2)); y=5
        bar_max_w=w-90
        for op,cnt in items:
            cat=self._cat(op); col=self.CAT_COLORS.get(cat,C['text'])
            bw=int(cnt/mx*bar_max_w)
            p.setPen(Qt.NoPen); p.setBrush(QColor(col)); p.setOpacity(0.7)
            p.drawRoundedRect(55,y,bw,bh,3,3); p.setOpacity(1)
            p.setPen(QColor(C['dim'])); p.setFont(FMS)
            p.drawText(2,y+bh-2,op)
            p.setPen(QColor(col)); p.drawText(60+bw,y+bh-2,f"{cnt}")
            y+=bh+2
        p.end()
    @staticmethod
    def _cat(op):
        if op in ('ADD','SUB','MUL','INC','DEC','CMP'): return 'arithmetic'
        if op in ('AND','OR','XOR','NOT','SHL','SHR'): return 'logic'
        if op in ('JMP','JZ','JNZ','JC','JNC','JN'): return 'branch'
        if op in ('MOV','LOAD','STORE'): return 'move'
        if op in ('PUSH','POP','CALL','RET'): return 'stack'
        if op in ('IN','OUT'): return 'io'
        return 'control'

# ═══════════════════════════════════════════════════════════════════
#  SECTION HELPER
# ═══════════════════════════════════════════════════════════════════
class Section(QFrame):
    def __init__(self, title, widget):
        super().__init__()
        self.setStyleSheet(f"Section{{background:{C['panel']};border:1px solid {C['border']};border-radius:6px;}}")
        ly=QVBoxLayout(self); ly.setContentsMargins(0,0,0,0); ly.setSpacing(0)
        lb=QLabel(f"  {title}"); lb.setFont(FTI); lb.setStyleSheet(f"color:{C['dim']};padding:4px 0;")
        ly.addWidget(lb); ly.addWidget(widget)

# ═══════════════════════════════════════════════════════════════════
#  CONDITION EVALUATOR
# ═══════════════════════════════════════════════════════════════════
def _eval_expr(expr, cpu):
    e = expr.strip().upper()
    if e in cpu.REGS: return cpu.reg[e]
    if e in cpu.FLAGS: return 1 if cpu.flg[e] else 0
    if e.startswith('[') and e.endswith(']'):
        inner=e[1:-1].strip()
        if inner in cpu.REGS: return cpu.mem[cpu.reg[inner]&0xFF]
        return cpu.mem[int(inner,16)&0xFF]
    return int(e,16) if e.startswith('0X') else int(e)

def eval_bp_cond(cond, cpu):
    cond=cond.strip()
    if not cond: return True
    for op in ['==','!=','>=','<=','>','<']:
        if op in cond:
            l,r=cond.split(op,1)
            try:
                lv=_eval_expr(l,cpu); rv=_eval_expr(r,cpu)
                if op=='==': return lv==rv
                if op=='!=': return lv!=rv
                if op=='>=': return lv>=rv
                if op=='<=': return lv<=rv
                if op=='>': return lv>rv
                if op=='<': return lv<rv
            except: return True
    try: return bool(_eval_expr(cond, cpu))
    except: return True

# ═══════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Emulator — 8-Bit [Ultimate]")
        self.resize(1340, 900)
        self.cpu=CPU(); self.asm=Assembler()
        self.assembled=False; self.running=False
        self.undo_stack=deque(maxlen=200)
        self.history_data={r:deque(maxlen=300) for r in 'ABCD'}
        self.profiler_counts={}
        self._build_ui(); self._build_menu()
        self._load_example("Counter"); self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow{{background:{C['bg']};}}
            QPushButton{{background:{C['panel']};color:{C['text']};border:1px solid {C['border']};border-radius:4px;padding:5px 10px;font-family:{FUI.family()};font-size:10px;}}
            QPushButton:hover{{border-color:{C['green']};color:{C['green']};}}
            QPushButton:pressed{{background:{C['border']};}}
            QPushButton:disabled{{color:{C['dim']};border-color:{C['border']};}}
            QComboBox{{background:{C['panel']};color:{C['text']};border:1px solid {C['border']};border-radius:4px;padding:5px 8px;font-family:{FUI.family()};font-size:10px;}}
            QComboBox::drop-down{{border:none;width:18px;}}
            QComboBox QAbstractItemView{{background:{C['panel']};color:{C['text']};selection-background-color:{C['border']};}}
            QTextEdit{{background:{C['panel']};color:{C['dim']};border:1px solid {C['border']};border-radius:4px;font-family:{FMS.family()};font-size:10px;padding:4px;}}
            QSlider::groove:horizontal{{background:{C['border']};height:4px;border-radius:2px;}}
            QSlider::handle:horizontal{{background:{C['green']};width:14px;height:14px;margin:-5px 0;border-radius:7px;}}
            QLineEdit{{background:{C['editor']};color:{C['text']};border:1px solid {C['border']};border-radius:3px;padding:4px;font-family:{FMS.family()};font-size:10px;}}
            QTabWidget::pane{{border:1px solid {C['border']};background:{C['panel']};border-radius:4px;}}
            QTabBar::tab{{background:{C['bg']};color:{C['dim']};border:1px solid {C['border']};padding:4px 10px;border-top-left-radius:4px;border-top-right-radius:4px;margin-right:1px;font-family:{FUI.family()};font-size:9px;}}
            QTabBar::tab:selected{{background:{C['panel']};color:{C['green']};border-bottom-color:{C['panel']};}}
            QTabBar::tab:hover{{color:{C['text']};}}
            QMenuBar{{background:{C['bg']};color:{C['text']};border-bottom:1px solid {C['border']};}}
            QMenuBar::item:selected{{background:{C['border']};}}
            QMenu{{background:{C['panel']};color:{C['text']};border:1px solid {C['border']};}}
            QMenu::item:selected{{background:{C['border']};color:{C['green']};}}
            QLabel{{background:transparent;}}
        """)

    def _build_menu(self):
        mb=self.menuBar()
        fm=mb.addMenu("File")
        fm.addAction("Save Source...",self._save_source,QKeySequence("Ctrl+S"))
        fm.addAction("Open Source...",self._open_source,QKeySequence("Ctrl+O"))
        fm.addSeparator(); fm.addAction("Export Memory...",self._save_mem)
        fm.addAction("Import Memory...",self._load_mem)
        fm.addSeparator(); fm.addAction("Exit",self.close,QKeySequence("Ctrl+Q"))
        dm=mb.addMenu("Debug")
        dm.addAction("Assemble",self._assemble,QKeySequence("F7"))
        dm.addAction("Step Into",self._step,QKeySequence("F11"))
        dm.addAction("Step Over",self._step_over,QKeySequence("F10"))
        dm.addAction("Step Back",self._step_back,QKeySequence("Shift+F11"))
        dm.addAction("Run",self._run,QKeySequence("F5"))
        dm.addAction("Stop",self._stop,QKeySequence("Shift+F5"))
        dm.addAction("Reset",self._reset,QKeySequence("Ctrl+Shift+R"))
        dm.addSeparator(); dm.addAction("Clear Breakpoints",self._clear_bp)
        dm.addAction("Clear Console",lambda:self.console.clear())
        dm.addAction("Clear History",lambda:self.history_chart.clear())

    def _build_ui(self):
        central=QWidget(); self.setCentralWidget(central)
        root=QVBoxLayout(central); root.setContentsMargins(6,6,6,6); root.setSpacing(4)
        # Toolbar
        tb=QHBoxLayout(); tb.setSpacing(5)
        self.combo=QComboBox(); self.combo.setMinimumWidth(140)
        self.combo.addItems(EXAMPLES.keys()); self.combo.currentTextChanged.connect(self._load_example)
        tb.addWidget(self.combo)
        for txt,slot,key in [("⬡Asm",self._assemble,"F7"),("⏬Into",self._step,"F11"),
                              ("⏭Over",self._step_over,"F10"),("⏪Back",self._step_back,"Shift+F11"),
                              ("▶Run",self._run,"F5"),("■Stop",self._stop,""),("↺Reset",self._reset,"")]:
            b=QPushButton(txt); b.clicked.connect(slot); b.setMinimumWidth(52)
            if key: b.setToolTip(key)
            tb.addWidget(b)
        tb.addSpacing(10); tb.addWidget(QLabel("Speed:"))
        self.speed=QSlider(Qt.Horizontal); self.speed.setRange(1,100); self.speed.setValue(50)
        self.speed.setFixedWidth(100); tb.addWidget(self.speed)
        self.speed_lbl=QLabel("50ms"); self.speed_lbl.setFixedWidth(36)
        self.speed_lbl.setStyleSheet(f"color:{C['dim']};")
        self.speed.valueChanged.connect(lambda v: self.speed_lbl.setText(f"{self._delay()}ms"))
        tb.addStretch()
        self.light=QFrame(); self.light.setFixedSize(12,12)
        self.light.setStyleSheet(f"background:{C['border']};border-radius:6px;"); tb.addWidget(self.light)
        root.addLayout(tb)
        # Main split
        splitter=QSplitter(Qt.Horizontal)
        self.editor=CodeEditor(); self.editor.setPlainText(""); Highlighter(self.editor.document())
        ef=QFrame(); ef.setStyleSheet(f"QFrame{{border:1px solid {C['border']};border-radius:6px;background:{C['editor']};}}")
        ely=QVBoxLayout(ef); ely.setContentsMargins(0,0,0,0); ely.addWidget(self.editor)
        splitter.addWidget(ef)
        # Right
        right=QWidget(); rly=QVBoxLayout(right); rly.setContentsMargins(0,0,0,0); rly.setSpacing(4)
        rg=QWidget(); rgl=QGridLayout(rg); rgl.setContentsMargins(6,4,6,4); rgl.setSpacing(5)
        self.regs={}
        for i,name in enumerate(['A','B','C','D']):
            c=RegCard(name); rgl.addWidget(c,0,i); self.regs[name]=c
        self.regs['PC']=RegCard('PC',True); rgl.addWidget(self.regs['PC'],1,0,1,2)
        self.regs['SP']=RegCard('SP',True); rgl.addWidget(self.regs['SP'],1,2,1,2)
        rly.addWidget(Section("REGISTERS",rg))
        fg=QWidget(); fgl=QHBoxLayout(fg); fgl.setContentsMargins(6,0,6,2); fgl.setSpacing(6)
        self.flags={}
        for f in ['Z','C','N','V']: d=FlagDot(f); fgl.addWidget(d); self.flags[f]=d
        rly.addWidget(Section("FLAGS",fg))
        # Tabs
        self.tabs=QTabWidget()
        self.io_panel=IOPanel(self.cpu)
        self.tabs.addTab(self._wrap(self.io_panel),"I/O")
        self.stack_view=StackView()
        self.tabs.addTab(self._wrap(self.stack_view),"Stack")
        self.mem_view=MemView(self.cpu)
        self.tabs.addTab(self._wrap(self.mem_view),"Memory")
        self.watch_panel=WatchPanel(self.cpu)
        self.tabs.addTab(self._wrap(self.watch_panel),"Watch")
        self.disasm_view=DisasmView()
        self.tabs.addTab(self._wrap(self.disasm_view),"Disasm")
        self.history_chart=HistoryChart()
        self.tabs.addTab(self._wrap(self.history_chart),"History")
        self.profiler=ProfilerWidget()
        self.tabs.addTab(self._wrap(self.profiler),"Profiler")
        ref=QTextEdit(); ref.setReadOnly(True); ref.setHtml(REF_HTML)
        ref.setStyleSheet(f"background:{C['panel']};border:none;")
        self.tabs.addTab(ref,"Ref ❓")
        rly.addWidget(self.tabs,stretch=1)
        splitter.addWidget(right); splitter.setSizes([460,540])
        splitter.setHandleWidth(2); root.addWidget(splitter,stretch=1)
        # Console
        cbox=QFrame(); cbox.setStyleSheet(f"QFrame{{border:1px solid {C['border']};border-radius:4px;}}")
        cly=QVBoxLayout(cbox); cly.setContentsMargins(0,0,0,0); cly.setSpacing(0)
        chr2=QHBoxLayout(); chr2.setSpacing(4)
        chr2.addWidget(QLabel("  CONSOLE"))
        chr2.addStretch()
        cb1=QPushButton("Copy"); cb1.setFixedWidth(40); cb1.clicked.connect(self._copy_console); chr2.addWidget(cb1)
        cb2=QPushButton("Clear"); cb2.setFixedWidth(40); cb2.clicked.connect(lambda:self.console.clear()); chr2.addWidget(cb2)
        cly.addLayout(chr2)
        self.console=QTextEdit(); self.console.setReadOnly(True); self.console.setMaximumHeight(110)
        self.console.setStyleSheet(f"background:{C['panel']};color:{C['dim']};border:none;font-family:{FMS.family()};font-size:10px;padding:2px;")
        cly.addWidget(self.console)
        # Debug input
        dib=QHBoxLayout(); dib.setSpacing(4)
        dib.addWidget(QLabel("  >"))
        self.dbg_input=QLineEdit(); self.dbg_input.setPlaceholderText("Type ? A | ? 0x20 | ! MOV A,5 | .fill 20 30 FF | .set A 42 | .help")
        self.dbg_input.setFont(FMS); self.dbg_input.returnPressed.connect(self._dbg_cmd)
        dib.addWidget(self.dbg_input); cly.addLayout(dib)
        root.addWidget(cbox)
        # Status
        sb=QHBoxLayout(); sb.setSpacing(14)
        self.st_cycles=QLabel("Cycles: 0"); self.st_cycles.setStyleSheet(f"color:{C['dim']};")
        self.st_state=QLabel("Idle"); self.st_state.setStyleSheet(f"color:{C['amber']};")
        self.st_pc=QLabel("PC: 00"); self.st_pc.setStyleSheet(f"color:{C['dim']};")
        self.st_bp=QLabel("BP: 0"); self.st_bp.setStyleSheet(f"color:{C['bp']};")
        self.st_undo=QLabel("Undo: 0"); self.st_undo.setStyleSheet(f"color:{C['dim']};")
        for w in [self.st_cycles,self.st_state,self.st_pc,self.st_bp,self.st_undo]: sb.addWidget(w)
        sb.addStretch(); root.addLayout(sb)
        self.timer=QTimer(self); self.timer.timeout.connect(self._auto_step)

    def _wrap(self, w):
        f=QWidget(); l=QVBoxLayout(f); l.setContentsMargins(2,2,2,2); l.addWidget(w); return f

    def _delay(self): v=self.speed.value(); return max(10,int(510-v*5))

    def _log(self, msg, color=None):
        c=color or C['dim']
        self.console.append(f"<span style='color:{c}'>{msg}</span>")
        sb=self.console.verticalScrollBar(); sb.setValue(sb.maximum())

    def _copy_console(self):
        txt=self.console.toPlainText(); QApplication.clipboard().setText(txt)
        self._log("Copied to clipboard", C['cyan'])

    def _load_example(self, name):
        if name in EXAMPLES: self.editor.setPlainText(EXAMPLES[name]); self._reset()

    def _assemble(self):
        try:
            prog,labels=self.asm.parse(self.editor.toPlainText())
            self.cpu.reset(); self.cpu.load(prog,labels); self.assembled=True
            self.undo_stack.clear(); self.history_data={r:deque(maxlen=300) for r in 'ABCD'}
            self.profiler_counts={}
            self._update_all(); self.editor.highlight_pc(-1); self.io_panel.reset_io()
            self.disasm_view.load(prog, labels); self.history_chart.clear(); self.profiler.clear()
            self._log(f"✔ Assembled: {len(prog)} instructions, {len(labels)} labels", C['green'])
            for lb,addr in labels.items(): self._log(f"  {lb} = 0x{addr:02X}", C['purple'])
        except SyntaxError as e:
            self._log(f"✘ {e}", C['red'])
            m=re.search(r'Line (\d+)', str(e))
            if m: self.editor.highlight_err(int(m.group(1))-1)

    def _check_bp(self):
        pc=self.cpu.reg['PC']
        if pc<len(self.cpu.prog):
            line=self.cpu.prog[pc]['line']
            if line in self.editor.ln_area.breakpoints:
                cond=self.editor.ln_area.bp_conds.get(line,'')
                if eval_bp_cond(cond, self.cpu):
                    self.editor.highlight_pc(line)
                    extra=f" [{cond}]" if cond else ""
                    self._log(f"● Breakpoint at line {line+1} (0x{pc:02X}){extra}", C['bp'])
                    self._update_all(); self._update_status(); return True
        return False

    def _step(self, log=True):
        if not self.assembled: self._log("⚠ Assemble first!",C['amber']); return False
        if self.cpu.halted: self._log("⚠ Halted — reset",C['amber']); return False
        if self._check_bp(): return False
        self.undo_stack.append(CPUState(self.cpu))
        pc=self.cpu.reg['PC']; instr=self.cpu.prog[pc]
        ok=self.cpu.step()
        if log:
            eff=[f"{r}={self.cpu.reg[r]:02X}" for r in sorted(self.cpu.changed_reg)]
            pef=[f"P{p}={self.cpu.ports[p]:02X}" for p in sorted(self.cpu.changed_port)]
            es=" → "+", ".join(eff+pef) if eff+pef else ""
            col=C['green'] if ok else C['red']
            self._log(f"<span style='color:{C['dim']}'>[{pc:02X}]</span> {instr['text']}{es}", col)
            if self.cpu.error:
                self._log(f"  ✘ {self.cpu.error}", C['red'])
                if pc<len(self.cpu.prog): self.editor.highlight_err(self.cpu.prog[pc]['line'])
        # Record history & profiler
        for r in 'ABCD': self.history_data[r].append(self.cpu.reg[r])
        self.history_chart.data = self.history_data
        self.profiler_counts[instr['op']]=self.profiler_counts.get(instr['op'],0)+1
        self.profiler.counts = dict(self.profiler_counts)
        self._update_all()
        if not self.cpu.halted and self.cpu.reg['PC']<len(self.cpu.prog):
            self.editor.highlight_pc(self.cpu.prog[self.cpu.reg['PC']]['line'])
            self.disasm_view.highlight_pc(self.cpu.reg['PC'])
        elif self.cpu.halted:
            self.editor.highlight_pc(-1); self.disasm_view.highlight_pc(-1)
            if log: self._log("■ Halted", C['amber'])
        self._update_status(); return ok

    def _step_back(self):
        if not self.undo_stack: self._log("⚠ Nothing to undo",C['amber']); return
        state=self.undo_stack.pop(); state.restore(self.cpu)
        self.cpu.changed_reg=set(self.cpu.REGS)
        self._update_all()
        pc=self.cpu.reg['PC']
        if pc<len(self.cpu.prog):
            self.editor.highlight_pc(self.cpu.prog[pc]['line'])
            self.disasm_view.highlight_pc(pc)
        else: self.editor.highlight_pc(-1); self.disasm_view.highlight_pc(-1)
        self._log(f"⏪ Stepped back → PC=0x{pc:02X}", C['cyan'])
        self._update_status()

    def _step_over(self):
        if not self.assembled: self._log("⚠ Assemble first!",C['amber']); return
        if self.cpu.halted: self._log("⚠ Halted",C['amber']); return
        if self._check_bp(): return
        pc=self.cpu.reg['PC']
        if pc<len(self.cpu.prog) and self.cpu.prog[pc]['op']=='CALL':
            ret_addr=pc+1; steps=0; saved_states=[]
            while self.cpu.reg['PC']!=ret_addr and not self.cpu.halted and steps<10000:
                saved_states.append(CPUState(self.cpu))
                self.cpu.step(); steps+=1
                self.profiler_counts[self.cpu.prog[min(pc,len(self.cpu.prog)-1)]['op']]=\
                    self.profiler_counts.get(self.cpu.prog[min(pc,len(self.cpu.prog)-1)]['op'],0)+1
            for s in saved_states: self.undo_stack.append(s)
            self._log(f"⏭ Step over CALL at 0x{pc:02X} ({steps} steps)", C['cyan'])
        else: self._step(); return
        self._update_all()
        if not self.cpu.halted and self.cpu.reg['PC']<len(self.cpu.prog):
            self.editor.highlight_pc(self.cpu.prog[self.cpu.reg['PC']]['line'])
            self.disasm_view.highlight_pc(self.cpu.reg['PC'])
        self._update_status()

    def _run(self):
        if not self.assembled: self._log("⚠ Assemble first!",C['amber']); return
        if self.cpu.halted: self._log("⚠ Halted",C['amber']); return
        self.running=True; self.timer.start(self._delay())
        self.light.setStyleSheet(f"background:{C['green']};border-radius:6px;")
        self.st_state.setText("Running"); self.st_state.setStyleSheet(f"color:{C['green']};")

    def _stop(self):
        self.running=False; self.timer.stop()
        self.light.setStyleSheet(f"background:{C['amber']};border-radius:6px;")
        self.st_state.setText("Paused"); self.st_state.setStyleSheet(f"color:{C['amber']};")

    def _auto_step(self):
        if not self.running or self.cpu.halted: self._stop(); return
        if self._check_bp(): self._stop(); return
        self._step(log=True)
        self.timer.setInterval(self._delay())

    def _reset(self):
        self._stop(); self.cpu.reset(); self.assembled=False
        self.undo_stack.clear(); self.history_data={r:deque(maxlen=300) for r in 'ABCD'}
        self.profiler_counts={}
        self._update_all(); self.editor.highlight_pc(-1)
        self.io_panel.reset_io(); self.watch_panel._rebuild()
        self.disasm_view.setRowCount(0); self.history_chart.clear(); self.profiler.clear()
        self.st_cycles.setText("Cycles: 0"); self.st_state.setText("Idle")
        self.st_state.setStyleSheet(f"color:{C['amber']};"); self.st_pc.setText("PC: 00")
        self.light.setStyleSheet(f"background:{C['border']};border-radius:6px;")
        self._log("↺ Reset", C['dim'])

    def _clear_bp(self):
        self.editor.ln_area.breakpoints.clear(); self.editor.ln_area.bp_conds.clear()
        self.editor.ln_area.update(); self._log("Breakpoints cleared", C['dim'])

    def _update_all(self):
        self._update_regs(); self._update_flags(); self.mem_view.update_view(self.cpu)
        self.io_panel.update_io(); self.stack_view.update_stack(self.cpu)
        self.watch_panel.update_watches(); self.history_chart.update(); self.profiler.update()
        self.st_bp.setText(f"BP: {len(self.editor.ln_area.breakpoints)}")
        self.st_undo.setText(f"Undo: {len(self.undo_stack)}")

    def _update_regs(self):
        for name,card in self.regs.items():
            old=card._val; new=self.cpu.reg[name]
            changed=[i for i in range(8) if ((old>>(7-i))&1)!=((new>>(7-i))&1)]
            card.set_val(new, changed if name in self.cpu.changed_reg else None)
            if name in self.cpu.changed_reg: card.flash()

    def _update_flags(self):
        for f,dot in self.flags.items(): dot.set_val(self.cpu.flg[f])

    def _update_status(self):
        self.st_cycles.setText(f"Cycles: {self.cpu.cycles}")
        self.st_pc.setText(f"PC: {self.cpu.reg['PC']:02X}")
        self.st_undo.setText(f"Undo: {len(self.undo_stack)}")
        if self.cpu.halted:
            self.st_state.setText("Halted"); self.st_state.setStyleSheet(f"color:{C['red']};")
            self.light.setStyleSheet(f"background:{C['red']};border-radius:6px;"); self._stop()

    # ── Debug Console ──
    def _dbg_cmd(self):
        cmd=self.dbg_input.text().strip(); self.dbg_input.clear()
        if not cmd: return
        try:
            if cmd.startswith('?'):
                expr=cmd[1:].strip()
                if expr.upper() in CPU.REGS:
                    r=expr.upper(); v=self.cpu.reg[r]
                    self._log(f"{r} = 0x{v:02X} = {v} = {v:08b}", C['cyan'])
                elif expr.upper() in CPU.FLAGS:
                    f=expr.upper(); v=self.cpu.flg[f]
                    self._log(f"{f} = {int(v)}", C['cyan'])
                else:
                    a=self._ph(expr)&0xFF; v=self.cpu.mem[a]
                    self._log(f"[0x{a:02X}] = 0x{v:02X} = {v} = {v:08b}", C['cyan'])
            elif cmd.startswith('!'):
                asm_cmd=cmd[1:].strip(); prog,labels=self.asm.parse(asm_cmd)
                if prog:
                    self.undo_stack.append(CPUState(self.cpu))
                    instr=prog[0]; pc=self.cpu.reg['PC']
                    self.cpu.prog=[instr]; self.cpu.labels={}
                    self.cpu.reg['PC']=0; ok=self.cpu.step()
                    self.cpu.prog=self.prog if hasattr(self,'_orig_prog') else []
                    self.cpu.labels=self.labels if hasattr(self,'_orig_labels') else {}
                    eff=[f"{r}={self.cpu.reg[r]:02X}" for r in sorted(self.cpu.changed_reg)]
                    es=" → "+", ".join(eff) if eff else ""
                    self._log(f"⚡ {instr['text']}{es}", C['amber'])
                    self._update_all()
            elif cmd.startswith('.set'):
                parts=cmd.split(None,2)
                if len(parts)>=3:
                    rn=parts[1].upper(); val=self._ph(parts[2])&0xFF
                    if rn in CPU.REGS:
                        self.undo_stack.append(CPUState(self.cpu))
                        self.cpu.reg[rn]=val; self.cpu.changed_reg.add(rn)
                        self._log(f"⚡ {rn} = 0x{val:02X}", C['amber']); self._update_all()
                    else: self._log(f"Unknown reg: {rn}", C['red'])
            elif cmd.startswith('.fill'):
                parts=cmd.split()
                if len(parts)>=4:
                    s=self._ph(parts[1])&0xFF; e=self._ph(parts[2])&0xFF; v=self._ph(parts[3])&0xFF
                    self.undo_stack.append(CPUState(self.cpu))
                    for a in range(min(s,e),max(s,e)+1): self.cpu.mem[a]=v
                    self._log(f"⚡ Filled 0x{s:02X}-0x{e:02X} with 0x{v:02X}", C['amber'])
                    self._update_all()
            elif cmd=='.clear': self.console.clear()
            elif cmd=='.help':
                self._log("Debug commands:", C['cyan'])
                self._log("  ? A        — show register (hex/dec/bin)", C['dim'])
                self._log("  ? 0x20     — show memory address", C['dim'])
                self._log("  ! MOV A,5  — execute instruction now", C['dim'])
                self._log("  .set A 42  — set register value", C['dim'])
                self._log("  .fill 20 30 FF — fill memory range", C['dim'])
                self._log("  .clear     — clear console", C['dim'])
            else: self._log(f"Unknown: {cmd} — type .help", C['red'])
        except Exception as ex: self._log(f"Error: {ex}", C['red'])

    def _ph(self, s):
        s=s.strip()
        return int(s,16) if s.lower().startswith('0x') else int(s,16) if s else 0

    # ── File I/O ──
    def _save_source(self):
        path,_=QFileDialog.getSaveFileName(self,"Save Source","","ASM (*.asm);;All (*)")
        if path:
            with open(path,'w') as f: f.write(self.editor.toPlainText())
            self._log(f"Saved: {path}", C['cyan'])

    def _open_source(self):
        path,_=QFileDialog.getOpenFileName(self,"Open Source","","ASM (*.asm);;All (*)")
        if path:
            with open(path) as f: self.editor.setPlainText(f.read())
            self._reset(); self._log(f"Loaded: {path}", C['cyan'])

    def _save_mem(self):
        path,_=QFileDialog.getSaveFileName(self,"Export Memory","","HEX (*.hex);;All (*)")
        if path:
            with open(path,'w') as f:
                f.write("; Memory Dump\n")
                for i in range(0,256,16):
                    f.write(f"{i:02X}: {' '.join(f'{self.cpu.mem[j]:02X}' for j in range(i,i+16))}\n")
            self._log(f"Exported: {path}", C['cyan'])

    def _load_mem(self):
        path,_=QFileDialog.getOpenFileName(self,"Import Memory","","HEX (*.hex);;All (*)")
        if path:
            try:
                with open(path) as f:
                    for line in f:
                        line=line.split(';')[0].strip()
                        if ':' in line:
                            parts=line.split(':'); addr=int(parts[0].strip(),16)
                            for j,h in enumerate(parts[1].strip().split()):
                                self.cpu.mem[(addr+j)&0xFF]=int(h,16)&0xFF
                self.mem_view.update_view(self.cpu); self._log(f"Imported: {path}", C['cyan'])
            except Exception as e: self._log(f"✘ Import error: {e}", C['red'])

def main():
    app=QApplication(sys.argv); app.setStyle("Fusion")
    pal=app.palette()
    pal.setColor(pal.ColorRole.Window, QColor(C['bg']))
    pal.setColor(pal.ColorRole.WindowText, QColor(C['text']))
    app.setPalette(pal)
    win=MainWindow(); win.show(); sys.exit(app.exec())

if __name__=="__main__": main()