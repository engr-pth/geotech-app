import io
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

st.set_page_config(page_title="Single Footing Suite", page_icon="🏗️", layout="wide")
st.title("🏗️ Single Footing Design Suite (Enhanced)")

col_in, col_res = st.columns([1.1, 1.1])

with col_in:
    st.header("1. General & Unit System Selection")
    unit_system = st.radio(
        "Unit System",
        [
            "SI Units (m, kN, kPa, mm)",
            "Metric Ton System (m, ton, t/m², mm)",
            "FPS - Kip System (ft, kips, ksf, in)",
        ],
    )

    is_imperial = "FPS" in unit_system
    is_ton = "Ton" in unit_system

    u_len = "ft" if is_imperial else "m"
    u_force = "kips" if is_imperial else ("ton" if is_ton else "kN")
    u_moment = "kip-ft" if is_imperial else ("ton-m" if is_ton else "kN-m")
    u_stress = "ksf" if is_imperial else ("t/m²" if is_ton else "kPa")
    u_gamma = "pcf" if is_imperial else ("t/m³" if is_ton else "kN/m³")
    u_rebar = "in" if is_imperial else "mm"

    st.header("2. Applied Loads & Eccentricity")
    col_p1, col_p2 = st.columns(2)
    P_DL = col_p1.number_input(f"Dead Load P_DL ({u_force})", 0.0, 100000.0, 60.0 if is_imperial else 300.0)
    P_LL = col_p2.number_input(f"Live Load P_LL ({u_force})", 0.0, 100000.0, 40.0 if is_imperial else 200.0)
    P_unfactored = P_DL + P_LL

    col_mx, col_my = st.columns(2)
    Mx_unfactored = col_mx.number_input(f"Moment Mx ({u_moment})", 0.0, 10000.0, 0.0)
    My_unfactored = col_my.number_input(f"Moment My ({u_moment})", 0.0, 10000.0, 0.0)

    st.header("3. Geotechnical Soil Inputs")
    q_allow_input = st.number_input(f"Gross Allowable Soil Capacity q_allow ({u_stress})", 0.1, 10000.0, 3.0 if is_imperial else 150.0)
    gamma_soil = st.number_input(f"Soil Unit Weight γ ({u_gamma})", 0.0, 500.0, 115.0 if is_imperial else 18.0)
    Dw = st.number_input(f"Water Table Depth Dw ({u_len})", 0.0, 50.0, 3.5 if is_imperial else 1.2)

    st.header("4. Footing & Column Geometry")
    col_b, col_l = st.columns(2)
    B = col_b.number_input(f"Footing Width B (X-dir) ({u_len})", 0.5, 50.0, 6.0 if is_imperial else 2.0)
    L = col_l.number_input(f"Footing Length L (Y-dir) ({u_len})", 0.5, 50.0, 6.0 if is_imperial else 2.0)

    col_cx, col_cy = st.columns(2)
    cx = col_cx.number_input(f"Column Size cx ({u_len})", 0.1, 5.0, 1.0 if is_imperial else 0.4)
    cy = col_cy.number_input(f"Column Size cy ({u_len})", 0.1, 5.0, 1.0 if is_imperial else 0.4)

    Df = st.number_input(f"Embedment Depth Df ({u_len})", 0.0, 20.0, 3.5 if is_imperial else 1.2)
    h_foot = st.number_input(f"Footing Thickness h ({u_len})", 0.1, 5.0, 1.5 if is_imperial else 0.45)

    st.header("5. Structural & Rebar Settings")
    u_fc = "psi" if is_imperial else "MPa"
    fc = st.number_input(f"Concrete Strength f'c ({u_fc})", 10.0, 10000.0, 4000.0 if is_imperial else 28.0)
    fy = st.number_input(f"Steel Yield Strength fy ({u_fc})", 100.0, 100000.0, 60000.0 if is_imperial else 420.0)

    if is_imperial:
        rebar_opts = {"#5": {"dia": 0.625, "area": 0.31}, "#6": {"dia": 0.75, "area": 0.44}, "#8": {"dia": 1.0, "area": 0.79}}
    else:
        rebar_opts = {"16 mm": {"dia": 16.0, "area": 201.06}, "20 mm": {"dia": 20.0, "area": 314.16}, "25 mm": {"dia": 25.0, "area": 490.87}}

    selected_bar = st.selectbox("Select Bar Size", list(rebar_opts.keys()))
    hook_type = st.radio("Hook Type", ["90-Degree Standard Hook", "180-Degree Standard Hook", "None"])

    calc_trigger = st.button("🚀 Run Calculations", type="primary", use_container_width=True)

