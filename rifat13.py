# ================= STREAMLIT-CLOUD PACKAGER =================
# This cell prepares a repo for Streamlit Cloud: writes app.py, requirements.txt, .streamlit/config.toml,
# and guarantees guide_image.png exists (picked or generated). Optional: push to your GitHub repo.

# 0) Minimal installs just to run image utilities here (Streamlit Cloud will install its own on deploy)
!pip -q install pillow >/dev/null

import os, glob, subprocess, json, textwrap
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

# ---------- A) Ensure a valid guide image ----------
def pick_best_local_image():
    pats = ["guide_image.*", "*.png","*.jpg","*.jpeg","*.PNG","*.JPG","*.JPEG","WhatsApp*.*","whatsapp*.*"]
    seen, files = set(), []
    for p in pats:
        for f in glob.glob(p):
            if os.path.isfile(f) and os.path.getsize(f) > 0 and f not in seen:
                files.append(f); seen.add(f)
    if not files: return None
    files.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return files[0]

def build_banner(path="guide_image.png"):
    W, H = 960, 420
    img = Image.new("RGB", (W, H), (11,16,32))
    d = ImageDraw.Draw(img)
    def center(text, y, size, color):
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except:
            font = ImageFont.load_default()
        bbox = d.textbbox((0,0), text, font=font)
        w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        d.text(((W-w)//2, y), text, fill=color, font=font)
    center("Project Guide", 110, 48, (248,250,252))
    center("Dr Swaminathan Annadurai", 180, 30, (229,231,235))
    center("Network Design • CIDR • VLSM • Supernetting", 235, 22, (156,163,175))
    img.save(path, "PNG", optimize=True)

def ensure_guide_image():
    if os.path.exists("guide_image.png"):
        try: os.remove("guide_image.png")
        except: pass
    src = pick_best_local_image()
    if src:
        try:
            img = Image.open(src).convert("RGB")
            img.thumbnail((900,900))
            img.save("guide_image.png", "PNG", optimize=True)
            print(f"✅ Using '{src}' → saved as guide_image.png")
            return
        except (UnidentifiedImageError, OSError) as e:
            print(f"⚠️ Could not read '{src}': {e}")
    build_banner("guide_image.png")
    print("ℹ️ Generated banner guide_image.png")

ensure_guide_image()

# ---------- B) Write Streamlit app ----------
APP_CODE = r'''
import streamlit as st
import pandas as pd
import math
import ipaddress as ipa
import matplotlib.pyplot as plt
import os

STUDENT_NAMES = "Ryan and Rifat"
GUIDE_NAME    = "Dr Swaminathan Annadurai"
GUIDE_IMAGE_PATH = "guide_image.png"

st.set_page_config(page_title="CIDR Subnet & Supernet Project", layout="wide")

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

def ip_int_to_dotted(n:int)->str:
    return ".".join(str((n>>(8*i))&255) for i in [3,2,1,0])

def usable_host_count(prefix:int)->int:
    if prefix==31: return 2
    if prefix==32: return 1
    return max(0,(2**(32-prefix))-2)

def first_last_usable(nw:int, bc:int, prefix:int):
    if prefix==32: return (nw,nw)
    if prefix==31: return (nw,bc)
    if bc-nw+1<3:  return (None,None)
    return (nw+1, bc-1)

def visualize_subnets(new_prefix:int, count:int):
    fig, ax = plt.subplots(figsize=(10,1.2))
    ax.set_facecolor("#0b1020"); fig.patch.set_facecolor("#0b1020")
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
    if count<=0: return fig
    width = 1.0/count
    for i in range(count):
        ax.add_patch(plt.Rectangle((i*width,0.1), width-0.002, 0.8, edgecolor="#22d3ee", facecolor="#172036"))
        ax.text(i*width+width/2, 0.5, f"{i+1}", ha='center', va='center', fontsize=9, color="#e5e7eb")
    ax.set_title(f"Subnet Visualization: /{new_prefix} (×{count})", pad=8, color="#cbd5e1")
    return fig

# Sidebar
with st.sidebar:
    st.markdown("### 📘 Project Guide")
    if os.path.exists(GUIDE_IMAGE_PATH):
        try: st.image(GUIDE_IMAGE_PATH, use_column_width=True)
        except Exception as e: st.warning(f"Guide image error: {e}")
    else:
        st.warning(f"'{GUIDE_IMAGE_PATH}' not found.")
    st.write(f"**{GUIDE_NAME}**")
    st.write(f"**Developed by {STUDENT_NAMES}**")
    st.divider()
    st.write("**Prefix vs Usable Hosts**")
    pref = [{"Prefix": f"/{p}", "Usable hosts": usable_host_count(p)} for p in range(24,31)]
    st.dataframe(pd.DataFrame(pref), use_container_width=True)

# Header
st.markdown('<div class="header-banner">', unsafe_allow_html=True)
c0, c1, c2 = st.columns([3.8, 1.1, 1.1])
with c0:
    st.markdown('<div class="big-title">CIDR Subnet & Supernet Project</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Subnetting (equal, VLSM, hierarchical) and supernetting with clean tables & visuals.</div>', unsafe_allow_html=True)
with c1:
    learn = st.button("How it works", key="learn")
with c2:
    tipsb = st.button("Quick tips", key="tips")
st.markdown('</div>', unsafe_allow_html=True)
if learn: st.info("Enter base IP/prefix → choose split mode → Run. See steps/tips below results.")
if tipsb: st.warning("Use VLSM for varied host needs; Level-2 split = hierarchical; check Remaining/Lagging.")

tab1, tab2 = st.tabs(["📌 Subnet Planner", "🌐 Supernetting"])

# Tab 1 — Subnet Planner
with tab1:
    st.markdown('<div class="section-title">User Input (Subnet Planner)</div>', unsafe_allow_html=True)
    st.markdown("<div class='card'>1.1 IP address • 1.2 Prefix length • 2. Number of networks</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.3,1,1])
    with c1: ip_text = st.text_input("1.1 IP Address (dotted decimal)", value="192.168.10.0")
    with c2: net_bits = st.number_input("1.2 Prefix length (bits for network)", 0, 32, 24, 1)
    with c3: num_networks = st.number_input("2. Number of networks", 1, 1_000_000, 4, 1)

    st.write("**Split Mode**")
    split_mode = st.radio("Choose how to split",
                          ["Split equally", "Split by addresses (VLSM)", "Hierarchical split (two-level)"],
                          index=0, horizontal=True, label_visibility="collapsed")
    host_list_text, level2_host_text = "", ""
    if split_mode=="Split by addresses (VLSM)":
        host_list_text = st.text_input("Usable hosts per subnet (comma-separated)", value="50, 20, 10")
    elif split_mode=="Hierarchical split (two-level)":
        st.markdown("<div class='card'>Base block split equally; then <b>Network #1</b> is split by host needs.</div>", unsafe_allow_html=True)
        level2_host_text = st.text_input("Level-2 usable hosts inside Network #1", value="50, 30, 10")

    if st.button("Run Subnet Planner", type="primary"):
        try:
            base_net = ipa.IPv4Network(f"{ip_text.strip()}/{int(net_bits)}", strict=False)
            base_net_int = int(base_net.network_address); base_bc_int = int(base_net.broadcast_address)
            base_block_size = base_bc_int - base_net_int + 1
            rows_main, rows_lvl2, steps = [], [], []
            steps.append(f"1️⃣ Base: {base_net.network_address}/{int(net_bits)}")
            steps.append(f"   • Range: {base_net.network_address} – {base_net.broadcast_address}")
            steps.append(f"   • Total: {base_block_size}")

            if split_mode=="Split equally":
                N = int(num_networks)
                bits_needed = math.ceil(math.log2(N))
                new_prefix = int(net_bits) + bits_needed
                if new_prefix>32: st.error("Too many equal networks for this block.")
                else:
                    child_block = 2**(32-new_prefix)
                    steps += ["2️⃣ Equal Split",
                              f"   • N: {N}",
                              f"   • Bits borrowed: {bits_needed}",
                              f"   • Child prefix: /{new_prefix}",
                              f"   • Child block: {child_block} addrs"]
                    for i in range(N):
                        nw = base_net_int + i*child_block; bc = nw + child_block - 1
                        if bc>base_bc_int: break
                        f,l = first_last_usable(nw,bc,new_prefix)
                        usable = usable_host_count(new_prefix)
                        rows_main.append({
                            "Network ID": ip_int_to_dotted(nw),
                            "First address": "-" if f is None else ip_int_to_dotted(f),
                            "Last address": "-" if l is None else ip_int_to_dotted(l),
                            "Broadcast address": ip_int_to_dotted(bc),
                            "Total address": child_block,
                            "Usable address": usable,
                            "Allocated address": usable,
                            "Remaining address": child_block - usable,
                            "Lagging address": child_block - usable,
                        })

            elif split_mode=="Split by addresses (VLSM)":
                reqs = [int(x.strip()) for x in host_list_text.split(",") if x.strip()]
                steps += ["2️⃣ VLSM", f"   • Hosts: {reqs}"]
                cur = base_net_int
                for idx,h in enumerate(reqs,1):
                    if h<=0: st.error(f"Host requirement #{idx} must be positive."); break
                    needed = h+2 if h>2 else h
                    host_bits = math.ceil(math.log2(needed))
                    pre = 32-host_bits; block = 2**(32-pre)
                    align = ((cur+block-1)//block)*block
                    nw = align; bc = nw+block-1
                    if bc>base_bc_int: st.error("Requirements do not fit in base block."); break
                    f,l = first_last_usable(nw,bc,pre)
                    usable = usable_host_count(pre)
                    rows_main.append({
                        "Network ID": ip_int_to_dotted(nw),
                        "First address": "-" if f is None else ip_int_to_dotted(f),
                        "Last address": "-" if l is None else ip_int_to_dotted(l),
                        "Broadcast address": ip_int_to_dotted(bc),
                        "Total address": block,
                        "Usable address": usable,
                        "Allocated address": min(h,usable),
                        "Remaining address": max(0, usable-min(h,usable)),
                        "Lagging address": block - h,
                    })
                    cur = bc+1

            else:  # Hierarchical two-level
                N = int(num_networks)
                bits_needed = math.ceil(math.log2(N))
                new_prefix = int(net_bits)+bits_needed
                if new_prefix>32: st.error("Too many equal networks for this block.")
                else:
                    child_block = 2**(32-new_prefix)
                    steps += ["2️⃣ Hierarchical L1", f"   • {N} nets of /{new_prefix}"]
                    for i in range(N):
                        nw = base_net_int + i*child_block; bc = nw + child_block - 1
                        if bc>base_bc_int: break
                        f,l = first_last_usable(nw,bc,new_prefix)
                        usable = usable_host_count(new_prefix)
                        rows_main.append({
                            "Network ID": ip_int_to_dotted(nw),
                            "First address": "-" if f is None else ip_int_to_dotted(f),
                            "Last address": "-" if l is None else ip_int_to_dotted(l),
                            "Broadcast address": ip_int_to_dotted(bc),
                            "Total address": child_block,
                            "Usable address": usable,
                            "Allocated address": usable,
                            "Remaining address": child_block - usable,
                            "Lagging address": child_block - usable,
                        })
                    steps.append("3️⃣ Hierarchical L2 (inside Network #1)")
                    if len(rows_main)>0 and level2_host_text.strip():
                        first_ip = rows_main[0]["Network ID"]
                        first_net = ipa.IPv4Network(f"{first_ip}/{new_prefix}", strict=False)
                        lvl2_base, lvl2_bc = int(first_net.network_address), int(first_net.broadcast_address)
                        lvl2_reqs = [int(x.strip()) for x in level2_host_text.split(",") if x.strip()]
                        steps.append(f"   • L2 hosts: {lvl2_reqs}")
                        cur = lvl2_base
                        for idx,h in enumerate(lvl2_reqs,1):
                            if h<=0: st.error(f"L2 host requirement #{idx} must be positive."); break
                            needed = h+2 if h>2 else h
                            host_bits = math.ceil(math.log2(needed))
                            pre = 32-host_bits; block = 2**(32-pre)
                            align = ((cur+block-1)//block)*block
                            nw = align; bc = nw+block-1
                            if bc>lvl2_bc: st.error("L2 requirements do not fit in Network #1."); break
                            f,l = first_last_usable(nw,bc,pre)
                            usable = usable_host_count(pre)
                            rows_lvl2 = st.session_state.get("rows_lvl2", [])
                            rows_lvl2.append({
                                "Network ID": ip_int_to_dotted(nw),
                                "First address": "-" if f is None else ip_int_to_dotted(f),
                                "Last address": "-" if l is None else ip_int_to_dotted(l),
                                "Broadcast address": ip_int_to_dotted(bc),
                                "Total address": block,
                                "Usable address": usable,
                                "Allocated address": min(h,usable),
                                "Remaining address": max(0, usable-min(h,usable)),
                                "Lagging address": block - h,
                            })
                            st.session_state["rows_lvl2"] = rows_lvl2
                            cur = bc+1

            tips = ["• Use VLSM when subnets need different sizes.",
                    "• Level-2 split = hierarchical subnetting for one branch.",
                    "• 'Remaining' vs 'Lagging' indicate address efficiency."]

            if rows_main:
                st.markdown('<div class="section-title">Primary Subnet Plan</div>', unsafe_allow_html=True)
                df_main = pd.DataFrame(rows_main)[["Network ID","First address","Last address","Broadcast address",
                                                   "Total address","Usable address","Allocated address","Remaining address","Lagging address"]]
                st.dataframe(df_main, use_container_width=True)
                cA, cB = st.columns([1,1])
                with cA:
                    st.markdown("**Steps**")
                    st.text_area("steps", "\\n".join(steps), height=240, label_visibility="collapsed")
                with cB:
                    try:
                        child_prefix = int(net_bits)
                        if split_mode in ["Split equally","Hierarchical split (two-level)"]:
                            import math as _m
                            child_prefix = int(net_bits) + _m.ceil(_m.log2(int(num_networks)))
                        fig = visualize_subnets(child_prefix, len(df_main))
                        st.pyplot(fig)
                    except Exception:
                        pass
                    st.info("\\n".join(tips))

            if "rows_lvl2" in st.session_state and st.session_state["rows_lvl2"]:
                st.markdown('<div class="section-title">Level-2 Split inside Network #1</div>', unsafe_allow_html=True)
                df2 = pd.DataFrame(st.session_state["rows_lvl2"])[["Network ID","First address","Last address",
                                                                   "Broadcast address","Total address","Usable address",
                                                                   "Allocated address","Remaining address","Lagging address"]]
                st.dataframe(df2, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")

# Tab 2 — Supernetting
with tab2:
    st.markdown('<div class="section-title">Supernetting (CIDR Aggregation)</div>', unsafe_allow_html=True)
    st.markdown("<div class='card'>Enter multiple CIDR blocks. The tool finds a common supernet and shows the table reduction.</div>", unsafe_allow_html=True)
    nets_text = st.text_area("CIDR blocks (comma or newline)", value="192.168.10.0/26, 192.168.10.64/26\n192.168.10.128/26")

    if st.button("Run Supernetting", type="primary", key="supernet"):
        try:
            raw = [p.strip() for p in nets_text.replace("\\n",",").split(",") if p.strip()]
            nets = []
            for item in raw:
                if "/" not in item: st.error(f"Missing /prefix in '{item}'."); st.stop()
                nets.append(ipa.IPv4Network(item, strict=False))

            nets.sort(key=lambda n: int(n.network_address))
            min_addr = int(nets[0].network_address)
            max_bc   = max(int(n.broadcast_address) for n in nets)

            def prefix_to_mask(prefix:int)->int: return (0xFFFFFFFF << (32-prefix)) & 0xFFFFFFFF

            agg_prefix = 32
            while agg_prefix >= 0:
                mask = prefix_to_mask(agg_prefix)
                agg_net = min_addr & mask
                agg_bc  = agg_net | (~mask & 0xFFFFFFFF)
                if agg_bc >= max_bc and agg_net <= min_addr: break
                agg_prefix -= 1

            def dotted(n:int)->str: return ".".join(str((n>>(8*i))&255) for i in [3,2,1,0])

            agg_net_ip, agg_bc_ip = dotted(agg_net), dotted(agg_bc)
            rows = []
            for i,n in enumerate(nets,1):
                total = int(n.broadcast_address)-int(n.network_address)+1
                usable = usable_host_count(n.prefixlen)
                rows.append({"Input #":i, "Network ID":str(n.network_address), "Broadcast address":str(n.broadcast_address),
                             "Prefix":f"/{n.prefixlen}", "Total address":total, "Usable address":usable})
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.markdown(
                f"**Supernet:** `{agg_net_ip}/{agg_prefix}`  \n"
                f"**Range:** `{agg_net_ip} – {agg_bc_ip}`  \n"
                f"**Original entries:** `{len(nets)}` → After supernetting: `1`  \n"
                f"**Routing table reduction:** `{len(nets)-1}` entries"
            )
        except Exception as e:
            st.error(f"Error: {e}")
'''

with open("app.py","w") as f:
    f.write(APP_CODE)
print("✅ Wrote app.py")

# ---------- C) requirements.txt for Streamlit Cloud ----------
reqs = """\
streamlit==1.39.0
pandas
matplotlib
pillow
"""
with open("requirements.txt","w") as f:
    f.write(reqs)
print("✅ Wrote requirements.txt")

# ---------- D) Optional theme (dark) ----------
os.makedirs(".streamlit", exist_ok=True)
with open(".streamlit/config.toml","w") as f:
    f.write('[theme]\nbase="dark"\nprimaryColor="#22d3ee"\nbackgroundColor="#0b1020"\nsecondaryBackgroundColor="#111827"\ntextColor="#e5e7eb"\n')
print("✅ Wrote .streamlit/config.toml")

# ---------- E) README for the repo ----------
readme = """\
# CIDR Subnet & Supernet Project (Streamlit)

Deployed on Streamlit Community Cloud.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
