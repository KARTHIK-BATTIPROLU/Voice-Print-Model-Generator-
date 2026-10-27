import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def draw_rounded_rect(draw, xy, radius, fill, outline, width=2):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def draw_arrow_horizontal(draw, x0, y, x1, color="#2D3748", width=2, arrow_len=8, arrow_w=5):
    # line
    draw.line([(x0, y), (x1, y)], fill=color, width=width)
    # arrowhead pointing right
    draw.polygon([(x1, y), (x1 - arrow_len, y - arrow_w), (x1 - arrow_len, y + arrow_w)], fill=color)

def draw_arrow_vertical_down(draw, x, y0, y1, color="#2D3748", width=2, arrow_len=8, arrow_w=5):
    # line
    draw.line([(x, y0), (x, y1)], fill=color, width=width)
    # arrowhead pointing down
    draw.polygon([(x, y1), (x - arrow_w, y1 - arrow_len), (x + arrow_w, y1 - arrow_len)], fill=color)

def create_fig2():
    # Dimensions: 1152 x 552, matching reference image2.png
    W, H = 1152, 552
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)

    # Box coordinates
    # Row 1: y from 54 to 212
    # Row 2: y from 296 to 454
    # Columns:
    # Col 1: 22 to 278
    # Col 2: 303 to 561
    # Col 3: 585 to 843
    # Col 4: 868 to 1126
    
    col_bounds = [
        (22, 278),
        (303, 561),
        (585, 843),
        (868, 1126)
    ]
    
    r1_y0, r1_y1 = 54, 212
    r2_y0, r2_y1 = 296, 454
    
    # Colors from reference image2.png:
    # Row 1 fill: [232, 238, 247] (#E8EEF7)
    # Row 2 fill: [226, 237, 222] (#E2EDDE)
    # Outline: #2D3748
    # Text: #0F172A
    
    c_r1_fill = (232, 238, 247, 255)
    c_r2_fill = (226, 237, 222, 255)
    c_outline = (45, 55, 72, 255)
    
    # Fonts
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 20)
        font_body = ImageFont.truetype("arial.ttf", 14)
        font_body_bold = ImageFont.truetype("arialbd.ttf", 14)
    except:
        try:
            font_title = ImageFont.truetype("calibrib.ttf", 20)
            font_body = ImageFont.truetype("calibri.ttf", 14)
            font_body_bold = ImageFont.truetype("calibrib.ttf", 14)
        except:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
            font_body_bold = ImageFont.load_default()

    # Content for Row 1
    r1_boxes = [
        {
            "title": "Input",
            "lines": ["16 kHz Mono Audio", "25ms Hamming / 10ms Hop", "80 Log-Mel Spectrogram"]
        },
        {
            "title": "Block 1",
            "lines": ["Conv1D (k=5, d=1)", "BatchNorm · LeakyReLU", "T × 512"]
        },
        {
            "title": "Block 2",
            "lines": ["SE-Res2Block (d=2)", "Conv 512 · SE (r=8)", "T × 512"]
        },
        {
            "title": "Block 3",
            "lines": ["SE-Res2Block (d=3)", "Conv 512 · SE (r=8)", "T × 512"]
        }
    ]

    # Content for Row 2
    r2_boxes = [
        {
            "title": "Block 4",
            "lines": ["SE-Res2Block (d=4)", "Conv 512 · SE (r=8)", "T × 512"]
        },
        {
            "title": "MFA Stage",
            "lines": ["Multi-layer Aggregation", "Concat (B2 + B3 + B4)", "T × 1536"]
        },
        {
            "title": "Ch-ASP Pooling",
            "lines": ["Channel-Attentive Stats", "Weighted Mean + Std", "3072 values"]
        },
        {
            "title": "Output",
            "lines": ["Dense 192 + L2 Norm", "Unit Hypersphere S¹⁹¹", "192-d Voiceprint"]
        }
    ]

    # Draw Row 1 boxes
    for idx, (x0, x1) in enumerate(col_bounds):
        draw_rounded_rect(draw, (x0, r1_y0, x1, r1_y1), radius=16, fill=c_r1_fill, outline=c_outline, width=2)
        b_info = r1_boxes[idx]
        
        # Draw title centered
        t_box = draw.textbbox((0, 0), b_info["title"], font=font_title)
        t_w = t_box[2] - t_box[0]
        draw.text((x0 + (x1 - x0 - t_w)//2, r1_y0 + 26), b_info["title"], fill=(15, 23, 42), font=font_title)
        
        # Draw body lines
        cur_y = r1_y0 + 64
        for l in b_info["lines"]:
            l_box = draw.textbbox((0, 0), l, font=font_body)
            l_w = l_box[2] - l_box[0]
            draw.text((x0 + (x1 - x0 - l_w)//2, cur_y), l, fill=(51, 65, 85), font=font_body)
            cur_y += 24

    # Draw Row 1 horizontal arrows
    y_arrow_r1 = (r1_y0 + r1_y1) // 2
    for i in range(3):
        x_from = col_bounds[i][1]
        x_to = col_bounds[i+1][0]
        draw_arrow_horizontal(draw, x_from, y_arrow_r1, x_to, color=c_outline, width=2, arrow_len=9, arrow_w=5)

    # Draw Row 2 boxes
    for idx, (x0, x1) in enumerate(col_bounds):
        draw_rounded_rect(draw, (x0, r2_y0, x1, r2_y1), radius=16, fill=c_r2_fill, outline=c_outline, width=2)
        b_info = r2_boxes[idx]
        
        # Draw title centered
        t_box = draw.textbbox((0, 0), b_info["title"], font=font_title)
        t_w = t_box[2] - t_box[0]
        draw.text((x0 + (x1 - x0 - t_w)//2, r2_y0 + 26), b_info["title"], fill=(15, 23, 42), font=font_title)
        
        # Draw body lines
        cur_y = r2_y0 + 64
        for l in b_info["lines"]:
            l_box = draw.textbbox((0, 0), l, font=font_body)
            l_w = l_box[2] - l_box[0]
            draw.text((x0 + (x1 - x0 - l_w)//2, cur_y), l, fill=(51, 65, 85), font=font_body)
            cur_y += 24

    # Draw Row 2 horizontal arrows
    y_arrow_r2 = (r2_y0 + r2_y1) // 2
    for i in range(3):
        x_from = col_bounds[i][1]
        x_to = col_bounds[i+1][0]
        draw_arrow_horizontal(draw, x_from, y_arrow_r2, x_to, color=c_outline, width=2, arrow_len=9, arrow_w=5)

    # -------------------------------------------------------------
    # DRAW STEPPED ORTHOGONAL CONNECTOR FROM BLOCK 3 TO BLOCK 4
    # Exactly like reference image2.png!
    # Starts at bottom center of Col 4 in Row 1: x_c4 = (868 + 1126)//2 = 997, y = r1_y1 (212)
    # Drops to middle alley: y_mid = 254
    # Runs horizontally left from 997 to x_c1 = (22 + 278)//2 = 150
    # Drops from y_mid (254) to r2_y0 (296) with arrow pointing down
    # -------------------------------------------------------------
    x_c4 = (col_bounds[3][0] + col_bounds[3][1]) // 2 # 997
    x_c1 = (col_bounds[0][0] + col_bounds[0][1]) // 2 # 150
    y_mid = (r1_y1 + r2_y0) // 2 # 254
    
    # Vertical line 1 from bottom of Block 3 down to y_mid
    draw.line([(x_c4, r1_y1), (x_c4, y_mid)], fill=c_outline, width=2)
    
    # Horizontal line from x_c4 to x_c1
    draw.line([(x_c4, y_mid), (x_c1, y_mid)], fill=c_outline, width=2)
    
    # Vertical line 2 down to top of Block 4 with arrowhead
    draw_arrow_vertical_down(draw, x_c1, y_mid, r2_y0, color=c_outline, width=2, arrow_len=10, arrow_w=5)

    out_p = "report_images/fig2_architecture.png"
    im.save(out_p, "PNG")
    print(f"Created exact pristine Figure 2: {out_p} ({os.path.getsize(out_p)} bytes)")

if __name__ == "__main__":
    create_fig2()
