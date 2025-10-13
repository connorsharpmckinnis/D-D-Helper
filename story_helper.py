import tkinter as tk
from tkinter import scrolledtext
from google import genai
from google.genai import types
import json
import os

# --- Gemini Client Setup ---
client = genai.Client(api_key="AIzaSyCMM5MV1r7g8DhFnn3tU3hfgXFrHb33V3s")  # Replace with your real key

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

# --- Save Catalog Entry ---
def save_catalog_entry(function_call, file_path="world_catalog.json"):
    entry_name = function_call.args['name']
    entry = function_call.args['entry']
    category = function_call.args.get('category', 'Uncategorized')

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                catalog = json.load(f)
            except json.JSONDecodeError:
                catalog = {}
    else:
        catalog = {}

    catalog[entry_name] = {"entry": entry, "category": category}

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)

    return entry_name

# --- Chat Setup ---
tools = types.Tool(function_declarations=[content_function])
config = types.GenerateContentConfig(tools=[tools])
chat = client.chats.create(model="gemini-2.5-flash-lite")

# --- UI Setup ---
root = tk.Tk()
root.title("Worldbuilder Assistant")

chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=30, font=("Consolas", 11))
chat_display.pack(padx=10, pady=10)
chat_display.insert(tk.END, "Worldbuilding Assistant Initialized.\n\n")

entry_field = tk.Entry(root, width=80, font=("Consolas", 11))
entry_field.pack(padx=10, pady=(0,10))

def display_message(sender, message, color="black"):
    chat_display.insert(tk.END, f"{sender}: {message}\n", ("color",))
    chat_display.tag_configure("color", foreground=color)
    chat_display.see(tk.END)

# --- Main Logic ---
def handle_user_input(event=None):
    user_text = entry_field.get().strip()
    if not user_text:
        return
    entry_field.delete(0, tk.END)
    display_message("You", user_text, "blue")

    response = chat.send_message(config=config, message=user_text)

    if response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        entry_name = save_catalog_entry(function_call)
        display_message("SYSTEM", f"📘 New entry added: {entry_name}", "green")

        follow_up = (
            f"SYSTEM MESSAGE: Added '{entry_name}' to catalog. "
            "You're a worldbuilding assistant. Please ask a deeper question about their latest entry or suggest a related topic. Be encouraging and helpful. Use your function at your discretion to populate the user's catalog. Don't ask them to pick their own category or name; choose both of those for them. "
        )
        response = chat.send_message(message=follow_up)

    bot_reply = response.text.strip() if hasattr(response, "text") else "[No reply]"
    display_message("AI", bot_reply, "purple")

entry_field.bind("<Return>", handle_user_input)

# --- Start conversation ---
init_response = chat.send_message("Ask the user what they want to call their world.")
display_message("AI", init_response.text, "purple")

root.mainloop()