# ============================================================
# core/ai_engine.py — Multi-provider AI
# Gemini Flash (1500/day free) → Groq (100/day free) → Rules
# ============================================================

import os, json, time, logging
import streamlit as st

log          = logging.getLogger(__name__)
GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES  = 3
RETRY_DELAY  = 1.5

INJECTION_PATTERNS = [
    "ignore previous","ignore all","system:","you are now",
    "forget everything","new instruction","disregard",
    "pretend you are","act as","jailbreak",
]


def sanitize_input(text: str, max_len: int = 500) -> str:
    if not isinstance(text, str):
        return ""
    text  = text.strip()[:max_len]
    lower = text.lower()
    for p in INJECTION_PATTERNS:
        if p in lower:
            log.warning("Injection blocked: '%s'", p)
            return "Please ask a question about the campaign sales data."
    return text


def _get_key(name: str) -> str:
    try:
        secret = st.secrets.get(name, "")
    except (KeyError, FileNotFoundError, AttributeError):
        secret = ""
    return (
        st.session_state.get(name, "") or
        os.getenv(name, "") or
        secret
    )


def _call_gemini(prompt: str, max_tokens: int):
    key = _get_key("GEMINI_API_KEY")
    if not key:
        return None
    try:
        import google.generativeai as genai          # type: ignore[import-untyped]
        import google.api_core.exceptions as gexc    # type: ignore[import-untyped]

        genai.configure(api_key=key)                 # type: ignore[attr-defined]
        model = genai.GenerativeModel(GEMINI_MODEL)  # type: ignore[attr-defined]

        for attempt in range(MAX_RETRIES):
            try:
                r = model.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": 0.3,
                    },
                )
                if r.text:
                    return r.text
            except (
                gexc.NotFound,
                gexc.InvalidArgument,
                gexc.ResourceExhausted,
                gexc.ServiceUnavailable,
                gexc.DeadlineExceeded,
                ValueError,
                RuntimeError,
                TimeoutError,
            ) as e:
                log.warning("Gemini attempt %d: %s", attempt + 1, e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))

    except ImportError:
        log.warning("google-generativeai not installed")
    return None


