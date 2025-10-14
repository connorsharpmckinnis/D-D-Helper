import tkinter as tk
from tkinter import scrolledtext, filedialog
from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv


load_dotenv()

# --- File Setup ---
selected_file = "world_catalog.json"
file_label = None

# --- Gemini Client Setup ---
client = genai.Client(api_key=os.getenv("API_KEY"))  # Replace with your real key

# --- Function Declarations ---
single_content_function = {
    "name": "generate_structured_content",
    "description": "Generates a structured dict of an entry for a worldbuilding catalog based on the conversation with the user. ",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The name for the entry in the catalog"},
            "entry": {"type": "string", "description": "The user's entry for the worldbuilding catalog."},
            "category": {
                "type": "string",
                "enum": [
                    "Geography","Nations","History","Culture","Society","Economy","Magic","Warfare","Science","Nature","Creatures","Religion","Technology","Mythology","Politics","Exploration","Philosophy"
                ],
                "description": "The category of the user's worldbuilding entry."
            }
        },
        "required": ["name", "entry", "category"]
    },
}

content_function = {
    "name": "generate_structured_content",
    "description": "Generates one or more structured catalog entries for worldbuilding content.",
    "parameters": {
        "type": "object",
        "properties": {
            "entries": {
                "type": "array",
                "description": "A list of catalog entries to add to the worldbuilding catalog.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "The name of the catalog entry."},
                        "entry": {"type": "string", "description": "The content or description for the entry."},
                        "category": {
                            "type": "string",
                            "enum": [
                                "Geography","Nations","History","Culture","Society","Economy","Magic","Warfare","Science",
                                "Nature","Creatures","Religion","Technology","Mythology","Politics","Exploration","Philosophy"
                            ],
                            "description": "The category of the catalog entry."
                        }
                    },
                    "required": ["name", "entry", "category"]
                }
            }
        },
        "required": ["entries"]
    },
}


def choose_file():
    global selected_file
    selected_file = filedialog.askopenfilename(
        title="Select World Catalog",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    file_label.config(text=os.path.basename(selected_file))

    if not selected_file:
        selected_file = "world_catalog.json"  # fallback default
        
    start_prompt = f"SYSTEM MESSAGE: If there is an existing world catalog, here is the information: {get_world_context()}\n\n You should ask the user a question to kick off (or kick back off) the brainstorming process. If there is no world name, start with that perhaps. "
    init_response = chat.send_message(start_prompt)
    display_message("AI", init_response.text, "purple")

# --- Robust Save Catalog Entry ---
def save_catalog_entry(function_call, file_path=None):
    """
    Saves one or more catalog entries from function_call.args['entries'] into a JSON file.
    Each entry must include: name, entry, and category.
    Returns a list of saved entry names and the absolute file path.
    """
    global selected_file
    file_path = file_path or selected_file

    parsed = getattr(function_call, "args", None)
    if not isinstance(parsed, dict):
        raise ValueError("function_call.args must be a dictionary")

    entries = parsed.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("function_call.args['entries'] must be a non-empty list")

    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(file_path)) or ".", exist_ok=True)

    # Load existing catalog (if present)
    catalog = {}
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

    saved_names = []
    for e in entries:
        name = e.get("name")
        text = e.get("entry")
        category = e.get("category", "Uncategorized")

        if not name or not text:
            raise ValueError(f"Each entry must include 'name' and 'entry'. Problematic entry: {e}")

        catalog[name] = {"entry": text, "category": category}
        saved_names.append(name)

    # Save updated catalog
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)

    return saved_names, os.path.abspath(file_path)

def get_world_context(file_path=None):
    global selected_file
    file_path = file_path or selected_file
    if not file_path:
        return "No file selected."
    
    if not os.path.exists(str(file_path)):
        return "No world entries yet."
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            catalog = json.load(f)
        except json.JSONDecodeError:
            catalog = {}
    # Simplify for context: just names and categories
    summary_lines = [f"{name} ({data['category']})" for name, data in catalog.items()]
    summary = "\n".join(summary_lines) if summary_lines else "No world entries yet."
    return f"Here is the world catalog so far:\n{summary}"

