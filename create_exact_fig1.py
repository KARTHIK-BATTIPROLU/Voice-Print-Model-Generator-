import os
import sys
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def draw_rounded_rect(draw, xy, radius, fill, outline, width=2):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def draw_arrow_horizontal(draw, x0, y, x1, color="#2D3748", width=2, arrow_len=9, arrow_w=5):
    draw.line([(x0, y), (x1, y)], fill=color, width=width)
    draw.polygon([(x1, y), (x1 - arrow_len, y - arrow_w), (x1 - arrow_len, y + arrow_w)], fill=color)

def draw_arrow_vertical_down(draw, x, y0, y1, color="#2D3748", width=2, arrow_len=9, arrow_w=5):
    draw.line([(x, y0), (x, y1)], fill=color, width=width)
    draw.polygon([(x, y1), (x - arrow_w, y1 - arrow_len), (x + arrow_w, y1 - arrow_len)], fill=color)

def create_fig1():
    W, H = 1152, 603
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 20)
        font_body = ImageFont.truetype("arial.ttf", 14)
    except:
        try:
            font_title = ImageFont.truetype("calibrib.ttf", 20)
            font_body = ImageFont.truetype("calibri.ttf", 14)
        except:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()

    # Colors
    c_r1_fill = (232, 238, 247, 255) # #E8EEF7 (light blue)
    c_r2_fill = (226, 237, 222, 255) # #E2EDDE (light green)
    c_r3_fill = (255, 243, 224, 255) # #FFF3E0 (soft peach/amber)
    c_outline = (45, 55, 72, 255)

    # 3 columns for Row 1 and Row 2
    col_bounds = [
        (31, 355),
        (413, 738),
        (796, 1120)
    ]
    r1_y0, r1_y1 = 45, 175
    r2_y0, r2_y1 = 245, 375
    r3_y0, r3_y1 = 445, 565

    # Content Row 1
    r1 = [
        {"title": "1. Input", "lines": ["Speech Audio Utterance", "16 kHz Mono PCM Signal"]},
        {"title": "2. Preprocessing", "lines": ["25ms Hamming / 10ms Hop", "80 Log-Mel Spectrogram + CMVN"]},
        {"title": "3. Augmentation", "lines": ["SpecAugment (Time/Freq)", "MUSAN Noise + RIR Reverb"]}
    ]

    for idx, (x0, x1) in enumerate(col_bounds):
        draw_rounded_rect(draw, (x0, r1_y0, x1, r1_y1), radius=16, fill=c_r1_fill, outline=c_outline, width=2)
        b = r1[idx]
        t_box = draw.textbbox((0, 0), b["title"], font=font_title)
        draw.text((x0 + (x1 - x0 - (t_box[2]-t_box[0]))//2, r1_y0 + 26), b["title"], fill=(15, 23, 42), font=font_title)
        cur_y = r1_y0 + 64
        for l in b["lines"]:
            l_box = draw.textbbox((0, 0), l, font=font_body)
            draw.text((x0 + (x1 - x0 - (l_box[2]-l_box[0]))//2, cur_y), l, fill=(51, 65, 85), font=font_body)
            cur_y += 24

    # Row 1 horizontal arrows
    y_r1_mid = (r1_y0 + r1_y1) // 2
    draw_arrow_horizontal(draw, col_bounds[0][1], y_r1_mid, col_bounds[1][0], color=c_outline)
    draw_arrow_horizontal(draw, col_bounds[1][1], y_r1_mid, col_bounds[2][0], color=c_outline)

    # Content Row 2
    r2 = [
        {"title": "4. ECAPA-TDNN", "lines": ["1D Dilated Convolutions", "SE-Res2Blocks (Channels=512)"]},
        {"title": "5. Ch-ASP Pooling", "lines": ["Channel-Dependent Attention", "Mean + Std (3072 values)"]},
        {"title": "6. Output", "lines": ["192-d Unit Embedding (S¹⁹¹)", "Cosine Scoring vs Tau (0.70)"]}
    ]

    for idx, (x0, x1) in enumerate(col_bounds):
        draw_rounded_rect(draw, (x0, r2_y0, x1, r2_y1), radius=16, fill=c_r2_fill, outline=c_outline, width=2)
        b = r2[idx]
        t_box = draw.textbbox((0, 0), b["title"], font=font_title)
        draw.text((x0 + (x1 - x0 - (t_box[2]-t_box[0]))//2, r2_y0 + 26), b["title"], fill=(15, 23, 42), font=font_title)
        cur_y = r2_y0 + 64
        for l in b["lines"]:
            l_box = draw.textbbox((0, 0), l, font=font_body)
            draw.text((x0 + (x1 - x0 - (l_box[2]-l_box[0]))//2, cur_y), l, fill=(51, 65, 85), font=font_body)
            cur_y += 24

    # Row 2 horizontal arrows
    y_r2_mid = (r2_y0 + r2_y1) // 2
    draw_arrow_horizontal(draw, col_bounds[0][1], y_r2_mid, col_bounds[1][0], color=c_outline)
    draw_arrow_horizontal(draw, col_bounds[1][1], y_r2_mid, col_bounds[2][0], color=c_outline)

    # Orthogonal stepped connector from Box 3 (Col 3, Row 1) to Box 4 (Col 1, Row 2)
    x_c3 = (col_bounds[2][0] + col_bounds[2][1]) // 2 # 958
    x_c1 = (col_bounds[0][0] + col_bounds[0][1]) // 2 # 193
    y_mid_alley = (r1_y1 + r2_y0) // 2 # 210

    draw.line([(x_c3, r1_y1), (x_c3, y_mid_alley)], fill=c_outline, width=2)
    draw.line([(x_c3, y_mid_alley), (x_c1, y_mid_alley)], fill=c_outline, width=2)
    draw_arrow_vertical_down(draw, x_c1, y_mid_alley, r2_y0, color=c_outline)

    # Row 3 (Explanation box: Attentive Saliency)
    # Span Col 1 and Col 2
    draw_rounded_rect(draw, (31, r3_y0, 738, r3_y1), radius=16, fill=c_r3_fill, outline=c_outline, width=2)
    t_box = draw.textbbox((0, 0), "Attentive Saliency (Explanation)", font=font_title)
    draw.text((31 + (707 - (t_box[2]-t_box[0]))//2, r3_y0 + 24), "Attentive Saliency (Explanation)", fill=(15, 23, 42), font=font_title)
    l1 = "Frame-level temporal attention weights from Ch-ASP layer over vocal formants"
    l1_box = draw.textbbox((0, 0), l1, font=font_body)
    draw.text((31 + (707 - (l1_box[2]-l1_box[0]))//2, r3_y0 + 64), l1, fill=(51, 65, 85), font=font_body)

    # Arrow from Box 4 (ECAPA-TDNN) to Attentive Saliency Box
    draw_arrow_vertical_down(draw, x_c1, r2_y1, r3_y0, color=c_outline)

    out_p = "report_images/fig1_workflow.png"
    im.save(out_p, "PNG")
    print(f"Created exact pristine Figure 1: {out_p} ({os.path.getsize(out_p)} bytes)")

if __name__ == "__main__":
    create_fig1()
