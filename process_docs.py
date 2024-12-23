def show_document_upload():
    import os
    import streamlit as st
    import hashlib
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_core.embeddings import DeterministicFakeEmbedding
    from uuid import uuid4
    from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        Docx2txtLoader,
        CSVLoader,
        UnstructuredImageLoader,
        UnstructuredPowerPointLoader,
        UnstructuredEPubLoader,
        UnstructuredMarkdownLoader,
        UnstructuredExcelLoader
    )
    from langchain_fireworks import FireworksEmbeddings

    import nltk
    nltk.download('all', quiet=True)

    # Configuration
    CHROMA_DB_PATH = "chroma_db"
    UPLOAD_PATH = "uploaded_files"
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    os.makedirs(UPLOAD_PATH, exist_ok=True)

    # Initialize Chroma vector store
    embeddings = FireworksEmbeddings(
    model="nomic-ai/nomic-embed-text-v1.5",
)
    vector_store = Chroma(
        collection_name="uploaded_files",
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )

    def calculate_file_hash(file_content):
        """Calculate SHA-256 hash of file content to prevent duplicates"""
        return hashlib.sha256(file_content).hexdigest()

    def get_loader_for_file(file_path):
        """Return appropriate loader based on file extension"""
        extension = os.path.splitext(file_path)[1].lower()
        
        loaders = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.docx': Docx2txtLoader,
            '.csv': CSVLoader,
            '.jpg': UnstructuredImageLoader,
            '.jpeg': UnstructuredImageLoader,
            '.png': UnstructuredImageLoader,
            '.pptx': UnstructuredPowerPointLoader,
            '.ppt': UnstructuredPowerPointLoader,
            '.epub': UnstructuredEPubLoader,
            '.md': UnstructuredMarkdownLoader,
            '.xlsx': UnstructuredExcelLoader,
            '.xls': UnstructuredExcelLoader
        }
        
        return loaders.get(extension)

    def process_uploaded_file(uploaded_file):
        """Process a single uploaded file"""
        try:
            # Get file content and calculate hash
            file_content = uploaded_file.getvalue()
            file_hash = calculate_file_hash(file_content)
            
            # Check for duplicates
            existing_files = os.listdir(UPLOAD_PATH)
            for existing_file in existing_files:
                with open(os.path.join(UPLOAD_PATH, existing_file), 'rb') as f:
                    if calculate_file_hash(f.read()) == file_hash:
                        return False, f"File '{uploaded_file.name}' is a duplicate of '{existing_file}'"
            
            # Save the file locally
            file_path = os.path.join(UPLOAD_PATH, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Get appropriate loader
            LoaderClass = get_loader_for_file(file_path)
            
            if LoaderClass is None:
                os.remove(file_path)
                return False, f"Unsupported file type: {os.path.splitext(uploaded_file.name)[1]}"
            
            # Load and process the document
            loader = LoaderClass(file_path)
            documents = loader.load()
            
            # Add metadata to each document
            for doc in documents:
                doc.metadata.update({
                    "file_name": uploaded_file.name,
                    "file_path": file_path,
                    "file_type": os.path.splitext(uploaded_file.name)[1],
                    "id": str(uuid4()),
                    "file_hash": file_hash
                })
            
            # Add documents to vector store
            vector_store.add_documents(documents)
            return True, f"Successfully processed {len(documents)} document(s) from '{uploaded_file.name}'"
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return False, f"Error processing file '{uploaded_file.name}': {str(e)}"

    def search_documents(query, k=5):
        """Search documents in the vector store"""
        results = vector_store.similarity_search(query, k=k)
        return results

    # Streamlit UI
    st.title("Document Management System")

    # File upload section
    st.header("Upload Files")
    file_types = ["pdf", "txt", "docx", "csv", "jpg", "jpeg", "png", "pptx", "ppt", "epub", "md", "xlsx", "xls"]
    uploaded_files = st.file_uploader("Choose files", type=file_types, accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            success, message = process_uploaded_file(uploaded_file)
            if success:
                st.success(message)
            else:
                st.warning(message)
    st.markdown("---")
    # Display uploaded files
    st.header("Uploaded Files")
    uploaded_files = os.listdir(UPLOAD_PATH)
    if uploaded_files:
        with st.expander("Available Files"):

            for file in uploaded_files:
                st.text(f"📄 {file}")
    else:
        st.info("No files uploaded yet.")

    def concatenate_file_contents(results):
        """Concatenate contents from the same file and remove duplicates."""
        content_by_file = {}
        
        for doc in results:
            file_name = doc.metadata['file_name']
            if file_name not in content_by_file:
                content_by_file[file_name] = {
                    'content': [],
                    'metadata': doc.metadata
                }
            content_by_file[file_name]['content'].append(doc.page_content)
        
        return content_by_file

    def search_and_display_results(search_query, vector_store):
        """Search documents and display concatenated results."""
        results = vector_store.similarity_search(search_query)
        
        if not results:
            st.info("No matching documents found.")
            return
        
        concatenated_results = concatenate_file_contents(results)
        
        st.subheader("Search Results")
        
        for file_name, data in concatenated_results.items():
            with st.expander(f"📄 {file_name}"):
                # Combine all content segments
                full_content = " ".join(data['content'])
                
                # Display metadata
                st.write("**File Details:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"File Type: {data['metadata']['file_type']}")
                with col2:
                    st.write(f"Location: {data['metadata']['file_path']}")
                
                # Display concatenated content with preview
                st.write("**Content Preview:**")
                st.write(full_content)
    st.header("Search Documents")
    search_query = st.text_input("Enter search query", placeholder="Type your search terms here...")

    if search_query:
        search_and_display_results(search_query, vector_store)
