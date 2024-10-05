import os
import openai
import fitz  # PyMuPDF
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings  # Updated import
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key is None:
    raise Exception("No OpenAI API key found. Please set it as an environment variable or in main.py")

# Function to load documents from the knowledge-base directory using PyMuPDF (fitz)
def load_documents(directory):
    documents = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and filename.endswith('.pdf'):
            # Using PyMuPDF to load and extract text from PDF
            with fitz.open(filepath) as pdf:
                text = ""
                for page_num in range(pdf.page_count):
                    page = pdf[page_num]
                    text += page.get_text()
            # Create a Document object with extracted text
            documents.append(Document(page_content=text, metadata={"source": filename}))  # Add metadata if needed
    return documents

# Function to add initial knowledge to documents
def add_initial_knowledge(documents):
    initial_knowledge = """
    This is the TerraFarm RAG project. The purpose of this project is to help farmers with tailored recommendations.
    """
    documents.append(Document(page_content=initial_knowledge))
    return documents

# Function to build the vector store for searching through documents
def build_vectorstore(documents):
    embeddings = OpenAIEmbeddings()  # Use the updated class
    vectorstore = Chroma.from_documents(documents, embeddings, persist_directory='db/')
    vectorstore.persist()
    return vectorstore

# Function to create the QA chain with retriever
def create_qa_chain(llm, retriever):
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm, retriever, return_source_documents=True
    )
    return qa_chain

# Setup RAG system (Load documents, build vectorstore, and create QA chain)
def setup_rag_system():
    documents = load_documents('knowledge-base/')
    documents = add_initial_knowledge(documents)
    vectorstore = build_vectorstore(documents)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = OpenAI(model_name='gpt-4', temperature=0)
    qa_chain = create_qa_chain(llm, retriever)
    return qa_chain

# Function to answer question by querying the QA chain
chat_history = []  # Maintain a history of conversations

def answer_question(question):
    qa_chain = setup_rag_system()  # Initialize the RAG system
    response = qa_chain({"question": question, "chat_history": chat_history})
    chat_history.append((question, response['answer']))  # Add question and answer to chat history
    return response['answer']
