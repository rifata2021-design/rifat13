import streamlit as st
import pandas as pd
import math
import ipaddress as ipa
import matplotlib.pyplot as plt
import os

# --- Display names & guide image path ---
STUDENT_NAMES = "Ryan and Rifat"
GUIDE_NAME    = "Dr Swaminathan Annadurai"
GUIDE_IMAGE_PATH = "guide_image.png"   # put your image in the repo root

st.set_page_config(page_title="CIDR Subnet & Supernet Project", layout="wide")

# =================== Styles ===================
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background-color:#0b1020; color:#e5e7eb; }
section[data-testid="stSidebar"] { background:#0b1020; border-right:1px solid #233046; }
.header-banner { background:#0e152b; border:1px solid #233046; border-radius:16px; padding:14px 18px; }
.big-title { font-size:28px; font-weight:800; color:#f9fafb; letter-spacing:.2px; }
.sub-title { font-size:14px; color:#cbd5e1; }
.section-title { font-size:18px; font-weight:700; color:#f8fafc; margin-top:8px; }
div.stButton > button { width:100%; background:#1f2937; color:#e5e7eb; border:1px solid #334155; border-radius:10px; }
div.stButton > button:hover { background:#334155; border-color:#475569; }
.card { background:linear-gradient(135deg,#0b1020 0%, #111827 55%, #0b1020 100%); border:1px solid #233046;
        border-radius:14px; padding:14px 16px; }
[data-testid="stDataFrame"] { border:1px solid #233046; border-radius:10px; background:#0b1020; }
input, textarea, .stSelectbox, .stNumberInput { color-scheme: dark; }
</style>
""", unsafe_allow_html=True)

# =================== Helpers ===================
def ip_int_to_dotted(n: int) -> str:
    return ".".join(str((n >> (8*i)) & 255) for i in [3,2,1,0])

def usable_host_count(prefix: int) -> int:
    if prefix == 31: return 2
    if prefix == 32: return 1
    return max(0, (2**(32-prefix)) - 2)

def first_last_usable(nw: int, bc: int, prefix: int):
    if prefix == 32: return (nw, nw)
    if prefix == 31: return (nw, bc)
    if bc - nw + 1 < 3: return (None, None)
    return (nw+1, bc-1)

def visualize_subnets(new_prefix: int, count: int):
    fig, ax = plt.subplots(figsize=(10,1.2))
    ax.set_facecolor("#0b1020"); fig.patch.set_facecolor("#0b1020")
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
    if count <= 0: return fig
    width = 1.0 / count
    for i in range(count):
        ax.add_patch(plt.Rectangle((i*width, 0.1), width-0.002, 0.8,
                                   edgecolor="#22d3ee", facecolor="#172036"))
        ax.text(i*width + width/2, 0.5, f"{i+1}", ha='center', va='center',
                fontsize=9, color="#e5e7eb")
    ax.set_title(f"Subnet Visualization: /{new_prefix} (×{count})", pad=8, color="#cbd5e1")
    return fig

# =================== Sidebar ===================
with st.sidebar:
    st.markdown("### 📘 Project Guide")
    if os.path.exists(GUIDE_IMAGE_PATH):
        try:
            st.image(GUIDE_IMAGE_PATH, use_column_width=True)
        except Exception as e:
            st.warning(f"Guide image error: {e}")
    else:
        st.info("guide_image.png not found. Add one to the repo root to show it here.")
    st.write(f"**{GUIDE_NAME}**")
    st.write(f"**Developed by {STUDENT_NAMES}**")
    st.divider()
    st.write("**Prefix vs Usable Hosts**")
    pref_data = [{"Prefix": f"/{p}", "Usable hosts": usable_host_count(p)} for p in range(24, 31)]
    st.dataframe(pd.DataFrame(pref_data), use_container_width=True)

# =================== Header ===================
st.markdown('<div class="header-banner">', unsafe_allow_html=True)
c0, c1, c2 = st.columns([3.8, 1.1, 1.1])
with c0:
    st.markdown('<div class="big-title">CIDR Subnet & Supernet Project</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Subnetting (equal, VLSM, hierarchical) and supernetting with clean tables & visuals.</div>', unsafe_allow_html=True)
with c1:
    learn = st.button("How it works", key="learn", help="Basic primer for the UI")
with c2:
    helpb = st.button("Quick tips", key="help", help="Steps to use the app")
st.markdown('</div>', unsafe_allow_html=True)
if learn:
    st.info("Enter base IP/prefix → choose split mode → run. See steps/tips under the results.")
if helpb:
    st.warning("Use VLSM for different host needs; Level-2 split is hierarchical; watch Remaining/Lagging columns.")
st.markdown("<br>", unsafe_allow_html=True)

# =================== Tabs ===================
tab1, tab2 = st.tabs(["📌 Subnet Planner", "🌐 Supernetting"])

# ===== TAB 1: SUBNET PLANNER =====
with tab1:
    st.markdown('<div class="section-title">User Input (Subnet Planner)</div>', unsafe_allow_html=True)
    st.markdown("<div class='card'>1.1 IP address • 1.2 Prefix length • 2. Number of networks</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.3, 1, 1])
    with col1:
        ip_text = st.text_input("1.1 IP Address (dotted decimal)", value="192.168.10.0")
    with col2:
        net_bits = st.number_input("1.2 Prefix length (bits for network)", min_value=0, max_value=32, value=24, step=1)
    with col3:
        num_networks = st.number_input("2. Number of networks", min_value=1, value=4, step=1)

    st.write("**Split Mode**")
    split_mode = st.radio(
        "Choose how to split",
        ["Split equally", "Split by addresses (VLSM)", "Hierarchical split (two-level)"],
        index=0, horizontal=True, label_visibility="collapsed"
    )

    host_list_text = ""
    level2_host_text = ""
    if split_mode == "Split by addresses (VLSM)":
        host_list_text = st.text_input("Usable hosts per subnet (comma-separated)", value="50, 20, 10")
    elif split_mode == "Hierarchical split (two-level)":
        st.markdown("<div class='card'>Base block split equally; then <b>Network #1</b> is split by host needs.</div>", unsafe_allow_html=True)
        level2_host_text = st.text_input("Level-2 usable hosts inside Network #1", value="50, 30, 10")

    go = st.button("Run Subnet Planner", type="primary")
    if go:
        try:
            base_net = ipa.IPv4Network(f"{ip_text.strip()}/{int(net_bits)}", strict=False)
            base_net_int = int(base_net.network_address)
            base_bc_int  = int(base_net.broadcast_address)
            base_block_size = base_bc_int - base_net_int + 1

            rows_main, rows_level2, steps = [], [], []
            steps.append(f"1️⃣ Base: {base_net.network_address}/{int(net_bits)}")
            steps.append(f"   • Range: {base_net.network_address} – {base_net.broadcast_address}")
            steps.append(f"   • Total: {base_block_size}")

            # --- Equal split ---
            if split_mode == "Split equally":
                N = int(num_networks)
                if N <= 0:
                    st.error("Number of networks must be ≥ 1.")
                else:
                    bits_needed = math.ceil(math.log2(N))
                    new_prefix = int(net_bits) + bits_needed
                    if new_prefix > 32:
                        st.error("Too many equal networks for this base block.")
                    else:
                        child_block_size = 2**(32 - new_prefix)
                        steps += [
                            "2️⃣ Equal Split",
                            f"   • N: {N}",
                            f"   • Bits borrowed: {bits_needed}",
                            f"   • Child prefix: /{new_prefix}",
                            f"   • Child block: {child_block_size} addrs",
                        ]
                        for i in range(N):
                            nw = base_net_int + i*child_block_size
                            bc = nw + child_block_size - 1
                            if bc > base_bc_int: break
                            f, l = first_last_usable(nw, bc, new_prefix)
                            usable_addr = usable_host_count(new_prefix)
                            rows_main.append({
                                "Network ID": ip_int_to_dotted(nw),
                                "First address": "-" if f is None else ip_int_to_dotted(f),
                                "Last address": "-" if l is None else ip_int_to_dotted(l),
                                "Broadcast address": ip_int_to_dotted(bc),
                                "Total address": child_block_size,
                                "Usable address": usable_addr,
                                "Allocated address": usable_addr,
                                "Remaining address": child_block_size - usable_addr,
                                "Lagging address": child_block_size - usable_addr,
                            })

            # --- VLSM ---
            elif split_mode == "Split by addresses (VLSM)":
                if not host_list_text.strip():
                    st.error("Enter at least one host requirement.")
                else:
                    host_reqs = [int(x.strip()) for x in host_list_text.split(",") if x.strip()]
                    steps += ["2️⃣ VLSM", f"   • Hosts: {host_reqs}"]
                    cur = base_net_int
                    for idx, h in enumerate(host_reqs, start=1):
                        if h <= 0:
                            st.error(f"Host requirement #{idx} must be positive."); break
                        needed = h + 2 if h > 2 else h
                        host_bits = math.ceil(math.log2(needed))
                        pre = 32 - host_bits
                        block_size = 2**(32 - pre)
                        align_start = ((cur + block_size - 1) // block_size) * block_size
                        nw = align_start; bc = nw + block_size - 1
                        if bc > base_bc_int:
                            st.error("Requirements do not fit inside base block."); break
                        f, l = first_last_usable(nw, bc, pre)
                        usable_addr = usable_host_count(pre)
                        rows_main.append({
                            "Network ID": ip_int_to_dotted(nw),
                            "First address": "-" if f is None else ip_int_to_dotted(f),
                            "Last address": "-" if l is None else ip_int_to_dotted(l),
                            "Broadcast address": ip_int_to_dotted(bc),
                            "Total address": block_size,
                            "Usable address": usable_addr,
                            "Allocated address": min(h, usable_addr),
                            "Remaining address": max(0, usable_addr - min(h, usable_addr)),
                            "Lagging address": block_size - h,
                        })
                        cur = bc + 1

            # --- Hierarchical (two-level) ---
            else:
                N = int(num_networks)
                if N <= 0:
                    st.error("Number of networks must be ≥ 1.")
                else:
                    bits_needed = math.ceil(math.log2(N))
                    new_prefix = int(net_bits) + bits_needed
                    if new_prefix > 32:
                        st.error("Too many equal networks for this base block.")
                    else:
                        child_block_size = 2**(32 - new_prefix)
                        steps += ["2️⃣ Hierarchical L1", f"   • {N} nets of /{new_prefix}"]
                        for i in range(N):
                            nw = base_net_int + i*child_block_size
                            bc = nw + child_block_size - 1
                            if bc > base_bc_int: break
                            f, l = first_last_usable(nw, bc, new_prefix)
                            usable_addr = usable_host_count(new_prefix)
                            rows_main.append({
                                "Network ID": ip_int_to_dotted(nw),
                                "First address": "-" if f is None else ip_int_to_dotted(f),
                                "Last address": "-" if l is None else ip_int_to_dotted(l),
                                "Broadcast address": ip_int_to_dotted(bc),
                                "Total address": child_block_size,
                                "Usable address": usable_addr,
                                "Allocated address": usable_addr,
                                "Remaining address": child_block_size - usable_addr,
                                "Lagging address": child_block_size - usable_addr,
                            })
                        steps.append("3️⃣ Hierarchical L2 (inside Network #1)")
                        if level2_host_text.strip() and len(rows_main) > 0:
                            first_net_ip = rows_main[0]["Network ID"]
                            first_net = ipa.IPv4Network(f"{first_net_ip}/{new_prefix}", strict=False)
                            lvl2_base, lvl2_bc = int(first_net.network_address), int(first_net.broadcast_address)
                            lvl2_hosts = [int(x.strip()) for x in level2_host_text.split(",") if x.strip()]
                            steps.append(f"   • L2 hosts: {lvl2_hosts}")
                            cur = lvl2_base
                            rows_level2_local = []
                            for idx, h in enumerate(lvl2_hosts, start=1):
                                if h <= 0:
                                    st.error(f"L2 host requirement #{idx} must be positive."); break
                                needed = h + 2 if h > 2 else h
                                host_bits = math.ceil(math.log2(needed))
                                pre = 32 - host_bits; block_size = 2**(32 - pre)
                                align_start = ((cur + block_size - 1) // block_size) * block_size
                                nw = align_start; bc = nw + block_size - 1
                                if bc > lvl2_bc:
                                    st.error("L2 requirements do not fit inside Network #1."); break
                                f, l = first_last_usable(nw, bc, pre)
                                usable_addr = usable_host_count(pre)
                                rows_level2_local.append({
                                    "Network ID": ip_int_to_dotted(nw),
                                    "First address": "-" if f is None else ip_int_to_dotted(f),
                                    "Last address": "-" if l is None else ip_int_to_dotted(l),
                                    "Broadcast address": ip_int_to_dotted(bc),
                                    "Total address": block_size,
                                    "Usable address": usable_addr,
                                    "Allocated address": min(h, usable_addr),
                                    "Remaining address": max(0, usable_addr - min(h, usable_addr)),
                                    "Lagging address": block_size - h,
                                })
                                cur = bc + 1
                            if rows_level2_local:
                                rows_level2.extend(rows_level2_local)

            # ---- Output tables + tips ----
            tips = [
                "• Use VLSM when subnets need different sizes.",
                "• Level-2 split = hierarchical subnetting for one branch.",
                "• 'Remaining' vs 'Lagging' help judge address efficiency.",
            ]

            if len(rows_main) > 0:
                st.markdown('<div class="section-title">Primary Subnet Plan</div>', unsafe_allow_html=True)
                df_main = pd.DataFrame(rows_main)[[
                    "Network ID","First address","Last address","Broadcast address",
                    "Total address","Usable address","Allocated address","Remaining address","Lagging address",
                ]]
                st.dataframe(df_main, use_container_width=True)

                colA, colB = st.columns([1,1])
                with colA:
                    st.markdown("**Steps**")
                    st.text_area("steps", "\n".join(steps), height=240, label_visibility="collapsed")
                with colB:
                    try:
                        child_prefix = int(net_bits)
                        if split_mode in ["Split equally", "Hierarchical split (two-level)"]:
                            child_prefix = int(net_bits) + math.ceil(math.log2(int(num_networks)))
                        fig = visualize_subnets(child_prefix, len(df_main))
                        st.pyplot(fig)
                    except Exception:
                        pass
                    st.info("\n".join(tips))

            if len(rows_level2) > 0:
                st.markdown('<div class="section-title">Level-2 Split inside Network #1</div>', unsafe_allow_html=True)
                df_lvl2 = pd.DataFrame(rows_level2)[[
                    "Network ID","First address","Last address","Broadcast address",
                    "Total address","Usable address","Allocated address","Remaining address","Lagging address",
                ]]
                st.dataframe(df_lvl2, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")

# ===== TAB 2: SUPERNETTING =====
with tab2:
    st.markdown('<div class="section-title">Supernetting (CIDR Aggregation)</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class='card'>Enter multiple CIDR blocks. The tool finds a common supernet that aggregates them "
        "and shows how many routing entries are reduced.</div>",
        unsafe_allow_html=True,
    )

    nets_text = st.text_area(
        "CIDR blocks (comma or newline)",
        value="192.168.10.0/26, 192.168.10.64/26\n192.168.10.128/26"
    )

    if st.button("Run Supernetting", type="primary", key="supernet"):
        try:
            raw = [p.strip() for p in nets_text.replace("\\n",",").split(",") if p.strip()]
            nets = []
            for item in raw:
                if "/" not in item:
                    st.error(f"Missing /prefix in '{item}'."); st.stop()
                nets.append(ipa.IPv4Network(item, strict=False))

            nets.sort(key=lambda n: int(n.network_address))
            min_addr = int(nets[0].network_address)
            max_bc   = max(int(n.broadcast_address) for n in nets)

            def prefix_to_mask_local(prefix: int) -> int:
                return (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF

            agg_prefix = 32
            while agg_prefix >= 0:
                mask = prefix_to_mask_local(agg_prefix)
                agg_net = min_addr & mask
                agg_bc  = agg_net | (~mask & 0xFFFFFFFF)
                if agg_bc >= max_bc and agg_net <= min_addr:
                    break
                agg_prefix -= 1

            def ip_int_to_dotted_local(n: int) -> str:
                return ".".join(str((n >> (8*i)) & 255) for i in [3,2,1,0])

            agg_net_ip = ip_int_to_dotted_local(agg_net)
            agg_bc_ip  = ip_int_to_dotted_local(agg_bc)

            rows = []
            for i, n in enumerate(nets, start=1):
                total_addr = int(n.broadcast_address) - int(n.network_address) + 1
                usable_addr = usable_host_count(n.prefixlen)
                rows.append({
                    "Input #": i,
                    "Network ID": str(n.network_address),
                    "Broadcast address": str(n.broadcast_address),
                    "Prefix": f"/{n.prefixlen}",
                    "Total address": total_addr,
                    "Usable address": usable_addr,
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

            st.markdown(
                f"**Supernet:** `{agg_net_ip}/{agg_prefix}`  \n"
                f"**Range:** `{agg_net_ip} – {agg_bc_ip}`  \n"
                f"**Original entries:** `{len(nets)}` → After supernetting: `1`  \n"
                f"**Routing table reduction:** `{len(nets)-1}` entries"
            )

        except Exception as e:
            st.error(f"Error: {e}")
