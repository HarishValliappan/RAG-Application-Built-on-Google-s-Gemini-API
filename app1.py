import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

st.title("RAG Application built on Google's Gemini API")

urls = [
    'https://www.bentleymotors.com/en/your-bentley/accessories.html',
    'https://www.bentleymotors.com/en/about-bentley/history-and-heritage.html',
    'https://www.bentleymotors.com/en/models.html#card-item-d6be51a31b',
    'https://www.bentleymotors.com/en/models/bentley-hybrids.html'
]

# Load documents
loader = UnstructuredURLLoader(urls=urls)
data = loader.load()

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
docs = text_splitter.split_documents(data)

# Set up environment variables for Chroma
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
)

# Set up retriever
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# Set up language model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.4, max_tokens=800, google_api_key=GOOGLE_API_KEY)

# Define the system prompt template
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

query = st.text_input("Ask a question:")
if query:
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = rag_chain.invoke({"input": query})
    st.write(response["answer"])
