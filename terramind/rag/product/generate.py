"""
Product RAG — prompt template and LLM answer generation.

TODO: Move from Rag_Pc.py:
  - RAG_PROMPT ChatPromptTemplate (context + question + answer rules)
  - Function: generate_answer(context, question) -> str (ChatOpenAI gpt-4o-mini)
  - Keep “answer only from context” rules in the template
See docs/PROJECT_STATUS.md (product migration).
"""
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

from terramind.rag.product.config import (
    CHAT_MODEL,
    RAG_PROMPT,
)

from terramind.rag.product.retrieve import (
    retrieve_chunks,
)

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
def generate_answer_with_chunks(
    question: str,
):
    """
    Retrieve relevant chunks and
    generate a grounded answer.

    Returns the final answer together with the
    retrieved chunks, so callers (e.g. evaluation)
    can inspect what was used as context.
    """

    # Retrieve relevant product information
    chunks = retrieve_chunks(
        question
    )

    if not chunks:

        return (
            "I could not find relevant "
            "information in the product catalog.\n\n"
            "Please rephrase your question "
            "or provide more details."
        ), chunks

    # Convert retrieved chunks into prompt context
    context = format_context(
        chunks
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

    # Debug helper:
    # print("\n=== CONTEXT ===\n")
    # print(context)

    # Generate grounded answer from retrieved context
    response = llm.invoke(
        prompt
    )


    # Return answer together with retrieval sources
    answer = (
        f"{response.content}\n\n"
        f"---\n\n"
        f"### Sources\n"
        f"{sources}"
    )

    return answer, chunks


def generate_answer(
    question: str,
) -> str:
    """
    Retrieve relevant chunks and
    generate a grounded answer.
    """

    answer, _chunks = generate_answer_with_chunks(
        question
    )

    return answer


# Development Test
# 
# Run this file directly to validate:
# - Retrieval
# - Prompt formatting
# - LLM generation
# - Source attribution
if __name__ == "__main__":

    question = (
        "What should I spray for red spider mites on citrus?"
    )

    answer = generate_answer(
        question
    )

    print(
        "\nAnswer:\n"
    )

    print(
        answer
    )