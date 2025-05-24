import os
from core.agent import Agent  # Assuming the Agent class is saved in GroqAgent.py

def test_chatbot():
    # Ensure the GROQ_API_KEY is set in the environment
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable is not set.")
        return

    # Create an instance of the Agent
    agent = Agent()

    # Set a user ID (equivalent to orgId in your previous code)
    agent.set_user_id("user_12345")

    # Define a system prompt
    system_prompt = "You are a knowledgeable assistant that provides concise and accurate answers."

    # Set the system prompt
    try:
        agent.system_prompt(system_prompt)
    except ValueError as e:
        print(f"Error setting system prompt: {e}")
        return

    # Define a sample user query
    user_query = "Explain the importance of fast language models."

    # Process the user query and get the response
    try:
        response = agent.chat(user_query)
        print(f"User Query: {user_query}")
        print(f"Assistant Response: {response}")
        
        # Print the conversation history
        print("\nConversation History:")
        for msg in agent.messages:
            print(f"{msg['role'].capitalize()}: {msg['content']}")
    except ValueError as e:
        print(f"Error during chat: {e}")

if __name__ == "__main__":
    test_chatbot()



    # agent class


# import os
# import json
# from groq import Groq

# class Agent:
#     def __init__(self):
#         self.client = Groq(
#             api_key=os.environ.get("GROQ_API_KEY")
#         )
#         self.messages = []
#         self.has_system_prompt = False  # Track if a system prompt is set
#         self.user_id = None  # Initialize user ID as None

#     def set_user_id(self, user_id: str):
#         """Set the user ID for this agent instance."""
#         self.user_id = user_id

#     # def add_tool(self, fn, definition):
#     #     """Add a tool to the agent (commented out as tools are not used)."""
#     #     self.tools[definition["function"]["name"]] = fn
#     #     self.tool_schemas.append(definition)

#     def system_prompt(self, prompt: str):
#         """Set the system prompt for the agent."""
#         if not prompt.strip():
#             raise ValueError("System prompt cannot be empty.")
        
#         self.messages.append({"role": "system", "content": prompt})
#         self.has_system_prompt = True  # Mark that system prompt is set

#     def _invoke(self):
#         """Invoke the Groq API with the current messages."""
#         try:
#             response = self.client.chat.completions.create(
#                 messages=self.messages,
#                 model="llama-3.3-70b-versatile",
#                 stream = True
#             )
#             return response
#         except Exception as e:
#             error_message = f"I encountered an error: {str(e)}. Please try again with a different query."
#             self.messages.append({"role": "assistant", "content": error_message})
#             return None

#     def chat(self, message: str):
#         """Process a user message and return the assistant's response."""
#         if not self.has_system_prompt:
#             raise ValueError("System prompt is required before starting a conversation.")

#         self.messages.append({"role": "user", "content": message})
        
#         response = self._invoke()
        
#         if response is None:
#             return self.messages[-1]["content"]  # Return the error message appended in _invoke
        
#         print(response)
#         response_message = response.choices[0].message.content
#         self.messages.append({"role": "assistant", "content": response_message})
        
#         return response_message


