import os
import re
import fitz  
import pandas as pd
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
import nltk
# nltk.download("punkt")

# === CONFIGURABLE PARAMETERS ===
SKIP_INTRO_PAGES = 131  # Pages to skip for font analysis
SAMPLE_PAGES_FOR_FONT = 20  # Pages used to calculate font threshold
HEADING_MIN_FONT_BUFFER = 2  # Buffer added to mean font size for heading detection

# === Topic Classifier ===
def extract_topic(text: str) -> str:
    topic_keywords = {
        "CBT": ["cognitive behavioral", "cbt", "beck"],
        "Anxiety": ["anxiety", "panic", "phobia", "worry"],
        "Depression": ["depression", "hopeless", "sad"],
        "Psychosis": ["hallucination", "delusion", "schizophrenia"],
        "PTSD": ["ptsd", "trauma", "flashback"],
        "Diagnosis": ["criteria", "diagnosis", "symptoms", "disorder"],
        "Assessment": ["assessment", "intake", "evaluation"],
        "Therapy Process": ["session", "therapist", "rapport", "treatment"]
    }
    text = text.lower()
    for topic, keywords in topic_keywords.items():
        if any(kw in text for kw in keywords):
            return topic
    return "General"


# === PDF Text Extraction with Dynamic Threshold and Heading Pattern ===
def extract_paragraphs_with_headings(pdf_path: str) -> List[Tuple[str, str]]:
    doc = fitz.open(pdf_path)
    paragraphs = []
    current_section = "Introduction"
    min_paragraph_length = 50

    font_sizes = []

    # Step 1: Collect font sizes from sample pages
    for page in doc[SKIP_INTRO_PAGES:SKIP_INTRO_PAGES + SAMPLE_PAGES_FOR_FONT]:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    if "size" in span:
                        font_sizes.append(span["size"])

    # Step 2: Compute dynamic threshold
    default_threshold = 14
    if font_sizes:
        mean_font = sum(font_sizes) / len(font_sizes)
        dynamic_font_threshold = mean_font + HEADING_MIN_FONT_BUFFER
    else:
        dynamic_font_threshold = default_threshold

    print(f"[INFO] Using dynamic heading font threshold: {dynamic_font_threshold:.2f}")

    # Step 3: Extract paragraphs and detect headings
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        current_paragraph = ""

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                line_text = " ".join([span["text"] for span in line["spans"] if span["text"].strip()])
                if not line_text:
                    continue

                font_sizes_line = [span["size"] for span in line["spans"] if "size" in span]
                if not font_sizes_line:
                    continue

                max_font = max(font_sizes_line)

                # Heading pattern detection
                is_heading_like = bool(re.match(r"^\d+(\.\d+)*\s+.+", line_text.strip())) or \
                                  (max_font >= dynamic_font_threshold and len(line_text.strip()) < 100)

                if is_heading_like:
                    if current_paragraph and len(current_paragraph) >= min_paragraph_length:
                        paragraphs.append((current_section, current_paragraph, page_num + 1))
                        current_paragraph = ""
                    current_section = line_text.strip().title()
                else:
                    current_paragraph += " " + line_text if current_paragraph else line_text

        if current_paragraph and len(current_paragraph) >= min_paragraph_length:
            paragraphs.append((current_section, current_paragraph, page_num + 1))  # +1 to make it 1-indexed

    return paragraphs

# === Improved Chunking Strategy ===
def chunk_with_metadata(paragraphs: List[Tuple[str, str]], book_path: str, book_type: str) -> List[dict]:
    book_name = os.path.splitext(os.path.basename(book_path))[0]
    chunk_id = 0
    all_chunks = []


    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  
        chunk_overlap=100,  
        length_function=len,
        separators=["\n\n", "\n\n", "\. ", "! ", "? ", "\n", " ", ""],  # Better separators
        keep_separator=True
    )

    for section_title, para, page_number in paragraphs:
        # Skip very short paragraphs
        if len(para) < 50:
            continue

        # Clean the paragraph
        para = re.sub(r'\s+', ' ', para).strip()

        # Split into chunks
        chunks = splitter.split_text(para)

        for chunk in chunks:
            # Skip very small chunks (except for the last one)
            if len(chunk) < 100 and chunk_id > 0:
                # Merge with previous chunk if too small
                if all_chunks and (len(all_chunks[-1]["text"]) + len(chunk) < 1500):
                    all_chunks[-1]["text"] += " " + chunk
                    continue

            all_chunks.append({
                "text": chunk,
                "book_name": book_name,
                "book_type": book_type,
                "section_title": section_title,
                "topic": extract_topic(chunk),
                "page_number": page_number,
                "chunk_id": f"{book_name}_{chunk_id}"
            })
            chunk_id += 1

    return all_chunks
# === Full Book Processing ===
def process_book(
    pdf_path: str,
    book_type: str = "treatment",
    export_path: str = None
) -> List[dict]:
    print(f"Processing: {pdf_path}")
    paragraphs = extract_paragraphs_with_headings(pdf_path)
    chunks = chunk_with_metadata(paragraphs, pdf_path, book_type)

    if export_path:
        df = pd.DataFrame(chunks)
        df.to_csv(export_path, index=False)
        print(f"Exported {len(chunks)} chunks to {export_path}")
    return chunks

# def export_debug_html(chunks: List[dict], export_path: str = "debug_output.html") -> None:
#     html_content = "<html><body><h1>Chunk Review</h1>"
#     for chunk in chunks:
#         html_content += f"<h2>{chunk['section_title']} - {chunk['chunk_id']}</h2>"
#         html_content += f"<p>{chunk['text']}</p><hr>"
#     html_content += "</body></html>"

#     with open(export_path, "w") as file:
#         file.write(html_content)
#     print(f"Exported debug output to {export_path}")


# === Example Usage ===
if __name__ == "__main__":
    dsm_chunks = process_book("./docs/DSM-book.pdf", book_type="reference", export_path="dsm_chunks.csv", )
    # clinical_chunks = process_book("/content/_Clinical Psychology_ Science, Practice, and Diversity2020.pdf", book_type="practice", export_path="clinical_chunks.csv")
    # export_debug_html(dsm_chunks)

    texts = [chunk["text"] for chunk in dsm_chunks]
    metadatas = [{k: v for k, v in chunk.items() if k != "text"} for chunk in dsm_chunks]

    # texts = [chunk["text"] for chunk in dsm_chunks + clinical_chunks]
    # metadatas = [{k: v for k, v in chunk.items() if k != "text"} for chunk in dsm_chunks + clinical_chunks]
