import streamlit as st
import subprocess
import tempfile
import os
import base64

st.set_page_config(page_title="Resume Builder", layout="wide")
st.title("Resume Builder")
st.caption("Fill in your details and generate a professional resume PDF")


# --- Helper to escape LaTeX special characters ---
def tex_escape(text):
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


# --- Session state initialization ---
DEFAULT_SECTIONS = ["Education", "Experience", "Projects", "Skills", "Awards and Achievements", "Certification"]

if "edu_count" not in st.session_state:
    st.session_state.edu_count = 2
if "exp_count" not in st.session_state:
    st.session_state.exp_count = 2
if "proj_count" not in st.session_state:
    st.session_state.proj_count = 1
if "custom_sections" not in st.session_state:
    st.session_state.custom_sections = []
if "section_order" not in st.session_state:
    st.session_state.section_order = DEFAULT_SECTIONS.copy()
if "reorder_counter" not in st.session_state:
    st.session_state.reorder_counter = 0


def get_all_sections():
    all_known = DEFAULT_SECTIONS + st.session_state.custom_sections
    for s in all_known:
        if s not in st.session_state.section_order:
            st.session_state.section_order.append(s)
    st.session_state.section_order = [s for s in st.session_state.section_order if s in all_known]
    return st.session_state.section_order


# ========== SIDEBAR ==========
with st.sidebar:
    st.header("Layout Settings")
    section_spacing = st.slider("Section spacing (pt)", min_value=4, max_value=20, value=12, step=1)
    after_rule_spacing = st.slider("After-rule spacing (pt)", min_value=4, max_value=16, value=10, step=1)
    bullet_spacing = st.slider("Bullet item spacing (pt)", min_value=-4, max_value=4, value=-2, step=1)

    st.divider()
    st.header("Section Order")
    st.caption("Reorder here — editor and PDF both follow this order")

    sections = get_all_sections()

    def move_section(sec_name, direction):
        order = st.session_state.section_order
        idx = order.index(sec_name)
        new_idx = idx + direction
        if 0 <= new_idx < len(order):
            order[idx], order[new_idx] = order[new_idx], order[idx]
            st.session_state.reorder_counter += 1

    rc = st.session_state.reorder_counter
    for i, sec in enumerate(sections):
        col_name, col_up, col_down = st.columns([4, 1, 1])
        col_name.write(f"**{i+1}.** {sec}")
        if i > 0:
            col_up.button("↑", key=f"up_{sec}_{rc}", on_click=move_section, args=(sec, -1))
        if i < len(sections) - 1:
            col_down.button("↓", key=f"down_{sec}_{rc}", on_click=move_section, args=(sec, 1))

    st.divider()
    st.header("Custom Sections")
    new_section_name = st.text_input("New section name", placeholder="e.g., Publications")
    if st.button("Add Custom Section"):
        if new_section_name.strip() and new_section_name.strip() not in st.session_state.custom_sections:
            st.session_state.custom_sections.append(new_section_name.strip())
            st.session_state.section_order.append(new_section_name.strip())
            st.rerun()

    for i, sec in enumerate(st.session_state.custom_sections):
        col1, col2 = st.columns([3, 1])
        col1.write(f"• {sec}")
        if col2.button("✕", key=f"del_custom_{i}"):
            st.session_state.custom_sections.pop(i)
            if sec in st.session_state.section_order:
                st.session_state.section_order.remove(sec)
            st.rerun()


# ========== PERSONAL INFO (always first) ==========
st.header("Personal Information")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name", "MEHRAJ PEERZADA")
    subtitle = st.text_input("Subtitle / Tagline", "Software Developer | Data Analyst | Expert at Codeforces (max 1626)")
with col2:
    phone = st.text_input("Phone", "+91 7006560568")
    email = st.text_input("Email", "shahmeraj510@gmail.com")
col3, col4 = st.columns(2)
with col3:
    linkedin_url = st.text_input("LinkedIn URL", "https://www.linkedin.com/in/mehraj-shah-803828219/")
    linkedin_label = st.text_input("LinkedIn Display Text", "LinkedIn")
with col4:
    location = st.text_input("Location", "Bangalore")

st.divider()


# ========== SECTION RENDERERS ==========
edu_entries = []
exp_entries = []
proj_entries = []
skills = ""
awards = ""
certs = ""
custom_section_data = {}