def _call_groq(prompt: str, max_tokens: int):
    key = _get_key("GROQ_API_KEY")
    if not key:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=key)
        for attempt in range(MAX_RETRIES):
            try:
                r = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=max_tokens,
                    timeout=15,
                )
                result = r.choices[0].message.content
                if result:
                    return result
            except (ValueError, RuntimeError, TimeoutError, ConnectionError) as e:
                log.warning("Groq attempt %d: %s", attempt + 1, e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
    except ImportError:
        log.warning("groq not installed")
    return None


def call_llm(prompt: str, max_tokens: int = 600) -> str:
    """Gemini → Groq → Rule-based fallback chain"""
    result = _call_gemini(prompt, max_tokens)
    if result:
        return result
    result = _call_groq(prompt, max_tokens)
    if result:
        return result
    return _fallback_message()


def generate_executive_summary(findings: dict) -> str:
    prompt = f"""
You are a senior marketing analyst writing for a non-technical business owner.
Analyze this campaign performance data and write a clear executive summary.

Data:
- Total Revenue: ${findings.get('total_revenue',0):,.0f}
- Total Profit: ${findings.get('total_profit',0):,.0f}
- Profit Margin: {findings.get('overall_margin_%',0):.1f}%
- Campaign Order Rate: {findings.get('campaign_orders_%',0):.1f}%
- Campaign Lift: {findings.get('campaign_lift_%',0):+.1f}%
- Best Region: {findings.get('best_region','N/A')}
- Worst Region: {findings.get('worst_region','N/A')}
- Best Segment: {findings.get('best_segment','N/A')}
- Best Category: {findings.get('best_category','N/A')}
- Peak Month: {findings.get('peak_month','N/A')}
- Best Discount Band: {findings.get('best_discount_band','N/A')}

Write exactly 3 short paragraphs:
1. Start "Your strongest performers are..." — what is working
2. Start "The biggest profit risk is..." — what is hurting you
3. Start "This month, focus on..." — 3 specific actions

Plain English. Specific numbers. No jargon. Max 180 words.
"""
    return call_llm(prompt, max_tokens=350)


def answer_question(question: str,
                    findings: dict,
                    df_summary: dict) -> str:
    q = sanitize_input(question)
    if not q:
        return "Please ask a valid question about your campaign data."
    prompt = f"""
You are a data analyst. Answer this question using only the data provided.
Be specific with numbers. Max 80 words.
If you cannot answer from this data, say so clearly.

Data: {json.dumps(findings, indent=2)}
Records: {df_summary.get('records',0):,}
Regions: {df_summary.get('regions',[])}
Segments: {df_summary.get('segments',[])}

Question: {q}
"""
    return call_llm(prompt, max_tokens=160)


def generate_recommendations(findings: dict, df_summary: dict) -> list:
    prompt = f"""
You are a marketing consultant. Generate exactly 6 recommendations.
Return ONLY valid JSON array, no other text.

Data:
- Margin: {findings.get('overall_margin_%',0):.1f}%
- Campaign rate: {findings.get('campaign_orders_%',0):.1f}%
- Best region: {findings.get('best_region','N/A')}
- Worst region: {findings.get('worst_region','N/A')}
- Best discount: {findings.get('best_discount_band','N/A')}
- Best segment: {findings.get('best_segment','N/A')}
- Peak month: {findings.get('peak_month','N/A')}

JSON format:
[{{"priority":"urgent","title":"Short title","description":"25 words max","impact":"$X or Y%"}}]

2 urgent, 2 high, 2 opportunity priorities.
"""
    raw = call_llm(prompt, max_tokens=700)
    try:
        start = raw.find("[")
        end   = raw.rfind("]") + 1
        if start != -1 and end > start:
            recs = json.loads(raw[start:end])
            if isinstance(recs, list) and recs:
                return recs
    except (json.JSONDecodeError, ValueError):
        pass
    return _rule_based_recommendations(findings)


def _fallback_message() -> str:
    return """
**AI Summary Unavailable**

Add a free API key to enable AI insights:
- **Gemini** (recommended): [aistudio.google.com](https://aistudio.google.com) — 1,500 free requests/day
- **Groq**: [console.groq.com](https://console.groq.com) — 100 free requests/day

Add your key in the **AI Settings** section of the sidebar.
In the meantime, visit the **Recommendations** page for
data-driven actions that work without any API key.
"""


def _rule_based_recommendations(findings: dict) -> list:
    recs   = []
    margin = findings.get("overall_margin_%", 15)
    camp   = findings.get("campaign_orders_%", 50)
    lift   = findings.get("campaign_lift_%", 0)
    best_r = findings.get("best_region", "top region")
    best_b = findings.get("best_discount_band", "1-10%")
    peak   = findings.get("peak_month", "November")
    best_s = findings.get("best_segment", "Consumer")

    recs.append({
        "priority": "urgent",
        "title"   : "Fix profit margin" if margin < 12
                    else f"Scale campaigns in {best_r}",
        "description": (
            f"Margin of {margin:.1f}% is critically low. "
            f"Audit all campaigns above 20% discount."
            if margin < 12 else
            f"{best_r} is your top performer. "
            f"Increase budget allocation here first."
        ),
        "impact": "Potential +5-8% margin" if margin < 12
                  else "Estimated +15% regional revenue",
    })
    recs.append({
        "priority": "urgent",
        "title"   : "Reduce discount dependency" if camp > 60
                    else "Investigate campaign lift",
        "description": (
            f"{camp:.0f}% of orders use discounts — "
            f"test loyalty rewards instead."
            if camp > 60 else
            f"Campaign lift is {lift:.1f}%. "
            f"Review discount strategy for ROI."
        ),
        "impact": "Improve baseline profitability",
    })
    recs.append({
        "priority"   : "high",
        "title"      : f"Use {best_b} as standard discount",
        "description": f"{best_b} delivers your highest ROI. "
                       f"Make this the campaign default.",
        "impact"     : "Optimise campaign profitability",
    })
    recs.append({
        "priority"   : "high",
        "title"      : f"Plan {peak} campaign now",
        "description": f"{peak} is your peak month. "
                       f"Prepare 6 weeks ahead.",
        "impact"     : "Capture full seasonal demand",
    })
    recs.append({
        "priority"   : "opportunity",
        "title"      : f"Upsell to {best_s} with bundles",
        "description": f"{best_s} drives most revenue. "
                       f"Bundle offers lift order value without discounting.",
        "impact"     : "+10-15% avg order value",
    })
    recs.append({
        "priority"   : "opportunity",
        "title"      : "Build customer loyalty programme",
        "description": "Replace one-time discounts with points rewards "
                       "to drive repeat purchases without margin erosion.",
        "impact"     : "Long-term LTV improvement",
    })
    return recs
