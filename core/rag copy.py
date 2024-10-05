import os
from langchain.document_loaders import UnstructuredLoader
from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import requests
from langchain.agents import tool
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.chains import ConversationalRetrievalChain

# Mendapatkan BASE_DIR (root proyek)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, 'knowledge_base')

def load_documents(directory):
    documents = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            loader = UnstructuredLoader(filepath)
            documents.extend(loader.load())
    return documents

def add_initial_knowledge(documents):
    initial_knowledge = """
    This is the TerraFarm RAG project.
    The purpose of this project is to help farmers provide watering recommendations based on weather data and historical data.
    """
    initial_doc = Document(page_content=initial_knowledge)
    documents.append(initial_doc)
    return documents

def build_vectorstore(documents):
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(documents, embeddings, persist_directory='db/')
    vectorstore.persist()
    return vectorstore

def get_weather_data(location):
    api_key = os.getenv('WEATHER_API_KEY')
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&lang=id&units=metric"
    response = requests.get(url)
    data = response.json()
    return data

def get_irrigation_history(crop_type):
    # Implementasi untuk mengambil data historis penyiraman
    # Misalnya, dari database atau API internal
    return "Data historis penyiraman untuk padi adalah ..."

@tool
def get_current_weather(location: str) -> str:
    """Mengambil data cuaca saat ini untuk lokasi tertentu."""
    data = get_weather_data(location)
    if data.get('weather'):
        weather_info = f"Cuaca saat ini di {location} adalah {data['weather'][0]['description']} dengan suhu {data['main']['temp']}°C."
    else:
        weather_info = f"Tidak dapat mengambil data cuaca untuk lokasi {location}."
    return weather_info

@tool
def get_crop_irrigation_history(crop_type: str) -> str:
    """Mengambil data historis penyiraman untuk jenis tanaman tertentu."""
    history = get_irrigation_history(crop_type)
    return history

def initialize_rag_agent():
    llm = OpenAI(model_name='gpt-4', temperature=0)
    tools = [get_current_weather, get_crop_irrigation_history]
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    return agent

def create_qa_chain(llm, retriever):
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm,
        retriever,
        return_source_documents=True
    )
    return qa_chain

# Inisialisasi vectorstore dan agent
def setup_rag_system():
    documents = load_documents('knowledge-base/')
    documents = add_initial_knowledge(documents)
    vectorstore = build_vectorstore(documents)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = OpenAI(model_name='gpt-4', temperature=0)
    qa_chain = create_qa_chain(llm, retriever)
    agent = initialize_rag_agent()
    return qa_chain, agent

# Menyimpan riwayat percakapan
chat_history = []

# Fungsi untuk menjawab pertanyaan
def answer_question(question):
    qa_chain, agent = setup_rag_system()
    response = qa_chain({"question": question, "chat_history": chat_history})
    chat_history.append((question, response['answer']))
    return response['answer']
