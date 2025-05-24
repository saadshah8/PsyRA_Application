import os
from groq import Groq
from utils.code_files.retriever import rag_retriever
from typing import List, Any

class Agent:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.messages = []
        self.has_system_prompt = False
        self.user_id = None

    def set_user_id(self, user_id: str):
        """Set the user ID for this agent instance."""
        self.user_id = user_id

    def system_prompt(self, prompt: str):
        """Set the system prompt for the agent."""
        if not prompt.strip():
            raise ValueError("System prompt cannot be empty.")
        self.messages.append({"role": "system", "content": prompt})
        self.has_system_prompt = True

    def is_context_relevant(self, user_input: str, retrieved_docs: List[Any]) -> bool:
        """Check if retrieved context is relevant using keyword matching."""
        if not retrieved_docs:
            return False
        user_words = set(user_input.lower().split())
        for doc in retrieved_docs:
            doc_words = set(doc.page_content.lower().split())
            common_words = user_words.intersection(doc_words)
            if len(common_words) / len(user_words) > 0.2:
                return True
        return False

    def format_context(self, retrieved_docs: List[Any]) -> str:
        """Format retrieved documents into context and source citations."""
        if not retrieved_docs:
            return "No relevant context was retrieved from the knowledge base."

        context_text = "\n--- Retrieved Sources ---\n"
        relevant_context = []
        for i, doc in enumerate(retrieved_docs, 1):
            section = doc.metadata.get("section_title", "Unknown Section")
            topic = doc.metadata.get("topic", "Unknown Topic")
            book = doc.metadata.get("book_name", "Unknown Book")
            page = doc.metadata.get("page_number", "N/A")
            context_text += f"[{i}] {book} - {section} | Topic: {topic} | Page: {page}\n"
            relevant_context.append(doc.page_content)

        context_body = "\n\n".join(relevant_context) or "No relevant context was retrieved."
        return f"{context_body.strip()}\n\n{context_text.strip()}"

    def _invoke(self):
        """Invoke the Groq API with streaming."""
        try:
            response = self.client.chat.completions.create(
                messages=self.messages,
                model="llama-3.3-70b-versatile",  # Use original model
                stream=True,
                temperature=0.4
            )
            return response
        except Exception as e:
            error_message = f"I encountered an error: {str(e)}. Please try again with a different query."
            self.messages.append({"role": "assistant", "content": error_message})
            return None

    def chat(self, message: str):
        """Process a user message with RAG context and return the assistant's response."""
        if not self.has_system_prompt:
            raise ValueError("System prompt is required before starting a conversation.")

        # Retrieve relevant docs using RAG
        retrieved_docs = rag_retriever.invoke(message)
        context_relevant = self.is_context_relevant(message, retrieved_docs)

        if not context_relevant:
            full_input = (
                f"{message.strip()}\n\n"
                f"--- SYSTEM NOTE: No relevant context was retrieved. Please provide a general, supportive response. ---"
            )
        else:
            context = self.format_context(retrieved_docs)
            full_input = (
                f"{message.strip()}\n\n"
                f"--- SYSTEM NOTE: The following clinical knowledge base context was retrieved. Use it to inform your response. Don't Cite it if used. ---\n"
                f"{context}"
            )

        # Append the full input (user message + context) to messages for the LLM
        self.messages.append({"role": "user", "content": full_input})

        response = self._invoke()
        if response is None:
            return self.messages[-1]["content"]

        # Collect streamed response
        response_message = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                response_message += chunk.choices[0].delta.content

        self.messages.append({"role": "assistant", "content": response_message})
        return response_message, message  # Return both response and original user message