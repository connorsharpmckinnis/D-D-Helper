import tkinter as tk
from tkinter import scrolledtext, filedialog
from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv


load_dotenv()

# --- File Setup ---
selected_file = None
file_label = None

# --- Gemini Client Setup ---
client = genai.Client(api_key=os.getenv("API_KEY"))  # Replace with your real key

# --- Function Declarations ---
content_function = {
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
                    "Characters","Races and Species","Cultures and Societies","Languages",
                    "Religions and Beliefs","Mythology and Legends","Magic and Sorcery",
                    "Artifacts and Relics","Technology and Inventions","Nations and Kingdoms",
                    "Cities and Settlements","Geography and Regions","Natural Features",
                    "Flora and Fauna","Organizations and Factions","Guilds and Orders",
                    "Economy and Trade","Politics and Government","Military and Warfare",
                    "Laws and Customs","Calendar and Timekeeping","Cosmology and Planes",
                    "Deities and Pantheons","Notable Events","Historical Eras",
                    "Conflicts and Wars","Heroes and Villains","Professions and Occupations",
                    "Transportation and Travel","Architecture and Structures","Art and Music",
                    "Cuisine and Food","Fashion and Clothing","Measurement and Currency",
                    "Education and Scholarship","Science and Alchemy","Entertainment and Games",
                    "Philosophy and Ethics","Superstitions and Folklore","Important Texts and Tomes",
                    "Climate and Weather","Disease and Medicine","Demography and Population",
                    "Rituals and Festivals","Prophesies and Omens","Exploration and Discovery"
                ],
                "description": "The category of the user's worldbuilding entry."
            }
        },
        "required": ["name", "entry", "category"]
    },
}



def choose_file():
    global selected_file
    selected_file = filedialog.askopenfilename(
        title="Select World Catalog",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if not selected_file:
        selected_file = "world_catalog.json"  # fallback default
        
    start_prompt = f"SYSTEM MESSAGE: If there is an existing world catalog, here is the information: {get_world_context()}\n\n You should ask the user a question to kick off (or kick back off) the brainstorming process. If there is no world name, start with that perhaps. "
    init_response = chat.send_message(start_prompt)
    display_message("AI", init_response.text, "purple")

# --- Robust Save Catalog Entry ---
def save_catalog_entry(function_call, file_path=None):
    """
    Accepts either:
      - function_call.args (a dict-like), or
      - function_call.arguments (a JSON string)
    Writes to JSON safely and forces an fsync so the file is persisted.
    Returns the saved entry name (or raises).
    """
    global selected_file
    file_path = file_path or selected_file
    # Try to extract args in a few shapes
    parsed = {}
    try:
        # common: function_call.args (already dict-like)
        if hasattr(function_call, "args") and function_call.args:
            parsed = dict(function_call.args)
        # some SDKs return a JSON string under .arguments
        elif hasattr(function_call, "arguments") and function_call.arguments:
            # it might already be a dict or a str
            raw = function_call.arguments
            if isinstance(raw, str):
                parsed = json.loads(raw)
            elif isinstance(raw, (dict, list)):
                parsed = dict(raw)
        else:
            raise ValueError("function_call has no 'args' or 'arguments' payload.")
    except Exception as e:
        # Re-raise with more context
        raise RuntimeError(f"Failed to parse function_call payload: {e}\nRaw: {getattr(function_call, 'arguments', None)}")

    # Required fields (defensive)
    entry_name = parsed.get("name")
    entry_text = parsed.get("entry") or parsed.get("description") or parsed.get("content")
    category = parsed.get("category", "Uncategorized")

    if not entry_name or not entry_text:
        raise ValueError(f"Parsed function_call missing name or entry. Parsed payload: {parsed}")

    # Ensure directory exists (in case user passed a path)
    os.makedirs(os.path.dirname(os.path.abspath(file_path)) or ".", exist_ok=True)

    # Read existing or create
    catalog = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except json.JSONDecodeError:
            # bad/corrupt JSON -> back it up and start fresh
            backup_path = file_path + ".bak"
            os.replace(file_path, backup_path)
            catalog = {}
    # Insert/overwrite entry
    catalog[entry_name] = {"entry": entry_text, "category": category}

    # Write atomically: write to temp then replace
    tmp_path = file_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, file_path)

    # Return absolute path and name for confirmation
    return entry_name, os.path.abspath(file_path)


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



# --- Chat Setup ---
tools = types.Tool(function_declarations=[content_function])
config = types.GenerateContentConfig(tools=[tools], system_instruction="You are a helpful, thoughtful, and conversational worldbuilding assistant. You don't just ask what the user wants to record in their worldbuilding catalog; you talk with them about their world to flesh it out naturally and you quietly execute functions to store their insights into the catalog. Give ideas, suggestions, and other things to add flavor to the world you are building together.")
chat = client.chats.create(model="gemini-2.5-flash-lite" )

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

def display_message(sender, message, color="black"):

    chat_display.insert(tk.END, f"{sender}: ", ("sender",))
    chat_display.insert(tk.END, f"{message}\n\n", ("color",))
    chat_display.tag_configure("sender", font=("Consolas", 11, "bold"))
    chat_display.tag_configure("color", foreground=color, font=("Consolas", 11))
    chat_display.see(tk.END)

# --- Main Logic ---
def handle_user_input(event=None):
    user_text = entry_field.get().strip()
    if not user_text:
        return
    entry_field.delete(0, tk.END)
    display_message("You", user_text, "blue")
    
    world_context = get_world_context()
    
    prompt = f"SYSTEM MESSAGE: Here is a summary of the world catalog so far: \n{world_context}\n\n Here is the user's latest prompt: {user_text}"

    response = chat.send_message(config=config, message=prompt)

    if response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        entry_name = save_catalog_entry(function_call)
        display_message("SYSTEM", f"📘 New entry added: {entry_name[0]}", "green")

        follow_up = (
            f"SYSTEM MESSAGE: Added '{entry_name}' to catalog. "
            "You're a collaborative and thoughtful worldbuilding assistant. Please ask a deeper question about their latest entry or suggest a related topic. Be encouraging and helpful. Use your function at your discretion to populate the user's catalog. Don't ask them to pick their own category or name; choose both of those for them. "
        )
        response = chat.send_message(message=follow_up)

    bot_reply = response.text.strip() if hasattr(response, "text") else "[No reply]"
    display_message("AI", bot_reply, "purple")

entry_field.bind("<Return>", handle_user_input)



root.mainloop()



