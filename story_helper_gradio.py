import gradio as gr
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("API_KEY"))  # Replace with your real key


system_instruction = (
    "You are a helpful, thoughtful, and conversational worldbuilding assistant. "
        "You talk naturally with the user about their world to flesh it out, but when the user explicitly "
        "instructs you to add or create an entry (for example, by saying 'add this', 'please save', 'put this in the catalog', "
        "or similar), you must immediately call the `generate_structured_content` function with the relevant data "
        "and continue the conversation without asking for confirmation. "
        "Use reasonable defaults for category and structure if the user doesn’t specify them. "
        "Do not ask permission before saving when the user gives a clear directive."
)




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










def save_catalog_entry(function_call, file_path='world_catalog.json'):
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

        # If entry already exists, append the new text
        if name in catalog:
            existing_text = catalog[name].get("entry", "")
            catalog[name]["entry"] = existing_text + "\n" + text
            # Optional: update category only if it differs or leave it as-is
            if catalog[name].get("category") != category:
                catalog[name]["category"] = category
        else:
            catalog[name] = {"entry": text, "category": category}

        saved_names.append(name)

    # Save updated catalog
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)

    return saved_names, os.path.abspath(file_path)

def get_world_context(file_path='world_catalog.json'):
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
    return summary

tools = types.Tool(function_declarations=[content_function])
config = types.GenerateContentConfig(tools=[tools], system_instruction=system_instruction)
chat = client.chats.create(model="gemini-2.5-flash-lite", config=config)

contents = []

def respond(message, history=None):

    # Get world context
    world_context = get_world_context()
    prompt = f"SYSTEM MESSAGE: Here is a summary of the world catalog so far:\n{world_context}\n\n Here is the user's latest prompt: {message}"
    contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
     
    print(contents)

    response = chat.send_message(config=config, message=prompt)

    #response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=contents, config=config)

    for part in response.candidates[0].content.parts:
        if hasattr(part, "function_call") and part.function_call:
            # A function call exists!
            func_name = part.function_call.name
            args = part.function_call.args  # This is usually a dict
            print("Function called:", func_name)
            print("Arguments:", args)
            if func_name == "generate_structured_content":
                saved_names, path = save_catalog_entry(part.function_call)
                saved_names_message = f"Saved to catalog: {', '.join(saved_names)}"
                ", ".join(saved_names)

                output = saved_names_message
                
        else: 
            output = response.text

    # Add AI message

    return output

demo = gr.ChatInterface(fn=respond, type="messages", examples=["hello", "hola", "merhaba"], title="Echo Bot")
demo.launch(share=True)