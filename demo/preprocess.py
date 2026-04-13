from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Set, Tuple


DEMO_ROOT = Path(__file__).parent
PROJECT_ROOT = DEMO_ROOT.parent
RAW_DATA_DIR = PROJECT_ROOT / "external_data" / "raw_data"
OUTPUT_DIR = DEMO_ROOT / "data"


def _strip_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%.*$", "", text, flags=re.MULTILINE)


def _find_main_tex(paper_dir: Path) -> Optional[Path]:
    tex_files = sorted(paper_dir.glob("*.tex"))
    if not tex_files:
        return None

    for f in tex_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        if "\\begin{document}" in content and "\\end{document}" in content:
            return f

    for name in ("main.tex", "0_main.tex"):
        candidate = paper_dir / name
        if candidate.exists():
            return candidate

    return tex_files[0]


def _normalize_include_target(target: str) -> str:
    target = target.strip()
    if target and not target.lower().endswith(".tex"):
        target += ".tex"
    return target


def _expand_includes(text: str, base_dir: Path, seen: Optional[Set[Path]] = None) -> str:
    if seen is None:
        seen = set()

    pattern = re.compile(r"\\(input|include)\s*\{([^}]+)\}")

    def replace(match: re.Match[str]) -> str:
        rel = _normalize_include_target(match.group(2))
        include_path = (base_dir / rel).resolve()
        if include_path in seen or not include_path.exists():
            return ""

        seen.add(include_path)
        content = include_path.read_text(encoding="utf-8", errors="ignore")
        content = _strip_comments(content)
        return "\n" + _expand_includes(content, include_path.parent, seen) + "\n"

    prev = None
    curr = text
    while prev != curr:
        prev = curr
        curr = pattern.sub(replace, curr)
    return curr


def _extract_body(full_tex: str) -> str:
    begin = re.search(r"\\begin\{document\}", full_tex)
    end = re.search(r"\\end\{document\}", full_tex)
    if not begin or not end or end.start() <= begin.end():
        return full_tex
    return full_tex[begin.end(): end.start()]


def _extract_title(full_tex: str) -> str:
    m = re.search(r"\\title(?:\[[^\]]*\])?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", full_tex, flags=re.DOTALL)
    if not m:
        return ""
    return _latex_to_text(m.group(1)).strip()


def _extract_abstract(body_tex: str) -> str:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body_tex, flags=re.DOTALL)
    if not m:
        return ""
    return _latex_to_text(m.group(1)).strip()


def _drop_block_environments(text: str) -> str:
    envs = [
        "figure", "figure*", "table", "table*", "equation", "equation*", "align", "align*",
        "tikzpicture", "tabular", "tabular*", "longtable", "CCSXML", "comment", "lstlisting",
    ]
    for env in envs:
        pattern = re.compile(rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}", flags=re.DOTALL)
        text = pattern.sub("\n", text)
    return text


def _latex_to_text(text: str) -> str:
    text = _strip_comments(text)
    text = re.sub(r"\\iffalse.*?\\fi", " ", text, flags=re.DOTALL)
    text = _drop_block_environments(text)

    text = re.sub(r"\\item\b", "\n- ", text)
    text = re.sub(r"\\begin\{(?:itemize|enumerate)\}", "\n", text)
    text = re.sub(r"\\end\{(?:itemize|enumerate)\}", "\n", text)
    text = re.sub(r"\\begin\{[^}]+\}", "\n", text)
    text = re.sub(r"\\end\{[^}]+\}", "\n", text)

    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\$[^$]*\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\\\[.*?\\\]", " ", text, flags=re.DOTALL)

    unwrap_cmds = ["textbf", "textit", "emph", "underline", "texttt", "mathrm", "mathbf", "mathit", "textrm"]
    for cmd in unwrap_cmds:
        text = re.sub(rf"\\{cmd}\s*\{{([^{{}}]*)\}}", r"\1", text)

    drop_cmds = [
        "cite", "citet", "citep", "citeauthor", "label", "ref", "eqref", "url", "footnote", "vspace",
        "hspace", "centering", "caption", "includegraphics", "maketitle", "bibliographystyle", "bibliography",
        "balance", "scriptsize", "small", "normalsize", "large", "Huge", "huge", "clearpage", "newpage",
    ]
    for cmd in drop_cmds:
        text = re.sub(rf"\\{cmd}(?:\[[^\]]*\])?\s*\{{[^{{}}]*\}}", " ", text)
        text = re.sub(rf"\\{cmd}\b", " ", text)

    text = re.sub(r"\\newcommand\s*\{[^}]+\}(?:\[[^\]]*\])?\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", " ", text)
    text = re.sub(r"\\def\\[a-zA-Z@]+\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", " ", text)

    text = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    cleaned_lines: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if " /.style" in line or "/.style" in line:
            continue
        if "node distance" in line or "Latex[length" in line:
            continue
        if re.match(r"^(enumerate\*?|itemize|tabular\*?|longtable|adjustbox|tikzpicture)\b", line):
            continue
        if len(re.findall(r"[A-Za-z]", line)) < 3 and not line.startswith("-"):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def _extract_sections(body_tex: str) -> List[Tuple[str, str]]:
    pattern = re.compile(r"\\(section|subsection|subsubsection)\*?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", flags=re.DOTALL)
    matches = list(pattern.finditer(body_tex))
    if not matches:
        return []

    sections: List[Tuple[str, str]] = []
    for i, m in enumerate(matches):
        title = _latex_to_text(m.group(2)).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body_tex)
        content = _latex_to_text(body_tex[start:end]).strip()
        if title or content:
            sections.append((title, content))
    return sections


def preprocess_paper_folder(paper_dir: Path, output_dir: Path = OUTPUT_DIR) -> Optional[Path]:
    main_tex = _find_main_tex(paper_dir)
    if not main_tex:
        return None

    raw_main = main_tex.read_text(encoding="utf-8", errors="ignore")
    raw_main = _strip_comments(raw_main)
    expanded_full = _expand_includes(raw_main, main_tex.parent, seen={main_tex.resolve()})

    body = _extract_body(expanded_full)
    title = _extract_title(expanded_full)
    abstract = _extract_abstract(body)
    sections = _extract_sections(body)

    parts: List[str] = []
    if title:
        parts.append(title.upper())
    if abstract:
        parts.append("ABSTRACT\n" + abstract)

    for sec_title, sec_text in sections:
        if sec_title and sec_text:
            parts.append(f"{sec_title}\n{sec_text}")
        elif sec_title:
            parts.append(sec_title)

    if not parts:
        cleaned = _latex_to_text(body)
        if cleaned:
            parts.append(cleaned)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{paper_dir.name}.txt"
    out_path.write_text("\n\n".join(p for p in parts if p.strip()) + "\n", encoding="utf-8")
    return out_path


def run_all(input_root: Path = RAW_DATA_DIR, output_dir: Path = OUTPUT_DIR) -> List[Path]:
    outputs: List[Path] = []
    if not input_root.exists():
        return outputs

    for sub in sorted(input_root.iterdir()):
        if not sub.is_dir():
            continue
        out = preprocess_paper_folder(sub, output_dir=output_dir)
        if out:
            outputs.append(out)
    return outputs


if __name__ == "__main__":
    generated = run_all()
    print("Generated files:")
    for p in generated:
        print(f"- {p}")
