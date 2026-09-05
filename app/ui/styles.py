"""Injected CSS + design tokens for the dashboard.

Colours are defined with rgba / semi-transparent fills so the same sheet reads
well on Streamlit's light and dark themes without per-theme overrides.
"""

CSS = """
<style>
:root {
    --fi-radius: 16px;
    --fi-border: rgba(130,140,160,0.22);
    --fi-card: rgba(140,150,170,0.06);
    --fi-card-hover: rgba(140,150,170,0.11);
    --fi-muted: rgba(130,140,160,0.95);
    --fi-pos: #16a34a;
    --fi-neg: #dc2626;
    --fi-warn: #d97706;
    --fi-info: #2563eb;
    --fi-accent: #7c3aed;
}

/* layout */
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px; }
[data-testid="stSidebar"] { border-right: 1px solid var(--fi-border); }
[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }
h1, h2, h3, h4 { letter-spacing: -0.01em; }

/* --- hero / header card --- */
.fi-hero {
    padding: 1.35rem 1.6rem;
    border-radius: var(--fi-radius);
    border: 1px solid var(--fi-border);
    background:
        radial-gradient(1200px 200px at 0% 0%, rgba(124,58,237,0.13), transparent 60%),
        radial-gradient(900px 200px at 100% 0%, rgba(37,99,235,0.12), transparent 55%),
        var(--fi-card);
    margin-bottom: 1rem;
}
.fi-hero-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.fi-hero h1 { font-size: 1.6rem; margin: 0; line-height: 1.15; }
.fi-hero .sub { opacity: 0.68; font-size: 0.88rem; margin-top: 0.25rem; }
.fi-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.85rem; }
.fi-chip {
    font-size: 0.74rem; padding: 0.2rem 0.62rem; border-radius: 999px;
    background: rgba(140,150,170,0.10); border: 1px solid var(--fi-border);
    white-space: nowrap;
}

/* --- big classification badge --- */
.fi-badge {
    display: inline-flex; align-items: center; gap: 0.35rem;
    padding: 0.42rem 0.95rem; border-radius: 999px;
    font-weight: 700; font-size: 0.9rem; letter-spacing: 0.02em; white-space: nowrap;
}
.fi-badge::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.fi-badge.bullish  { background: rgba(22,163,74,0.16);  color: var(--fi-pos); border: 1px solid rgba(22,163,74,0.4); }
.fi-badge.bearish  { background: rgba(220,38,38,0.16);  color: var(--fi-neg); border: 1px solid rgba(220,38,38,0.4); }
.fi-badge.neutral  { background: rgba(217,119,6,0.15);  color: var(--fi-warn); border: 1px solid rgba(217,119,6,0.4); }

/* --- signal strip (the 4 agent verdicts) --- */
.fi-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.7rem; margin: 0.4rem 0 1rem; }
@media (max-width: 900px) { .fi-strip { grid-template-columns: repeat(2, 1fr); } }
.fi-signal {
    border-radius: 14px; border: 1px solid var(--fi-border);
    background: var(--fi-card); padding: 0.85rem 1rem; position: relative; overflow: hidden;
}
.fi-signal::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--sig, var(--fi-muted));
}
.fi-signal .k { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; opacity: 0.6; }
.fi-signal .v { font-size: 1.12rem; font-weight: 700; margin-top: 0.2rem; color: var(--sig, inherit); }
.fi-signal .d { font-size: 0.78rem; opacity: 0.7; margin-top: 0.15rem; }
.sig-pos { --sig: var(--fi-pos); }
.sig-neg { --sig: var(--fi-neg); }
.sig-warn { --sig: var(--fi-warn); }
.sig-mut { --sig: var(--fi-muted); }

/* --- verdict pills (health factors etc.) --- */
.fi-pill {
    display: inline-block; padding: 0.12rem 0.55rem; border-radius: 999px;
    font-size: 0.74rem; font-weight: 600;
}
.fi-pill.strong   { background: rgba(22,163,74,0.16); color: var(--fi-pos); }
.fi-pill.moderate { background: rgba(217,119,6,0.15); color: var(--fi-warn); }
.fi-pill.weak     { background: rgba(220,38,38,0.16); color: var(--fi-neg); }
.fi-pill.unknown  { background: rgba(140,150,170,0.16); color: var(--fi-muted); }

/* --- news list --- */
.fi-news { border-bottom: 1px solid var(--fi-border); padding: 0.7rem 0; }
.fi-news:last-child { border-bottom: none; }
.fi-news a { font-weight: 600; text-decoration: none; }
.fi-news a:hover { text-decoration: underline; }
.fi-news .meta { font-size: 0.76rem; opacity: 0.62; margin-top: 0.2rem; }

/* --- misc --- */
.fi-note { font-size: 0.78rem; opacity: 0.62; margin-top: 0.4rem; }
.fi-disclaimer {
    font-size: 0.76rem; opacity: 0.72; border-left: 3px solid rgba(217,119,6,0.55);
    padding: 0.45rem 0.8rem; margin-top: 0.7rem; background: rgba(217,119,6,0.05);
    border-radius: 0 8px 8px 0;
}
.fi-section-title { font-size: 1.05rem; font-weight: 700; margin: 0.2rem 0 0.6rem; }

[data-testid="stMetric"] {
    background: var(--fi-card); border: 1px solid var(--fi-border);
    padding: 0.7rem 0.9rem; border-radius: 12px;
}
[data-testid="stMetricLabel"] { opacity: 0.7; }

.stTabs [data-baseweb="tab-list"] { gap: 0.15rem; }
.stTabs [data-baseweb="tab"] { font-size: 0.88rem; padding: 0.4rem 0.8rem; }

/* landing feature cards */
.fi-features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; margin-top: 1.1rem; }
@media (max-width: 900px) { .fi-features { grid-template-columns: 1fr; } }
.fi-feature {
    border: 1px solid var(--fi-border); border-radius: 14px; padding: 1rem 1.1rem;
    background: var(--fi-card);
}
.fi-feature h4 { margin: 0 0 0.3rem; font-size: 0.98rem; }
.fi-feature p { margin: 0; font-size: 0.84rem; opacity: 0.72; }
.fi-flow {
    font-size: 0.82rem; opacity: 0.75; margin-top: 1rem; padding: 0.8rem 1rem;
    border: 1px dashed var(--fi-border); border-radius: 12px; line-height: 1.7;
}
</style>
"""