def render_education():
    global edu_entries
    st.header("Education")
    col_add, col_remove, _ = st.columns([1, 1, 4])
    with col_add:
        if st.button("+ Add", key="add_edu"):
            st.session_state.edu_count += 1
            st.rerun()
    with col_remove:
        if st.button("- Remove", key="rm_edu") and st.session_state.edu_count > 1:
            st.session_state.edu_count -= 1
            st.rerun()

    edu_entries.clear()
    for i in range(st.session_state.edu_count):
        with st.expander(f"Education {i+1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                inst = st.text_input("Institution", key=f"edu_inst_{i}")
                degree = st.text_input("Degree / Program", key=f"edu_degree_{i}")
            with c2:
                dates = st.text_input("Dates", key=f"edu_dates_{i}", placeholder="09/2020 -- 05/2024")
                gpa = st.text_input("GPA (optional)", key=f"edu_gpa_{i}", placeholder="8.92 / 10")
            edu_entries.append({"inst": inst, "degree": degree, "dates": dates, "gpa": gpa})
    st.divider()


def render_experience():
    global exp_entries
    st.header("Experience")
    col_add, col_remove, _ = st.columns([1, 1, 4])
    with col_add:
        if st.button("+ Add", key="add_exp"):
            st.session_state.exp_count += 1
            st.rerun()
    with col_remove:
        if st.button("- Remove", key="rm_exp") and st.session_state.exp_count > 1:
            st.session_state.exp_count -= 1
            st.rerun()

    exp_entries.clear()
    for i in range(st.session_state.exp_count):
        with st.expander(f"Experience {i+1}", expanded=(i == 0)):
            c1, c2 = st.columns(2)
            with c1:
                company = st.text_input("Company", key=f"exp_company_{i}")
                role = st.text_input("Role / Title", key=f"exp_role_{i}")
            with c2:
                loc = st.text_input("Location", key=f"exp_loc_{i}")
                dates = st.text_input("Dates", key=f"exp_dates_{i}")
            bullets = st.text_area(
                "Bullet points (one per line, 'Title: Description' for colored titles)",
                key=f"exp_bullets_{i}", height=150,
                placeholder="Project Name: Description of work done..."
            )
            exp_entries.append({"company": company, "role": role, "loc": loc, "dates": dates, "bullets": bullets})
    st.divider()


def render_projects():
    global proj_entries
    st.header("Projects")
    col_add, col_remove, _ = st.columns([1, 1, 4])
    with col_add:
        if st.button("+ Add", key="add_proj"):
            st.session_state.proj_count += 1
            st.rerun()
    with col_remove:
        if st.button("- Remove", key="rm_proj") and st.session_state.proj_count > 1:
            st.session_state.proj_count -= 1
            st.rerun()

    proj_entries.clear()
    for i in range(st.session_state.proj_count):
        with st.expander(f"Project {i+1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Project Title", key=f"proj_title_{i}")
                desc = st.text_input("One-line description (italic)", key=f"proj_desc_{i}")
            with c2:
                source = st.text_input("Source (e.g., Kaggle)", key=f"proj_source_{i}")
                dates = st.text_input("Dates", key=f"proj_dates_{i}")
            bullets = st.text_area("Bullet points (one per line)", key=f"proj_bullets_{i}", height=100)
            proj_entries.append({"title": title, "desc": desc, "source": source, "dates": dates, "bullets": bullets})
    st.divider()


def render_skills():
    global skills
    st.header("Skills")
    skills = st.text_area(
        "Skills (comma separated)",
        "C, C++, Python, Rust, Java, Scala, JavaScript, TypeScript, HTML5, CSS3, React, jQuery, TailWind CSS, Spark, REST API, UI/UX Design, Database Management, TensorFlow, LangChain, Shell Scripting, Bash, NLP, SQL, AWS, CDK, Smithy, Coral, Cypress, Git, Algorithms and Data Structures, Deep Learning, Machine Learning, Django",
        height=100, key="skills_input"
    )
    st.divider()


def render_awards():
    global awards
    st.header("Awards and Achievements")
    awards = st.text_area(
        "Awards (one per line)",
        "Expert at CODEFORCES (rating: 1662)\nAIR 1400 in IIT JEE ADVANCE 2020\nIndian Math Olympiad (IOQM) Qualifier",
        height=80, key="awards_input"
    )
    st.divider()


def render_certification():
    global certs
    st.header("Certifications")
    certs = st.text_area(
        "Certifications (one per line, 'Course --- Provider, Year' format)",
        "Complete Machine Learning & Data Science Bootcamp --- Zero to Mastery Academy, 2023\nLLM Mastery: ChatGPT, Gemini, Claude, Llama3, OpenAI & APIs --- Udemy, 2024\nThe complete course on Data Structures and Algorithms --- AlgoZenith Technologies\nThe Complete Full-Stack Web Development Bootcamp --- Udemy, 2023",
        height=100, key="certs_input"
    )
    st.divider()


def render_custom_section(sec_name):
    st.header(sec_name)
    content = st.text_area(
        f"Content (one item per line, 'Title: Description' for colored titles)",
        key=f"custom_{sec_name}", height=120,
        placeholder="Item 1: Description...\nItem 2: Description..."
    )
    custom_section_data[sec_name] = content
    st.divider()


# ========== RENDER SECTIONS IN ORDER ==========
section_renderers = {
    "Education": render_education,
    "Experience": render_experience,
    "Projects": render_projects,
    "Skills": render_skills,
    "Awards and Achievements": render_awards,
    "Certification": render_certification,
}

for sec in get_all_sections():
    if sec in section_renderers:
        section_renderers[sec]()
    elif sec in st.session_state.custom_sections:
        render_custom_section(sec)


# ========== LATEX GENERATION ==========
def build_education_latex(entries):
    edu_block = ""
    for e in entries:
        if not e['inst']:
            continue
        gpa_str = f" \\enspace$|$\\enspace GPA: {tex_escape(e['gpa'])}" if e['gpa'] else ""
        edu_block += f"""    \\item
    \\begin{{tabular*}}{{0.97\\textwidth}}[t]{{l@{{\\extracolsep{{\\fill}}}}r}}
      {{\\color{{collegegrey}}{tex_escape(e['inst'])}}} & {tex_escape(e['dates'])} \\\\
      {tex_escape(e['degree'])}{gpa_str} & \\\\
    \\end{{tabular*}}\\vspace{{-4pt}}
"""
    return f"""\\section{{Education}}
  \\resumeSubHeadingListStart
{edu_block}  \\resumeSubHeadingListEnd
"""


def build_experience_latex(entries):
    exp_block = ""
    for e in entries:
        if not e['company']:
            continue
        bullets_tex = ""
        if e['bullets'].strip():
            for line in e['bullets'].strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                if ':' in line:
                    parts = line.split(':', 1)
                    title_part = tex_escape(parts[0].strip())
                    desc_part = tex_escape(parts[1].strip())
                    bullets_tex += f"        \\resumeItem{{{{\\color{{darkgray}}{title_part}:}} {desc_part}}}\n"
                else:
                    bullets_tex += f"        \\resumeItem{{{tex_escape(line)}}}\n"
        exp_block += f"""
    \\resumeSubheading
      {{{tex_escape(e['company'])}}}{{{tex_escape(e['loc'])}}}
      {{{tex_escape(e['role'])}}}{{{tex_escape(e['dates'])}}}
      \\resumeItemListStart
{bullets_tex}      \\resumeItemListEnd
"""
    return f"""\\section{{Experience}}
  \\resumeSubHeadingListStart
{exp_block}
  \\resumeSubHeadingListEnd
"""


def build_projects_latex(entries):
    proj_block = ""
    for p in entries:
        if not p['title']:
            continue
        bullets_tex = ""
        if p['bullets'].strip():
            for line in p['bullets'].strip().split('\n'):
                line = line.strip()
                if line:
                    bullets_tex += f"            \\resumeItem{{{tex_escape(line)}}}\n"
        proj_block += f"""      \\resumeProjectHeading
          {{{tex_escape(p['title'])}}}{{{{\\color{{collegegrey}}{tex_escape(p['source'])}}}}}
      \\resumeProjectHeading
          {{\\emph{{{tex_escape(p['desc'])}}}}}{{{tex_escape(p['dates'])}}}
          \\resumeItemListStart
{bullets_tex}          \\resumeItemListEnd
"""
    return f"""\\section{{Projects}}
    \\resumeSubHeadingListStart
{proj_block}    \\resumeSubHeadingListEnd
"""


def build_skills_latex(skills_text):
    skill_items = [s.strip() for s in skills_text.split(',') if s.strip()]
    skills_tex = " $\\cdot$ ".join([tex_escape(s) for s in skill_items])
    return f"""\\section{{Skills}}
 \\begin{{itemize}}[leftmargin=0.1in, label={{}}]
    \\small{{\\item{{
     {skills_tex}
    }}}}
 \\end{{itemize}}
"""


def build_awards_latex(awards_text):
    award_lines = [a.strip() for a in awards_text.strip().split('\n') if a.strip()]
    awards_tex = " \\hfill ".join([f"$\\diamondsuit$ {tex_escape(a)}" for a in award_lines])
    return f"""\\section{{Awards and Achievements}}
 \\begin{{itemize}}[leftmargin=0.1in, label={{}}]
    \\small{{\\item{{
     {awards_tex}
    }}}}
 \\end{{itemize}}
"""


def build_certification_latex(certs_text):
    cert_lines = [c.strip() for c in certs_text.strip().split('\n') if c.strip()]
    certs_tex = ""
    for c in cert_lines:
        if '---' in c:
            parts = c.split('---', 1)
            certs_tex += f"     {tex_escape(parts[0].strip())} --- {{\\color{{collegegrey}}{tex_escape(parts[1].strip())}}} \\\\\n"
        else:
            certs_tex += f"     {tex_escape(c)} \\\\\n"
    certs_tex = certs_tex.rstrip(" \\\\\n")
    return f"""\\section{{Certification}}
 \\begin{{itemize}}[leftmargin=0.1in, label={{}}]
    \\small{{\\item{{
{certs_tex}
    }}}}
 \\end{{itemize}}
"""


def build_custom_section_latex(sec_name, content):
    if not content.strip():
        return ""
    items_tex = ""
    for line in content.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            parts = line.split(':', 1)
            items_tex += f"        \\resumeItem{{{{\\color{{darkgray}}{tex_escape(parts[0].strip())}:}} {tex_escape(parts[1].strip())}}}\n"
        else:
            items_tex += f"        \\resumeItem{{{tex_escape(line)}}}\n"
    return f"""\\section{{{tex_escape(sec_name)}}}
  \\resumeItemListStart
{items_tex}  \\resumeItemListEnd
"""


def generate_latex_full():
    section_builders = {
        "Education": lambda: build_education_latex(edu_entries),
        "Experience": lambda: build_experience_latex(exp_entries),
        "Projects": lambda: build_projects_latex(proj_entries),
        "Skills": lambda: build_skills_latex(skills),
        "Awards and Achievements": lambda: build_awards_latex(awards),
        "Certification": lambda: build_certification_latex(certs),
    }
    for sec_name in st.session_state.custom_sections:
        section_builders[sec_name] = lambda sn=sec_name: build_custom_section_latex(sn, custom_section_data.get(sn, ""))

    body = ""
    for sec in get_all_sections():
        if sec in section_builders:
            body += section_builders[sec]() + "\n"

    return f"""%-------------------------
% Resume generated by Resume Builder
%-------------------------

\\documentclass[a4paper,11pt]{{article}}
\\usepackage[empty]{{fullpage}}
\\usepackage{{titlesec}}
\\usepackage[usenames,dvipsnames]{{color}}
\\usepackage{{enumitem}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage{{fancyhdr}}
\\usepackage{{fontawesome5}}

\\usepackage[english]{{babel}}
\\usepackage{{tabularx}}
\\usepackage[T1]{{fontenc}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[sfdefault]{{roboto}}
\\usepackage{{xcolor}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyfoot{{}}
\\renewcommand{{\\headrulewidth}}{{0pt}}
\\renewcommand{{\\footrulewidth}}{{0pt}}

\\usepackage[left=0.6in, right=0.6in, top=0.5in, bottom=0.5in]{{geometry}}

\\urlstyle{{same}}
\\raggedbottom
\\raggedright
\\setlength{{\\tabcolsep}}{{0in}}

\\definecolor{{sectionrule}}{{RGB}}{{180, 140, 50}}
\\definecolor{{collegegrey}}{{RGB}}{{111, 123, 134}}
\\definecolor{{darkgray}}{{RGB}}{{70, 70, 70}}

\\titleformat{{\\section}}{{
  \\centering\\large\\bfseries
}}{{}}{{0em}}{{}}[\\vspace{{-0.1pt}}\\color{{sectionrule}}\\hrule height 0.8pt]
\\titlespacing*{{\\section}}{{0pt}}{{{section_spacing}pt}}{{{after_rule_spacing}pt}}

\\newcommand{{\\resumeItem}}[1]{{
  \\item\\small{{
    {{#1 \\vspace{{{bullet_spacing}pt}}}}
  }}
}}

\\newcommand{{\\resumeSubheading}}[4]{{
  \\vspace{{-1pt}}\\item
    \\begin{{tabular*}}{{0.97\\textwidth}}[t]{{l@{{\\extracolsep{{\\fill}}}}r}}
      {{\\color{{collegegrey}}#1}} & #2 \\\\
      \\textit{{\\small#3}} & \\textit{{\\small #4}} \\\\
    \\end{{tabular*}}\\vspace{{-7pt}}
}}

\\newcommand{{\\resumeProjectHeading}}[2]{{
    \\item
    \\begin{{tabular*}}{{0.97\\textwidth}}{{l@{{\\extracolsep{{\\fill}}}}r}}
      \\small#1 & #2 \\\\
    \\end{{tabular*}}\\vspace{{-7pt}}
}}

\\newcommand{{\\resumeSubHeadingListStart}}{{\\begin{{itemize}}[leftmargin=0.1in, label={{}}]}}
\\newcommand{{\\resumeSubHeadingListEnd}}{{\\end{{itemize}}}}
\\newcommand{{\\resumeItemListStart}}{{\\begin{{itemize}}[leftmargin=0.15in, label={{\\color{{collegegrey}}\\textbullet}}]}}
\\newcommand{{\\resumeItemListEnd}}{{\\end{{itemize}}\\vspace{{-5pt}}}}

\\begin{{document}}

\\begin{{center}}
    {{\\LARGE\\bfseries {tex_escape(name)}}} \\\\ \\vspace{{2pt}}
    {{\\small {tex_escape(subtitle)}}} \\\\ \\vspace{{2pt}}
    {{\\small
    \\faPhone\\ {tex_escape(phone)} \\enspace
    \\faEnvelope\\enspace\\href{{mailto:{email}}}{{{tex_escape(email)}}}
    \\enspace
    \\faLinkedin\\enspace\\href{{{linkedin_url}}}{{{tex_escape(linkedin_label)}}}
    \\enspace
    \\faMapMarker\\enspace {tex_escape(location)}
    }}
\\end{{center}}

{body}
\\end{{document}}
"""


def compile_latex(latex_code):
    tmpdir = tempfile.mkdtemp()
    tex_path = os.path.join(tmpdir, "resume.tex")
    pdf_path = os.path.join(tmpdir, "resume.pdf")
    with open(tex_path, 'w') as f:
        f.write(latex_code)
    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', tmpdir, tex_path],
            capture_output=True, text=True, timeout=30
        )
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                return f.read(), None
        else:
            return None, result.stdout + "\n" + result.stderr
    except subprocess.TimeoutExpired:
        return None, "LaTeX compilation timed out"
    except Exception as e:
        return None, str(e)


# ========== GENERATE ==========
if st.button("Generate Resume", type="primary", use_container_width=True):
    latex_code = generate_latex_full()

    tab1, tab2 = st.tabs(["PDF Preview", "LaTeX Code"])

    with tab2:
        st.code(latex_code, language="latex")
        st.download_button("Download .tex file", latex_code, file_name="resume.tex", mime="text/plain")

    with tab1:
        with st.spinner("Compiling LaTeX to PDF..."):
            pdf_bytes, error = compile_latex(latex_code)
        if pdf_bytes:
            st.success("PDF generated successfully!")
            st.download_button("Download PDF", pdf_bytes, file_name="resume.pdf", mime="application/pdf")
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800" type="application/pdf"></iframe>', unsafe_allow_html=True)
        else:
            st.error("PDF compilation failed")
            st.code(error, language="text")
