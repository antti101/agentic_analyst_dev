# main.py - Main application with AutoGen integration

from dotenv import load_dotenv

from .config_loader import config
from .semantic_layer_mcp import DataPlatformApp

load_dotenv()

class EnhancedDataPlatformApp(DataPlatformApp):
    """Enhanced version with AutoGen BI Analyst support"""
    
    def __init__(self):
        semantic_layer_path = config.get_semantic_layer_path()
        super().__init__(semantic_layer_path)
        
        self.bi_analyst = None
    
    def chat_with_bi_analyst(self, message: str, chat_history: list):
        """Chat with the BI Analyst agent, maintaining conversation history."""
        if self.bi_analyst:
            try:
                # The agent expects the full history, including the latest user message
                full_history = chat_history + [{"role": "user", "content": message}]
                response = self.bi_analyst.run_generate_agent_reply(full_history)
                return response
            except Exception as e:
                return f"Error in BI Analyst chat: {e}"
        else:
            return "BI Analyst not available. Check AutoGen installation and OpenAI API key."

def main():
    """Main function to run an interactive, stateful chat session via the CLI."""
    app = EnhancedDataPlatformApp()
    
    if not app.bi_analyst:
        print("Could not start chat. BI Analyst agent failed to initialize.")
        return

    print("=== Cube Analyst Interactive Chat ===")
    print("Starting a new conversation. Type 'quit' or 'exit' to end.")
    print("-" * 35)

    chat_history = []

    while True:
        try:
            message = input("You: ")
            if message.lower() in ['quit', 'exit']:
                break
            if not message:
                continue

            response = app.chat_with_bi_analyst(message, chat_history)

            if response:
                if isinstance(response, dict):
                    assistant_message = response.get("content", str(response))
                else:
                    assistant_message = str(response)
            else:
                assistant_message = "Sorry, I couldn't get a response."

            print(f"\nAgent: {assistant_message}\n")

            # Add the user message and the agent's response to the history for the next turn
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": assistant_message})

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    
    print("\nConversation ended.")


if __name__ == "__main__":
    import duckdb
    duckdb.query("SELECT 1 AS ok").df()
    #main()