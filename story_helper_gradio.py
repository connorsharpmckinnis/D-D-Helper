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
        "You talk naturally, if a little dramatically and fantastically, with the user about their world to flesh it out, but when the user explicitly "
        "instructs you to add or create an entry (for example, by saying 'add this', 'please save', 'put this in the catalog', "
        "or similar), you must immediately call the `generate_structured_content` function with the relevant data "
        "and continue the conversation without asking for confirmation. "
        "Use reasonable defaults for category and structure if the user doesn’t specify them. "
        "Do not ask permission before saving when the user gives a clear directive."
)

choices = [
    "Geography","Nations","History","Culture","Society","Economy","Magic","Warfare","Science",
    "Nature","Creatures","Religion","Technology","Mythology","Politics","Exploration","Philosophy"
]


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
                            "enum": choices,
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

def get_world_context(file_path=None):
    global selected_file
    file_path = selected_file
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

selected_file = None

def select_file(file_obj):
    global selected_file
    if file_obj is None:
        return "No file selected."

    # Copy uploaded file to a stable local path
    base_name = os.path.basename(file_obj.name)
    persistent_path = os.path.join(os.getcwd(), base_name)

    try:
        # Copy (not move) so the temp file isn't deleted prematurely
        with open(file_obj.name, "rb") as src, open(persistent_path, "wb") as dst:
            dst.write(src.read())
    except FileNotFoundError:
        # Some Gradio versions already delete temp files; fall back to assuming it's local
        persistent_path = os.path.join(os.getcwd(), base_name)

    selected_file = persistent_path
    return f"Selected file: {selected_file}"

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
            
            #send chat message with function confirmation adn get follow-up
            message = f"SYSTEM: You have just saved the following entries to the catalog: {', '.join(saved_names)}. Please share a message that confirms the saving of these entries and prompts the user to discuss the world in greater depth or suggest a new topic to explore."

            second_response = chat.send_message(config=config, message=message)
            output = second_response.text
                
        else: 
            output = response.text

    # Add AI message

    return output


def refresh_catalog(search_entry="", filter_choice="All"):
    print(selected_file)
    if not selected_file or not os.path.exists(selected_file):
        return []
    with open(selected_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        rows = []
        for name, data in catalog.items():
            cat = data.get("category", "Uncategorized")
            if (
                (filter_choice == "All" or cat == filter_choice)
                and (search_entry.lower() in name.lower())
            ):
                rows.append([name])    
    return rows

def load_entry(evt: gr.SelectData):
    global selected_file
    if not selected_file:
        return "No file selected.", "", ""
    with open(selected_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    row_index = evt.index[0]  # first index in (row, col)
    names = list(catalog.keys())
    if row_index < len(names):
        name = names[row_index]
        entry_data = catalog[name]
        return name, entry_data.get("entry", ""), entry_data.get("category", "")
    return "", "", ""

def save_entry(name, text, category):
    global selected_file
    print(selected_file)
    if not selected_file:
        return "No file selected."
    with open(selected_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    catalog[name] = {"entry": text, "category": category}
    with open(selected_file, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=4)
    return f"Saved changes to '{name}'."


with gr.Blocks(title="Worldbuilding Assistant") as demo:
    gr.Markdown("# 🌍 Worldbuilding Assistant")

    with gr.Tab("Chat"):
        file_selector = gr.File(label="Select or upload a JSON catalog", file_types=[".json"])
        file_output = gr.Textbox(label="Current File", interactive=False)

        chat_interface = gr.ChatInterface(fn=respond, type="messages", title="World Chat")

        file_selector.change(fn=select_file, inputs=file_selector, outputs=file_output)


    choices_with_all = choices + ["All"]

    with gr.Tab("Catalog Viewer"):
        search_bar = gr.Textbox(label="Search Catalog", interactive=True)
        category_filter = gr.Dropdown(label="Category", value="All", choices = choices_with_all)
        catalog_list = gr.Dataframe(headers=["Name"], interactive=False, label="Catalog")
        selected_entry = gr.Textbox(label="Selected Entry", interactive=True)
        category_text = gr.Textbox(label="Category", interactive=True)
        catalog_text = gr.Textbox(label="Entry Content", lines=10, interactive=True)
        

        catalog_list.select(fn=load_entry, outputs=[selected_entry, catalog_text, category_text])        

        refresh_button = gr.Button(value="Refresh Catalog")
        refresh_button.click(fn=refresh_catalog, outputs=catalog_list)
        search_bar.change(
            fn=refresh_catalog,
            inputs=[search_bar, category_filter],
            outputs=catalog_list
        )
        category_filter.change(
            fn=refresh_catalog,
            inputs=[search_bar, category_filter],
            outputs=catalog_list
        )

        save_button = gr.Button(value="Save Changes")
        save_status = gr.Textbox(label="Save Status", interactive=False)
        save_button.click(fn=save_entry, inputs=[selected_entry, catalog_text, category_text], outputs=save_status)
demo.launch(share=False)