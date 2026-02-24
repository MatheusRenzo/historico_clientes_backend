import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from parametro.services import get_parametro_cliente #, get_sufixo_api_jira, get_prefixo_api_jira
from .models import RagDocument


# Guardar índice local por cliente (simples)
_FAISS_BY_CLIENTE: dict[int, FAISS] = {}


def _build_vectorstore_for_cliente(cliente_id: int) -> FAISS:
    docs_qs = RagDocument.objects.filter(cliente_id=cliente_id).only("titulo", "conteudo", "fonte")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    lc_docs: list[Document] = []

    for d in docs_qs:
        chunks = splitter.split_text(d.conteudo)
        for i, chunk in enumerate(chunks):
            lc_docs.append(
                Document(
                    page_content=chunk,
                    metadata={"titulo": d.titulo, "fonte": d.fonte, "chunk": i},
                )
            )

    #embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    OPENAI_API_KEY = get_parametro_cliente(str(cliente_id), "OPEN_API_KEY")#os.getenv("OPENAI_API_KEY")
    embeddings = OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    api_key=OPENAI_API_KEY,
                    )
    return FAISS.from_documents(lc_docs, embeddings)


def get_or_build_index(cliente_id: int) -> FAISS:
    if cliente_id not in _FAISS_BY_CLIENTE:
        _FAISS_BY_CLIENTE[cliente_id] = _build_vectorstore_for_cliente(cliente_id)
    return _FAISS_BY_CLIENTE[cliente_id]


def rag_answer(cliente_id: int, pergunta: str, k: int = 4) -> dict:
    vs = get_or_build_index(cliente_id)
    retriever = vs.as_retriever(search_kwargs={"k": k})

    context_docs = retriever.invoke(pergunta)
    context = "\n\n".join(
        f"[{i+1}] {d.metadata.get('titulo','')} ({d.metadata.get('fonte','')})\n{d.page_content}"
        for i, d in enumerate(context_docs)
    )

    #llm = ChatOpenAI(model="gpt-4.1-mini")  # ajuste o modelo conforme seu plano/latência
    OPENAI_API_KEY = get_parametro_cliente(str(cliente_id), "OPEN_API_KEY")
    llm = ChatOpenAI(
                    model="gpt-4.1-mini",
                    api_key=OPENAI_API_KEY,
                )   
    prompt = f"""
Você é um assistente que responde usando APENAS o contexto abaixo.
Se não houver evidência no contexto, diga que não encontrou.

CONTEXTO:
{context}

PERGUNTA:
{pergunta}
""".strip()

    resp = llm.invoke(prompt)
    return {
        "answer": getattr(resp, "content", str(resp)),
        "sources": [d.metadata for d in context_docs],
    }
