"""Shared numbering, source labels and explanatory layout for notebook figures."""
import re

GUIDE_HEADINGS = ("**How to read**", "**What the results show**", "**Interpretation limits**")
SAVED_HEADING = "## Saved clinical results"


def format_guide(reading, results, limits):
    return "\n\n".join(part for heading, text in zip(GUIDE_HEADINGS, [reading, results, limits])
                       for part in [heading, text])


def bullet_guide(text, reading, results, limits):
    """Group existing explanatory bullets without changing their numerical text."""
    bullets = [line for line in text.splitlines() if line.startswith("- ")]
    groups = [reading, results, limits]
    if sorted(i for group in groups for i in group) != list(range(len(bullets))):
        raise ValueError("Figure explanation grouping must include every bullet once")
    return format_guide(*( "\n".join(bullets[i] for i in group) for group in groups))


def saved_intro(source_href):
    return (SAVED_HEADING + "\n\n"
            "The tables and figures in this section display saved clinical execution results from "
            f"[the public aggregate record]({source_href}). They do not represent a new clinical rerun. "
            "The separately labeled execution section describes how to reproduce outputs. Any synthetic execution is explicitly labeled and is not a clinical MIMIC result.")


def figure_block(number, title, image_href, guide, source_href):
    return (f"### Figure {number} — {title}\n\n"
            f"**Data source:** Saved clinical execution results; [aggregate record]({source_href}).\n\n"
            f"![Figure {number} — {title}]({image_href})\n\n" + guide)


def normalize_runtime(book, kind, guide):
    """Keep the original plot code/output cells intact and standardize adjacent prose."""
    import nbformat
    titles = {"cluster": "Ordinary and patient-cluster inference",
              "competing": "Death and live discharge cumulative incidence",
              "landmark": "Ordinary and patient-cluster inference"}
    for cell in book.cells:
        if cell.cell_type=='markdown' and cell.source.startswith(('## Runtime results', '## Runtime execution')):
            _,separator,body=cell.source.partition('\n')
            cell.source='## Runtime execution'+separator+body
    indices = [i for i,c in enumerate(book.cells) if c.cell_type == "code" and "display(figure)" in c.source]
    if len(indices) != 1:
        raise ValueError("Expected one runtime figure in the supplement notebook")
    index = indices[0]
    if index == 0 or book.cells[index-1].cell_type != "markdown":
        raise ValueError("Runtime figure heading must immediately precede its plot cell")
    book.cells[index-1].source = (
        f"### Figure 2 — {titles[kind]} (selected execution)\n\n"
        "**Data source:** Selected execution input; check the printed `data_origin` and plot title. "
        "Synthetic execution is a software demonstration, not a clinical MIMIC result.")
    if index+1 < len(book.cells) and book.cells[index+1].cell_type == "markdown" and (
            "How to read" in book.cells[index+1].source):
        book.cells[index+1].source = guide
    else:
        book.cells.insert(index+1,nbformat.v4.new_markdown_cell(guide,id="runtime-figure-guide-"+kind))


def validate_layout(book):
    """Verify consecutive numbers, source labels and immediate figure explanations."""
    figures=[]
    for i,cell in enumerate(book.cells):
        if cell.cell_type != "markdown":continue
        matches=list(re.finditer(r"^### Figure (\d+) — .+$",cell.source,re.M))
        for match in matches:
            block=cell.source[match.start():]
            if "**Data source:**" not in block:
                raise ValueError("Figure source label missing")
            if "![" in block:
                image=re.search(r'!\[[^\]]*\]\([^)]+\)',block)
                if image is None or block.find('**Data source:**')>image.start():
                    raise ValueError("Figure source label must precede the image")
                explanation=block[image.end():]
                positions=[explanation.find(h) for h in GUIDE_HEADINGS]
                if any(p<0 for p in positions) or positions!=sorted(positions):
                    raise ValueError("Saved figure explanation order differs")
            else:
                if i+2 >= len(book.cells) or book.cells[i+1].cell_type != "code" or "display(figure)" not in book.cells[i+1].source:
                    raise ValueError("Runtime figure heading is not adjacent to its plot")
                explanation=book.cells[i+2].source
                positions=[explanation.find(h) for h in GUIDE_HEADINGS]
                if any(p<0 for p in positions) or positions!=sorted(positions):
                    raise ValueError("Runtime figure explanation order differs")
            figures.append(int(match[1]))
    if figures and figures!=list(range(1,len(figures)+1)):
        raise ValueError("Notebook figures must be numbered consecutively from 1")
    return figures
