"""make_image.py — draws the news-image-20261122 front page.

Pure Python standard library only (zlib, struct, os). No network, no
randomness, no wall-clock use: two runs produce byte-identical PNGs.

Layout (1024 x 1024):
  masthead band, then 6 news panels (2 columns x 3 rows), then a footer
  strip with sources. Text is rendered with a hand-built 5x7 bitmap font.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# Palette.
PAPER = (247, 243, 234)      # warm newsprint off-white
INK = (20, 38, 63)           # deep navy (masthead, footer, headlines)
GOLD = (232, 184, 75)        # masthead rule + accents
WHITE = (255, 255, 255)
PANEL_LINE = (216, 210, 196)  # panel border
BODY = (58, 58, 52)          # body copy
MUTED = (110, 108, 96)       # small print
RED = (176, 58, 46)
GREEN = (27, 122, 77)
BLUE = (46, 95, 163)
PURPLE = (142, 68, 173)
BROWN = (183, 121, 31)
TEAL = (23, 114, 69)


# ---------------------------------------------------------------- font ----
# Each glyph is 7 rows of 5 cells; '1' is ink, '0' is blank.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}

# Glyphs N-Z (appended after the A-M block above).
FONT.update({
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
})


# ------------------------------------------------------------- canvas -----
class Canvas:
    """An RGB pixel buffer with simple drawing primitives."""

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.pixels = bytearray(background * (width * height))

    def _offset(self, x, y):
        return (y * self.width + x) * 3

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            off = self._offset(x, y)
            self.pixels[off:off + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            off = self._offset(x0, yy)
            self.pixels[off:off + len(row)] = row

    def rect_outline(self, x, y, w, h, color, thickness=1):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)

    def line(self, x0, y0, x1, y1, color, thickness=1):
        """Bresenham line with a square brush of the given thickness."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thickness // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, thickness, thickness, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, filled=False):
        """Midpoint circle; filled draws horizontal spans."""
        x = 0
        y = r
        d = 1 - r
        while x <= y:
            if filled:
                for xx in range(cx - x, cx + x + 1):
                    self.set_pixel(xx, cy + y, color)
                    self.set_pixel(xx, cy - y, color)
                for xx in range(cx - y, cx + y + 1):
                    self.set_pixel(xx, cy + x, color)
                    self.set_pixel(xx, cy - x, color)
            else:
                for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                               (cx + x, cy - y), (cx - x, cy - y),
                               (cx + y, cy + x), (cx - y, cy + x),
                               (cx + y, cy - x), (cx - y, cy - x)):
                    self.set_pixel(px, py, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def triangle(self, points, color):
        """Filled triangle via a scanline walk over its edges."""
        (x0, y0), (x1, y1), (x2, y2) = points
        ymin = max(0, min(y0, y1, y2))
        ymax = min(self.height - 1, max(y0, y1, y2))
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by) or (yy == ymax and yy == max(ay, by)):
                    t = (yy - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            if len(xs) >= 2:
                lo = max(0, int(min(xs)))
                hi = min(self.width - 1, int(max(xs)))
                for xx in range(lo, hi + 1):
                    self.set_pixel(xx, yy, color)


# -------------------------------------------------------------- text ------
def text_width(text, scale):
    """Pixel width of text at the given scale (6 px advance per glyph)."""
    return len(text) * 6 * scale


def draw_text(canvas, x, y, text, scale, color):
    """Draw uppercase text; unknown glyphs render as blank."""
    cursor = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    canvas.fill_rect(cursor + col * scale, y + row * scale,
                                     scale, scale, color)
        cursor += 6 * scale
    return cursor


def draw_text_centered(canvas, cx, y, text, scale, color):
    x = cx - text_width(text, scale) // 2
    draw_text(canvas, x, y, text, scale, color)
    return x


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width px."""
    words = text.split(' ')
    lines = []
    current = ''
    for word in words:
        trial = word if not current else current + ' ' + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# -------------------------------------------------------------- icons -----
# Small pictograms drawn in the top-right corner of each panel (48x48 box).
def icon_globe(canvas, x, y, color):
    canvas.circle(x + 24, y + 24, 20, color)
    canvas.line(x + 4, y + 24, x + 44, y + 24, color, 2)
    canvas.line(x + 10, y + 12, x + 38, y + 12, color, 2)
    canvas.line(x + 10, y + 36, x + 38, y + 36, color, 2)
    canvas.line(x + 24, y + 4, x + 24, y + 44, color, 2)
    canvas.line(x + 12, y + 12, x + 36, y + 36, RED, 3)
    canvas.line(x + 36, y + 12, x + 12, y + 36, RED, 3)


def icon_handcuffs(canvas, x, y, color):
    canvas.circle(x + 13, y + 24, 10, color)
    canvas.circle(x + 35, y + 24, 10, color)
    canvas.line(x + 20, y + 16, x + 28, y + 16, color, 3)
    canvas.fill_rect(x + 11, y + 22, 4, 4, PAPER)
    canvas.fill_rect(x + 33, y + 22, 4, 4, PAPER)


def icon_tanker(canvas, x, y, color):
    canvas.fill_rect(x + 6, y + 26, 36, 10, color)
    canvas.triangle([(x + 42, y + 26), (x + 42, y + 36), (x + 30, y + 36)], color)
    canvas.fill_rect(x + 10, y + 16, 7, 10, color)
    canvas.fill_rect(x + 19, y + 16, 7, 10, color)
    canvas.fill_rect(x + 28, y + 16, 7, 10, color)
    canvas.triangle([(x + 24, y + 2), (x + 18, y + 14), (x + 30, y + 14)], (226, 120, 40))
    canvas.line(x + 4, y + 42, x + 44, y + 42, color, 2)


def icon_blast(canvas, x, y, color):
    cx, cy = x + 24, y + 20
    for dx, dy in ((-20, 0), (20, 0), (0, -14), (0, 14),
                   (-14, -10), (14, -10), (-14, 10), (14, 10)):
        canvas.line(cx, cy, cx + dx, cy + dy, color, 2)
    canvas.circle(cx, cy, 5, RED, filled=True)
    canvas.fill_rect(x + 8, y + 36, 10, 10, color)
    canvas.fill_rect(x + 22, y + 38, 8, 8, color)
    canvas.fill_rect(x + 34, y + 36, 10, 10, color)


def icon_chart(canvas, x, y, color):
    canvas.line(x + 6, y + 42, x + 44, y + 42, color, 2)
    canvas.line(x + 6, y + 42, x + 6, y + 6, color, 2)
    canvas.line(x + 8, y + 12, x + 18, y + 20, RED, 3)
    canvas.line(x + 18, y + 20, x + 28, y + 18, RED, 3)
    canvas.line(x + 28, y + 18, x + 40, y + 34, RED, 3)
    canvas.triangle([(x + 40, y + 34), (x + 33, y + 32), (x + 38, y + 26)], RED)


def icon_bottle(canvas, x, y, color):
    canvas.fill_rect(x + 19, y + 6, 10, 6, color)
    canvas.fill_rect(x + 16, y + 12, 16, 28, color)
    canvas.triangle([(x + 16, y + 40), (x + 32, y + 40), (x + 24, y + 30)], color)
    canvas.circle(x + 24, y + 24, 20, RED)
    canvas.line(x + 10, y + 10, x + 38, y + 38, RED, 3)


ICONS = {
    'globe': icon_globe,
    'handcuffs': icon_handcuffs,
    'tanker': icon_tanker,
    'blast': icon_blast,
    'chart': icon_chart,
    'bottle': icon_bottle,
}


# ------------------------------------------------------------- content ----
# Six verified stories of Sunday 22 November 2026 (re-checked 23 Nov 2026
# against Reuters / AP / AFP / NPR reporting of the day).
PANELS = [
    {
        'tag': 'CLIMATE', 'accent': GREEN, 'icon': 'globe',
        'headline': 'COP31 ENDS WITH NO DEAL',
        'body': 'After record overtime in Antalya, the EU and island states '
                'rejected a pact that left out fossil fuels. The longest '
                'climate summit ever ends with no cover deal.',
        'stat': '44 HOURS OF OVERTIME',
    },
    {
        'tag': 'MEXICO', 'accent': RED, 'icon': 'handcuffs',
        'headline': 'EL CHAPO ISIDRO CAPTURED',
        'body': 'Mexican forces seized cartel boss Fausto Isidro Meza Flores '
                'in Sinaloa. The raid set off cartel violence that left 11 '
                'people dead.',
        'stat': '11 KILLED IN SINALOA',
    },
    {
        'tag': 'GULF', 'accent': PURPLE, 'icon': 'tanker',
        'headline': 'IRAN HITS BAHRAIN AND HORMUZ',
        'body': 'Tehran struck a civilian plant on Sitra Island and two '
                'tankers in the Strait of Hormuz as the US blockade of Iran '
                'passed 130 days.',
        'stat': '2 TANKERS HIT',
    },
    {
        'tag': 'UKRAINE', 'accent': BLUE, 'icon': 'blast',
        'headline': 'MISSILES HIT KRYVYI RIH',
        'body': "A Russian strike on Zelenskyy's hometown killed a 7-year-old "
                'boy and a 20-year-old paramedic, and wounded 60 people, six '
                'of them children.',
        'stat': '2 KILLED, 60 WOUNDED',
    },
    {
        'tag': 'MARKETS', 'accent': BROWN, 'icon': 'chart',
        'headline': 'S&P 500 SLIPS INTO CORRECTION',
        'body': 'Wall Street fell 11.6% from its October high as the AI trade '
                'unwound. The Nasdaq erased its gains for the year; Nvidia '
                'slid again.',
        'stat': '-11.6% FROM OCT HIGH',
    },
    {
        'tag': 'EUROPE', 'accent': TEAL, 'icon': 'bottle',
        'headline': 'EU PLASTIC EXPORT BAN BEGINS',
        'body': 'From 21 November the EU bans plastic waste exports to '
                'non-OECD states, rerouting flows from Malaysia, Indonesia '
                'and Vietnam until at least 2029.',
        'stat': 'BAN UNTIL MAY 2029',
    },
]


# ------------------------------------------------------------- layout -----
def draw_panel(canvas, px, py, pw, ph, panel):
    accent = panel['accent']
    canvas.fill_rect(px, py, pw, ph, WHITE)
    canvas.rect_outline(px, py, pw, ph, PANEL_LINE, 2)
    canvas.fill_rect(px, py, pw, 8, accent)
    # Tag chip.
    tag = panel['tag']
    chip_w = text_width(tag, 2) + 16
    canvas.fill_rect(px + 18, py + 22, chip_w, 24, accent)
    draw_text(canvas, px + 26, py + 27, tag, 2, WHITE)
    # Icon, top right.
    ICONS[panel['icon']](canvas, px + pw - 66, py + 18, accent)
    # Headline, up to two lines.
    inner_w = pw - 36
    head_lines = wrap_text(panel['headline'], inner_w, 3)[:2]
    hy = py + 58
    for line in head_lines:
        draw_text(canvas, px + 18, hy, line, 3, INK)
        hy += 26
    # Body copy.
    by = hy + 10
    for line in wrap_text(panel['body'], inner_w, 2):
        draw_text(canvas, px + 18, by, line, 2, BODY)
        by += 18
    # Stat line pinned near the bottom.
    draw_text(canvas, px + 18, py + ph - 28, panel['stat'], 2, accent)


def render(path):
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    # Masthead.
    canvas.fill_rect(0, 0, WIDTH, 132, INK)
    draw_text_centered(canvas, WIDTH // 2, 26, 'THE WORLD IN ONE DAY', 5, WHITE)
    draw_text_centered(canvas, WIDTH // 2, 82,
                       'SUNDAY, 22 NOVEMBER 2026  |  SIX STORIES THAT DEFINED THE DAY',
                       2, GOLD)
    canvas.fill_rect(0, 128, WIDTH, 4, GOLD)
    # Panels: 2 columns x 3 rows.
    margin = 16
    gap = 12
    pw = (WIDTH - 2 * margin - gap) // 2
    ph = 260
    top = 148
    for i, panel in enumerate(PANELS):
        col = i % 2
        row = i // 2
        px = margin + col * (pw + gap)
        py = top + row * (ph + gap)
        draw_panel(canvas, px, py, pw, ph, panel)
    # Footer strip.
    canvas.fill_rect(0, 968, WIDTH, 56, INK)
    draw_text_centered(canvas, WIDTH // 2, 984,
                       'SOURCES: REUTERS, AP, AFP, NPR, EUROPEAN COMMISSION',
                       2, WHITE)
    draw_text_centered(canvas, WIDTH // 2, 1004,
                       'BUILT BY AN AI AGENT FOR MAKE.FUN', 1, GOLD)
    write_png(canvas, path)


# --------------------------------------------------------------- png ------
def _chunk(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    out += struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    width = canvas.width
    for y in range(canvas.height):
        raw.append(0)  # filter: none
        start = y * width * 3
        raw += canvas.pixels[start:start + width * 3]
    ihdr = struct.pack('>IIBBBBB', width, canvas.height, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += _chunk(b'IHDR', ihdr)
    png += _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += _chunk(b'IEND', b'')
    with open(path, 'wb') as handle:
        handle.write(png)


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR')
    if not out_dir:
        out_dir = '/output' if os.path.isdir('/output') else 'out'
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'entry.png')
    render(path)
    print('wrote ' + path)


if __name__ == '__main__':
    main()
