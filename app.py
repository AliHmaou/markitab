from __future__ import annotations
from typing import List, Tuple

from docling.document_converter import DocumentConverter

import gradio as gr
import shutil, tempfile
from pathlib import Path

def convert_directory(
    directory: Path | str,
    theme: str,
    objectif: str,
    output_markdown: Path | str = "dossier_documentaire.md",
) -> None:
    """Parcourt *directory* et consolide les documents en un document Markdown
    consolidé.
    """
    EXTENSIONS = {
        "pdf",
        "docx", "xlsx", "pptx",
        "md",
        "adoc", "asciidoc",
        "html", "xhtml",
        "csv",
        "png", "jpeg", "jpg", "tiff", "bmp",
    }

    directory = Path(directory)

    if not directory.is_dir():
            raise NotADirectoryError(f"{directory} n'est pas un répertoire valide")
    
    doc_paths = sorted(
        p for p in directory.rglob("*")
        if p.is_file() and p.suffix.lstrip(".").lower() in EXTENSIONS
    )

    if not doc_paths:
        raise FileNotFoundError("Aucun fichier PDF trouvé dans le répertoire")
    
    output_markdown = Path(output_markdown)

    converter = DocumentConverter()

    # Accumulate markdown blocks, index entries and temp‑PDFs to merge.
    markdown_blocks: List[str] = ["# Dossier documentaire\n", f"**Thème : {theme}**\n", f"**Objectif du dossier : {objectif}**\n" ]
    index_entries: List[str] = ["\n## Index des documents \n"]

    current_global_page = 1

    

    # First pass – convert each PDF, capture markdown pages and produce a temp PDF.
    all_docs_pages: List[Tuple[str, List[str]]] = []
    for doc_path in doc_paths:
        result = converter.convert(str(doc_path))

        pages_md: List[str] = [
            result.document.export_to_markdown(page_no=i)
            for i in range(len(result.document.pages)+1)
        ]
        all_docs_pages.append((doc_path.name, pages_md))

        # Index
        index_entries.append(f"p. {current_global_page} \t : \t {doc_path.name} \n")
        current_global_page += len(pages_md)

    # Add index to markdown.
    markdown_blocks.extend(index_entries)

    # Second pass – build content section.
    for file_name, pages_md in all_docs_pages:
        markdown_blocks.append("\n\n---\n\n")  # Saut de page dans le markdown
        markdown_blocks.append(f"*Début du document : {file_name}*\n")
        for page_number, page_md in enumerate(pages_md, start=0):
            markdown_blocks.append(f"*Début de la page {page_number} du doc : {file_name}*\n")
            markdown_blocks.append(page_md.strip())
            markdown_blocks.append(f"\n*Fin de la page {page_number} du doc : {file_name}**\n")
            markdown_blocks.append("\n\n---\n\n")  # Saut de page dans le markdown
        markdown_blocks.append(f"*Fin du document : {file_name}*\n")

    # Écriture du markdown consolidé.
    output_markdown.write_text("\n".join(markdown_blocks), encoding="utf-8")
    print(f"✅ Markdown écrit → {output_markdown.resolve()}")

# --- petit wrappeur multifile ---
def run_convert(files: list[str],
                theme: str,
                objectif: str,
                output_markdown: str = "dossier_documentaire.md") -> str:
    """
    Copie les fichiers uploadés dans un dossier temporaire,
    appelle convert_directory, puis renvoie le chemin du markdown.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for f in files:                         # f est un chemin vers le fichier uploadé
            shutil.copy(f, tmp_path / Path(f).name)
        convert_directory(tmp_path, theme, objectif, output_markdown)
    return str(Path(output_markdown).resolve())  # Gradio générera le téléchargement

# --- IHM Gradio multifile ---
with gr.Blocks(title="Dossier documentaire") as demo:
    gr.Markdown("## Générer un dossier documentaire à partir de fichiers")

    files_in    = gr.Files(label="Fichiers source (plusieurs); extensions PDF, DOCX, PNG…",
                           file_count="multiple")
    theme_in    = gr.Textbox(label="Thème")
    obj_in      = gr.Textbox(label="Objectif")
    out_name_in = gr.Textbox(label="Nom du fichier markdown de sortie",
                             value="dossier_documentaire.md")

    launch_btn  = gr.Button("Convertir 📄➡️📝")
    md_out      = gr.File(label="Markdown généré")

    launch_btn.click(run_convert,
                     inputs=[files_in, theme_in, obj_in, out_name_in],
                     outputs=md_out)

if __name__ == "__main__":
    demo.launch()