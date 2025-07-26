# exam_question_predictor.py

import os
import tempfile
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
import streamlit as st

# Load environment variables
load_dotenv()

# Initialize LLM and Embeddings
llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-preview-05-20')
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")

# Define storage
persist_dir = "./vector_store"

# --- Streamlit UI ---
st.title("📚 Exam Question Predictor")
st.markdown("Predict possible exam questions based on syllabus, textbooks, and past papers.")

# File uploader
uploaded_files = st.file_uploader("Upload study materials (PDF or .txt):", type=["pdf", "txt"], accept_multiple_files=True)

# Input topic or chapter
chapter_name = st.text_input("Enter topic/chapter name (optional):")

if st.button("🔍 Predict Questions"):
    if not uploaded_files:
        st.warning("Please upload at least one document.")
        st.stop()

    # Load and split documents
    all_docs = []

for file in uploaded_files:
    print("file uploaded")
    ext = os.path.splitext(file.name)[1].lower()
    
    if ext in [".pdf", ".txt"]:
        suffix = ext
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.read())
            tmp.flush()

            if ext == ".pdf":
                loader = PyPDFLoader(tmp.name)
            else:
                loader = TextLoader(tmp.name)

            docs = loader.load()
            # print("docs", docs)

        # ❗ Filter out empty documents
        docs = [doc for doc in docs if doc.page_content.strip()]
        for doc in docs:
            doc.metadata['source'] = file.name
        all_docs.extend(docs)
        # print("doccs",all_docs)
    else:
        st.warning(f"Unsupported file format: {file.name}")
        continue

#  Split
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(all_docs)

# print("chunkssdjg", chunks)

    if not chunks:
        st.warning("No content available for vectorization. Please upload non-empty files.")
        st.stop()

    # Create vector DB
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )

    # Search relevant context
    query = f"Generate exam questions for: {chapter_name}" if chapter_name else "Generate possible exam questions from the entire syllabus."
    docs = vector_store.similarity_search(query, k=5)
    context = "\n\n".join([doc.page_content for doc in docs])

    # Ask LLM to generate questions
    system_prompt = (
        "You are a smart exam question predictor. Based on the following text chunks from textbooks, syllabus, and past papers, predict clear and relevant exam questions.\n"
        "Do not repeat content. Format each question in a new line. Always follow the question format "
    )

    full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nNow Give exactly same number of question."
    response = llm.invoke(full_prompt)

    if not response.content:
        st.error("No questions were generated. Please try again.")
    else:
        st.success("Predicted Questions:")
        for i, line in enumerate(response.content.split("\n"), 1):
            if line.strip():
                st.markdown(f"**Q{i}.** {line.strip()}")

        st.download_button("📥 Download Questions", response.content, file_name="predicted_questions.txt")