# Calculation Logic
if calc_trigger or "single_footing_calc" in st.session_state:
    st.session_state["single_footing_calc"] = True

    # 1. Soil Pressure Analysis
    q_surcharge = gamma_soil * Df
    q_net_allow = max(0.01, q_allow_input - q_surcharge)
    footing_area = B * L

    q_avg_service = P_unfactored / footing_area
    Mx_total = Mx_unfactored
    My_total = My_unfactored

    q_max_service = q_avg_service + (6 * Mx_total / (B * (L**2))) + (6 * My_total / (L * (B**2)))
    q_min_service = q_avg_service - (6 * Mx_total / (B * (L**2))) - (6 * My_total / (L * (B**2)))

    # 2. Structural Shears & Flexure
    Pu = (1.2 * P_DL) + (1.6 * P_LL)
    qu_factored = Pu / footing_area

    cover = (3.0 / 12.0) if is_imperial else 0.075
    d_eff = h_foot - cover

    # X-direction Critical Moment & Rebar
    cantilever_x = (B - cx) / 2.0
    Mu_x = (qu_factored * L * (cantilever_x**2)) / 2.0

    # Y-direction Critical Moment & Rebar
    cantilever_y = (L - cy) / 2.0
    Mu_y = (qu_factored * B * (cantilever_y**2)) / 2.0

    if is_imperial:
        # X-Direction Rebar Area (in2)
        Mu_x_inlbs = Mu_x * 12000.0
        Rn_x = Mu_x_inlbs / (0.9 * (L * 12.0) * ((d_eff * 12.0) ** 2))
        rho_x = (0.85 * fc / fy) * (1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn_x) / (0.85 * fc))))
        As_x_req = max(rho_x, 0.0018) * (L * 12.0) * (d_eff * 12.0)

        # Y-Direction Rebar Area (in2)
        Mu_y_inlbs = Mu_y * 12000.0
        Rn_y = Mu_y_inlbs / (0.9 * (B * 12.0) * ((d_eff * 12.0) ** 2))
        rho_y = (0.85 * fc / fy) * (1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn_y) / (0.85 * fc))))
        As_y_req = max(rho_y, 0.0018) * (B * 12.0) * (d_eff * 12.0)

        bar_area = rebar_opts[selected_bar]["area"]
    else:
        # Metric Area (mm2)
        Mu_x_Nmm = Mu_x * 1e6
        Rn_x = Mu_x_Nmm / (0.9 * (L * 1000.0) * ((d_eff * 1000.0) ** 2))
        rho_x = (0.85 * fc / fy) * (1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn_x) / (0.85 * fc))))
        As_x_req = max(rho_x, 0.0018) * (L * 1000.0) * (d_eff * 1000.0)

        Mu_y_Nmm = Mu_y * 1e6
        Rn_y = Mu_y_Nmm / (0.9 * (B * 1000.0) * ((d_eff * 1000.0) ** 2))
        rho_y = (0.85 * fc / fy) * (1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn_y) / (0.85 * fc))))
        As_y_req = max(rho_y, 0.0018) * (B * 1000.0) * (d_eff * 1000.0)

        bar_area = rebar_opts[selected_bar]["area"]

    # Rebar Count & Spacing
    nbars_x = max(2, int(np.ceil(As_x_req / bar_area)))
    nbars_y = max(2, int(np.ceil(As_y_req / bar_area)))

    sp_x = ((L * 12.0) - 6.0) / (nbars_x - 1) if is_imperial else ((L * 1000.0) - 150.0) / (nbars_x - 1)
    sp_y = ((B * 12.0) - 6.0) / (nbars_y - 1) if is_imperial else ((B * 1000.0) - 150.0) / (nbars_y - 1)

    # Drawing Utilities
    def generate_plan_view():
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.add_patch(patches.Rectangle((-B / 2, -L / 2), B, L, facecolor="#E5E7EB", edgecolor="black", linewidth=2.0))
        ax.add_patch(patches.Rectangle((-cx / 2, -cy / 2), cx, cy, facecolor="#374151", edgecolor="black", linewidth=1.5))

        # Rebar In X-Direction (Parallel to B, Spaced along L)
        y_locs_x = np.linspace(-L / 2 + cover, L / 2 - cover, nbars_x)
        for y_pos in y_locs_x:
            ax.plot([-B / 2 + cover, B / 2 - cover], [y_pos, y_pos], color="red", linewidth=1.2, zorder=3)

        # Rebar In Y-Direction (Parallel to L, Spaced along B)
        x_locs_y = np.linspace(-B / 2 + cover, B / 2 - cover, nbars_y)
        for x_pos in x_locs_y:
            ax.plot([x_pos, x_pos], [-L / 2 + cover, L / 2 - cover], color="blue", linestyle="--", linewidth=1.2, zorder=3)

        # Dimensions & Annotations
        ax.annotate("", xy=(-B / 2, L / 2 + 0.3), xytext=(B / 2, L / 2 + 0.3), arrowprops=dict(arrowstyle="<->", color="black"))
        ax.text(0, L / 2 + 0.45, f"B = {B} {u_len}", ha="center", fontweight="bold")

        ax.annotate("", xy=(B / 2 + 0.3, -L / 2), xytext=(B / 2 + 0.3, L / 2), arrowprops=dict(arrowstyle="<->", color="black"))
        ax.text(B / 2 + 0.45, 0, f"L = {L} {u_len}", va="center", rotation=-90, fontweight="bold")

        ax.text(0, 0, f"Col\n{cx}x{cy}", color="white", ha="center", va="center", fontsize=8)

        ax.set_xlim(-B / 2 - 1.0, B / 2 + 1.2)
        ax.set_ylim(-L / 2 - 1.0, L / 2 + 1.2)
        ax.set_aspect("equal")
        ax.axis("off")
        plt.title(f"Plan Top View\nX-Dir: {nbars_x} Nos {selected_bar} | Y-Dir: {nbars_y} Nos {selected_bar}", fontsize=9, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    def generate_sec_view():
        fig, ax = plt.subplots(figsize=(6.5, 4))
        f_bottom = -Df - h_foot
        ax.add_patch(patches.Rectangle((-B / 2, f_bottom), B, h_foot, facecolor="#9CA3AF", edgecolor="black", linewidth=1.5))
        ax.add_patch(patches.Rectangle((-cx / 2, -Df), cx, Df + 0.3, facecolor="#4B5563", edgecolor="black", linewidth=1.5))

        # Ground & Water Table Lines
        ax.axhline(0, color="brown", linestyle="-", linewidth=1.5, label="Ground Level")
        ax.axhline(-Dw, color="cyan", linestyle="--", linewidth=2.0, label=f"Water Table (Dw={Dw} {u_len})")

        # Rebar
        ry = f_bottom + cover
        lx, rx = -B / 2 + cover, B / 2 - cover
        ax.plot([lx, rx], [ry, ry], color="red", linewidth=2.0, label=f"X-Dir Rebar ({nbars_x} Nos)")

        if "90-Degree" in hook_type:
            ax.plot([lx, lx], [ry, ry + 0.2], color="red", linewidth=2.0)
            ax.plot([rx, rx], [ry, ry + 0.2], color="red", linewidth=2.0)
        elif "180-Degree" in hook_type:
            ax.plot([lx, lx], [ry, ry + 0.2], color="red", linewidth=2.0)
            ax.plot([lx, lx + 0.03], [ry + 0.2, ry + 0.2], color="red", linewidth=2.0)
            ax.plot([lx + 0.03, lx + 0.03], [ry + 0.2, ry + 0.05], color="red", linewidth=2.0)

            ax.plot([rx, rx], [ry, ry + 0.2], color="red", linewidth=2.0)
            ax.plot([rx, rx - 0.03], [ry + 0.2, ry + 0.2], color="red", linewidth=2.0)
            ax.plot([rx - 0.03, rx - 0.03], [ry + 0.2, ry + 0.05], color="red", linewidth=2.0)

        # Transverse Dots
        dot_xs = np.linspace(lx + 0.05, rx - 0.05, nbars_y)
        ax.scatter(dot_xs, [ry + 0.03] * nbars_y, color="blue", s=15, zorder=5, label=f"Y-Dir Rebar ({nbars_y} Nos)")

        ax.set_xlim(-B / 2 - 0.8, B / 2 + 0.8)
        ax.set_ylim(f_bottom - 0.5, 0.6)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.legend(loc="upper right", fontsize=7)
        plt.title("Elevation Section View", fontsize=9, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    plan_img_buf = generate_plan_view()
    sec_img_buf = generate_sec_view()

    # Generate PDF Function
    def generate_pdf_report():
        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=16, leading=20, textColor=colors.HexColor("#1E3A8A"))
        h2_style = ParagraphStyle("H2Style", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#1F2937"))
        body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=9, leading=12)

        story.append(Paragraph("Single Footing Structural Design Calculation Report", title_style))
        story.append(Spacer(1, 10))

        # Data Summary Table
        table_data = [
            ["Parameter", "Value", "Parameter", "Value"],
            ["Unfactored P_DL", f"{P_DL} {u_force}", "Unfactored P_LL", f"{P_LL} {u_force}"],
            ["Footing Size (BxL)", f"{B} x {L} {u_len}", "Thickness h", f"{h_foot} {u_len}"],
            ["Column Size (cx x cy)", f"{cx} x {cy} {u_len}", "Embedment Df", f"{Df} {u_len}"],
            ["Gross Soil Capacity", f"{q_allow_input} {u_stress}", "Net Allowable", f"{q_net_allow:.2f} {u_stress}"],
        ]
        t = Table(table_data, colWidths=[130, 120, 130, 120])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Step-by-Step Design Calculations:", h2_style))
        calc_steps = f"""
        <b>Step 1: Soil Pressure Verification</b><br/>
        • Service Axial Load P = {P_unfactored:.2f} {u_force}<br/>
        • Actual Max Soil Pressure q_max = {q_max_service:.2f} {u_stress} vs Allowable Net = {q_net_allow:.2f} {u_stress}<br/>
        • Status: {"SAFE" if q_max_service <= q_net_allow else "OVERLOADED"}<br/><br/>
        <b>Step 2: Factored Load & Flexural Design</b><br/>
        • Factored Axial Load Pu = 1.2({P_DL}) + 1.6({P_LL}) = {Pu:.2f} {u_force}<br/>
        • Factored Soil Pressure qu = {qu_factored:.2f} {u_stress}<br/>
        • Required As (X-Direction) = {As_x_req:.2f} | Provided = {nbars_x} Nos {selected_bar} @ {sp_x:.1f} {u_rebar} c/c<br/>
        • Required As (Y-Direction) = {As_y_req:.2f} | Provided = {nbars_y} Nos {selected_bar} @ {sp_y:.1f} {u_rebar} c/c<br/>
        """
        story.append(Paragraph(calc_steps, body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("Reinforcement Drawings:", h2_style))
        img_p = RLImage(plan_img_buf, width=240, height=240)
        img_s = RLImage(sec_img_buf, width=260, height=160)
        img_table = Table([[img_p, img_s]], colWidths=[250, 270])
        story.append(img_table)

        doc.build(story)
        pdf_buf.seek(0)
        return pdf_buf

    # Display Results In Streamlit UI
    with col_res:
        st.header("📊 Design Check Summary")

        st.subheader("1. Soil Bearing Pressure Check")
        st.metric("Service Max Pressure (q_max)", f"{q_max_service:.2f} {u_stress}", delta="✅ OK" if q_max_service <= q_net_allow else "❌ OVERLOADED")
        st.caption(f"Net Allowable Capacity = {q_net_allow:.2f} {u_stress} (Subtracted Soil Surcharge {q_surcharge:.2f} {u_stress})")

        st.subheader("2. Rebar Requirements (Exact Counts)")
        r1, r2 = st.columns(2)
        r1.metric("X-Direction Rebar", f"{nbars_x} Nos - {selected_bar}", f"@ {sp_x:.1f} {u_rebar} c/c")
        r2.metric("Y-Direction Rebar", f"{nbars_y} Nos - {selected_bar}", f"@ {sp_y:.1f} {u_rebar} c/c")

        st.image(plan_img_buf, caption="Plan Top View with Dimensions and Exact Rebar Setup")
        st.image(sec_img_buf, caption="Section View showing Water Table Depth")

        pdf_bytes = generate_pdf_report()
        st.download_button(
            label="📄 Download Full Step-by-Step Calculation PDF Report",
            data=pdf_bytes,
            file_name="Single_Footing_Design_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
