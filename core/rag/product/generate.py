"""Product RAG — prompt template and LLM answer generation."""
# Product Answer Generation
# 
# Responsible for generating grounded answers using:
# - Retrieved Product RAG chunks
# - Product RAG prompt template
# - GPT-4o-mini
#
# Pipeline:
# User Question
# → Retrieve Relevant Chunks
# → Build Context
# → Apply Product Prompt
# → Generate Answer
# → Attach Retrieval Sources
#
# The model must answer only from retrieved product information.

from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma

from core.rag.product.config import (
    CHAT_MODEL,
    RAG_PROMPT,
)

from core.rag.product.hybrid import (
    hybrid_retrieve,
)

from core.rag.product.rerank import (
    rerank_chunks,
)

from core.rag.product.rewrite import (
    rewrite_query,
)
from core.rag.product.store import load_vector_store

# Context Builder
# 
# Convert retrieved chunks into a single context block that can be
# inserted into the Product RAG prompt.

def format_context(
    chunks,
) -> str:
    """
    Convert retrieved chunks into
    prompt context.
    """

    blocks = []
    
    # Add chunk labels to help the LLM distinguish sources
    for i, chunk in enumerate(
        chunks,
        start=1,
    ):
        blocks.append(
            f"[Chunk {i}]\n"
            f"{chunk.page_content}"
        )

    return "\n\n".join(
        blocks
    )

# Source Formatter
# 
# Build a unique source list from retrieved chunks.
#
# Sources are appended to the final answer to improve
# transparency and debugging.
def format_sources(
    chunks,
) -> str:
    """
    Build a unique source list
    from retrieved chunks.
    """
    
    # Prevent duplicate source entries
    seen = set()
    sources = []

    for chunk in chunks:
        source = (
            chunk.metadata.get(
                "product_id"
            ),
            chunk.metadata.get(
                "product_name"
            ),
           
        )

        if source not in seen:

            seen.add(
                source
            )

            sources.append(

              f"- {source[1]} "
              f"({source[0]}) "
        )

    return "\n".join(
        sources
    )

    


# Create the Product RAG language model used for answer generation.
def create_llm():
    """
    Create Product RAG chat model.
    """

    return ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0,
    )

# Product RAG Generation
# 
# End-to-end Product RAG flow:
#
# 1. Retrieve relevant chunks
# 2. Build prompt context
# 3. Generate grounded answer
# 4. Append retrieval sources
#
# Returns:
# Final user-facing answer with source references.
def generate_answer(
    db: Chroma,
    question: str,
) -> str:
    """
    Retrieve relevant chunks and
    generate a grounded answer.
    """
    
    retrieval_query = rewrite_query(
    question
    )

    print(
        f"\nOriginal Query: {question}"
    )

    print(
        f"Rewritten Query: {retrieval_query}\n"
    )

    candidates = hybrid_retrieve(
        db,
        retrieval_query,
        k=8,
    )

    # Cross Encoder Re-ranking
    chunks = rerank_chunks(
        question,
        candidates,
        top_k=3,
    )

    
    
    # Convert retrieved chunks into prompt context
    context = format_context(
        chunks
    )
    
    if not chunks:

        return (
            "I could not find relevant "
            "information in the product catalog.\n\n"
            "Please rephrase your question "
            "or provide more details."
        )


    # Build source references for answer transparency
    sources = format_sources(
        chunks
    )
    
    # Inject context and user question into the Product RAG prompt
    prompt = RAG_PROMPT.format(
        context=context,
        question=question,
    )

    llm = create_llm()
    
    # Generate grounded answer from retrieved context
    response = llm.invoke(
        prompt
    )
    

    # Return answer together with retrieval sources
    return (
        f"{response.content}\n\n"
        f"---\n\n"
        f"### Sources\n"
        f"{sources}"
    )



def generate_answer_with_metadata(
    db: Chroma,
    question: str,
):
    """
    Return answer together with retrieved chunks.
    """

    retrieval_query = rewrite_query(
    question
    )

    print(
        f"\nOriginal Query: {question}"
    )
    
    print(
        f"Rewritten Query: {retrieval_query}\n"
    )
    
    candidates = hybrid_retrieve(
        db,
        retrieval_query,
        k=8,
    )

    chunks = rerank_chunks(
        question,
        candidates,
        top_k=3,
    )

    context = format_context(
        chunks
    )

    if not chunks:

        return {
            "answer":
                "I could not find relevant information in the product catalog.",
            "retrieved": [],
        }

    prompt = RAG_PROMPT.format(
        context=context,
        question=question,
    )

    llm = create_llm()

    response = llm.invoke(
        prompt
    )

    return {
        "answer": response.content,
        "retrieved": chunks,
    }

    
# Development Test
# 
# Run this file directly to validate:
# - Retrieval
# - Prompt formatting
# - LLM generation
# - Source attribution
if __name__ == "__main__":

    question = (
        "What is the dilution for Onion-Ginger-Garlic Bacteria Clear?"
    )

    answer = generate_answer(
        load_vector_store(),
        question
    )

    print(
        "\nAnswer:\n"
    )

    print(
        answer
    )