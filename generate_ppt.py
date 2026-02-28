"""
Generate a professional PPT for the Support Ticket Resolution System.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Brand colours ──────────────────────────────────────────────────────────────
DARK_NAVY   = RGBColor(0x0D, 0x1B, 0x2A)   # slide backgrounds
ACCENT_BLUE = RGBColor(0x1B, 0x6C, 0xA8)   # headers / shapes
LIGHT_BLUE  = RGBColor(0x4F, 0xA3, 0xD8)   # sub-accents
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY  = RGBColor(0xF0, 0xF4, 0xF8)
MID_GRAY    = RGBColor(0xA0, 0xB0, 0xC0)
ORANGE      = RGBColor(0xFF, 0x6B, 0x35)
GREEN       = RGBColor(0x2E, 0xCC, 0x71)
PURPLE      = RGBColor(0x8E, 0x44, 0xAD)
TEAL        = RGBColor(0x16, 0xA0, 0x85)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK_LAYOUT = prs.slide_layouts[6]   # completely blank


# ── Helpers ────────────────────────────────────────────────────────────────────

def bg(slide, color=DARK_NAVY):
    """Fill slide background."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def rect(slide, l, t, w, h, fill_color, alpha=None, radius=None):
    shape = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape


def textbox(slide, text, l, t, w, h,
            font_size=18, bold=False, color=WHITE,
            align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb


def heading(slide, text, l=0.4, t=0.18, w=12.5, size=30):
    textbox(slide, text, l, t, w, 0.55, font_size=size, bold=True,
            color=WHITE, align=PP_ALIGN.LEFT)


def sub_heading(slide, text, l=0.4, t=0.72, w=12.5, size=14, color=LIGHT_BLUE):
    textbox(slide, text, l, t, w, 0.35, font_size=size, bold=False,
            color=color, align=PP_ALIGN.LEFT)


def accent_bar(slide, color=ACCENT_BLUE, t=0.75):
    rect(slide, 0.4, t, 1.2, 0.06, color)


def card(slide, l, t, w, h, fill=ACCENT_BLUE, title="", body="",
         title_size=13, body_size=11, title_color=WHITE, body_color=LIGHT_GRAY):
    rect(slide, l, t, w, h, fill)
    if title:
        textbox(slide, title, l + 0.15, t + 0.12, w - 0.3, 0.4,
                font_size=title_size, bold=True, color=title_color)
    if body:
        textbox(slide, body, l + 0.15, t + 0.52, w - 0.3, h - 0.65,
                font_size=body_size, color=body_color, wrap=True)


def bullet_list(slide, items, l, t, w, h,
                font_size=12, color=WHITE, spacing=0.35, bullet="▸ "):
    for i, item in enumerate(items):
        textbox(slide, bullet + item, l, t + i * spacing, w, 0.35,
                font_size=font_size, color=color)


def divider(slide, t, color=ACCENT_BLUE, w=12.53, l=0.4):
    rect(slide, l, t, w, 0.04, color)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 – Title
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s, DARK_NAVY)

# Left accent stripe
rect(s, 0, 0, 0.08, 7.5, ACCENT_BLUE)
# Bottom accent
rect(s, 0, 7.1, 13.33, 0.4, ACCENT_BLUE)

# Big title
textbox(s, "Support Ticket Resolution System",
        0.5, 1.6, 12.3, 1.4, font_size=44, bold=True,
        color=WHITE, align=PP_ALIGN.LEFT)

# Tagline
textbox(s, "AI-Powered RAG Knowledge Base  •  Multi-Region  •  Third-Party Integrations",
        0.5, 3.1, 12.3, 0.5, font_size=16, color=LIGHT_BLUE, align=PP_ALIGN.LEFT)

# Accent bar
rect(s, 0.5, 3.72, 3.5, 0.07, ORANGE)

# Sub info
textbox(s, "IncubXperts Hackathon 2026",
        0.5, 3.95, 6, 0.4, font_size=13, color=MID_GRAY)

# Bottom-right badge
rect(s, 10.5, 6.4, 2.5, 0.55, ACCENT_BLUE)
textbox(s, "Cohere  •  ChromaDB  •  Streamlit",
        10.55, 6.43, 2.4, 0.45, font_size=9, color=WHITE, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 – Agenda
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Agenda", 0.4, 0.18, 12, 0.7, font_size=32, bold=True,
        color=WHITE, align=PP_ALIGN.LEFT)

agenda = [
    ("01", "Problem Statement",        "The challenge with modern support workflows"),
    ("02", "Solution Overview",        "What the system does and how"),
    ("03", "System Architecture",      "Components, data flow, tech stack"),
    ("04", "Key Features",             "RAG, multi-region, streaming, admin"),
    ("05", "Third-Party Integrations", "CRM, Jira, ServiceNow via webhooks"),
    ("06", "Auto-Assignment & AI",     "Intelligent routing and priority scoring"),
    ("07", "Demo Screens",             "UI walkthrough"),
    ("08", "Roadmap",                  "What's next"),
]

