"""Shared figure/table numbering, explanations and section-level input context."""
import re
from presentation_catalog import metadata, CATALOG

GUIDE_HEADINGS = ("**How to read**", "**What the results show**", "**Interpretation limits**")
SAVED_HEADING = "## Saved clinical results"
INPUT_MARKER = "<!-- Generated notebook input context -->"


def input_context_section(notebook):
    prefix=notebook.split('_',1)[0]
    parts=[INPUT_MARKER,'','## Inputs and execution mode','']
    if prefix in ['01','02','03a','03b','04d']:
        sources={item[2][1]:item[2][0] for item in reversed(CATALOG[prefix]['tables'])}
        parts.append('Input definitions: '+ '; '.join(f'[{label}]({href})' for href,label in reversed(list(sources.items())))+'.')
        parts.append('')
    if prefix.startswith('05'):
        parts.append('The saved clinical section identifies its aggregate input once. New execution defaults to synthetic inputs; current/local mode is explicit, and the selected input origin is shown once when that section begins or its input changes.')
    else:
        parts.append('New execution uses the queries and shared loader shown in the code. The stored outputs below were refreshed from saved clinical aggregates, without a new clinical query or model refit.')
    parts+=['','Stored-output evidence: [original clinical execution](../docs/NOTEBOOK_EXECUTION_VALIDATION.json) · [presentation refresh](../docs/NOTEBOOK_PRESENTATION_VALIDATION.json).']
    return '\n'.join(parts)


def normalize_input_context(book, notebook):
    import nbformat
    previous=next((c.id for c in book.cells if c.cell_type=='markdown' and c.source.startswith(INPUT_MARKER)), 'notebook-input-context')
    book.cells=[c for c in book.cells if not (c.cell_type=='markdown' and c.source.startswith(INPUT_MARKER))]
    first=next(i for i,c in enumerate(book.cells) if c.cell_type=='markdown')
    book.cells[first].source=re.sub(r'\n\n> Stored-output provenance:[^\n]*','',book.cells[first].source)
    book.cells.insert(first+1,nbformat.v4.new_markdown_cell(input_context_section(notebook),id=previous))


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
            f"![Figure {number} — {title}]({image_href})\n\n" + guide)


def saved_figure_block(notebook, key, image_href, guide, source_href=None):
    meta=metadata(notebook,'figures',key)
    return figure_block(meta['number'],meta['title'],image_href,guide,source_href or meta['source_href'])


def normalize_runtime(book, kind, guide=None):
    """Keep the original plot code/output cells intact and standardize adjacent prose."""
    for cell in book.cells:
        if cell.cell_type=='markdown' and cell.source.startswith(('## Runtime results', '## Runtime execution')):
            cell.source = ("## Runtime execution\n\n"
                           "The selected input origin is displayed once below, and again only if it changes. "
                           "A new execution defaults to synthetic inputs unless current/local mode is selected. "
                           "Synthetic outputs validate software execution only. "
                           "Figure 1 above remains the fixed published aggregate snapshot.")
    section=next(i for i,c in enumerate(book.cells) if c.cell_type=='markdown' and c.source.startswith('## Runtime execution'))
    selection=next(i for i,c in enumerate(book.cells) if c.cell_type=='code' and 'DATA_MODE =' in c.source)
    if section>selection:
        intro=book.cells.pop(section);book.cells.insert(selection,intro)
    indices = [i for i,c in enumerate(book.cells) if c.cell_type == "code" and "display_runtime_figure(" in c.source]
    if len(indices) != 1:
        raise ValueError("Expected one runtime figure in the supplement notebook")
    index = indices[0]
    if index == 0 or book.cells[index-1].cell_type != "markdown":
        raise ValueError("Runtime figure heading must immediately precede its plot cell")
    book.cells[index-1].source = (
        "### Selected-execution figure\n\n"
        "The following shared display call generates the figure number, title "
        "and numerical interpretation from this execution's aggregate result.")
    if index+1 < len(book.cells) and book.cells[index+1].cell_type == "markdown" and (
            "How to read" in book.cells[index+1].source):
        del book.cells[index+1]


def validate_layout(book):
    """Verify consecutive numbers and immediate figure explanations."""
    figures=[]
    for i,cell in enumerate(book.cells):
        if cell.cell_type=='code' and 'display_runtime_figure(' in cell.source:
            match=re.search(r'display_runtime_figure\(bundle,\s*["\'](cluster|competing|landmark)["\']\)',cell.source)
            if not match:raise ValueError('Runtime figure must identify its aggregate analysis explicitly')
            prefix={'cluster':'05a','competing':'05b','landmark':'05c'}[match[1]]
            figures.append(metadata(prefix,'figures','runtime')['number'])
            if cell.get('outputs'):
                html='\n'.join(o.get('data',{}).get('text/html','') for o in cell.outputs)
                if not all(h.strip('*') in html for h in GUIDE_HEADINGS):
                    raise ValueError('Executed runtime figure lacks a caption or interpretation')
        if cell.cell_type != "markdown":continue
        matches=list(re.finditer(r"^### Figure (\d+) — .+$",cell.source,re.M))
        for match in matches:
            block=cell.source[match.start():]
            if "![" in block:
                image=re.search(r'!\[[^\]]*\]\([^)]+\)',block)
                if image is None:
                    raise ValueError("Saved figure image missing")
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


def validate_tables(book, notebook):
    """Check declared table order and every retained aggregate table output."""
    numbers=[]
    for cell in book.cells:
        if cell.cell_type=='markdown':
            for match in re.finditer(r'^### Table (\d+) — .+$',cell.source,re.M):
                block=cell.source[match.start():]
                if '**Summary:**' not in block:
                    raise ValueError('Saved table lacks a numerical summary')
                numbers.append(int(match[1]))
        elif cell.cell_type=='code':
            calls=re.findall(r'display_table\(["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']',cell.source)
            declared=[metadata(prefix,'tables',key)['number'] for prefix,key in calls]
            numbers.extend(declared)
            outputs=[o.get('data',{}).get('text/html','') for o in cell.get('outputs',[]) if '<table' in o.get('data',{}).get('text/html','')]
            if outputs:
                actual=[]
                for html in outputs:
                    found=re.search(r'data-table-number="(\d+)"',html)
                    if not found or '<h3 id="table_' not in html or 'Summary:' not in html:
                        raise ValueError('Runtime table lacks a generated caption/summary')
                    actual.append(int(found[1]))
                if actual!=declared:raise ValueError('Rendered table order differs from declared catalog')
    from presentation_catalog import CATALOG
    expected=list(range(1,len(CATALOG[notebook.split('_',1)[0]]['tables'])+1))
    if numbers!=expected:raise ValueError('Tables must follow consecutive per-notebook catalog order')
    return numbers
