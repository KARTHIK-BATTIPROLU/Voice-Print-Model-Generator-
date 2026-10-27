import os
import sys
import markdown

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def generate_report_html():
    with open("VOICEPRINT_PROJECT_REPORT.md", "r", encoding="utf-8") as f:
        md = f.read()

    # Convert markdown to HTML with tables, fenced_code, and toc
    body_html = markdown.markdown(md, extensions=['tables', 'fenced_code', 'toc'])

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VoicePrint · Academic Project Report & Publication Paper</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
  <style>
    :root {{
      --bg-primary: #0b0f19;
      --bg-surface: #111827;
      --bg-card: #1f2937;
      --border-color: #374151;
      --text-primary: #f3f4f6;
      --text-secondary: #9ca3af;
      --accent-blue: #3b82f6;
      --accent-cyan: #06b6d4;
      --accent-emerald: #10b981;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background: var(--bg-primary);
      color: var(--text-primary);
      font-family: 'Inter', sans-serif;
      line-height: 1.75;
      padding-bottom: 80px;
    }}
    header {{
      background: rgba(17, 24, 39, 0.95);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-color);
      position: sticky;
      top: 0;
      z-index: 100;
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand h1 {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #fff;
      letter-spacing: -0.02em;
    }}
    .badge {{
      background: rgba(59, 130, 246, 0.2);
      border: 1px solid rgba(59, 130, 246, 0.4);
      color: #60a5fa;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .action-links {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s;
    }}
    .btn-primary {{
      background: #2563eb;
      color: #fff;
    }}
    .btn-primary:hover {{
      background: #1d4ed8;
    }}
    .btn-outline {{
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-primary);
    }}
    .btn-outline:hover {{
      background: rgba(255, 255, 255, 0.05);
      border-color: #6b7280;
    }}
    .container {{
      max-width: 980px;
      margin: 0 auto;
      padding: 36px 20px;
    }}
    .paper-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 48px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }}
    @media (max-width: 768px) {{
      .paper-card {{
        padding: 24px;
      }}
    }}
    /* Typography */
    h1, h2, h3, h4 {{
      color: #f9fafb;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    .paper-card h1 {{
      font-size: 1.85rem;
      line-height: 1.3;
      margin-bottom: 16px;
      text-align: center;
      color: #ffffff;
    }}
    .paper-card h2 {{
      font-size: 1.35rem;
      margin-top: 36px;
      margin-bottom: 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 6px;
      color: #60a5fa;
    }}
    .paper-card h3 {{
      font-size: 1.1rem;
      margin-top: 24px;
      margin-bottom: 10px;
      color: #93c5fd;
    }}
    .paper-card p {{
      margin-bottom: 16px;
      color: #cbd5e1;
      font-size: 0.98rem;
      line-height: 1.75;
      text-align: justify;
    }}
    .paper-card ul, .paper-card ol {{
      margin-bottom: 16px;
      padding-left: 24px;
      color: #cbd5e1;
      font-size: 0.96rem;
    }}
    .paper-card li {{
      margin-bottom: 6px;
    }}
    /* Images */
    .paper-card img {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 20px auto 6px auto;
      border-radius: 8px;
      border: 1px solid #334155;
      background: #0f172a;
    }}
    .paper-card em {{
      color: #94a3b8;
    }}
    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      font-size: 0.88rem;
      background: #0f172a;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #334155;
    }}
    th {{
      background: #1e293b;
      color: #f8fafc;
      font-weight: 600;
      text-align: left;
      padding: 10px 14px;
      border-bottom: 2px solid #475569;
    }}
    td {{
      padding: 10px 14px;
      border-bottom: 1px solid #1e293b;
      color: #e2e8f0;
    }}
    tr:nth-child(even) td {{
      background: #131c2e;
    }}
    tr:hover td {{
      background: rgba(59, 130, 246, 0.1);
    }}
    .download-banner {{
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(6, 182, 212, 0.2));
      border: 1px solid rgba(59, 130, 246, 0.4);
      border-radius: 10px;
      padding: 20px 24px;
      margin-bottom: 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .download-banner-text h3 {{
      font-size: 1.15rem;
      color: #fff;
      margin-bottom: 4px;
    }}
    .download-banner-text p {{
      font-size: 0.88rem;
      color: #94a3b8;
      margin-bottom: 0;
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span style="font-size: 1.5rem;">🎙️</span>
      <div>
        <h1>VoicePrint Biometrics</h1>
        <div style="font-size: 0.72rem; color: #94a3b8;">Academic Research & Case Study Portal</div>
      </div>
      <span class="badge">AANN Deep Learning Lab</span>
    </div>

    <div class="action-links">
      <a href="/VoicePrint_Academic_Project_Report.docx" download class="btn btn-primary">📥 Download Unified Paper (.docx)</a>
      <a href="/VoicePrint_DeepLearning_CaseStudy.pptx" download class="btn btn-outline">📥 Presentation (.pptx)</a>
      <a href="/casestudy" class="btn btn-outline">🖥️ Slides</a>
      <a href="/" class="btn btn-outline">🎙️ Web App</a>
    </div>
  </header>

  <div class="container">
    <div class="download-banner">
      <div class="download-banner-text">
        <h3>📄 Unified Publication-Grade Project Report</h3>
        <p>Complete academic research paper formatted exactly like the reference document with all 13 project figures and 7 tables.</p>
      </div>
      <div>
        <a href="/VoicePrint_Academic_Project_Report.docx" download class="btn btn-primary" style="font-size: 0.95rem; padding: 10px 20px;">📥 Download Word Document (.docx)</a>
      </div>
    </div>

    <div class="paper-card">
      {body_html}
    </div>
  </div>
</body>
</html>
"""

    with open("frontend/public/report.html", "w", encoding="utf-8") as f:
        f.write(page_html)

    with open("frontend/public/research.html", "w", encoding="utf-8") as f:
        f.write(page_html)

    # Also copy report_images into frontend/public/report_images so web page can render images!
    os.makedirs("frontend/public/report_images", exist_ok=True)
    import shutil
    for fn in os.listdir("report_images"):
        shutil.copy2(os.path.join("report_images", fn), os.path.join("frontend", "public", "report_images", fn))

    if os.path.exists("frontend/dist"):
        os.makedirs("frontend/dist/report_images", exist_ok=True)
        for fn in os.listdir("report_images"):
            shutil.copy2(os.path.join("report_images", fn), os.path.join("frontend", "dist", "report_images", fn))

    print("Successfully built frontend/public/report.html with report_images!")

if __name__ == "__main__":
    generate_report_html()
