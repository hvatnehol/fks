import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import database as db

st.set_page_config(
    page_title="FKS Leadsystem",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand colours ─────────────────────────────────────────────────────────────
PRIMARY   = "#5D2F82"
PRIMARY_D = "#37124A"
DARK      = "#1E2D3D"
SIDEBAR_BG = "#131820"

STATUS_COLORS = {
    "Ny lead":            "#7F8C8D",
    "Kontaktet":          "#2980B9",
    "Besøk avtalt":       "#8E44AD",
    "Besøk gjennomført":  "#6C3483",
    "Søkt":               "#E07B2B",
    "Elev":               "#27AE60",
    "Sluttet":            "#C0392B",
}

st.markdown(f"""
<style>
    :root {{
        --bg: #F7F8FB;
        --surface: #FFFFFF;
        --text: #1E2D3D;
        --muted: #5D677A;
        --border: #E6E9F2;
        --primary: {PRIMARY};
        --primary-dark: {PRIMARY_D};
    }}

    body {{ background: var(--bg); }}
    .stApp {{ color: var(--text); }}
    .stSidebar {{ background-color: {SIDEBAR_BG} !important; }}
    .stSidebar [data-testid="stImage"] img {{ border-radius: 16px; }}

    .page-hero {{
        background: linear-gradient(180deg, rgba(82,32,106,0.08), rgba(255,255,255,0.95));
        border-radius: 36px;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }}
    .page-hero::before {{
        content: "";
        position: absolute;
        right: -80px;
        top: -60px;
        width: 240px;
        height: 240px;
        background: rgba(82,32,106,0.16);
        border-radius: 40px;
    }}
    .page-hero::after {{
        content: "";
        position: absolute;
        right: 40px;
        bottom: -40px;
        width: 160px;
        height: 160px;
        background: rgba(82,32,106,0.08);
        border-radius: 32px;
    }}
    .hero-eyebrow {{
        text-transform: uppercase;
        letter-spacing: 0.25rem;
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 1rem;
    }}
    .hero-heading {{
        font-size: clamp(2.6rem, 4vw, 3.8rem);
        line-height: 1.02;
        margin-bottom: 1rem;
        color: var(--text);
        font-weight: 800;
    }}
    .hero-copy {{
        max-width: 680px;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #4E596C;
    }}

    .section-card {{
        background: var(--surface);
        border-radius: 28px;
        padding: 1.9rem;
        box-shadow: 0 30px 60px rgba(17, 24, 39, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.7);
        margin-bottom: 1.5rem;
    }}
    .metric-card {{
        background: var(--surface);
        border-radius: 24px;
        padding: 1.35rem;
        box-shadow: 0 18px 45px rgba(17, 24, 39, 0.06);
        min-height: 120px;
    }}
    .page-login-card {{
        background: var(--surface);
        border-radius: 32px;
        padding: 2.5rem 2rem;
        box-shadow: 0 30px 80px rgba(17, 24, 39, 0.08);
        max-width: 520px;
        margin: 3rem auto 2rem;
        border: 1px solid rgba(226, 232, 240, 0.8);
    }}
    .login-brand {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }}
    .login-brand h2 {{
        margin: 0;
        font-size: 1.45rem;
        color: var(--text);
        letter-spacing: 0.02em;
    }}

    .stButton > button {{ border-radius: 14px !important; padding: 0.92rem 1.1rem !important; }}
    .stButton > button[kind="primary"] {{ background-color: var(--primary) !important; border-color: var(--primary) !important; color: white !important; }}
    .stButton > button[kind="primary"]:hover {{ background-color: var(--primary-dark) !important; border-color: var(--primary-dark) !important; }}
    .stButton > button:not([kind="primary"]) {{ border-radius: 14px !important; }}

    .badge {{
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
        color: white;
        letter-spacing: 0.02em;
    }}
    .pipeline-step {{
        text-align: center;
        padding: 0.75rem 0.6rem;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }}
    .nav-btn > button {{
        background: transparent !important;
        border: none !important;
        color: #CBD5E0 !important;
        text-align: left !important;
        font-size: 0.95rem !important;
        padding: 0.4rem 0.8rem !important;
        border-radius: 6px !important;
        width: 100% !important;
    }}
    .nav-btn > button:hover {{
        background: rgba(255,255,255,0.1) !important;
        color: white !important;
    }}
    .nav-btn-active > button {{
        background: var(--primary) !important;
        color: white !important;
    }}
    .status-log-entry {{
        border-left: 3px solid #E0E0E0;
        padding: 1rem 1rem 1rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.92rem;
        color: #4E596C;
    }}
</style>
""", unsafe_allow_html=True)


def badge(status):
    color = STATUS_COLORS.get(status, "#999")
    return f'<span class="badge" style="background:{color}">{status}</span>'


def pipeline_bar(current_status):
    steps = [s for s in db.STATUSES if s != "Sluttet"]
    try:
        current_idx = steps.index(current_status)
    except ValueError:
        current_idx = -1

    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        color = STATUS_COLORS.get(step, "#ccc")
        if i < current_idx:
            bg, fg = color + "55", color
            border = f"2px solid {color}"
        elif i == current_idx:
            bg, fg = color, "white"
            border = f"2px solid {color}"
        else:
            bg, fg = "#F0F0F0", "#AAAAAA"
            border = "2px solid #E0E0E0"
        col.markdown(
            f'<div class="pipeline-step" style="background:{bg};color:{fg};border:{border}">{step}</div>',
            unsafe_allow_html=True,
        )


def family_status_summary(children):
    """Returns the most advanced status among a family's children."""
    if not children:
        return "Ny lead"
    order = {s: i for i, s in enumerate(db.STATUSES)}
    return max(children, key=lambda c: order.get(c["status"], 0))["status"]


# ── Init ──────────────────────────────────────────────────────────────────────
db.create_tables()


# ── LOGIN ─────────────────────────────────────────────────────────────────────

def page_login():
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(
            """
            <div class="page-login-card">
                <div class="login-brand">
                    <img src="logo.png" width="60" />
                    <h2>FKS Leadsystem</h2>
                </div>
                <p style="color:#5D677A;text-align:center;margin-bottom:2rem">Logg inn for å få full oversikt over leads, familier og oppfølging.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login"):
            username = st.text_input("Brukernavn")
            password = st.text_input("Passord", type="password")
            if st.form_submit_button("Logg inn", use_container_width=True, type="primary"):
                user = db.verify_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.error("Feil brukernavn eller passord.")

        st.caption("Standardkonto: admin / admin123")


# ── SIDEBAR NAV ───────────────────────────────────────────────────────────────

def sidebar():
    user = st.session_state.user
    current = st.session_state.get("page", "Dashboard")

    with st.sidebar:
        st.image("logo.png", width=160)
        st.markdown('<p style="font-size:0.75rem;color:#7A8FA6;padding-left:0.5rem;margin-bottom:1rem">Leadsystem</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:0.8rem;color:#7A8FA6;padding-left:0.5rem">Innlogget som<br><strong style="color:#E2E8F0">{user["full_name"]}</strong></p>', unsafe_allow_html=True)
        st.divider()

        pages = ["Dashboard", "Leads", "Ny lead"]
        icons  = ["📊", "👥", "➕"]
        if user["role"] == "admin":
            pages.append("Admin")
            icons.append("⚙️")

        for p, icon in zip(pages, icons):
            active = "nav-btn-active" if current == p else "nav-btn"
            with st.container():
                st.markdown(f'<div class="{active}">', unsafe_allow_html=True)
                if st.button(f"{icon}  {p}", key=f"nav_{p}", use_container_width=True):
                    st.session_state.page = p
                    st.session_state.selected_child = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        with st.expander("🔑  Endre passord"):
            with st.form("sidebar_change_pw"):
                cur_pw  = st.text_input("Nåværende passord", type="password")
                new_pw1 = st.text_input("Nytt passord", type="password")
                new_pw2 = st.text_input("Bekreft nytt passord", type="password")
                if st.form_submit_button("Oppdater passord", use_container_width=True):
                    if not db.verify_user(user["username"], cur_pw):
                        st.error("Feil nåværende passord.")
                    elif not new_pw1:
                        st.error("Nytt passord kan ikke være tomt.")
                    elif new_pw1 != new_pw2:
                        st.error("Passordene stemmer ikke overens.")
                    elif len(new_pw1) < 6:
                        st.error("Minst 6 tegn.")
                    else:
                        db.change_password(user["id"], new_pw1)
                        st.success("Passord oppdatert.")

        if st.button("🚪  Logg ut", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

def page_dashboard():
    st.markdown(
        """
        <div class="page-hero">
            <p class="hero-eyebrow">FKS Leadsystem</p>
            <h1 class="hero-heading">Oversikt og kontroll for alle familier, barn og oppfølginger.</h1>
            <p class="hero-copy">Få rask innsikt i pipeline, kommende oppfølginger og elevstatus i et moderne og tydelig kontrollpanel.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stats         = db.get_stats()
    status_counts = db.get_status_counts()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Aktive leads",        stats["active_leads"])
    c2.metric("Elever på skolen",    stats["active_students"])
    c3.metric("Familier",            stats["total_families"])
    c4.metric("Sluttet (3 mnd)",     stats["closed_3m"])
    c5.metric(
        "Forfalt oppfølging",
        stats["overdue"],
        delta=f"+{stats['upcoming_7d']} denne uken" if stats["upcoming_7d"] else None,
        delta_color="off",
    )

    st.divider()

    # ── Lead-pipeline (Ny lead → Søkt) ──
    st.subheader("Lead-pipeline")
    pipeline_labels = db.LEAD_PIPELINE_STATUSES
    pipeline_values = [status_counts.get(s, 0) for s in pipeline_labels]
    pipeline_colors = [STATUS_COLORS.get(s, "#ccc") for s in pipeline_labels]
    fig_pipe = go.Figure(go.Bar(
        x=pipeline_labels, y=pipeline_values,
        marker_color=pipeline_colors,
        text=pipeline_values, textposition="outside",
    ))
    fig_pipe.update_layout(
        height=280, margin=dict(t=20, b=10),
        plot_bgcolor="white", yaxis_title="Antall",
        showlegend=False,
    )
    fig_pipe.update_yaxes(gridcolor="#F0F0F0")
    st.plotly_chart(fig_pipe, use_container_width=True)

    st.divider()

    # ── Sluttede elever med tidsfilter ──
    st.subheader("Sluttede elever")
    sf1, sf2 = st.columns(2)
    with sf1:
        slutt_fra = st.date_input("Fra dato", value=None, key="slutt_fra", format="DD.MM.YYYY")
    with sf2:
        slutt_til = st.date_input("Til dato", value=None, key="slutt_til", format="DD.MM.YYYY")

    fra_str = slutt_fra.isoformat() if slutt_fra else None
    til_str = slutt_til.isoformat() if slutt_til else None
    sluttet_list = db.get_sluttet_by_period(fra_str, til_str)
    reasons_period = db.get_sluttet_reason_counts_by_period(fra_str, til_str)

    sr1, sr2 = st.columns(2)
    with sr1:
        st.metric("Sluttet i valgt periode", len(sluttet_list))
        if reasons_period:
            fig_reasons = go.Figure(go.Bar(
                x=list(reasons_period.keys()),
                y=list(reasons_period.values()),
                marker_color=STATUS_COLORS["Sluttet"],
                text=list(reasons_period.values()),
                textposition="outside",
            ))
            fig_reasons.update_layout(
                height=260, margin=dict(t=10, b=10),
                plot_bgcolor="white", yaxis_title="Antall",
                showlegend=False,
            )
            fig_reasons.update_xaxes(tickangle=-20)
            fig_reasons.update_yaxes(gridcolor="#F0F0F0")
            st.plotly_chart(fig_reasons, use_container_width=True)
        else:
            st.info("Ingen sluttede i valgt periode.")

    with sr2:
        if sluttet_list:
            for child in sluttet_list:
                closed = child.get("closed_at", "")[:10] if child.get("closed_at") else "—"
                reason = child.get("close_reason") or "—"
                detail = f" · {child['close_reason_detail']}" if child.get("close_reason_detail") else ""
                st.markdown(
                    f"**{child['name']}** ({child['family_name']})  \n"
                    f"*{reason}{detail}*  ·  {closed}"
                )
                st.markdown('<hr style="margin:4px 0;border-color:#f0f0f0">', unsafe_allow_html=True)

    # Avg days per status
    st.subheader("Gjennomsnittlig dager i hvert steg")
    avg_days = db.get_avg_days_per_status()
    if avg_days:
        fig4 = go.Figure(go.Bar(
            x=list(avg_days.keys()),
            y=list(avg_days.values()),
            marker_color=[STATUS_COLORS.get(s, "#ccc") for s in avg_days.keys()],
            text=[f"{v}d" for v in avg_days.values()],
            textposition="outside",
        ))
        fig4.update_layout(
            height=240, margin=dict(t=10, b=10),
            plot_bgcolor="white", yaxis_title="Dager",
            showlegend=False,
        )
        fig4.update_yaxes(gridcolor="#F0F0F0")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Ingen statushistorikk ennå.")

    st.subheader("Nye leads siste 12 måneder")
    monthly = db.get_monthly_new_leads(12)
    if monthly:
        df = pd.DataFrame(monthly)
        fig3 = px.bar(
            df, x="month", y="count",
            labels={"month": "Måned", "count": "Antall"},
            color_discrete_sequence=[PRIMARY],
        )
        fig3.update_layout(height=240, margin=dict(t=10, b=10), plot_bgcolor="white")
        fig3.update_yaxes(gridcolor="#F0F0F0")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Ingen data ennå.")

    col_ov, col_up = st.columns(2)

    with col_ov:
        st.subheader("⚠️ Forfalt oppfølging")
        overdue = db.get_overdue_followups()
        if overdue:
            for fu in overdue:
                days_ago = (date.today() - date.fromisoformat(fu["next_followup_date"])).days
                if st.button(
                    f"**{fu['child_name']}** — {fu['next_followup_date']} ({days_ago}d siden)",
                    key=f"ov_{fu['id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_child = fu["child_id"]
                    st.session_state.page = "Leads"
                    st.rerun()
        else:
            st.success("Ingen forfalte oppfølginger!")

    with col_up:
        st.subheader("📅 Kommende oppfølginger (7 dager)")
        upcoming = db.get_upcoming_followups()
        if upcoming:
            for fu in upcoming:
                if st.button(
                    f"**{fu['child_name']}** — {fu['next_followup_date']} ({fu['type']})",
                    key=f"up_{fu['id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_child = fu["child_id"]
                    st.session_state.page = "Leads"
                    st.rerun()
        else:
            st.info("Ingen kommende oppfølginger.")


# ── LEADS LIST ────────────────────────────────────────────────────────────────

def page_leads():
    if st.session_state.get("selected_child"):
        page_detail(st.session_state.selected_child)
        return

    st.title("Leads")

    col1, col2 = st.columns([3, 3])
    with col1:
        search = st.text_input("Søk navn (barn eller familie)", placeholder="Søk…")
    with col2:
        status_filter = st.multiselect(
            "Filter på status",
            db.STATUSES,
            default=[s for s in db.STATUSES if s != "Sluttet"],
        )

    families_with_children = db.get_families_with_children()

    # Apply filters
    filtered = []
    s_low = search.lower() if search else ""
    for fam, children in families_with_children:
        filtered_children = children
        if s_low:
            filtered_children = [
                c for c in filtered_children
                if s_low in c["name"].lower() or s_low in fam["display_name"].lower()
            ]
        if status_filter:
            filtered_children = [c for c in filtered_children if c["status"] in status_filter]
        if filtered_children:
            filtered.append((fam, filtered_children))

    total_children = sum(len(ch) for _, ch in filtered)
    st.caption(f"{len(filtered)} familier · {total_children} barn vises")

    if not filtered:
        st.info("Ingen leads funnet.")
        return

    for fam, children in filtered:
        fam_status = family_status_summary(children)
        fam_color  = STATUS_COLORS.get(fam_status, "#999")

        with st.container(border=True):
            # Family header row
            fam_col, del_col = st.columns([7, 1])
            with fam_col:
                guardians = db.get_guardians(fam["id"])
                g_names = "  ·  ".join(f"{g['name']} ({g['relation']})" for g in guardians) if guardians else "—"
                st.markdown(
                    f"### {fam['display_name']} "
                    f'<span class="badge" style="background:{fam_color};font-size:11px">{fam_status}</span>',
                    unsafe_allow_html=True,
                )
                st.caption(f"Foresatte: {g_names}")
            with del_col:
                if st.button("🗑", key=f"del_fam_btn_{fam['id']}", help="Slett familie"):
                    st.session_state[f"confirm_del_fam_{fam['id']}"] = True

            if st.session_state.get(f"confirm_del_fam_{fam['id']}"):
                n_children = len(children)
                st.warning(f"Slett **{fam['display_name']}** og alle {n_children} barn? Dette kan ikke angres.")
                cc1, cc2 = st.columns(2)
                if cc1.button("Bekreft sletting", key=f"conf_del_fam_{fam['id']}", type="primary"):
                    db.delete_family(fam["id"])
                    del st.session_state[f"confirm_del_fam_{fam['id']}"]
                    st.rerun()
                if cc2.button("Avbryt", key=f"cancel_del_fam_{fam['id']}"):
                    del st.session_state[f"confirm_del_fam_{fam['id']}"]
                    st.rerun()

            # Children rows
            for child in children:
                _, grade_label = db.calculate_grade(child["birth_year"])
                follow_ups = db.get_follow_ups(child["id"])
                last_fu   = follow_ups[0] if follow_ups else None
                next_date = next((fu["next_followup_date"] for fu in follow_ups if fu["next_followup_date"]), None)

                cc1, cc2, cc3, cc4 = st.columns([3, 2, 3, 1])
                with cc1:
                    st.markdown(f"**{child['name']}**")
                    st.markdown(badge(child["status"]), unsafe_allow_html=True)
                with cc2:
                    st.markdown(f"**{grade_label}**  ·  f. {child['birth_year']}")
                    if child.get("enrolled_at"):
                        st.caption(f"Startet: {child['enrolled_at']}")
                with cc3:
                    if last_fu:
                        st.caption(f"Siste: {last_fu['created_at'][:10]} — {last_fu['type']} ({last_fu['performed_by_name']})")
                    if next_date:
                        overdue = next_date < date.today().isoformat()
                        icon  = "⚠️" if overdue else "📅"
                        color = "#C0392B" if overdue else "#E07B2B"
                        st.markdown(f'<span style="color:{color};font-size:0.85rem">{icon} Neste: {next_date}</span>', unsafe_allow_html=True)
                with cc4:
                    if st.button("Åpne →", key=f"open_{child['id']}", type="primary"):
                        st.session_state.selected_child = child["id"]
                        st.rerun()

                st.markdown('<hr style="margin:4px 0;border-color:#f0f0f0">', unsafe_allow_html=True)


# ── LEAD DETAIL ───────────────────────────────────────────────────────────────

def page_detail(child_id):
    child = db.get_child(child_id)
    if not child:
        st.error("Fant ikke barnet.")
        st.session_state.selected_child = None
        return

    user = st.session_state.user
    _, grade_label = db.calculate_grade(child["birth_year"])

    if st.button("← Tilbake til leads"):
        st.session_state.selected_child = None
        st.rerun()

    # ── Header ──
    col_h1, col_h2 = st.columns([3, 2])
    with col_h1:
        st.title(child["name"])
        st.markdown(
            f"**Familie:** {child['family_name']}  |  "
            f"**Trinn:** {grade_label}  |  "
            f"**Fødselsår:** {child['birth_year']}"
        )
        st.markdown(badge(child["status"]), unsafe_allow_html=True)
        if child["status"] == "Sluttet" and child.get("close_reason"):
            detail = f" — {child['close_reason_detail']}" if child.get("close_reason_detail") else ""
            st.warning(f"Avsluttet: **{child['close_reason']}**{detail}")
    with col_h2:
        st.markdown(f"**Registrert:** {child['created_at'][:10]}")
        if child.get("enrolled_at"):
            st.markdown(f"**Startet på skolen:** {child['enrolled_at']}")
        if child.get("closed_at"):
            st.markdown(f"**Avsluttet:** {child['closed_at'][:10]}")

    if child.get("note"):
        st.info(child["note"])

    st.divider()

    # ── Pipeline ──
    pipeline_bar(child["status"])
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Status actions ──
    if child["status"] != "Sluttet":
        act1, act2, act3 = st.columns(3)
        with act1:
            idx = db.STATUSES.index(child["status"]) if child["status"] in db.STATUSES else 0
            non_terminal = [s for s in db.STATUSES if s != "Sluttet"]
            if idx < len(non_terminal) - 1:
                next_s = non_terminal[idx + 1]
                if st.button(f"Neste steg: {next_s}", type="primary", use_container_width=True):
                    db.update_child_status(child_id, next_s, user["id"], user["full_name"])
                    st.rerun()
        with act2:
            if child["status"] != "Elev":
                if st.button("✓ Merk som Elev", type="primary", use_container_width=True):
                    db.update_child_status(child_id, "Elev", user["id"], user["full_name"])
                    st.rerun()
        with act3:
            if st.button("Merk som sluttet", use_container_width=True):
                st.session_state[f"closing_{child_id}"] = True

    if st.session_state.get(f"closing_{child_id}"):
        with st.form(f"close_form_{child_id}"):
            st.subheader("Registrer slutt")
            reason = st.selectbox("Årsak til slutt", db.CLOSE_REASONS)
            detail = st.text_area("Utfyllende informasjon (valgfritt)")
            ca, cb = st.columns(2)
            if ca.form_submit_button("Bekreft slutt", type="primary"):
                db.close_child_lead(child_id, reason, detail, user["id"], user["full_name"])
                del st.session_state[f"closing_{child_id}"]
                st.rerun()
            if cb.form_submit_button("Avbryt"):
                del st.session_state[f"closing_{child_id}"]
                st.rerun()

    st.divider()

    tab_fu, tab_info, tab_guardians, tab_siblings = st.tabs(
        ["📋 Oppfølging", "✏️ Barneinformasjon", "👨‍👩‍👧 Foresatte", "👶 Søsken / Familie"]
    )

    # ── TAB: Oppfølging ──────────────────────────────────────────────────────
    with tab_fu:
        st.subheader("Registrer ny oppfølging")
        with st.form(f"fu_form_{child_id}"):
            fc1, fc2 = st.columns([1, 2])
            with fc1:
                fu_type = st.selectbox("Type", db.FOLLOWUP_TYPES)
                fu_next = st.date_input("Neste oppfølgingsdato", value=None, format="DD.MM.YYYY")
            with fc2:
                fu_note = st.text_area("Notat", height=110, placeholder="Hva ble gjort / avtalt?")
            if st.form_submit_button("Lagre oppfølging", type="primary"):
                db.add_follow_up(
                    child_id, fu_type, fu_note, user["id"], user["full_name"],
                    fu_next.isoformat() if fu_next else None,
                )
                st.success("Oppfølging lagret.")
                st.rerun()

        # Status history
        status_log = db.get_status_log(child_id)
        if status_log:
            with st.expander("📌 Statushistorikk", expanded=False):
                for entry in status_log:
                    old = entry["old_status"] or "—"
                    ts  = entry["changed_at"][:16].replace("T", " ")
                    color = STATUS_COLORS.get(entry["new_status"], "#999")
                    st.markdown(
                        f'<div class="status-log-entry">'
                        f'{ts} · <strong style="color:{color}">{entry["new_status"]}</strong>'
                        f' (fra {old}) — {entry["changed_by_name"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.subheader("Oppfølgingslogg")
        follow_ups = db.get_follow_ups(child_id)

        if not follow_ups:
            st.info("Ingen oppfølginger registrert ennå.")
        else:
            for fu in follow_ups:
                with st.container(border=True):
                    lc1, lc2 = st.columns([6, 1])
                    with lc1:
                        ts = fu["created_at"][:16].replace("T", " ")
                        st.markdown(f"**{fu['type']}** · {ts}")
                        st.caption(f"Utført av: {fu['performed_by_name']}")
                        if fu["note"]:
                            st.write(fu["note"])
                        if fu["next_followup_date"]:
                            today_s = date.today().isoformat()
                            overdue = fu["next_followup_date"] < today_s
                            icon  = "⚠️" if overdue else "📅"
                            color = "#C0392B" if overdue else "#2980B9"
                            st.markdown(
                                f'<span style="color:{color}">{icon} Neste oppfølging: <strong>{fu["next_followup_date"]}</strong></span>',
                                unsafe_allow_html=True,
                            )
                    with lc2:
                        can_delete = user["role"] == "admin" or fu["performed_by_id"] == user["id"]
                        if can_delete and st.button("🗑", key=f"del_fu_{fu['id']}", help="Slett"):
                            db.delete_follow_up(fu["id"])
                            st.rerun()

    # ── TAB: Barneinformasjon ────────────────────────────────────────────────
    with tab_info:
        st.subheader("Rediger barneinformasjon")
        with st.form(f"edit_child_{child_id}"):
            new_name = st.text_input("Navn", value=child["name"])
            new_birth = st.number_input(
                "Fødselsår", min_value=2000, max_value=2030, value=child["birth_year"], step=1
            )
            _, gl = db.calculate_grade(new_birth)
            st.info(f"Nåværende trinn: **{gl}** (oppdateres automatisk basert på fødselsår)")

            _editable_statuses = [s for s in db.STATUSES if s != "Sluttet"]
            if child["status"] == "Sluttet":
                st.warning("Barnet er markert som **Sluttet**. Velg en annen status nedenfor for å gjenåpne leaden.")
                new_status = st.selectbox("Gjenåpne med status", _editable_statuses, index=0)
            else:
                new_status = st.selectbox(
                    "Status",
                    _editable_statuses,
                    index=_editable_statuses.index(child["status"]) if child["status"] in _editable_statuses else 0,
                )

            # Enrolled date — only relevant for Elev
            enrolled_val = None
            if child.get("enrolled_at"):
                try:
                    enrolled_val = date.fromisoformat(child["enrolled_at"])
                except Exception:
                    enrolled_val = None
            new_enrolled = st.date_input(
                "Startdato på skolen",
                value=enrolled_val,
                format="DD.MM.YYYY",
                help="Sett dato for når barnet begynte på skolen (relevant for Elev-status)",
            )

            new_note = st.text_area("Notat", value=child.get("note") or "")
            if st.form_submit_button("Lagre endringer", type="primary"):
                db.update_child(child_id, new_name, new_birth, new_status, new_note, user["id"], user["full_name"])
                db.update_enrolled_at(child_id, new_enrolled.isoformat() if new_enrolled else None)
                st.success("Lagret.")
                st.rerun()

        with st.expander("⚠️ Slett barn (permanent)"):
            st.warning("Sletter barnet og all tilhørende historikk. Kan ikke angres.")
            if st.button("Slett barn permanent", key=f"del_child_{child_id}"):
                db.delete_child(child_id)
                st.session_state.selected_child = None
                st.rerun()

    # ── TAB: Foresatte ───────────────────────────────────────────────────────
    with tab_guardians:
        guardians = db.get_guardians(child["family_id"])

        st.subheader("Registrerte foresatte")
        if not guardians:
            st.info("Ingen foresatte registrert.")

        for g in guardians:
            with st.container(border=True):
                gc1, gc2 = st.columns([5, 1])
                with gc1:
                    st.markdown(f"**{g['name']}** — *{g['relation']}*")
                    parts = []
                    if g["phone"]: parts.append(f"📱 {g['phone']}")
                    if g["email"]: parts.append(f"✉️ {g['email']}")
                    if parts:
                        st.markdown("  ·  ".join(parts))
                with gc2:
                    if st.button("Rediger", key=f"edit_g_{g['id']}"):
                        st.session_state["editing_guardian"] = g["id"]
                    if st.button("Slett", key=f"del_g_{g['id']}"):
                        db.delete_guardian(g["id"])
                        st.rerun()

            if st.session_state.get("editing_guardian") == g["id"]:
                with st.form(f"edit_g_form_{g['id']}"):
                    st.markdown(f"**Rediger: {g['name']}**")
                    eg1, eg2 = st.columns(2)
                    with eg1:
                        e_name = st.text_input("Navn", value=g["name"])
                        e_rel_idx = db.RELATIONS.index(g["relation"]) if g["relation"] in db.RELATIONS else 0
                        e_rel = st.selectbox("Relasjon", db.RELATIONS, index=e_rel_idx)
                    with eg2:
                        e_phone = st.text_input("Telefon", value=g["phone"] or "")
                        e_email = st.text_input("E-post", value=g["email"] or "")
                    sa, sb = st.columns(2)
                    if sa.form_submit_button("Lagre", type="primary"):
                        db.update_guardian(g["id"], e_name, e_phone, e_email, e_rel)
                        st.session_state["editing_guardian"] = None
                        st.rerun()
                    if sb.form_submit_button("Avbryt"):
                        st.session_state["editing_guardian"] = None
                        st.rerun()

        st.divider()
        show_g_form_key = f"show_add_guardian_{child['family_id']}"
        if not st.session_state.get(show_g_form_key):
            if st.button("+ Legg til foresatt", key=f"show_g_btn_{child['family_id']}"):
                st.session_state[show_g_form_key] = True
                st.rerun()
        else:
            st.subheader("Legg til foresatt")
            with st.form(f"add_g_form_{child['family_id']}"):
                ag1, ag2 = st.columns(2)
                with ag1:
                    g_name = st.text_input("Navn *")
                    g_rel = st.selectbox("Relasjon", db.RELATIONS)
                with ag2:
                    g_phone = st.text_input("Telefon")
                    g_email = st.text_input("E-post")
                ga, gb = st.columns(2)
                if ga.form_submit_button("Legg til foresatt", type="primary"):
                    if not g_name.strip():
                        st.error("Navn er påkrevd.")
                    else:
                        db.add_guardian(child["family_id"], g_name.strip(), g_phone.strip(), g_email.strip(), g_rel)
                        st.session_state[show_g_form_key] = False
                        st.rerun()
                if gb.form_submit_button("Avbryt"):
                    st.session_state[show_g_form_key] = False
                    st.rerun()

    # ── TAB: Søsken / Familie ────────────────────────────────────────────────
    with tab_siblings:
        siblings = db.get_children_by_family(child["family_id"])

        st.subheader(f"Barn i familie: {child['family_name']}")
        for s in siblings:
            _, s_grade = db.calculate_grade(s["birth_year"])
            with st.container(border=True):
                sc1, sc2 = st.columns([5, 1])
                with sc1:
                    is_current = s["id"] == child_id
                    label = f"**{s['name']}** ← *dette barnet*" if is_current else f"**{s['name']}**"
                    st.markdown(label)
                    st.caption(f"{s_grade}  ·  f. {s['birth_year']}  ·  {s['status']}")
                with sc2:
                    if not is_current:
                        if st.button("Åpne →", key=f"sib_{s['id']}", type="primary"):
                            st.session_state.selected_child = s["id"]
                            st.rerun()

        st.divider()
        show_sib_key = f"show_add_sibling_{child['family_id']}"
        if not st.session_state.get(show_sib_key):
            if st.button("+ Legg til nytt barn i familien", key=f"show_sib_btn_{child['family_id']}"):
                st.session_state[show_sib_key] = True
                st.rerun()
        else:
            st.subheader("Legg til nytt barn i familien")
            with st.form(f"add_sibling_{child['family_id']}"):
                sib_name  = st.text_input("Barnets fulle navn *")
                sib_birth = st.number_input("Fødselsår *", min_value=2000, max_value=2030, step=1, value=2018)
                _, sib_grade = db.calculate_grade(sib_birth)
                st.info(f"Nåværende trinn: **{sib_grade}**")
                sib_note   = st.text_area("Notat", height=70)
                sib_status = st.selectbox("Status", [s for s in db.STATUSES if s != "Sluttet"], index=0)
                sba, sbb = st.columns(2)
                if sba.form_submit_button("Legg til barn", type="primary"):
                    if not sib_name.strip():
                        st.error("Barnets navn er påkrevd.")
                    else:
                        dupes = db.find_duplicate_children(sib_name.strip(), sib_birth)
                        if dupes:
                            st.warning(f"Mulig duplikat: **{dupes[0]['name']}** (f. {dupes[0]['birth_year']}) finnes allerede i familie {dupes[0]['family_name']}. Lagre likevel via knappen nedenfor.")
                            st.session_state[f"pending_sib_{child['family_id']}"] = (sib_name.strip(), sib_birth, sib_status, sib_note.strip())
                        else:
                            db.add_child(child["family_id"], sib_name.strip(), sib_birth, sib_status, sib_note.strip())
                            st.session_state[show_sib_key] = False
                            st.rerun()
                if sbb.form_submit_button("Avbryt"):
                    st.session_state[show_sib_key] = False
                    st.rerun()

            pending_sib = st.session_state.get(f"pending_sib_{child['family_id']}")
            if pending_sib:
                sc1, sc2 = st.columns(2)
                if sc1.button("Lagre likevel", key=f"force_sib_{child['family_id']}", type="primary"):
                    db.add_child(child["family_id"], *pending_sib)
                    del st.session_state[f"pending_sib_{child['family_id']}"]
                    st.session_state[show_sib_key] = False
                    st.rerun()
                if sc2.button("Avbryt", key=f"cancel_sib_{child['family_id']}"):
                    del st.session_state[f"pending_sib_{child['family_id']}"]
                    st.rerun()


# ── NY LEAD ───────────────────────────────────────────────────────────────────

def page_new_lead():
    st.title("Registrer ny lead")

    with st.form("new_lead"):
        st.subheader("1. Familie")
        family_name = st.text_input("Familienavn *", placeholder="F.eks. Familie Hansen")
        family_note = st.text_area("Notat om familien", height=70)

        st.divider()
        st.subheader("2. Barn")
        child_name = st.text_input("Barnets fulle navn *")
        birth_year = st.number_input("Fødselsår *", min_value=2000, max_value=2030, step=1, value=2018)
        _, grade_label = db.calculate_grade(birth_year)
        st.info(f"Nåværende trinn basert på fødselsår: **{grade_label}**")
        child_note = st.text_area("Notat om barnet", height=70)
        status = st.selectbox("Initial status", [s for s in db.STATUSES if s != "Sluttet"], index=0)

        st.divider()
        st.subheader("3. Foresatt #1")
        p1c1, p1c2 = st.columns(2)
        with p1c1:
            g1_name = st.text_input("Navn *", key="g1n")
            g1_rel  = st.selectbox("Relasjon", db.RELATIONS, key="g1r")
        with p1c2:
            g1_phone = st.text_input("Telefon", key="g1p")
            g1_email = st.text_input("E-post", key="g1e")

        st.subheader("3b. Foresatt #2 (valgfritt)")
        add_p2 = st.checkbox("Legg til foresatt #2")
        g2_name = g2_rel = g2_phone = g2_email = ""
        if add_p2:
            p2c1, p2c2 = st.columns(2)
            with p2c1:
                g2_name  = st.text_input("Navn", key="g2n")
                g2_rel   = st.selectbox("Relasjon", db.RELATIONS, key="g2r")
            with p2c2:
                g2_phone = st.text_input("Telefon", key="g2p")
                g2_email = st.text_input("E-post", key="g2e")

        submitted = st.form_submit_button("Registrer lead", type="primary", use_container_width=True)

        if submitted:
            errors = []
            if not family_name.strip(): errors.append("Familienavn mangler.")
            if not child_name.strip():  errors.append("Barnets navn mangler.")
            if not g1_name.strip():     errors.append("Navn på foresatt #1 mangler.")
            for e in errors:
                st.error(e)
            if not errors:
                dupes = db.find_duplicate_children(child_name.strip(), birth_year)
                if dupes and not st.session_state.get("new_lead_force"):
                    st.error(
                        f"⚠️ **Mulig duplikat:** {dupes[0]['name']} (f. {dupes[0]['birth_year']}) "
                        f"er allerede registrert i familie **{dupes[0]['family_name']}** "
                        f"med status **{dupes[0]['status']}**. "
                        f"Scroll ned for å bekrefte eller avbryte."
                    )
                    st.session_state.new_lead_pending = dict(
                        family_name=family_name, family_note=family_note,
                        child_name=child_name, birth_year=birth_year,
                        child_note=child_note, status=status,
                        g1_name=g1_name, g1_phone=g1_phone, g1_email=g1_email, g1_rel=g1_rel,
                        g2_name=g2_name, g2_phone=g2_phone, g2_email=g2_email, g2_rel=g2_rel,
                        add_p2=add_p2,
                    )
                    st.session_state.new_lead_dupes = dupes
                else:
                    st.session_state.pop("new_lead_force", None)
                    st.session_state.pop("new_lead_pending", None)
                    st.session_state.pop("new_lead_dupes", None)
                    user     = st.session_state.user
                    fam_id   = db.add_family(family_name.strip(), family_note.strip())
                    child_id = db.add_child(fam_id, child_name.strip(), birth_year, status, child_note.strip())
                    db.add_guardian(fam_id, g1_name.strip(), g1_phone.strip(), g1_email.strip(), g1_rel)
                    if add_p2 and g2_name.strip():
                        db.add_guardian(fam_id, g2_name.strip(), g2_phone.strip(), g2_email.strip(), g2_rel)
                    db.update_child_status(child_id, status, user["id"], user["full_name"])
                    st.success(f"Lead opprettet for {child_name}!")
                    st.session_state.selected_child = child_id
                    st.session_state.page = "Leads"
                    st.rerun()

    # Duplicate warning shown outside the form
    dupes = st.session_state.get("new_lead_dupes")
    if dupes:
        st.warning("⚠️ Mulig duplikat funnet — finnes allerede i systemet:")
        for d in dupes:
            st.markdown(f"- **{d['name']}** (f. {d['birth_year']}) · Familie: {d['family_name']} · Status: {d['status']}")
        dc1, dc2 = st.columns(2)
        if dc1.button("Registrer likevel", type="primary", key="force_new_lead"):
            st.session_state.new_lead_force = True
            pending = st.session_state.new_lead_pending
            user = st.session_state.user
            fam_id   = db.add_family(pending["family_name"].strip(), pending["family_note"].strip())
            child_id = db.add_child(fam_id, pending["child_name"].strip(), pending["birth_year"], pending["status"], pending["child_note"].strip())
            db.add_guardian(fam_id, pending["g1_name"].strip(), pending["g1_phone"].strip(), pending["g1_email"].strip(), pending["g1_rel"])
            if pending["add_p2"] and pending["g2_name"].strip():
                db.add_guardian(fam_id, pending["g2_name"].strip(), pending["g2_phone"].strip(), pending["g2_email"].strip(), pending["g2_rel"])
            db.update_child_status(child_id, pending["status"], user["id"], user["full_name"])
            for k in ["new_lead_force", "new_lead_pending", "new_lead_dupes"]:
                st.session_state.pop(k, None)
            st.session_state.selected_child = child_id
            st.session_state.page = "Leads"
            st.rerun()
        if dc2.button("Avbryt", key="cancel_new_lead_dupe"):
            for k in ["new_lead_force", "new_lead_pending", "new_lead_dupes"]:
                st.session_state.pop(k, None)
            st.rerun()


# ── ADMIN ─────────────────────────────────────────────────────────────────────

def page_admin():
    if st.session_state.user["role"] != "admin":
        st.error("Ingen tilgang.")
        return

    st.title("Administrasjon")
    user = st.session_state.user

    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["👤 Brukere", "📥 Importer elever", "🔑 Endre passord"])

    # ── Brukere ──────────────────────────────────────────────────────────────
    with admin_tab1:
        st.subheader("Brukere")
        users = db.get_all_users()
        current_uid = user["id"]

        for u in users:
            with st.container(border=True):
                uc1, uc2, uc3 = st.columns([3, 2, 2])
                with uc1:
                    st.markdown(f"**{u['full_name']}**  (`{u['username']}`)")
                    a_color = "#27AE60" if u["active"] else "#C0392B"
                    a_label = "Aktiv" if u["active"] else "Deaktivert"
                    st.markdown(f'<span style="color:{a_color}">● {a_label}</span>', unsafe_allow_html=True)
                with uc2:
                    st.markdown(f"Rolle: **{u['role']}**")
                    st.caption(f"Opprettet: {u['created_at'][:10]}")
                with uc3:
                    if u["id"] != current_uid:
                        label = "Deaktiver" if u["active"] else "Aktiver"
                        if st.button(label, key=f"tog_{u['id']}"):
                            db.toggle_user_active(u["id"])
                            st.rerun()
                        new_role = "admin" if u["role"] == "bruker" else "bruker"
                        if st.button(f"Gjør til {new_role}", key=f"rol_{u['id']}"):
                            db.update_user_role(u["id"], new_role)
                            st.rerun()
                        if st.button("Tilbakestill passord", key=f"reset_pw_btn_{u['id']}"):
                            st.session_state[f"show_reset_pw_{u['id']}"] = True

                if st.session_state.get(f"show_reset_pw_{u['id']}"):
                    with st.form(f"reset_pw_form_{u['id']}"):
                        reset_pw1 = st.text_input("Nytt passord", type="password", key=f"reset_pw1_{u['id']}")
                        reset_pw2 = st.text_input("Bekreft nytt passord", type="password", key=f"reset_pw2_{u['id']}")
                        submit = st.form_submit_button("Lagre nytt passord", type="primary")
                        cancel = st.form_submit_button("Avbryt")

                        if cancel:
                            del st.session_state[f"show_reset_pw_{u['id']}"]
                            st.rerun()
                        if submit:
                            if not reset_pw1:
                                st.error("Passord kan ikke være tomt.")
                            elif reset_pw1 != reset_pw2:
                                st.error("Passordene stemmer ikke overens.")
                            elif len(reset_pw1) < 6:
                                st.error("Passordet må være minst 6 tegn.")
                            else:
                                db.change_password(u["id"], reset_pw1)
                                st.success(f"Passordet til {u['full_name']} er oppdatert.")
                                del st.session_state[f"show_reset_pw_{u['id']}"]
                                st.rerun()

        st.divider()
        st.subheader("Legg til ny bruker")
        with st.form("add_user"):
            ac1, ac2 = st.columns(2)
            with ac1:
                nu_user = st.text_input("Brukernavn")
                nu_name = st.text_input("Fullt navn")
            with ac2:
                nu_pw   = st.text_input("Passord", type="password")
                nu_role = st.selectbox("Rolle", ["bruker", "admin"])
            if st.form_submit_button("Opprett bruker", type="primary"):
                if not all([nu_user.strip(), nu_name.strip(), nu_pw]):
                    st.error("Alle felt er påkrevd.")
                else:
                    try:
                        db.add_user(nu_user.strip(), nu_pw, nu_name.strip(), nu_role)
                        st.success(f"Bruker '{nu_user}' opprettet.")
                        st.rerun()
                    except Exception:
                        st.error("Brukernavnet er allerede i bruk.")

    # ── Import ────────────────────────────────────────────────────────────────
    with admin_tab2:
        st.subheader("Importer elever fra fil")

        with st.expander("📖 Hvordan bygge opp Excel-filen", expanded=False):
            st.markdown("""
**Krav:**
- Første rad må være kolonneoverskrifter (rad 1 = tittelrad, rad 2+ = data)
- Kun én fane/ark brukes (første ark i filen)
- Én rad per barn

**Anbefalte kolonnenavn** (kan hete hva som helst — du kobler dem selv):

| Kolonne | Eksempel | Kommentar |
|---|---|---|
| `Barnets navn` | Ole Hansen | **Påkrevd** |
| `Fødselsår` | 2015 | **Påkrevd** — kun årstall, ikke fødselsdato |
| `Familienavn` | Familie Hansen | Brukes til å gruppere søsken. Samme navn = samme familie |
| `Foresatt navn` | Kari Hansen | Navn på første foresatt |
| `Foresatt relasjon` | Mor | Mor / Far / Stefar / Stemor osv. |
| `Foresatt telefon` | 91234567 | |
| `Foresatt e-post` | kari@epost.no | |
| `Status` | Elev | Må matche eksakt: Ny lead / Kontaktet / Søkt / Elev / Avsluttet osv. |
| `Notat` | Allergisk mot nøtter | Valgfritt notat om barnet |

**Tips for søsken:** Gi begge barna samme familienavn (f.eks. `Familie Hansen`), så havner de i samme familie automatisk.

**Eksempel på oppsett:**
```
Barnets navn | Fødselsår | Familienavn      | Foresatt navn | Foresatt relasjon | Foresatt telefon | Status
Ole Hansen   | 2015      | Familie Hansen   | Kari Hansen   | Mor               | 91234567         | Elev
Anna Hansen  | 2017      | Familie Hansen   | Kari Hansen   | Mor               | 91234567         | Ny lead
Per Olsen    | 2014      | Familie Olsen    | Jon Olsen     | Far               | 98765432         | Søkt
```
            """)

        st.markdown("Last opp en **Excel (.xlsx)** eller **CSV** fil med elevregisteret.")

        uploaded = st.file_uploader("Velg fil", type=["csv", "xlsx"])

        if uploaded:
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded)
            except Exception as e:
                st.error(f"Kunne ikke lese filen: {e}")
                return

            st.markdown(f"**{len(df)} rader lest.** Forhåndsvisning:")
            st.dataframe(df.head(5), use_container_width=True)

            columns = ["(ingen)"] + list(df.columns)

            st.subheader("Koble kolonner til felter")
            st.caption("Velg hvilken kolonne i filen som tilsvarer hvert felt. Kun Barnets navn og Fødselsår er påkrevd.")

            im1, im2 = st.columns(2)
            with im1:
                col_child_name    = st.selectbox("Barnets navn *",     columns, key="imp_cn")
                col_birth_year    = st.selectbox("Fødselsår *",        columns, key="imp_by")
                col_family_name   = st.selectbox("Familienavn",        columns, key="imp_fn")
                col_note          = st.selectbox("Notat",              columns, key="imp_note")
            with im2:
                col_guardian_name = st.selectbox("Foresatt navn",      columns, key="imp_gn")
                col_guardian_rel  = st.selectbox("Foresatt relasjon",  columns, key="imp_gr")
                col_guardian_phone= st.selectbox("Foresatt telefon",   columns, key="imp_gp")
                col_guardian_email= st.selectbox("Foresatt e-post",    columns, key="imp_ge")
                col_status        = st.selectbox("Status",             columns, key="imp_st")

            default_status = st.selectbox("Standard status (brukes hvis statuskolonne mangler/ugyldig)", db.STATUSES, index=0)

            if col_child_name == "(ingen)" or col_birth_year == "(ingen)":
                st.warning("Velg minst Barnets navn og Fødselsår for å importere.")
            else:
                if st.button("Start import", type="primary"):
                    col_map = {
                        "child_name":       col_child_name,
                        "birth_year":       col_birth_year,
                        "family_name":      col_family_name,
                        "note":             col_note,
                        "guardian_name":    col_guardian_name,
                        "guardian_relation":col_guardian_rel,
                        "guardian_phone":   col_guardian_phone,
                        "guardian_email":   col_guardian_email,
                        "status":           col_status,
                    }
                    imported, skipped, errors = db.import_from_df(
                        df, col_map, default_status, user["id"], user["full_name"]
                    )
                    st.success(f"✅ {imported} barn importert, {skipped} hoppet over.")
                    if errors:
                        with st.expander(f"⚠️ {len(errors)} feil under import"):
                            for e in errors:
                                st.caption(e)

    # ── Endre passord ─────────────────────────────────────────────────────────
    with admin_tab3:
        st.subheader("Endre passord")
        users = db.get_all_users()
        user_options = {f"{u['full_name']} ({u['username']})": u["id"] for u in users}
        selected_label = st.selectbox("Velg bruker", list(user_options.keys()))
        selected_uid = user_options[selected_label]

        with st.form("admin_change_pw"):
            new_pw1 = st.text_input("Nytt passord", type="password")
            new_pw2 = st.text_input("Bekreft nytt passord", type="password")
            if st.form_submit_button("Lagre nytt passord", type="primary"):
                if not new_pw1:
                    st.error("Passord kan ikke være tomt.")
                elif new_pw1 != new_pw2:
                    st.error("Passordene stemmer ikke overens.")
                elif len(new_pw1) < 6:
                    st.error("Passordet må være minst 6 tegn.")
                else:
                    db.change_password(selected_uid, new_pw1)
                    st.success(f"Passord oppdatert for {selected_label}.")


# ── ROUTER ────────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.get("logged_in"):
        page_login()
        return

    sidebar()

    page = st.session_state.get("page", "Dashboard")

    if st.session_state.get("selected_child"):
        page_leads()
    elif page == "Dashboard":
        page_dashboard()
    elif page == "Leads":
        page_leads()
    elif page == "Ny lead":
        page_new_lead()
    elif page == "Admin":
        page_admin()


main()