system_instruction = (
    "You are a helpful, thoughtful, and conversational worldbuilding assistant. "
        "You talk naturally with the user about their world to flesh it out, but when the user explicitly "
        "instructs you to add or create an entry (for example, by saying 'add this', 'please save', 'put this in the catalog', "
        "or similar), you must immediately call the `generate_structured_content` function with the relevant data "
        "and continue the conversation without asking for confirmation. "
        "Use reasonable defaults for category and structure if the user doesn’t specify them. "
        "Do not ask permission before saving when the user gives a clear directive."
)

# --- Chat Setup ---
tools = types.Tool(function_declarations=[content_function])
config = types.GenerateContentConfig(tools=[tools], system_instruction=system_instruction)
chat = client.chats.create(model="gemini-2.5-flash-lite", config=config)

# --- UI Setup ---
root = tk.Tk()
root.title("Worldbuilder Assistant")

top_frame = tk.Frame(root)
top_frame.pack(padx=10, pady=(10, 0), fill="x")

file_label = tk.Label(top_frame, text="No file selected", font=("Consolas", 10, "italic"))
file_label.pack(side="left", padx=(0, 10))

choose_button = tk.Button(top_frame, text="Choose Catalog File", command=lambda: choose_file())
choose_button.pack(side="left")

chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=30, font=("Consolas", 11))
chat_display.pack(padx=10, pady=10)
chat_display.insert(tk.END, "Worldbuilding Assistant Initialized.\n\n")

entry_field = tk.Entry(root, width=80, font=("Consolas", 11))
entry_field.pack(padx=10, pady=(0, 10))

def display_message(sender, message, msg_type=None, color=None):
    """
    Display a message in the chat_display with color coding.
    
    msg_type: "user", "ai", "system" (defaults to black if unknown)
    color: optional override for msg_type
    """
    # Define default colors per message type
    type_colors = {
        "user": "blue",
        "ai": "purple",
        "system": "green"
    }

    # Decide which color to use
    final_color = color or type_colors.get(msg_type, "black")

    # Insert sender name
    chat_display.insert(tk.END, f"{sender}: ", ("sender",))
    chat_display.insert(tk.END, f"{message}\n\n", ("color",))

    # Configure tags
    chat_display.tag_configure("sender", font=("Consolas", 11, "bold"))
    chat_display.tag_configure("color", foreground=final_color, font=("Consolas", 11))

    chat_display.see(tk.END)

# --- Main Logic ---
def handle_user_input(event=None):
    user_text = entry_field.get().strip()
    if not user_text:
        return
    entry_field.delete(0, tk.END)
    display_message("You", user_text, msg_type="user", color="blue")

    world_context = get_world_context()
    prompt = (
        f"SYSTEM MESSAGE: Here is a summary of the world catalog so far:\n{world_context}\n\n"
        f"Here is the user's latest prompt: {user_text}"
    )

    response = chat.send_message(message=prompt)

    text_output = []
    function_called = False

    for part in response.candidates[0].content.parts:
        # Handle function calls
        if hasattr(part, "function_call") and part.function_call:
            saved_names, path = save_catalog_entry(part.function_call)
            display_message("SYSTEM", f"📘 Saved to catalog: {', '.join(saved_names)}", msg_type="system", color="green")
            function_called = True

        # Handle text replies
        elif hasattr(part, "text") and part.text:
            text_output.append(part.text.strip())

    # Display any text parts together
    if text_output:
        display_message("AI", "\n".join(text_output), msg_type="ai", color="purple")
    elif function_called:
        # If a function was called but no text was sent, prompt the model to continue
        follow_up = chat.send_message(
            message="The entries have been saved. Continue the conversation naturally."
        )
        if follow_up and follow_up.candidates:
            for part in follow_up.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    display_message("AI", part.text.strip(), msg_type="ai", color="purple")
    

entry_field.bind("<Return>", handle_user_input)



root.mainloop()



