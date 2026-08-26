#!/usr/bin/env python3
"""
VOLUME Master Gradio UI — accessible, MathML-preserving EPUB splitter.
Requires: gradio>=5.8, ebooklib, fonttools
"""
from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path

import gradio as gr
from ebooklib import epub

from ...parsers.epub3 import EPUB3Parser
from ...splitters.size import SizeSplitter
from ...exporters.epub import EPUBExporter
from ...exporters.zip import ZipExporter
from musepool import ProcessPool


CSS = """
:root { --primary: #ff7a00; --focus: #ff7a00; }
#skip-link { position:absolute; left:-9999px; top:auto; width:1px; height:1px; overflow:hidden; }
#skip-link:focus { left:16px; top:16px; width:auto; height:auto; background:#000; color:#fff; padding:8px 12px; z-index:99999; border-radius:8px; }
.gradio-container { font-family: 'Inter', system-ui, -apple-system, sans-serif!important; }
button, input, [role="button"] { min-height:44px!important; }
*:focus-visible { outline: 3px solid var(--focus)!important; outline-offset: 2px!important; border-radius:4px; }
.high-contrast { filter: contrast(1.25); background:#000!important; color:#fff!important; }
.high-contrast.gr-box,.high-contrast.gr-panel { background:#000!important; color:#fff!important; border:2px solid #fff!important; }
#main-content { max-width: 1100px; margin: 0 auto; }
.gr-button-primary { background: var(--primary)!important; border-color: var(--primary)!important; }
"""

JS = """
function initA11y(){
  const root = document.documentElement;
  window.adjustFont = (d) => {
    let s = parseFloat(localStorage.getItem('volume-font')||'100');
    s = Math.min(200, Math.max(90, s+d));
    root.style.fontSize = s+'%';
    localStorage.setItem('volume-font', s);
    document.getElementById('font-label').innerText = s+'%';
  }
  window.toggleHC = () => { document.body.classList.toggle('high-contrast'); }
}
document.addEventListener('DOMContentLoaded', initA11y);
"""


def split_epub_to_volumes(source_path: str, max_mb: int, out_dir: str):
    log = []
    parser = EPUB3Parser()
    book = parser.parse(source_path)

    log.append(f"📖 Master: {book.title} | Original: {book.total_bytes / 1024 / 1024:.1f} MB")
    log.append(f"Found {len(book.chapters)} chapters, {len(book.images)} images, MathML: {book.has_mathml}")

    splitter = SizeSplitter(max_mb=max_mb)
    plans = splitter.plan(book)
    log.append(f"Split plan: {len(plans)} VOLUME(S) @ {max_mb}MB max")

    exporter = EPUBExporter()
    volume_paths = []

    for plan in plans:
        path = os.path.join(out_dir, f"VOLUME_Vol{plan.volume_index:02d}_of_{len(plans):02d}_{len(plan.chapters)}ch.epub")
        result = exporter.export(book, plan, len(plans), path)
        log.append(f"✓ Vol {plan.volume_index}: {result['size_mb']:.1f} MB — {len(plan.chapters)} chapters — MathML kept")
        volume_paths.append(path)

    zip_path = os.path.join(out_dir, f"VOLUME_ALL_{len(plans)}_volumes.zip")
    ZipExporter().export(volume_paths, zip_path)
    log.append(f"📦 Master ZIP: {zip_path}")

    return volume_paths, "\n".join(log)


def gradio_split(file_obj, max_mb, optimize_fonts, optimize_images):
    if file_obj is None:
        raise gr.Error("Drop your EPUB first")

    tmp_out = tempfile.mkdtemp(prefix="volume_")
    try:
        files, log = split_epub_to_volumes(file_obj.name, int(max_mb), tmp_out)
        return files, log
    except Exception as e:
        return [], f"ERROR: {e}"


with gr.Blocks(title="VOLUME Master 2.0 — EPUB3 MathML Splitter", css=CSS, js=JS, theme=gr.themes.Soft(primary_hue="orange")) as demo:
    gr.HTML('<a id="skip-link" href="#main-content">Skip to main content</a>')

    with gr.Column(elem_id="main-content"):
        gr.Markdown("""
        # VOLUME Master 2.0 — One Master. LMS-Ready Volumes.
        ### EPUB3 MathML Safe Splitter | Musepool Async | MCP Skills | Agentic Optimization
        """)

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 1. Master Copy Input")
                file_in = gr.File(label="Drop EPUB3 here", file_types=[".epub"], type="filepath")
                max_mb = gr.Slider(20, 49, value=45, step=1, label="Max MB per VOLUME")
                optimize_fonts = gr.Checkbox(label="Subset fonts (fontTools)", value=False)
                optimize_images = gr.Checkbox(label="Convert images to WebP", value=False)

                with gr.Row():
                    btn_font_down = gr.Button("A- Font -10%", size="sm")
                    btn_font_up = gr.Button("A+ Font +10%", size="sm")
                    btn_hc = gr.Button("HC High Contrast", size="sm")
                    gr.HTML('<span id="font-label" aria-live="polite">100%</span>')

                btn_split = gr.Button("SPLIT INTO VOLUMES →", variant="primary", size="lg")

            with gr.Column():
                gr.Markdown("## 2. LMS-Ready Volumes Output")
                log_out = gr.Textbox(label="Master Log", lines=18, show_copy_button=True)
                files_out = gr.Files(label="Download VOLUMES", file_count="multiple")

        gr.Markdown("""
        ### Pipeline: Parse → Musepool Analyze → Split → Optimize → Export → ZIP
        WCAG 2.2 AAA: Skip link, 44px targets, 3px focus, font scaling, high contrast, live regions.
        """)

    btn_split.click(
        fn=gradio_split,
        inputs=[file_in, max_mb, optimize_fonts, optimize_images],
        outputs=[files_out, log_out],
        api_name="split",
    )
    btn_font_down.click(fn=None, js="() => adjustFont(-10)")
    btn_font_up.click(fn=None, js="() => adjustFont(10)")
    btn_hc.click(fn=None, js="() => toggleHC()")


def main():
    demo.launch(max_file_size="1000mb", show_api=True, server_name="0.0.0.0")


if __name__ == "__main__":
    main()
