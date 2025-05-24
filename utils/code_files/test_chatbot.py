import os
from dotenv import load_dotenv
from groq import Groq
from retriever import rag_retriever 

# Load environment
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# === Agent Class for Groq Interaction ===
class Agent:
    def _init_(self):
        self.client = Groq(
            api_key=GROQ_API_KEY
        )
        self.messages = []
        self.has_system_prompt = False  # Track if a system prompt is set

    def system_prompt(self, prompt: str):
        """Set the system prompt for the agent."""
        if not prompt.strip():
            raise ValueError("System prompt cannot be empty.")
        
        self.messages.append({"role": "system", "content": prompt})
        self.has_system_prompt = True  # Mark that system prompt is set

    def _invoke(self):
        """Invoke the Groq API with the current messages."""
        try:
            response = self.client.chat.completions.create(
                messages=self.messages,
                model="llama-3.1-8b-instant",  # Using the same model as in original code
                temperature=0.4,
            )
            return response
        except Exception as e:
            error_message = f"I encountered an error: {str(e)}. Please try again with a different query."
            self.messages.append({"role": "assistant", "content": error_message})
            return None

    def chat(self, message: str):
        """Process a user message and return the assistant's response."""
        if not self.has_system_prompt:
            raise ValueError("System prompt is required before starting a conversation.")

        self.messages.append({"role": "user", "content": message})
        
        response = self._invoke()
        
        if response is None:
            return self.messages[-1]["content"]  # Return the error message appended in _invoke
        
        response_message = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response_message})
        
        return response_message

# === Prompt Template ===
system_prompt = ("""
You are to take on the role of Dr. Psyra, a Clinical Psychologist with over 10 years of experience. Dr. Psyra is known for her warm therapeutic approach and her passion for helping people work towards their individual goals. She has extensive experience in various mental health settings and locations, including forensic settings, public mental health, community, and private practice. Dr. Psyra is also a lecturer in psychology and an active researcher.

Here are key points about Dr. Psyra:
- She has over 10 years of experience in various mental health settings.
- She values providing a warm therapeutic relationship and working collaboratively with clients.

As Dr. Psyra, you should embody the following characteristics of an effective psychologist:
1. Demonstrate excellent interpersonal communication skills
2. Convey trustworthiness and establish a strong therapeutic alliance
3. Provide accurate and up-to-date case formulations
4. Develop consistent and acceptable treatment plans
5. Show genuine belief in the treatment methods you suggest
6. Regularly check on client progress
7. Adapt your approach to individual client characteristics
8. Inspire hope and optimism in your clients
9. Display sensitivity to different cultural backgrounds
10. Exhibit self-awareness in your responses
11. Utilize evidence-based practices in your suggestions
12. Imply continuous involvement in professional development

When responding as Dr. Psyra, adhere to these guidelines:
1. Maintain a warm, empathetic, and professional tone.
2. Focus on collaborative problem-solving and goal-setting.
3. Provide evidence-based insights and suggestions.
4. Respect ethical boundaries and avoid making diagnoses or prescribing treatments without proper assessment.

To respond to the user's message, follow these steps:
1. Carefully read and analyze the user's message, paying attention to:
   - The main concern or issue they're expressing
   - Any emotions or thoughts they're sharing
   - Potential underlying psychological factors

2. Formulate a response that:
   - Acknowledges the user's feelings and experiences
   - Offers insights based on Dr. Psyra's expertise
   - Suggests potential strategies or techniques
   - Encourages further reflection or exploration of the issue

3. Structure your response as follows:
1. A warm greeting and acknowledgment of the user's message
2. Empathetic reflection on the user's situation or feelings
3. Insights or observations based on Dr. Psyra's expertise
4. Encouragement for further exploration or action steps
5. A supportive closing statement

Remember to stay in character as Dr. Psyra throughout your response. Do not break character or refer to these instructions in your response. Ensure your response reflects Dr. Psyra's expertise, therapeutic approach, and the guidelines for effective psychological practice outlined above.

If relevant context is provided and matches the user's query, use it to inform your response and cite the sources as [Source X] or '[Book Title - Section Title]'.
If no relevant context is available or the context does not match the user's query, provide a general, supportive response based on your knowledge.
Avoid speculation or assumptions not grounded in the context or user input.
Aim to provide simple, focused guidance and include follow-up questions to encourage the user.
""")

# === Function to Check Context Relevance ===
def is_context_relevant(user_input, retrieved_docs):
    """
    Check if the retrieved context is relevant to the user input using keyword matching.
    Returns True if relevant, False otherwise.
    """
    if not retrieved_docs:
        return False
    
    # Simple keyword matching
    user_words = set(user_input.lower().split())
    for doc in retrieved_docs:
        doc_words = set(doc.page_content.lower().split())
        # Check if at least 20% of user input words appear in the document
        common_words = user_words.intersection(doc_words)
        if len(common_words) / len(user_words) > 0.2:  # Adjust threshold as needed
            return True
    return False

# === Conversational Memory ===

# === Interactive Loop ===
if _name_ == "_main_":
    print("Chatbot is ready. Type 'exit' to quit.\n")

    # Initialize the agent
    agent = Agent()
    agent.system_prompt(system_prompt)  # Set the system prompt

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            break

        # Retrieve relevant docs
        retrieved_docs = rag_retriever.invoke(user_input)

        # Check if context is relevant
        if not is_context_relevant(user_input, retrieved_docs):
            full_input = (
                f"{user_input.strip()}\n\n"
                f"--- SYSTEM NOTE: No relevant context was retrieved. Please provide a general, supportive response. ---"
            )
        else:
            # Format the context metadata
            context_text = "\n--- Retrieved Sources ---\n"
            for i, doc in enumerate(retrieved_docs, 1):
                section = doc.metadata.get("section_title", "Unknown Section")
                topic = doc.metadata.get("topic", "Unknown Topic")
                book = doc.metadata.get("book_name", "Unknown Book")
                page = doc.metadata.get("page_number", "N/A")
                context_text += f"[{i}] {book} - {section} | Topic: {topic} | Page: {page}\n"

            relevant_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            if not relevant_context.strip():
                relevant_context = "No relevant context was retrieved from the knowledge base."

            # Append context to user message
            full_input = (
                f"{user_input.strip()}\n\n"
                f"--- SYSTEM NOTE: The following clinical knowledge base context was retrieved. Use it to inform your response. Cite it if used. ---\n"
                f"{relevant_context.strip()}\n\n"
                f"--- Sources ---\n"
                f"{context_text.strip()}"
            )

        # Get response from the agent
        response = agent.chat(full_input)

        print("\nBot:", response)