cols = [(0.35, 3.0), (6.8, 3.0)]
for i, (num, title, desc) in enumerate(agenda):
    col_idx = i % 2
    row_idx = i // 2
    l = cols[col_idx][0]
    t = 1.25 + row_idx * 1.3
    w = cols[col_idx][1]
    rect(s, l, t, w, 1.1, ACCENT_BLUE)
    rect(s, l, t, 0.55, 1.1, LIGHT_BLUE)
    textbox(s, num, l + 0.08, t + 0.3, 0.45, 0.5,
            font_size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    textbox(s, title, l + 0.65, t + 0.08, w - 0.75, 0.38,
            font_size=13, bold=True, color=WHITE)
    textbox(s, desc, l + 0.65, t + 0.52, w - 0.75, 0.5,
            font_size=10, color=LIGHT_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 – Problem Statement
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Problem Statement", 0.4, 0.18, 12, 0.7,
        font_size=32, bold=True, color=WHITE)

problems = [
    ("⏱ Slow Resolution",
     "Support agents spend hours searching through emails, wikis, and old tickets to find relevant solutions."),
    ("🔁 Repeated Work",
     "The same issues are resolved from scratch every time because there's no centralised, searchable knowledge base."),
    ("🌍 Multi-Region Complexity",
     "Different regions (India, US, Global) have different policies, infra setups, and resolution procedures."),
    ("📋 Manual Ticket Routing",
     "Tickets land in a generic queue — assigning them to the right team/person relies entirely on human judgement."),
    ("🔗 Siloed Tools",
     "Jira, ServiceNow, CRMs and other tools don't talk to each other, causing context loss and duplicate effort."),
    ("📉 No Priority Intelligence",
     "Ticket priority is set manually or defaults to MEDIUM, causing critical issues to go unnoticed."),
]

for i, (title, body) in enumerate(problems):
    col = i % 2
    row = i // 2
    l = 0.35 + col * 6.5
    t = 1.2 + row * 1.85
    rect(s, l, t, 6.1, 1.7,
         RGBColor(0x14, 0x2A, 0x45) if col == 0 else RGBColor(0x0F, 0x22, 0x36))
    rect(s, l, t, 0.06, 1.7, ORANGE)
    textbox(s, title, l + 0.2, t + 0.12, 5.7, 0.42,
            font_size=13, bold=True, color=ORANGE)
    textbox(s, body, l + 0.2, t + 0.55, 5.7, 1.0,
            font_size=10.5, color=LIGHT_GRAY, wrap=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 – Solution Overview
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Solution Overview", 0.4, 0.18, 12, 0.7,
        font_size=32, bold=True, color=WHITE)

# Left description
textbox(s,
        "An AI-powered support ticket resolution system built on Retrieval-Augmented Generation (RAG). "
        "It ingests historical tickets, internal documents, and policy PDFs to create a searchable, "
        "intelligent knowledge base that answers support queries with cited sources and confidence scores.",
        0.4, 1.15, 5.8, 1.6, font_size=12.5, color=LIGHT_GRAY, wrap=True)

pillars = [
    (GREEN,  "📥 Ingest",     "PDF, DOCX, JSON\nticket resolutions"),
    (ACCENT_BLUE, "🔍 Retrieve", "Semantic vector\nsearch via ChromaDB"),
    (LIGHT_BLUE,  "🤖 Generate", "Cohere LLM with\nstreaming answers"),
    (ORANGE, "📊 Cite",       "Sources, confidence\n& audit log"),
]

for i, (color, title, body) in enumerate(pillars):
    l = 0.35 + i * 3.22
    t = 2.95
    rect(s, l, t, 3.0, 0.45, color)
    textbox(s, title, l + 0.1, t + 0.06, 2.8, 0.35,
            font_size=13, bold=True, color=WHITE)
    rect(s, l, t + 0.45, 3.0, 1.4, RGBColor(0x14, 0x2A, 0x45))
    textbox(s, body, l + 0.15, t + 0.55, 2.7, 1.2,
            font_size=11, color=LIGHT_GRAY, wrap=True)

# Arrow connectors text
for i in range(3):
    l = 3.2 + i * 3.22
    textbox(s, "→", l + 0.05, 3.1, 0.25, 0.25,
            font_size=18, bold=True, color=ACCENT_BLUE)

# Bottom bullets
features = [
    "Multi-region filtering (All / India / US)",
    "Department-scoped search (Infra, HR, Finance, General)",
    "Streaming chat UI with confidence metric",
    "Admin panel: upload, list & delete documents",
    "Query audit logging (JSONL)",
]
textbox(s, "Core Capabilities", 0.4, 4.55, 5, 0.35,
        font_size=13, bold=True, color=LIGHT_BLUE)
bullet_list(s, features, 0.4, 4.95, 12.5, 2.0,
            font_size=11, color=LIGHT_GRAY, spacing=0.38)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 – System Architecture
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "System Architecture", 0.4, 0.18, 12, 0.7,
        font_size=32, bold=True, color=WHITE)

