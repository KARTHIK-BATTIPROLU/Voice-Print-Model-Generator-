"""
Script to generate the Advanced Deep Learning Lab Case Study presentation:
VoicePrint: Case Study in Deep Neural Speaker Verification
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return RGBColor(*(int(hex_str[i:i+2], 16) for i in (0, 2, 4)))

# Theme Palette (Deep Navy / Cyber Academic Lab)
BG_COLOR = hex_to_rgb('0B1120')       # Deepest Navy/Midnight
CARD_BG = hex_to_rgb('162036')        # Dark Slate Card
CARD_BORDER = hex_to_rgb('2D3E63')    # Card subtle border
TEXT_WHITE = hex_to_rgb('FFFFFF')     # Crisp White
TEXT_HEAD = hex_to_rgb('F1F5F9')      # Slate 100
TEXT_MUTED = hex_to_rgb('94A3B8')     # Slate 400
TEXT_SECONDARY = hex_to_rgb('CBD5E1') # Slate 300
ACCENT_BLUE = hex_to_rgb('38BDF8')    # Cyan / Sky Blue
ACCENT_INDIGO = hex_to_rgb('818CF8')  # Indigo
ACCENT_TEAL = hex_to_rgb('2DD4BF')    # Teal / Mint
ACCENT_EMERALD = hex_to_rgb('34D399') # Emerald
ACCENT_AMBER = hex_to_rgb('FBBF24')   # Amber
ACCENT_ROSE = hex_to_rgb('F43F5E')    # Rose Red

def set_slide_background(slide, color):
    # Add a full-bleed rectangle as background
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background() # No border
    return bg

def add_header(slide, tag_text, title_text, slide_num, total_slides=14):
    # Top Tag
    tb_tag = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(9.0), Inches(0.35))
    tf_tag = tb_tag.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = tag_text.upper()
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = ACCENT_BLUE

    # Title
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.5), Inches(0.65))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.size = Pt(25)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE

    # Slide Number & Footer Tracker
    tb_num = slide.shapes.add_textbox(Inches(10.5), Inches(0.4), Inches(2.0), Inches(0.35))
    tf_num = tb_num.text_frame
    tf_num.margin_left = tf_num.margin_top = tf_num.margin_right = tf_num.margin_bottom = 0
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.text = f"{slide_num:02d} / {total_slides:02d}"
    p_num.font.size = Pt(12)
    p_num.font.bold = True
    p_num.font.color.rgb = TEXT_MUTED

    # Bottom footer subtle line & note
    tb_ft = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.3))
    tf_ft = tb_ft.text_frame
    tf_ft.margin_left = tf_ft.margin_top = tf_ft.margin_right = tf_ft.margin_bottom = 0
    p_ft = tf_ft.paragraphs[0]
    p_ft.text = "VoicePrint · Advanced Artificial Neural Networks Lab Case Study | ECAPA-TDNN Speaker Verification"
    p_ft.font.size = Pt(9.5)
    p_ft.font.color.rgb = TEXT_MUTED

def add_card(slide, left, top, width, height, border_color=CARD_BORDER, bg_color=CARD_BG):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.2)
    return card

def build_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide layout

    total_slides = 14

    # ==========================================
    # SLIDE 1: Title Slide
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, BG_COLOR)

    # Accent decorative banner card
    card_title = add_card(s1, Inches(1.2), Inches(1.0), Inches(10.933), Inches(5.5), border_color=hex_to_rgb('3B82F6'))
    
    tb1 = s1.shapes.add_textbox(Inches(1.8), Inches(1.4), Inches(9.733), Inches(4.7))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "ADVANCED ARTIFICIAL NEURAL NETWORKS (AANN) · LAB CASE STUDY"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_BLUE

    p1 = tf1.add_paragraph()
    p1.text = "VoicePrint"
    p1.font.size = Pt(50)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_before = Pt(8)

    p2 = tf1.add_paragraph()
    p2.text = "Case Study in Deep Neural Speaker Verification & Hyperspherical Latent Embeddings"
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = ACCENT_TEAL
    p2.space_before = Pt(4)

    p3 = tf1.add_paragraph()
    p3.text = "An in-depth investigation into Time-Delay Neural Architectures, Channel Attention (Squeeze-and-Excitation), Attentive Statistics Pooling, and Angular Margin Metric Learning for offline biometrics."
    p3.font.size = Pt(14)
    p3.font.color.rgb = TEXT_SECONDARY
    p3.space_before = Pt(14)

    p4 = tf1.add_paragraph()
    p4.text = "Presented by: BATTIPROLU KARTHIK  |  Model: SpeechBrain ECAPA-TDNN (192-dim, AAM-Softmax)  |  Offline Inference"
    p4.font.size = Pt(13)
    p4.font.bold = True
    p4.font.color.rgb = ACCENT_AMBER
    p4.space_before = Pt(24)

    # ==========================================
    # SLIDE 2: Task Formulation & Problem Space
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, BG_COLOR)
    add_header(s2, "Biometric Formulation & Task Taxonomy", "Speaker Recognition: Identification vs. Verification Paradigms", 2, total_slides)

    # Card 1: Identification vs Verification
    add_card(s2, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tb2_left = s2.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(4.8))
    tf2_l = tb2_left.text_frame
    tf2_l.word_wrap = True
    
    p = tf2_l.paragraphs[0]
    p.text = "1. Closed-Set Identification vs. Open-Set Verification"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    points_l = [
        ("Closed-Set Identification (1:N):", " Given utterance X, select speaker s* in known gallery S = {s1..sN}. Standard multiclass classification problem."),
        ("Open-Set Verification (1:1):", " Core biometric problem. Given claimed identity ID and test speech X_test, evaluate binary hypothesis testing:\n  • H0: Speaker is genuine claim (X_test matches enrolled profile c_ID)\n  • H1: Speaker is an impostor (X_test does not match c_ID)"),
        ("The Open-Set Challenge:", " Real-world test speakers were NEVER seen during neural network training (S_test ∩ S_train = ∅). The network cannot output fixed class probabilities; it must output a generalized speaker descriptor vector.")
    ]
    for h, b in points_l:
        p = tf2_l.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(10)

    # Card 2: Acoustic Variance & Mathematical Objective
    add_card(s2, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    tb2_right = s2.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.333), Inches(4.8))
    tf2_r = tb2_right.text_frame
    tf2_r.word_wrap = True

    p = tf2_r.paragraphs[0]
    p.text = "2. Acoustic Variabilities & The Metric Learning Goal"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    points_r = [
        ("Intra-Speaker Variability:", " High variance within the same person due to phonemic context, emotional state, respiratory illness, vocal fatigue, microphone distance, and ambient room reverberation."),
        ("Inter-Speaker Variability:", " Two distinct individuals may share similar pitch, formant ranges, or accents. The deep model must isolate subtle anatomical vocal tract signatures."),
        ("Mathematical Objective:", " Learn a non-linear mapping f_θ: X ↦ z ∈ R^d such that:\n  • Intra-speaker geodesic distance: d(z_i^(a), z_i^(b)) → 0\n  • Inter-speaker geodesic distance: d(z_i, z_j) ≥ m (large margin)"),
        ("Zero-Cloud Offline Imperative:", " Voice contains personal biometric markers. Local CPU neural inference guarantees total user privacy and zero data leakage.")
    ]
    for h, b in points_r:
        p = tf2_r.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(10)

    # ==========================================
    # SLIDE 3: Acoustic Front-End Feature Extraction
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, BG_COLOR)
    add_header(s3, "Acoustic Signal Processing", "Front-End Feature Extraction: Raw Waveform to Log-Mel Spectrogram", 3, total_slides)

    # 3 Horizontal Cards for pipeline
    col_w = Inches(3.7)
    gap = Inches(0.3)
    y_top = Inches(1.5)
    h_card = Inches(5.2)

    # Col 1: STFT & Framing
    add_card(s3, Inches(0.8), y_top, col_w, h_card)
    tb_s3_1 = s3.shapes.add_textbox(Inches(1.0), y_top + Inches(0.2), col_w - Inches(0.4), h_card - Inches(0.4))
    tf3_1 = tb_s3_1.text_frame
    tf3_1.word_wrap = True
    p = tf3_1.paragraphs[0]
    p.text = "1. Framing & STFT"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    pts_c1 = [
        "Sampling Rate: 16,000 Hz (16 kHz mono PCM audio)",
        "Frame Length: N = 400 samples (25 ms analysis window)",
        "Frame Shift: H = 160 samples (10 ms hop, 60% overlap)",
        "Hamming Windowing: w(n) = 0.54 - 0.46·cos(2πn/(N-1)) applied to suppress spectral edge discontinuities.",
        "Short-Time Fourier Transform:",
        "X(m, k) = Σ x(mH + n) w(n) e^(-j 2πkn/N)",
        "Captures local quasi-stationary acoustic frequency content across time."
    ]
    for item in pts_c1:
        p = tf3_1.add_paragraph()
        p.text = "• " + item if not item.startswith("X(m") else "   " + item
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(6)

    # Col 2: Mel-Filterbank Integration
    add_card(s3, Inches(0.8) + col_w + gap, y_top, col_w, h_card)
    tb_s3_2 = s3.shapes.add_textbox(Inches(1.0) + col_w + gap, y_top + Inches(0.2), col_w - Inches(0.4), h_card - Inches(0.4))
    tf3_2 = tb_s3_2.text_frame
    tf3_2.word_wrap = True
    p = tf3_2.paragraphs[0]
    p.text = "2. 80-Channel Mel Scale"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    pts_c2 = [
        "Perceptual Non-Linearity: Human auditory cochlea has higher frequency resolution at low frequencies (< 1 kHz).",
        "Mel Frequency Mapping:",
        "m = 2595 · log10(1 + f / 700)",
        "80 Triangular Bandpass Filters:",
        "Spans 0 Hz to Nyquist frequency (8000 Hz) to model vocal tract formants (F1, F2, F3).",
        "Logarithmic Compression:",
        "S_mel(t, f) = log(1 + |X_mel(t, f)|)",
        "Compresses high dynamic range, matching decibel loudness perception."
    ]
    for item in pts_c2:
        p = tf3_2.add_paragraph()
        p.text = "• " + item if not item.startswith("m =") and not item.startswith("S_mel") else "   " + item
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(6)

    # Col 3: Cepstral Normalization (CMVN)
    add_card(s3, Inches(0.8) + (col_w + gap)*2, y_top, col_w, h_card)
    tb_s3_3 = s3.shapes.add_textbox(Inches(1.0) + (col_w + gap)*2, y_top + Inches(0.2), col_w - Inches(0.4), h_card - Inches(0.4))
    tf3_3 = tb_s3_3.text_frame
    tf3_3.word_wrap = True
    p = tf3_3.paragraphs[0]
    p.text = "3. Temporal CMVN"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    pts_c3 = [
        "Cepstral Mean & Variance Normalization:",
        "Computes mean μ_f and variance σ_f^2 per filter channel f along time dimension T.",
        "Ŝ(t, f) = [S(t, f) - μ_f] / σ_f",
        "Channel Invariance:",
        "Eliminates stationary additive background noise and linear microphone frequency response distortions.",
        "Resulting Tensor Input:",
        "Shape: (Batch, T_frames, 80)",
        "Standardized neural front-end fed directly into frame-level 1D dilated convolutions."
    ]
    for item in pts_c3:
        p = tf3_3.add_paragraph()
        p.text = "• " + item if not item.startswith("Ŝ(t") and not item.startswith("Shape:") else "   " + item
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(6)

    # ==========================================
    # SLIDE 4: Existing Solutions vs ECAPA-TDNN (Comparison)
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, BG_COLOR)
    add_header(s4, "Evolution of Speaker Recognition", "Existing Solutions vs. Proposed ECAPA-TDNN Deep Architecture", 4, total_slides)

    # Table comparing paradigms
    t_left = Inches(0.8)
    t_top = Inches(1.5)
    t_w = Inches(11.733)
    t_h = Inches(3.2)

    rows, cols = 5, 5
    table_shape = s4.shapes.add_table(rows, cols, t_left, t_top, t_w, t_h)
    tbl = table_shape.table

    tbl.columns[0].width = Inches(2.3)
    tbl.columns[1].width = Inches(2.6)
    tbl.columns[2].width = Inches(2.2)
    tbl.columns[3].width = Inches(1.8)
    tbl.columns[4].width = Inches(2.833)

    headers = ["Architecture Era", "Representation & Method", "Temporal Modeling", "VoxCeleb1 EER", "Primary Architectural Bottleneck"]
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = hex_to_rgb('1E293B')
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_BLUE

    row_data = [
        ("GMM-UBM (Reynolds 2000)", "Gaussian Mixture Model (512-2048 comps) with MAP adaptation", "Orderless statistical frame aggregation", "~15.20%", "Shallow density fit; vulnerable to acoustic channel mismatch & noise"),
        ("i-Vector + PLDA (Dehak 2011)", "Low-rank factor analysis: M = m + Tw (w in R^400) + PLDA", "Global utterance statistics via Baum-Welch", "~5.39%", "Linear subspace assumption fails on non-linear acoustic manifolds"),
        ("TDNN x-vector (Snyder 2018)", "Time-Delay Neural Network (1D Conv) + Mean/Std Pooling", "Uniform temporal pooling over all frames", "~3.12%", "Equal temporal frame weights; lacks channel-wise feature recalibration"),
        ("ECAPA-TDNN (VoicePrint)", "Dilated Res2Net + SE + MFA + Channel-Attentive Pooling", "Dynamic Channel-Attentive Statistics (Ch-ASP)", "0.98% (SOTA)", "Optimal SOTA balance: 6.2M params, sub-120ms CPU latency, high margin")
    ]

    for i, row in enumerate(row_data):
        for j, val in enumerate(row):
            cell = tbl.cell(i+1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = hex_to_rgb('141B2D') if i % 2 == 0 else hex_to_rgb('0F172A')
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.color.rgb = ACCENT_EMERALD if i == 3 and j == 3 else (TEXT_WHITE if j == 0 else TEXT_SECONDARY)
            if i == 3:
                p.font.bold = True

    # Card below table summarizing key technological leaps
    add_card(s4, Inches(0.8), Inches(4.9), Inches(11.733), Inches(1.9), border_color=ACCENT_INDIGO)
    tb4_b = s4.shapes.add_textbox(Inches(1.0), Inches(5.0), Inches(11.333), Inches(1.7))
    tf4_b = tb4_b.text_frame
    tf4_b.word_wrap = True

    p = tf4_b.paragraphs[0]
    p.text = "Key Paradigm Shift in VoicePrint's ECAPA-TDNN Approach:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    p_pts = [
        "1. Hierarchical Multi-Scale Features: Replaces rigid uniform receptive fields with Res2Net multi-granular temporal sub-bands.",
        "2. Dynamic Channel Attention: Squeeze-and-Excitation selectively excites vocal tract formant frequencies while damping noise.",
        "3. Channel-Dependent Attentive Pooling: Gives non-uniform weight to phonetically rich frames over unvoiced silence."
    ]
    for pt in p_pts:
        p = tf4_b.add_paragraph()
        p.text = pt
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(3)

    # ==========================================
    # SLIDE 5: ECAPA-TDNN Dilated Convolutions & Res2Net
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, BG_COLOR)
    add_header(s5, "Detailed Neural Architecture", "1D Dilated Convolutions & Res2Net Hierarchical Multi-Scale Blocks", 5, total_slides)

    add_card(s5, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tb5_l = s5.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(4.8))
    tf5_l = tb5_l.text_frame
    tf5_l.word_wrap = True

    p = tf5_l.paragraphs[0]
    p.text = "1. Temporal Dilated Convolutions"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    pts_5l = [
        ("Exponential Receptive Field Growth:", " Standard Conv1D requires deep layers to view broad time spans. Dilated convolutions insert spaces (holes) into kernels:"),
        ("Receptive Field Equation:", " RF = 1 + Σ (k_i - 1) · d_i, where k_i is kernel size (k=3 or 5) and d_i is dilation factor."),
        ("Dilation Progression:", " Layer 1 uses d=1 (local 5-frame phoneme), Blocks 2-4 use d ∈ {2, 3, 4}, expanding context to >150 ms without parameter bloat."),
        ("Computational Efficiency:", " Avoids expensive recurrent state unrolling (RNN/LSTM) and quadratic self-attention memory overhead O(T^2) of standard Transformers.")
    ]
    for h, b in pts_5l:
        p = tf5_l.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(10)

    add_card(s5, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    tb5_r = s5.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.333), Inches(4.8))
    tf5_r = tb5_r.text_frame
    tf5_r.word_wrap = True

    p = tf5_r.paragraphs[0]
    p.text = "2. Res2Net Multi-Scale Processing"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    pts_5r = [
        ("Channel Sub-Grouping:", " The feature map with C=512 channels is split into s=8 equal sub-feature groups: x = [x_1, x_2, ..., x_s], where each x_i ∈ R^(C/s)."),
        ("Hierarchical Residual Feeding:", " Sub-group 1 is passed directly (y_1 = x_1). Sub-groups i ≥ 2 compute:\n  y_i = Conv_1D(x_i + y_{i-1}, kernel=3, dilation=d)"),
        ("Combinatorial Scale Explosion:", " Sub-group y_i processes features with an effective receptive field wider than y_{i-1}. When concatenated: Y = [y_1, y_2, ..., y_s], the block captures multi-scale acoustic phenomena simultaneously."),
        ("Speaker Benefit:", " Seamlessly captures short transient consonants (plosives: 10-20ms) alongside long sustained vowel formants (100-250ms).")
    ]
    for h, b in pts_5r:
        p = tf5_r.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(10)

    # ==========================================
    # SLIDE 6: Squeeze-and-Excitation & Multi-Layer Feature Aggregation
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, BG_COLOR)
    add_header(s6, "Channel Attention & Feature Propagation", "Squeeze-and-Excitation (SE) & Multi-Layer Feature Aggregation (MFA)", 6, total_slides)

    add_card(s6, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tb6_l = s6.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(4.8))
    tf6_l = tb6_l.text_frame
    tf6_l.word_wrap = True

    p = tf6_l.paragraphs[0]
    p.text = "1. Squeeze-and-Excitation (SE) Channel Recalibration"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    pts_6l = [
        ("Motivation:", " Different acoustic channels represent different frequency harmonics. SE explicitly models non-linear inter-channel dependencies."),
        ("Squeeze Operation (Global Context):", " Compresses temporal dimension T into channel descriptor z ∈ R^C via Global Average Pooling:\n  z_c = (1 / T) Σ_{t=1}^T u_c(t)"),
        ("Excitation Operation (Channel Gating):", " Two-layer bottleneck MLP with reduction ratio r=8:\n  s = σ( W_2 · ReLU(W_1 · z) ), where s ∈ (0, 1)^C"),
        ("Scale / Recalibration:", " Re-weights input feature map u:\n  ũ_{c, t} = s_c · u_{c, t}\nAmplifies discriminative vocal resonance; attenuates background hums.")
    ]
    for h, b in pts_6l:
        p = tf6_l.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(10)

    add_card(s6, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    tb6_r = s6.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.333), Inches(4.8))
    tf6_r = tb6_r.text_frame
    tf6_r.word_wrap = True

    p = tf6_r.paragraphs[0]
    p.text = "2. Multi-Layer Feature Aggregation (MFA)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    pts_6r = [
        ("The Shallow vs. Deep Dilemma:", " Early layers capture fine-grained phonetic textures (pitch, glottal pulse). Deeper layers capture abstract speaker identities. Traditional networks discard early layers."),
        ("Multi-Layer Concatenation:", " ECAPA-TDNN aggregates the output feature maps of all three SE-Res2Net residual blocks:\n  h_MFA(t) = [ h_1(t) ; h_2(t) ; h_3(t) ] ∈ R^(3C × T)"),
        ("Dense 1×1 Projection:", " A 1×1 Conv layer projects concatenated 1536 channels back down to C=512 channels, fusing complementary multi-depth information."),
        ("Impact on Robustness:", " Prevents vanishing gradient; ensures temporal statistics pooling receives both acoustic timbre and high-level identity features.")
    ]
    for h, b in pts_6r:
        p = tf6_r.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(10)

    # ==========================================
    # SLIDE 7: Channel-Dependent Attentive Statistics Pooling
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, BG_COLOR)
    add_header(s7, "Temporal Pooling Mechanism", "Channel-Dependent Attentive Statistics Pooling (Ch-ASP)", 7, total_slides)

    # Mathematical cards
    add_card(s7, Inches(0.8), Inches(1.5), Inches(11.733), Inches(2.5), border_color=ACCENT_INDIGO)
    tb7_top = s7.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.333), Inches(2.2))
    tf7_t = tb7_top.text_frame
    tf7_t.word_wrap = True

    p = tf7_t.paragraphs[0]
    p.text = "Mathematical Formulation of Channel-Dependent Attentive Statistics Pooling:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p_eqs = [
        "1. Attention Energy Computation:  e_{c, t} = v_c^T · f( W · h_t + b ),  where h_t is MFA frame representation at time t",
        "2. Softmax Temporal Normalization:  α_{c, t} = exp(e_{c, t}) / Σ_{τ=1}^T exp(e_{c, τ}),  guaranteeing Σ_t α_{c, t} = 1 for each channel c",
        "3. Weighted Channel Mean Vector:  μ̃_c = Σ_{t=1}^T α_{c, t} · h_{c, t}",
        "4. Weighted Channel Std Deviation:  σ̃_c = √[ Σ_{t=1}^T α_{c, t} · (h_{c, t} - μ̃_c)^2 ]"
    ]
    for eq in p_eqs:
        p = tf7_t.add_paragraph()
        p.text = eq
        p.font.size = Pt(12.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(6)

    # 2 Comparison cards below
    add_card(s7, Inches(0.8), Inches(4.2), Inches(5.6), Inches(2.5))
    tb7_bl = s7.shapes.add_textbox(Inches(1.0), Inches(4.35), Inches(5.2), Inches(2.2))
    tf7_bl = tb7_bl.text_frame
    tf7_bl.word_wrap = True
    p = tf7_bl.paragraphs[0]
    p.text = "Why Standard Temporal Pooling Fails"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ROSE

    pts_7bl = [
        "• Uniform weighting (1/T) treats silence, background room noise, coughs, and key speaker formants with identical importance.",
        "• Vulnerable to variable utterance length: short pauses skew the global mean vector.",
        "• Scalar attention applies one weight across all channels, ignoring frequency-selective speaker traits."
    ]
    for pt in pts_7bl:
        p = tf7_bl.add_paragraph()
        p.text = pt
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(4)

    add_card(s7, Inches(6.8), Inches(4.2), Inches(5.733), Inches(2.5))
    tb7_br = s7.shapes.add_textbox(Inches(7.0), Inches(4.35), Inches(5.333), Inches(2.2))
    tf7_br = tb7_br.text_frame
    tf7_br.word_wrap = True
    p = tf7_br.paragraphs[0]
    p.text = "Ch-ASP Advantage in VoicePrint"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_EMERALD

    pts_7br = [
        "• Channel-Specific Attention: Frame importance α_{c, t} is distinct for each feature channel c. High-frequency formants attend to different frames than low-pitch glottal bursts.",
        "• Output Concatenation: p = [ μ̃ ; σ̃ ] ∈ R^(2C = 1024), capturing both central tendency and temporal dynamics.",
        "• Bottleneck Projection: Fully-connected layer projects 1024-dim down to the final compact 192-dim voiceprint embedding."
    ]
    for pt in pts_7br:
        p = tf7_br.add_paragraph()
        p.text = pt
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(4)

    # ==========================================
    # SLIDE 8: Deep Metric Learning & Loss Functions (AAM-Softmax)
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, BG_COLOR)
    add_header(s8, "Deep Metric Learning", "Loss Functions: Softmax Cross-Entropy vs. AAM-Softmax (ArcFace)", 8, total_slides)

    add_card(s8, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tb8_l = s8.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(4.8))
    tf8_l = tb8_l.text_frame
    tf8_l.word_wrap = True

    p = tf8_l.paragraphs[0]
    p.text = "1. Standard Cross-Entropy Failure in Open-Set"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ROSE

    pts_8l = [
        ("Euclidean Softmax Loss:", " L_CE = -log [ e^(W_y^T x + b_y) / Σ_j e^(W_j^T x + b_j) ]"),
        ("Flaw: Separable but not Discriminative:", " Standard cross-entropy only separates training classes with linear hyperplanes in Euclidean space."),
        ("No Intra-Class Compaction:", " It does NOT force samples of the same speaker to form tight geometric clusters, nor does it enforce a margin between different speakers."),
        ("Failure on Unseen Speakers:", " In open-set testing, features from new speakers scatter into arbitrary gaps in Euclidean space, leading to false acceptances.")
    ]
    for h, b in pts_8l:
        p = tf8_l.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(8)

    add_card(s8, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    tb8_r = s8.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.333), Inches(4.8))
    tf8_r = tb8_r.text_frame
    tf8_r.word_wrap = True

    p = tf8_r.paragraphs[0]
    p.text = "2. Additive Angular Margin Softmax (AAM / ArcFace)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_EMERALD

    pts_8r = [
        ("Hyperspherical Constraint:", " Normalize both embedding ||x_i|| = 1 and class weights ||W_j|| = 1, fixing bias b=0. The logit simplifies to cos(θ_j)."),
        ("AAM-Softmax Objective:", " L_AAM = -(1/N) Σ log [ e^(s · cos(θ_y + m)) / ( e^(s · cos(θ_y + m)) + Σ_{j≠y} e^(s · cos(θ_j)) ) ]"),
        ("Scale & Margin Parameters:", " Scale s = 30 defines the hypersphere radius; additive angular margin m = 0.20 radians enforces strict geodesic separation on S^(191)."),
        ("Geometric Guarantee:", " Forces intra-speaker clustering on the unit hypersphere and guarantees an angular buffer zone between different speaker identities.")
    ]
    for h, b in pts_8r:
        p = tf8_r.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(8)

    # ==========================================
    # SLIDE 9: Vector Space Inference & Decision Theory
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, BG_COLOR)
    add_header(s9, "Inference & Decision Theory", "Cosine Similarity Metric, Decision Threshold (τ=0.70), and Error Rates", 9, total_slides)

    # 3 Horizontal Cards
    card_w = Inches(3.7)
    gap_9 = Inches(0.3)

    # Card 1: Cosine Similarity
    add_card(s9, Inches(0.8), Inches(1.5), card_w, Inches(5.2))
    tb9_1 = s9.shapes.add_textbox(Inches(1.0), Inches(1.7), card_w - Inches(0.4), Inches(4.8))
    tf9_1 = tb9_1.text_frame
    tf9_1.word_wrap = True
    p = tf9_1.paragraphs[0]
    p.text = "1. Cosine Distance Metric"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    pts_91 = [
        "Inference Formulation:",
        "Score(x_test, c) = (x_test · c) / ( ||x_test||_2 · ||c||_2 )",
        "Geodesic Angle: Equals cos(θ), bounded in [-1.0, 1.0].",
        "L2-Normalization: With normalized unit vectors ||x||=1, ||c||=1, cosine similarity simplifies to a fast inner product dot product (x_test^T c).",
        "Sub-Millisecond Speed: Vector multiplication takes < 0.1 ms in NumPy/PyTorch, enabling instant decision verification on low-power devices."
    ]
    for pt in pts_91:
        p = tf9_1.add_paragraph()
        p.text = pt
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(8)

    # Card 2: Threshold Calibration
    add_card(s9, Inches(0.8) + card_w + gap_9, Inches(1.5), card_w, Inches(5.2))
    tb9_2 = s9.shapes.add_textbox(Inches(1.0) + card_w + gap_9, Inches(1.7), card_w - Inches(0.4), Inches(4.8))
    tf9_2 = tb9_2.text_frame
    tf9_2.word_wrap = True
    p = tf9_2.paragraphs[0]
    p.text = "2. Threshold Calibration (τ = 0.70)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    pts_92 = [
        "Binary Decision Rule:",
        "Verdict = 'VERIFIED' if Score ≥ 0.70 else 'REJECTED'",
        "Threshold Selection Trade-off:",
        "• Higher τ (> 0.80): High security (banking, vault access). Extremely low FAR, but higher FRR for users with hoarse voices.",
        "• Lower τ (< 0.60): Convenience (smart speakers). Low FRR, but higher risk of impostor acceptance.",
        "Calibrated Balance: τ = 0.70 represents the empirical Equal Error Rate operating point for 16 kHz clean speech."
    ]
    for pt in pts_92:
        p = tf9_2.add_paragraph()
        p.text = pt
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(8)

    # Card 3: Biometric Error Theory
    add_card(s9, Inches(0.8) + (card_w + gap_9)*2, Inches(1.5), card_w, Inches(5.2))
    tb9_3 = s9.shapes.add_textbox(Inches(1.0) + (card_w + gap_9)*2, Inches(1.7), card_w - Inches(0.4), Inches(4.8))
    tf9_3 = tb9_3.text_frame
    tf9_3.word_wrap = True
    p = tf9_3.paragraphs[0]
    p.text = "3. Evaluation Metrics"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    pts_93 = [
        "False Acceptance Rate (FAR / Type I):",
        "FAR(τ) = P(Score ≥ τ | Impostor)",
        "Probability that an unauthorized voice is granted access.",
        "False Rejection Rate (FRR / Type II):",
        "FRR(τ) = P(Score < τ | Target)",
        "Probability that genuine enrolled user is locked out.",
        "Equal Error Rate (EER):",
        "The unique operating point τ* where FAR(τ*) = FRR(τ*). Lower is better. ECAPA-TDNN achieves 0.98% on VoxCeleb1."
    ]
    for pt in pts_93:
        p = tf9_3.add_paragraph()
        p.text = pt
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(8)

    # ==========================================
    # SLIDE 10: Empirical Benchmarks & Ablation Study
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, BG_COLOR)
    add_header(s10, "Empirical Benchmarks & Ablation", "Performance Evaluation on VoxCeleb1 and Architectural Ablation Analysis", 10, total_slides)

    # Table comparing benchmarks
    tbl_s10 = s10.shapes.add_table(5, 5, Inches(0.8), Inches(1.5), Inches(6.0), Inches(3.2)).table
    tbl_s10.columns[0].width = Inches(2.2)
    tbl_s10.columns[1].width = Inches(1.0)
    tbl_s10.columns[2].width = Inches(1.3)
    tbl_s10.columns[3].width = Inches(1.5)

    headers_10 = ["Neural Model", "Params", "VoxCeleb1 EER", "CPU Latency"]
    for j, h in enumerate(headers_10):
        cell = tbl_s10.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = hex_to_rgb('1E293B')
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = ACCENT_BLUE

    rows_10 = [
        ("i-Vector + PLDA", "4.2M", "5.39%", "850 ms"),
        ("TDNN x-vector", "4.4M", "3.12%", "190 ms"),
        ("ResNet-34 (Heavy)", "21.8M", "1.34%", "380 ms"),
        ("ECAPA-TDNN (VoicePrint)", "6.2M", "0.98%", "115 ms")
    ]
    for i, r in enumerate(rows_10):
        for j, val in enumerate(r):
            cell = tbl_s10.cell(i+1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = hex_to_rgb('141B2D') if i % 2 == 0 else hex_to_rgb('0F172A')
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.color.rgb = ACCENT_EMERALD if i == 3 and j in (2, 3) else (TEXT_WHITE if j == 0 else TEXT_SECONDARY)
            if i == 3:
                p.font.bold = True

    # Ablation Study Table / Card right side
    add_card(s10, Inches(7.1), Inches(1.5), Inches(5.433), Inches(5.2))
    tb10_r = s10.shapes.add_textbox(Inches(7.3), Inches(1.7), Inches(5.033), Inches(4.8))
    tf10_r = tb10_r.text_frame
    tf10_r.word_wrap = True

    p = tf10_r.paragraphs[0]
    p.text = "Architectural Component Ablation Study"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    p_ab = [
        ("Baseline Standard TDNN (x-vector):", " 3.12% EER\nUniform temporal pooling, simple Conv1D layers."),
        ("+ Res2Net Multi-Scale Blocks:", " 2.15% EER (-31.1% relative)\nHierarchical feature splitting captures multi-granular formants."),
        ("+ Squeeze-and-Excitation (SE):", " 1.68% EER (-21.9% relative)\nExplicit channel recalibration boosts formant channel SNR."),
        ("+ Multi-Layer Feature Aggregation (MFA):", " 1.32% EER (-21.4% relative)\nConcatenation preserves low-level acoustic timbre."),
        ("+ Channel-Attentive Pooling (Ch-ASP):", " 0.98% EER (-25.8% relative)\nFrame importance weighted independently per channel.")
    ]
    for h, b in p_ab:
        p = tf10_r.add_paragraph()
        p.text = h + b
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(7)

    # Metric Highlight Card on Bottom Left
    add_card(s10, Inches(0.8), Inches(4.9), Inches(6.0), Inches(1.8), border_color=ACCENT_EMERALD)
    tb10_bl = s10.shapes.add_textbox(Inches(1.0), Inches(5.0), Inches(5.6), Inches(1.6))
    tf10_bl = tb10_bl.text_frame
    tf10_bl.word_wrap = True
    p = tf10_bl.paragraphs[0]
    p.text = "Efficiency Takeaways for Offline CPU Deployment:"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_EMERALD

    pts_bl = [
        "• Parameter Footprint: Only 6.2 Million weights (26.4 MB in FP32).",
        "• Real-Time Factor (RTF): 0.038 on Intel/AMD standard CPU (processes 3-second speech in ~115 ms).",
        "• Zero GPU Requirement: Completely eliminates specialized cloud accelerators."
    ]
    for pt in pts_bl:
        p = tf10_bl.add_paragraph()
        p.text = pt
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(3)

    # ==========================================
    # SLIDE 11: End-to-End Implementation & Outlier Rejection
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, BG_COLOR)
    add_header(s11, "System Implementation & Engineering", "Centroid Enrollment, Outlier Filtering & Production Architecture", 11, total_slides)

    add_card(s11, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tb11_l = s11.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(4.8))
    tf11_l = tb11_l.text_frame
    tf11_l.word_wrap = True

    p = tf11_l.paragraphs[0]
    p.text = "1. Centroid Enrollment & Outlier Rejection"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    pts_11l = [
        ("Multi-Sample Enrollment:", " The user speaks K ≥ 3 short audio clips during enrollment to sample acoustic variability."),
        ("Pairwise Similarity Matrix:", " The system computes a K×K cosine matrix: S_{i, j} = cos(e_i, e_j)."),
        ("Outlier Rejection Metric:", " For each clip i, calculate mean angular distance to other clips: d_i = 1 - (1/(K-1)) Σ_{j≠i} S_{i, j}."),
        ("IQR Filtering Filter:", " If d_i > Q_3 + 1.5·IQR or S_{i, median} < 0.65, clip i is automatically purged (cough, background horn, truncated word)."),
        ("Unit-Normalized Centroid:", " c = (Σ_{k ∈ valid} e_k) / || Σ_{k ∈ valid} e_k ||_2\nEnsures the stored voiceprint rests precisely on the S^(191) unit sphere.")
    ]
    for h, b in pts_11l:
        p = tf11_l.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(7)

    add_card(s11, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    tb11_r = s11.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.333), Inches(4.8))
    tf11_r = tb11_r.text_frame
    tf11_r.word_wrap = True

    p = tf11_r.paragraphs[0]
    p.text = "2. Production Software Architecture"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    pts_11r = [
        ("PyTorch & SpeechBrain Core:", " Loads pretrained `spkrec-ecapa-voxceleb` in PyTorch eval mode (`torch.no_grad()`)."),
        ("FastAPI Async Backend:", " Provides high-throughput REST endpoints (`/api/verify/live`, `/api/verify/batch`, `/api/enroll`) with non-blocking async execution."),
        ("Atomic Storage Engine:", " Profile centroids saved as NumPy `.npy` files with accompanying JSON metadata (enrollment date, sample count, SNR)."),
        ("Responsive Web Client:", " HTML5 Web Audio API records 16 kHz uncompressed WAV; dynamic visual waveform meters and real-time verdict gauges.")
    ]
    for h, b in pts_11r:
        p = tf11_r.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(7)

    # ==========================================
    # SLIDE 12: Adversarial Threats & Anti-Spoofing Countermeasures
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, BG_COLOR)
    add_header(s12, "Security & Adversarial Robustness", "Adversarial Threats: Replay Attacks, Synthetic Deepfakes & Countermeasures", 12, total_slides)

    add_card(s12, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tb12_l = s12.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(4.8))
    tf12_l = tb12_l.text_frame
    tf12_l.word_wrap = True

    p = tf12_l.paragraphs[0]
    p.text = "1. Threat Vectors in Voice Biometrics"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ROSE

    pts_12l = [
        ("Replay Attacks:", " An adversary surreptitiously records the victim's voice and plays it back through high-end smartphone speakers or transducers."),
        ("Neural TTS Deepfakes:", " Text-to-Speech synthesis models (VITS, FastSpeech2) trained on victim's speech to generate arbitrary spoken sentences."),
        ("Voice Conversion (VC):", " Real-time latent conversion (Diffusion/GAN vocoders) that transforms an attacker's live speech into the victim's vocal timbre."),
        ("Adversarial Perturbations:", " Injecting imperceptible high-frequency acoustic noise δ (||δ||_∞ < ε) designed to alter embedding cosine orientation.")
    ]
    for h, b in pts_12l:
        p = tf12_l.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(9)

    add_card(s12, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    tb12_r = s12.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.333), Inches(4.8))
    tf12_r = tb12_r.text_frame
    tf12_r.word_wrap = True

    p = tf12_r.paragraphs[0]
    p.text = "2. State-of-the-Art Countermeasures"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_EMERALD

    pts_12r = [
        ("Front-End Liveness Classifiers:", " ASVspoof-compliant neural detectors (AASIST / RawNet2) analyzing high-frequency phase inconsistencies and vocoder phase artifacts."),
        ("Dynamic Challenge-Response:", " Presenting cryptographically pseudo-random phrase challenges (e.g. 'Read: 7-4-9-Alpha') validated via on-device ASR to prevent static replays."),
        ("Reverberation & Acoustic RIR Analysis:", " Detecting loudspeaker enclosure transfer functions and secondary room impulse response (RIR) signatures."),
        ("Cryptographic Vector Protection:", " AES-256 storage and homomorphic vector encryption allowing secure matching without decrypting raw centroids.")
    ]
    for h, b in pts_12r:
        p = tf12_r.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(9)

    # ==========================================
    # SLIDE 13: Live Demonstration & System Architecture
    # ==========================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, BG_COLOR)
    add_header(s13, "System Verification & Walkthrough", "Live Verification Flow, User Experience & API Interface", 13, total_slides)

    # Flow chart cards (4 steps)
    step_w = Inches(2.7)
    step_gap = Inches(0.3)
    step_y = Inches(1.5)
    step_h = Inches(3.0)

    steps_data = [
        ("Step 1: Capture", "Live browser audio streaming or 16 kHz WAV upload. Preprocessed with peak normalization and clipping filters.", ACCENT_BLUE),
        ("Step 2: Forward Pass", "STFT -> Log-Mel -> ECAPA-TDNN forward pass extracts 192-dim unit vector z in 115 ms.", ACCENT_TEAL),
        ("Step 3: Cosine Match", "Dot product: Score = z · c_profile. Evaluated against calibrated threshold τ = 0.70.", ACCENT_INDIGO),
        ("Step 4: Real-Time UI", "Verdict card, animated circular gauge, confidence percentage, and detailed audit log.", ACCENT_EMERALD)
    ]

    for i, (title, desc, acc_color) in enumerate(steps_data):
        x_pos = Inches(0.8) + i * (step_w + step_gap)
        add_card(s13, x_pos, step_y, step_w, step_h, border_color=acc_color)
        tb = s13.shapes.add_textbox(x_pos + Inches(0.15), step_y + Inches(0.2), step_w - Inches(0.3), step_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = acc_color

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(11.5)
        p_desc.font.color.rgb = TEXT_SECONDARY
        p_desc.space_before = Pt(8)

    # Big Lower summary card
    add_card(s13, Inches(0.8), Inches(4.8), Inches(11.733), Inches(1.9), border_color=hex_to_rgb('3B82F6'))
    tb13_b = s13.shapes.add_textbox(Inches(1.0), Inches(4.95), Inches(11.333), Inches(1.6))
    tf13_b = tb13_b.text_frame
    tf13_b.word_wrap = True

    p = tf13_b.paragraphs[0]
    p.text = "Key System Capabilities Implemented in the Workspace:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    points_sys = [
        "• Single-Page Interactive Web Application: Real-time profile selector, live mic testing, and sample audio batch evaluation.",
        "• Pre-enrolled Benchmark Profiles: Tested against real vocal samples (e.g. ASTA3, ASTA_primary) with high confidence separation (>0.82 genuine vs <0.38 impostor).",
        "• Dual Frontend Deployment: Standalone zero-dependency HTML interface and React SPA for full developer flexibility."
    ]
    for pt in points_sys:
        p = tf13_b.add_paragraph()
        p.text = pt
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(3)

    # ==========================================
    # SLIDE 14: Conclusion & Future Research Horizons
    # ==========================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, BG_COLOR)
    add_header(s14, "Summary & Future Directions", "Case Study Conclusions, Academic Insights & Future Research Horizons", 14, total_slides)

    add_card(s14, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tb14_l = s14.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(4.8))
    tf14_l = tb14_l.text_frame
    tf14_l.word_wrap = True

    p = tf14_l.paragraphs[0]
    p.text = "1. Summary of Academic Findings"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    pts_14l = [
        ("Architecture Superiority:", " Synergistic integration of 1D dilated convolutions, Res2Net multi-scale features, Squeeze-and-Excitation, and Attentive Statistics Pooling reduces EER by >68% relative to standard TDNN."),
        ("Hyperspherical Margin Power:", " AAM-Softmax (ArcFace) loss mathematically guarantees a geodesic angular margin m on the unit sphere S^(191), making zero-shot open-set verification feasible."),
        ("Edge Computational Feasibility:", " With 6.2M parameters and 115 ms CPU latency, deep neural voice biometrics can operate 100% locally on commodity hardware without cloud latency or privacy exposure.")
    ]
    for h, b in pts_14l:
        p = tf14_l.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(8)

    add_card(s14, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    tb14_r = s14.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.333), Inches(4.8))
    tf14_r = tb14_r.text_frame
    tf14_r.word_wrap = True

    p = tf14_r.paragraphs[0]
    p.text = "2. Future Research Horizons"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL

    pts_14r = [
        ("Self-Supervised Acoustic Representations:", " Integrating foundation speech models (WavLM, HuBERT, Wav2Vec 2.0) into the front-end feature extractor."),
        ("Post-Training Quantization (INT8):", " Quantizing model weights using ONNX Runtime or TensorRT for ultra-low memory footprints (<10 MB) on mobile / embedded edge chips."),
        ("Online Bayesian Centroid Adaptation:", " Continuous updating of enrolled centroids to account for long-term vocal tract aging and natural pitch drift."),
        ("Q&A & Discussion:", " Open for faculty questions and technical discussion on neural speaker verification.")
    ]
    for h, b in pts_14r:
        p = tf14_r.add_paragraph()
        p.text = h + b
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_SECONDARY
        p.space_before = Pt(8)

    # Save presentation
    output_filename = "VoicePrint_DeepLearning_CaseStudy.pptx"
    prs.save(output_filename)
    print(f"✅ Successfully generated PowerPoint presentation: {os.path.abspath(output_filename)}")

if __name__ == '__main__':
    build_deck()
