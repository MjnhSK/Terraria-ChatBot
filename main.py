import chainlit as cl
from sklearn.metrics.pairwise import cosine_similarity

# Langchain imports
from langchain_core.prompts import PromptTemplate
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferWindowMemory, ConversationBufferMemory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Langchain-OLLAMA specific import
from langchain_ollama import OllamaLLM

# Chainlit imports
from chainlit.types import ThreadDict

# FastAPI imports
from fastapi import Request, Response

# Constants
DB_FAISS_PATH = "vectorstores/db_faiss"
LLAMA_MODEL = "llama3.2:3b"
EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Custom Prompt Template
custom_prompt_template = """
You are a helpful assistant. Use the following conversation history and context to provide a concise answer, only referencing history when needed.

Conversation History: {chat_history}

Context: {context}

Question: {question}

Answer:
"""

def set_custom_prompt():
    """Return a custom prompt template."""
    return PromptTemplate(template=custom_prompt_template, input_variables=['chat_history', 'context', 'question'])

def load_llm():
    """Load the Ollama LLM with required settings."""
    try:
        llm = OllamaLLM(
            model=LLAMA_MODEL,
            verbose=True,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        )
        return llm
    except Exception as e:
        raise RuntimeError(f"Failed to load LLM: {e}")

def compute_similarity(question, previous_question):
    """Compute cosine similarity between two questions."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
    try:
        question_embedding = embeddings.embed_query(question)
        prev_embedding = embeddings.embed_query(previous_question)
        return cosine_similarity([question_embedding], [prev_embedding])[0][0]
    except Exception as e:
        raise RuntimeError(f"Error in computing similarity: {e}")

def reset_memory_if_topic_changes(new_question, memory):
    """Reset memory if a topic change is detected."""
    if memory.chat_memory.messages:
        last_question = memory.chat_memory.messages[-1].content
        if compute_similarity(new_question, last_question) < 0.15:
            memory.clear()

def retrieval_qa_chain(llm, db, memory):
    """Set up the Conversational Retrieval Chain with custom prompt."""
    prompt = set_custom_prompt()
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=db.as_retriever(search_kwargs={'k': 2}),
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": prompt},
        verbose=False
    )

def qa_bot():
    """Initialize the QA bot with embeddings, database, LLM, and memory."""
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL, model_kwargs={'device': 'cpu'})
        db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        llm = load_llm()

        memory = ConversationBufferWindowMemory(k=3, memory_key="chat_history", input_key="question", output_key="answer", return_messages=True)
        return retrieval_qa_chain(llm, db, memory)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize QA bot: {e}")

# Chainlit event handlers
@cl.on_logout
def on_logout(request: Request, response: Response):
    response.delete_cookie("my_cookie")

@cl.password_auth_callback
def auth():
    return cl.User(identifier="User12345")

@cl.on_chat_start
async def start():
    """Initialize chat with welcome message and QA bot."""
    try:
        chain = qa_bot()
        cl.user_session.set("chain", chain)
        cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))

        welcome_message = cl.Message(content="Hi, Welcome to Chat With Documents using Ollama (Llama3.2:3B) and LangChain. Please keep testing even if Terminal displays errors, since it does not affect the performance in some cases!")
        await welcome_message.send()
    except Exception as e:
        await cl.Message(content=f"Error initializing the bot: {e}").send()

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """Resume chat and set memory from the previous session."""
    try:
        chain = qa_bot()
        memory = ConversationBufferMemory(return_messages=True)
        root_messages = [m for m in thread["steps"] if m["parentId"] is None]
        
        for message in root_messages:
            if message["type"] == "user_message":
                memory.chat_memory.add_user_message(message["output"])
            else:
                memory.chat_memory.add_ai_message(message["output"])
        
        cl.user_session.set("memory", memory)
        cl.user_session.set("chain", chain)
    except Exception as e:
        await cl.Message(content=f"Error resuming chat: {e}").send()

@cl.on_message
async def on_message(message):
    """Handle incoming user messages and respond with answers."""
    chain = cl.user_session.get("chain")
    memory = cl.user_session.get("memory")

    if not chain:
        await cl.Message(content="Bot initialization failed. Please restart the chat.").send()
        return

    reset_memory_if_topic_changes(message.content, memory)

    try:
        inputs = {"question": message.content, "chat_history": memory.chat_memory.messages}
        res = await chain.acall(inputs)
        answer = res.get("answer", "No answer found")
        if not res.get("source_documents"):
            answer += "\nNo Sources Found."

        await cl.Message(content=answer).send()

        memory.chat_memory.add_user_message(message.content)
        memory.chat_memory.add_ai_message(answer)
    except Exception as e:
        await cl.Message(content=f"Error during processing: {e}").send()