# ─── Row 1: Ingestion Pipeline ───────────────────────────────────────────────
textbox(s, "INGESTION PIPELINE", 0.4, 1.1, 3.5, 0.3,
        font_size=9, bold=True, color=ORANGE)
ingestion = [
    ("PDF / DOCX\nDocuments", ACCENT_BLUE),
    ("Document\nLoader", RGBColor(0x14, 0x4A, 0x7A)),
    ("Text\nChunker", RGBColor(0x14, 0x4A, 0x7A)),
    ("Cohere\nEmbeddings", TEAL),
    ("ChromaDB\nVector Store", GREEN),
]
for i, (label, color) in enumerate(ingestion):
    l = 0.35 + i * 2.57
    rect(s, l, 1.42, 2.3, 0.9, color)
    textbox(s, label, l + 0.1, 1.52, 2.1, 0.7,
            font_size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    if i < 4:
        textbox(s, "→", l + 2.32, 1.72, 0.28, 0.28,
                font_size=14, bold=True, color=LIGHT_BLUE)

# Also ticket JSON
textbox(s, "Ticket\nJSON", 0.35, 2.52, 2.3, 0.7, )
rect(s, 0.35, 2.52, 2.3, 0.7, PURPLE)
textbox(s, "Ticket JSON\nResolutions", 0.45, 2.58, 2.1, 0.6,
        font_size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
# arrow from ticket json to chunker
textbox(s, "↗", 2.67, 2.55, 0.28, 0.28, font_size=14, bold=True, color=LIGHT_BLUE)

# ─── Row 2: Query Pipeline ───────────────────────────────────────────────────
textbox(s, "QUERY PIPELINE", 0.4, 3.35, 3.5, 0.3,
        font_size=9, bold=True, color=GREEN)
query_steps = [
    ("User\nQuestion", ACCENT_BLUE),
    ("Embed\nQuery", TEAL),
    ("Vector\nSearch", GREEN),
    ("Cohere\nLLM Chat", RGBColor(0x8E, 0x44, 0xAD)),
    ("Stream +\nCite + Log", ORANGE),
]
for i, (label, color) in enumerate(query_steps):
    l = 0.35 + i * 2.57
    rect(s, l, 3.65, 2.3, 0.9, color)
    textbox(s, label, l + 0.1, 3.75, 2.1, 0.7,
            font_size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    if i < 4:
        textbox(s, "→", l + 2.32, 3.95, 0.28, 0.28,
                font_size=14, bold=True, color=LIGHT_BLUE)

# ─── Row 3: Tech Stack ───────────────────────────────────────────────────────
textbox(s, "TECHNOLOGY STACK", 0.4, 4.7, 3.5, 0.3,
        font_size=9, bold=True, color=LIGHT_BLUE)
tech = [
    ("Streamlit\nUI", RGBColor(0x0A, 0x2A, 0x42)),
    ("Cohere\ncommand-a-03", RGBColor(0x0A, 0x2A, 0x42)),
    ("Cohere\nembed-english-v3", RGBColor(0x0A, 0x2A, 0x42)),
    ("ChromaDB\nVector DB", RGBColor(0x0A, 0x2A, 0x42)),
    ("pypdf\npython-docx", RGBColor(0x0A, 0x2A, 0x42)),
]
for i, (label, color) in enumerate(tech):
    l = 0.35 + i * 2.57
    rect(s, l, 5.0, 2.3, 0.85, color)
    rect(s, l, 5.0, 2.3, 0.1, ACCENT_BLUE)
    textbox(s, label, l + 0.1, 5.08, 2.1, 0.72,
            font_size=10.5, bold=False, color=LIGHT_GRAY, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 – Key Features
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Key Features", 0.4, 0.18, 12, 0.7,
        font_size=32, bold=True, color=WHITE)

features_data = [
    (GREEN,  "🌍 Multi-Region Support",
     "Filter knowledge by region (All / India / US) so agents always get contextually relevant answers."),
    (ORANGE, "🏢 Department Scoping",
     "Narrow searches to Infra, HR, Finance, or General departments for precise, noise-free results."),
    (ACCENT_BLUE, "⚡ Streaming Responses",
     "Answers stream token-by-token via Cohere's chat_stream API, giving users instant feedback."),
    (PURPLE, "📎 Source Citations",
     "Every answer is backed by cited document names, regions and similarity-scored excerpts."),
    (TEAL,   "📊 Confidence Scoring",
     "Automatic confidence percentage based on retrieval quality and LLM certainty signals."),
    (ORANGE, "🔒 I-Don't-Know Fallback",
     "When context is insufficient the system explicitly says so instead of hallucinating."),
    (GREEN,  "🗂 Admin Panel",
     "Upload PDF/DOCX, sync ticket resolutions JSON, view document library, delete documents."),
    (LIGHT_BLUE, "📝 Audit Logging",
     "Every query is logged to JSONL with timestamp, region, answer excerpt, confidence, sources."),
]

for i, (color, title, body) in enumerate(features_data):
    col = i % 2
    row = i // 2
    l = 0.35 + col * 6.5
    t = 1.15 + row * 1.55
    rect(s, l, t, 6.1, 1.4, RGBColor(0x0F, 0x22, 0x38))
    rect(s, l, t, 0.07, 1.4, color)
    textbox(s, title, l + 0.22, t + 0.1, 5.7, 0.4,
            font_size=13, bold=True, color=color)
    textbox(s, body, l + 0.22, t + 0.52, 5.7, 0.78,
            font_size=10.5, color=LIGHT_GRAY, wrap=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 – Third-Party Integrations (Overview)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Third-Party Integrations", 0.4, 0.18, 12, 0.7,
        font_size=32, bold=True, color=WHITE)

textbox(s,
        "The Support Ticket Resolution System is designed as an open integration layer. "
        "It can connect to any CRM, ITSM, or ticketing platform to read historical data, "
        "enrich it with AI analysis, and push back resolutions, assignments, and priority scores.",
        0.4, 1.1, 12.5, 0.9, font_size=12, color=LIGHT_GRAY, wrap=True)

divider(s, 2.1)

integrations = [
    (ORANGE,    "Jira",        "Webhook →\nFetch issue",      "Analyse &\nClassify",   "Auto-assign,\nSet priority,\nPost resolution"),
    (GREEN,     "ServiceNow",  "Webhook →\nFetch incident",   "Analyse &\nClassify",   "Auto-assign,\nSet priority,\nPost resolution"),
    (LIGHT_BLUE,"Salesforce\nCRM", "API Poll /\nWebhook",     "Analyse &\nClassify",   "Route to\nagent, Add\nresolution note"),
    (PURPLE,    "Zendesk",     "Webhook →\nFetch ticket",     "Analyse &\nClassify",   "Macro apply,\nAssign group,\nAuto-resolve"),
    (TEAL,      "Any REST\nSystem", "REST / GraphQL\n/ Webhook", "Analyse &\nClassify", "Push back\nvia API"),
]

for i, (color, name, step1, step2, step3) in enumerate(integrations):
    l = 0.3 + i * 2.6
    t = 2.3
    rect(s, l, t, 2.4, 0.55, color)
    textbox(s, name, l + 0.1, t + 0.08, 2.2, 0.42,
            font_size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    for j, step in enumerate([step1, step2, step3]):
        rect(s, l, t + 0.65 + j * 1.5, 2.4, 1.35,
             RGBColor(0x0E, 0x20, 0x35))
        rect(s, l, t + 0.65 + j * 1.5, 2.4, 0.08, color)
        textbox(s, step, l + 0.1, t + 0.75 + j * 1.5, 2.2, 1.15,
                font_size=10, color=LIGHT_GRAY, align=PP_ALIGN.CENTER, wrap=True)

# Step labels on left
for j, label in enumerate(["01  Ingest", "02  Analyse", "03  Act"]):
    textbox(s, label, 13.0, 2.98 + j * 1.5, 0.25, 0.4,
            font_size=8, bold=True, color=MID_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 – Integration Architecture (Flow Diagram)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Integration Architecture & Data Flow", 0.4, 0.18, 12, 0.7,
        font_size=28, bold=True, color=WHITE)

# ── Layer 1: Source systems ──────────────────────────────────────────────────
textbox(s, "SOURCE SYSTEMS", 0.35, 1.1, 3, 0.28, font_size=8, bold=True, color=ORANGE)
sources = ["Jira", "ServiceNow", "Salesforce CRM", "Zendesk", "Custom REST API"]
for i, src in enumerate(sources):
    rect(s, 0.35, 1.42 + i * 0.98, 2.4, 0.82, RGBColor(0x12, 0x28, 0x40))
    rect(s, 0.35, 1.42 + i * 0.98, 0.06, 0.82, ORANGE)
    textbox(s, src, 0.5, 1.54 + i * 0.98, 2.15, 0.55,
            font_size=11, color=WHITE)

# ── Arrow to middleware ──────────────────────────────────────────────────────
rect(s, 2.85, 3.3, 1.4, 0.07, LIGHT_BLUE)
textbox(s, "Webhook /\nREST API", 2.9, 2.85, 1.3, 0.55,
        font_size=9, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
textbox(s, "→", 4.15, 3.2, 0.3, 0.3, font_size=20, bold=True, color=LIGHT_BLUE)

# ── Layer 2: Integration Middleware ─────────────────────────────────────────
textbox(s, "AI PROCESSING LAYER", 4.5, 1.1, 4, 0.28, font_size=8, bold=True, color=GREEN)
middleware = [
    (GREEN,        "Event Listener\n(Webhook Handler)",      4.5, 1.42),
    (TEAL,         "Data Parser &\nNormaliser",               4.5, 2.52),
    (ACCENT_BLUE,  "RAG Query Engine\n(Cohere + ChromaDB)",   4.5, 3.62),
    (PURPLE,       "Decision Engine\n(Assignee + Priority)",  4.5, 4.72),
]
for color, label, l, t in middleware:
    rect(s, l, t, 3.8, 0.88, RGBColor(0x0E, 0x22, 0x38))
    rect(s, l, t, 3.8, 0.08, color)
    textbox(s, label, l + 0.15, t + 0.15, 3.5, 0.65,
            font_size=11, bold=True, color=WHITE)
    if t < 4.72:
        textbox(s, "↓", l + 1.7, t + 0.9, 0.3, 0.3,
                font_size=14, bold=True, color=color)

# ── Arrow to output ──────────────────────────────────────────────────────────
textbox(s, "→", 8.35, 3.2, 0.3, 0.3, font_size=20, bold=True, color=LIGHT_BLUE)
rect(s, 8.35, 3.3, 0.5, 0.07, LIGHT_BLUE)

# ── Layer 3: Outputs ─────────────────────────────────────────────────────────
textbox(s, "ACTIONS & OUTPUT", 8.9, 1.1, 4, 0.28, font_size=8, bold=True, color=LIGHT_BLUE)
outputs = [
    (ORANGE,     "Auto-Assign to\nRight Person/Team"),
    (GREEN,      "Set Ticket\nPriority (P1–P4)"),
    (ACCENT_BLUE,"Post AI Resolution\nin Comments"),
    (PURPLE,     "Notify via\nSlack / Email"),
    (TEAL,       "Update Audit\nLog & Analytics"),
]
for i, (color, label) in enumerate(outputs):
    rect(s, 8.9, 1.42 + i * 0.98, 3.8, 0.82, RGBColor(0x0E, 0x22, 0x38))
    rect(s, 8.9, 1.42 + i * 0.98, 0.06, 0.82, color)
    textbox(s, label, 9.05, 1.54 + i * 0.98, 3.55, 0.62,
            font_size=11, color=WHITE)

# Bottom note
rect(s, 0.35, 6.75, 12.6, 0.55, RGBColor(0x0A, 0x18, 0x28))
textbox(s,
        "💡  The AI Processing Layer is platform-agnostic. Any system that emits webhooks or exposes a REST/GraphQL API can be integrated without code changes to the core RAG engine.",
        0.5, 6.8, 12.3, 0.45, font_size=10, color=LIGHT_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 – Jira & ServiceNow Deep Dive
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Deep Dive: Jira & ServiceNow Integration", 0.4, 0.18, 12, 0.7,
        font_size=28, bold=True, color=WHITE)

# ── Jira ─────────────────────────────────────────────────────────────────────
rect(s, 0.35, 1.1, 5.9, 5.9, RGBColor(0x0A, 0x1E, 0x32))
rect(s, 0.35, 1.1, 5.9, 0.48, ORANGE)
textbox(s, "🔵  Jira", 0.5, 1.17, 5.6, 0.38,
        font_size=15, bold=True, color=WHITE)
jira_steps = [
    ("1. Webhook Trigger",     "New issue created / status changed → Jira fires webhook to integration endpoint."),
    ("2. Fetch Full Context",  "System calls Jira REST API to fetch issue details: title, description, labels, project, reporter."),
    ("3. RAG Analysis",        "Issue text is embedded and queried against the knowledge base for similar past tickets."),
    ("4. Decision Engine",     "AI determines: assignee (based on component/dept), priority (P1–P4), and resolution steps."),
    ("5. Write Back",          "System posts a comment with resolution, updates assignee field and priority label via Jira API."),
]
for i, (step, desc) in enumerate(jira_steps):
    rect(s, 0.5, 1.68 + i * 1.02, 5.6, 0.9, RGBColor(0x0F, 0x26, 0x3E))
    textbox(s, step, 0.65, 1.72 + i * 1.02, 5.3, 0.32,
            font_size=11, bold=True, color=ORANGE)
    textbox(s, desc, 0.65, 2.04 + i * 1.02, 5.3, 0.55,
            font_size=9.5, color=LIGHT_GRAY, wrap=True)

# ── ServiceNow ───────────────────────────────────────────────────────────────
rect(s, 6.65, 1.1, 6.3, 5.9, RGBColor(0x0A, 0x1E, 0x32))
rect(s, 6.65, 1.1, 6.3, 0.48, GREEN)
textbox(s, "🟢  ServiceNow", 6.8, 1.17, 6.0, 0.38,
        font_size=15, bold=True, color=WHITE)
snow_steps = [
    ("1. Business Rule / Webhook", "Incident created → ServiceNow Business Rule fires outbound REST message to AI service."),
    ("2. Retrieve Incident Data",  "Fetch full incident: short_desc, description, category, caller, urgency, impact."),
    ("3. Knowledge Base Query",    "System searches ChromaDB for top-5 matching resolutions from historical incidents."),
    ("4. AI Classification",       "Cohere LLM analyses context → outputs structured JSON: assignee_group, priority, solution."),
    ("5. Update Incident",         "Scripted REST pushes resolution note to work notes, sets assignment_group and priority."),
]
for i, (step, desc) in enumerate(snow_steps):
    rect(s, 6.8, 1.68 + i * 1.02, 6.0, 0.9, RGBColor(0x0F, 0x26, 0x3E))
    textbox(s, step, 6.95, 1.72 + i * 1.02, 5.7, 0.32,
            font_size=11, bold=True, color=GREEN)
    textbox(s, desc, 6.95, 2.04 + i * 1.02, 5.7, 0.55,
            font_size=9.5, color=LIGHT_GRAY, wrap=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 – Auto-Assignment & Priority Intelligence
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Auto-Assignment & Priority Intelligence", 0.4, 0.18, 12, 0.7,
        font_size=28, bold=True, color=WHITE)

# Left: Assignee logic
rect(s, 0.35, 1.12, 6.0, 5.8, RGBColor(0x0A, 0x1E, 0x32))
rect(s, 0.35, 1.12, 6.0, 0.45, ACCENT_BLUE)
textbox(s, "🎯  Smart Assignee Detection", 0.5, 1.18, 5.7, 0.38,
        font_size=14, bold=True, color=WHITE)

assign_points = [
    "Ticket keywords mapped to department taxonomy (Infra, HR, Finance, General)",
    "Similarity search finds the agent/team who resolved the most similar past tickets",
    "If multiple candidates: system ranks by recency, resolution success rate",
    "Falls back to team/group assignment when individual mapping is unavailable",
    "Supports skill-based routing: e.g. 'VPN issues' → Network team",
    "Works across regions: India tickets routed to India team, US tickets to US team",
]
for i, pt in enumerate(assign_points):
    rect(s, 0.5, 1.68 + i * 0.82, 5.7, 0.7, RGBColor(0x0F, 0x26, 0x3E))
    rect(s, 0.5, 1.68 + i * 0.82, 0.06, 0.7, ACCENT_BLUE)
    textbox(s, pt, 0.65, 1.74 + i * 0.82, 5.4, 0.6,
            font_size=10, color=LIGHT_GRAY, wrap=True)

# Right: Priority matrix
rect(s, 6.75, 1.12, 6.2, 5.8, RGBColor(0x0A, 0x1E, 0x32))
rect(s, 6.75, 1.12, 6.2, 0.45, ORANGE)
textbox(s, "🚨  Priority Scoring Matrix", 6.9, 1.18, 5.9, 0.38,
        font_size=14, bold=True, color=WHITE)

priorities = [
    (RGBColor(0xE7, 0x4C, 0x3C), "P1 – Critical",
     "Production down, data loss, security breach\nImmediate page + auto-escalate"),
    (ORANGE,                      "P2 – High",
     "Major feature broken, >10 users affected\nAssign within 1 hour"),
    (RGBColor(0xF3, 0x9C, 0x12), "P3 – Medium",
     "Minor functionality impacted, workaround exists\nAssign within 4 hours"),
    (GREEN,                       "P4 – Low",
     "Cosmetic issue, how-to question, enhancement\nBest effort / backlog"),
]
for i, (color, level, desc) in enumerate(priorities):
    rect(s, 6.9, 1.68 + i * 1.28, 5.85, 1.15, RGBColor(0x0F, 0x26, 0x3E))
    rect(s, 6.9, 1.68 + i * 1.28, 0.12, 1.15, color)
    textbox(s, level, 7.1, 1.74 + i * 1.28, 5.55, 0.35,
            font_size=12, bold=True, color=color)
    textbox(s, desc, 7.1, 2.1 + i * 1.28, 5.55, 0.65,
            font_size=10, color=LIGHT_GRAY, wrap=True)

# AI scoring note
rect(s, 6.9, 6.75 - 0.08, 5.85, 0.0, RGBColor(0x0F, 0x26, 0x3E))


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 – CRM Integration
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "CRM Integration", 0.4, 0.18, 12, 0.7,
        font_size=32, bold=True, color=WHITE)

textbox(s,
        "Connect the AI engine to any CRM (Salesforce, HubSpot, Zoho, Freshdesk, etc.) "
        "to automatically identify problems, match them to historical resolutions, "
        "and deliver answers directly within the CRM workflow — no context switching for agents.",
        0.4, 1.1, 12.5, 0.85, font_size=12, color=LIGHT_GRAY, wrap=True)

crm_cards = [
    (ACCENT_BLUE, "📥 Auto-Ingest Past Cases",
     "Bulk sync historical CRM cases into the knowledge base. Each case becomes a searchable resolution vector."),
    (TEAL, "🔔 Real-Time Case Trigger",
     "New case opened → webhook fires → system analyses and enriches the case before any agent touches it."),
    (GREEN, "🤖 AI-Powered Suggestions",
     "System suggests resolution steps, links to similar past cases, and confidence score — right inside the CRM."),
    (ORANGE, "👤 Smart Routing",
     "Route cases to the best-fit agent based on skill matching, historical success, and current workload."),
    (PURPLE, "📈 Analytics Layer",
     "Track resolution times, confidence trends, top recurring issues, and agent performance over time."),
    (LIGHT_BLUE, "🔄 Bidirectional Sync",
     "When an agent resolves the ticket, the solution is automatically ingested back into the knowledge base."),
]

for i, (color, title, body) in enumerate(crm_cards):
    col = i % 3
    row = i // 3
    l = 0.35 + col * 4.35
    t = 2.1 + row * 2.2
    rect(s, l, t, 4.1, 2.0, RGBColor(0x0E, 0x22, 0x38))
    rect(s, l, t, 4.1, 0.08, color)
    textbox(s, title, l + 0.18, t + 0.2, 3.7, 0.45,
            font_size=12, bold=True, color=color)
    textbox(s, body, l + 0.18, t + 0.7, 3.7, 1.15,
            font_size=10.5, color=LIGHT_GRAY, wrap=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 12 – UI Walkthrough
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Application UI Walkthrough", 0.4, 0.18, 12, 0.7,
        font_size=32, bold=True, color=WHITE)

screens = [
    (ACCENT_BLUE, "Chat Interface",
     ["Region & Department filters", "Streaming token-by-token answers",
      "Source citations per response", "Confidence % metric",
      "New Chat button (clear history)"]),
    (GREEN, "Admin Panel",
     ["Sync Ticket Resolutions from JSON", "Upload PDF / DOCX documents",
      "Select Region & Department per doc", "Document library with chunk counts",
      "One-click delete per document"]),
]

for i, (color, title, bullets) in enumerate(screens):
    l = 0.35 + i * 6.5
    # Mock screen frame
    rect(s, l, 1.15, 6.1, 3.8, RGBColor(0x08, 0x18, 0x28))
    rect(s, l, 1.15, 6.1, 0.38, color)
    textbox(s, title, l + 0.15, 1.2, 5.8, 0.32,
            font_size=13, bold=True, color=WHITE)
    # Mock content lines
    for j in range(4):
        rect(s, l + 0.2, 1.7 + j * 0.7, 5.7, 0.45, RGBColor(0x12, 0x2A, 0x42))
    rect(s, l + 0.2, 1.7, 1.8, 0.45, RGBColor(0x1B, 0x4A, 0x70))
    textbox(s, "Region ▾", l + 0.3, 1.77, 1.5, 0.3, font_size=9, color=MID_GRAY)
    rect(s, l + 2.1, 1.7, 1.8, 0.45, RGBColor(0x1B, 0x4A, 0x70))
    textbox(s, "Department ▾", l + 2.2, 1.77, 1.6, 0.3, font_size=9, color=MID_GRAY)
    rect(s, l + 0.2, 2.4, 5.7, 0.8, RGBColor(0x14, 0x30, 0x50))
    textbox(s, "💬  Ask a question about your documentation...",
            l + 0.35, 2.57, 5.3, 0.4, font_size=9, color=MID_GRAY)
    rect(s, l + 0.2, 3.3, 5.7, 1.45, RGBColor(0x0C, 0x20, 0x35))
    textbox(s, "Answer will appear here with citations...",
            l + 0.35, 3.45, 5.3, 0.5, font_size=9, color=MID_GRAY, italic=True)
    rect(s, l + 0.2, 4.55, 1.2, 0.28, color)
    textbox(s, "Confidence", l + 0.25, 4.57, 1.1, 0.22, font_size=7.5, color=WHITE)

    # Bullet list below
    textbox(s, "Features:", l + 0.15, 5.05, 5.8, 0.3,
            font_size=11, bold=True, color=color)
    for j, b in enumerate(bullets):
        textbox(s, f"• {b}", l + 0.2, 5.4 + j * 0.38, 5.8, 0.35,
                font_size=10, color=LIGHT_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 13 – Roadmap
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s)
rect(s, 0, 0, 13.33, 1.05, ACCENT_BLUE)
textbox(s, "Roadmap & Future Enhancements", 0.4, 0.18, 12, 0.7,
        font_size=30, bold=True, color=WHITE)

phases = [
    (GREEN, "Phase 1 — Foundation\n(Current)",
     ["Multi-region RAG knowledge base", "PDF/DOCX ingestion pipeline",
      "Ticket resolution JSON sync", "Streaming chat UI with confidence",
      "Admin document management"]),
    (ORANGE, "Phase 2 — Integrations\n(Next 30 days)",
     ["Jira webhook listener + write-back", "ServiceNow integration",
      "CRM connector (Salesforce / Zendesk)", "Auto-assign & priority scoring",
      "Slack/Teams notification on assignment"]),
    (PURPLE, "Phase 3 — Intelligence\n(60–90 days)",
     ["Fine-tuned assignee routing model", "SLA breach prediction",
      "Trending issue detection & alerts", "Self-learning: ingest resolved tickets",
      "Multi-language support"]),
    (LIGHT_BLUE, "Phase 4 — Enterprise\n(90+ days)",
     ["SSO / RBAC access control", "Analytics dashboard (resolution KPIs)",
      "On-premise / private cloud deploy", "Custom LLM fine-tuning",
      "API-first headless mode"]),
]

for i, (color, phase, items) in enumerate(phases):
    l = 0.32 + i * 3.22
    rect(s, l, 1.12, 3.0, 6.0, RGBColor(0x0A, 0x1E, 0x32))
    rect(s, l, 1.12, 3.0, 0.6, color)
    textbox(s, phase, l + 0.12, 1.17, 2.76, 0.56,
            font_size=12, bold=True, color=WHITE)
    for j, item in enumerate(items):
        rect(s, l + 0.15, 1.88 + j * 1.0, 2.7, 0.82, RGBColor(0x0F, 0x26, 0x3E))
        rect(s, l + 0.15, 1.88 + j * 1.0, 0.06, 0.82, color)
        textbox(s, item, l + 0.28, 1.96 + j * 1.0, 2.5, 0.65,
                font_size=10, color=LIGHT_GRAY, wrap=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 14 – Thank You / Summary
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK_LAYOUT)
bg(s, DARK_NAVY)

rect(s, 0, 0, 0.08, 7.5, ACCENT_BLUE)
rect(s, 0, 7.1, 13.33, 0.4, ACCENT_BLUE)

textbox(s, "Thank You", 0.5, 1.4, 12, 1.0,
        font_size=52, bold=True, color=WHITE, align=PP_ALIGN.LEFT)

rect(s, 0.5, 2.65, 4.0, 0.07, ORANGE)

summary_items = [
    "✅  RAG-based ticket resolution with Cohere + ChromaDB",
    "✅  Multi-region, multi-department knowledge base",
    "✅  Real-time third-party integration (Jira, ServiceNow, CRM)",
    "✅  Auto-assign, priority scoring, AI resolution comments",
    "✅  Fully extensible — any REST/webhook system supported",
]
for i, item in enumerate(summary_items):
    textbox(s, item, 0.5, 2.9 + i * 0.55, 8.5, 0.5,
            font_size=13, color=LIGHT_GRAY)

textbox(s, "Built at IncubXperts Hackathon 2026",
        0.5, 5.95, 8, 0.4, font_size=12, color=MID_GRAY)

# Right side tech stack pill
rect(s, 9.8, 2.3, 3.1, 4.0, RGBColor(0x0A, 0x1E, 0x32))
textbox(s, "Tech Stack", 9.95, 2.45, 2.8, 0.38,
        font_size=13, bold=True, color=ACCENT_BLUE, align=PP_ALIGN.CENTER)
for i, (label, color) in enumerate([
    ("Cohere LLM",       ORANGE),
    ("Cohere Embeddings",LIGHT_BLUE),
    ("ChromaDB",         GREEN),
    ("Streamlit",        ACCENT_BLUE),
    ("Python 3.13",      PURPLE),
]):
    rect(s, 10.0, 2.92 + i * 0.65, 2.6, 0.5, RGBColor(0x0F, 0x26, 0x3E))
    rect(s, 10.0, 2.92 + i * 0.65, 0.06, 0.5, color)
    textbox(s, label, 10.12, 2.98 + i * 0.65, 2.4, 0.38,
            font_size=11, color=WHITE)


# ── Save ───────────────────────────────────────────────────────────────────────
out = r"D:\IncubXperts\hackthon\ticket-system\Support_Ticket_Resolution_System.pptx"
prs.save(out)
print("Saved: " + out)
