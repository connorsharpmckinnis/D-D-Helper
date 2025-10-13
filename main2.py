"""
Simple, readable D&D helper UI (Tkinter).

Features:
- Load / save character (JSON)
- Ability checks & skills (shows modifiers)
- Custom dice roller
- Weapon To-Hit and Damage rolls
- Initiative roll
- Notes and inventory add/remove
- Scrollable UI that works on Windows/macOS/Linux

Keep it simple: small helper functions, clear variable names, and inline comments.
"""

import random
import json
import copy
import platform
import tkinter as tk
from tkinter import ttk

# Optional theme; if not installed we gracefully fall back to plain Tk.
try:
    from ttkthemes import ThemedTk
    def make_root():
        return ThemedTk(theme="black")
except Exception:
    def make_root():
        return tk.Tk()


# ---------- Simple constants & defaults ----------
CHAR_FILE = "character.json"

STYLE = {
    "font_title": ("Helvetica", 12, "bold"),
    "font_normal": ("Helvetica", 10),
}

# Default character data (keeps the UI working if no file is present)
DEFAULT_CHARACTER = {
    "name": "Gingus",
    "race": "Human",
    "class": "Barbarian",
    "level": 1,
    "proficiency": 2,
    "stats": {"STR": 20, "DEX": 20, "CON": 20, "INT": 6, "WIS": 6, "CHA": 6},
    "weapons": {
        "Longsword": {"hit_mod": 2, "damage_die": 6, "damage_die_count": 1, "damage_mod": 2},
        "Shortbow":   {"hit_mod": 2, "damage_die": 6, "damage_die_count": 1, "damage_mod": 2},
    },
    "inventory": [],
    "gold": 10,
    "notes": "",
    "hp": {"current": 12, "max": 12},
    "ac": 14,
    "skills": {
        "Athletics": {"ability": "STR", "prof": 2},
        "Acrobatics": {"ability": "DEX", "prof": 2},
    },
}


# ---------- Utility functions (small and well-named) ----------
def save_character_to_file(character, filename=CHAR_FILE):
    """Write the character dict to disk as JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(character, f, indent=4, ensure_ascii=False)


def load_character_from_file(filename=CHAR_FILE):
    """Return the character dict loaded from JSON (raises FileNotFoundError if missing)."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def calc_mods(stats):
    """Return ability modifiers (e.g. STR 15 -> +2)."""
    return {ab: (val - 10) // 2 for ab, val in stats.items()}


def roll(d_sides, count=1):
    """Roll `count` dice of `d_sides` and return the sum."""
    return sum(random.randint(1, d_sides) for _ in range(count))


def roll_with_mod(d_sides, count, mod):
    """Roll dice and add a flat modifier."""
    return roll(d_sides, count) + mod


def ability_check(character, ability):
    """Do a 1d20 ability check using the character's modifier for `ability`."""
    mods = calc_mods(character["stats"])
    return roll_with_mod(20, 1, mods[ability])


def skill_modifier(character, skill_name):
    """Return the total skill modifier (ability mod + proficiency)."""
    skill = character["skills"][skill_name]
    mods = calc_mods(character["stats"])
    return mods[skill["ability"]] + skill.get("prof", 0)


def skill_check(character, skill_name):
    """Perform a skill check (1d20 + skill modifier)."""
    return roll(20) + skill_modifier(character, skill_name)


def roll_to_hit(weapon):
    """Return a single d20 roll + weapon hit modifier."""
    return roll(20) + weapon.get("hit_mod", 0)


def roll_damage(weapon):
    """Roll weapon damage dice and add damage modifier."""
    return roll(weapon["damage_die"], weapon["damage_die_count"]) + weapon.get("damage_mod", 0)


# ---------- GUI (grouped into small helper sections) ----------
def gui_app():
    # Keep a working (mutable) character dict local to the app.
    character = copy.deepcopy(DEFAULT_CHARACTER)

    # Try to load saved character (if available) and overwrite defaults.
    try:
        loaded = load_character_from_file()
        character.clear()
        character.update(loaded)
    except FileNotFoundError:
        # It's fine — we'll use the default character and let the user save later.
        pass

    # Root window
    root = make_root()
    root.title("D&D Helper")
    root.geometry("800x600")

    style = ttk.Style()
    style.configure("Accent.TButton", font=STYLE["font_normal"], padding=(8, 4))

    # Scrollable area setup (common Tk pattern: canvas + inner frame)
    outer = tk.Frame(root)
    outer.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer, highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    inner = tk.Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor="nw")

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    inner.bind("<Configure>", on_configure)

    # Platform-sensitive mouse wheel support
    def _on_mousewheel(event):
        # Windows / Linux: event.delta is multiples of 120
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_mac(event):
        # macOS sends different delta values
        canvas.yview_scroll(int(-1 * event.delta), "units")

    if platform.system() == "Darwin":
        canvas.bind_all("<MouseWheel>", _on_mousewheel_mac)
    else:
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ---------- Helper to refresh UI widgets from `character` ----------
    # We'll create widget references below and update them here.
    stats_buttons = {}
    stats_result_labels = {}
    skill_buttons = {}
    skill_result_labels = {}
    inventory_listbox = None
    notes_text = None
    hp_current_entry = None
    hp_max_entry = None
    ac_entry = None
    name_entry = None
    initiative_result_label = None

    def refresh_ui():
        """Update UI widgets so they reflect the current `character` data."""
        mods = calc_mods(character["stats"])

        # Basic fields
        name_entry.delete(0, tk.END)
        name_entry.insert(0, character["name"])
        hp_current_entry.delete(0, tk.END)
        hp_current_entry.insert(0, character["hp"]["current"])
        hp_max_entry.delete(0, tk.END)
        hp_max_entry.insert(0, character["hp"]["max"])
        ac_entry.delete(0, tk.END)
        ac_entry.insert(0, character["ac"])
        notes_text.delete("1.0", tk.END)
        notes_text.insert("1.0", character.get("notes", ""))

        # Inventory
        inventory_listbox.delete(0, tk.END)
        for it in character.get("inventory", []):
            inventory_listbox.insert(tk.END, it)

        # Update stats & skill button labels to show current modifiers
        for ab, btn in stats_buttons.items():
            mod = mods[ab]
            btn.config(text=f"{ab} ({mod:+d})")
            stats_result_labels[ab].config(text="")  # clear last result

        for sk, btn in skill_buttons.items():
            # show total skill modifier (ability mod + prof)
            sk_mod = skill_modifier(character, sk)
            btn.config(text=f"{sk} ({sk_mod:+d})")
            skill_result_labels[sk].config(text="")  # clear last result

        # Clear initiative result
        if initiative_result_label:
            initiative_result_label.config(text="")

    # ---------- Top: Character info ----------
    info_frame = ttk.Frame(inner, padding=8)
    info_frame.pack(fill="x", padx=6, pady=4)

    ttk.Label(info_frame, text="Character Name:", font=STYLE["font_normal"]).grid(row=0, column=0, sticky="e", padx=6)
    name_entry = tk.Entry(info_frame, width=24, font=STYLE["font_normal"])
    name_entry.grid(row=0, column=1, sticky="w", padx=6)
    ttk.Label(info_frame, text=f'Level {character["level"]} {character["race"]} {character["class"]}', font=STYLE["font_normal"]).grid(row=0, column=2, padx=10)

    # ---------- Ability checks ----------
    stats_frame = ttk.LabelFrame(inner, text="Ability Checks", padding=8)
    stats_frame.pack(fill="x", padx=6, pady=6)

    # one button per ability, and a label for result beneath it
    for col, ability in enumerate(character["stats"].keys()):
        # result label (shows the numeric roll result)
        res_lbl = ttk.Label(stats_frame, text="", font=STYLE["font_normal"])
        res_lbl.grid(row=1, column=col, padx=6, pady=4)
        stats_result_labels[ability] = res_lbl

        # button runs an ability_check and shows the result in the label
        btn = ttk.Button(
            stats_frame,
            text=ability,  # will be updated by refresh_ui()
            command=lambda a=ability: stats_result_labels[a].config(text=str(ability_check(character, a))),
            style="Accent.TButton"
        )
        btn.grid(row=0, column=col, padx=6, pady=4)
        stats_buttons[ability] = btn

    # ---------- Skills ----------
    skills_frame = ttk.LabelFrame(inner, text="Skills", padding=8)
    skills_frame.pack(fill="x", padx=6, pady=6)

    for i, skill_name in enumerate(character["skills"].keys()):
        row = (i // 3) * 2       # two rows per skill (button + result label)
        col = (i % 3)
        sk_res_lbl = ttk.Label(skills_frame, text="", font=STYLE["font_normal"])
        sk_res_lbl.grid(row=row + 1, column=col, padx=6, pady=4, sticky="w")
        skill_result_labels[skill_name] = sk_res_lbl

        sk_btn = ttk.Button(
            skills_frame,
            text=skill_name,  # will be updated by refresh_ui()
            command=lambda s=skill_name: skill_result_labels[s].config(text=str(skill_check(character, s))),
            style="Accent.TButton"
        )
        sk_btn.grid(row=row, column=col, padx=6, pady=4, sticky="w")
        skill_buttons[skill_name] = sk_btn

    # ---------- Custom roller ----------
    roller_frame = ttk.LabelFrame(inner, text="Custom Roller", padding=8)
    roller_frame.pack(fill="x", padx=6, pady=6)

    dice_count_entry = tk.Entry(roller_frame, width=5, font=STYLE["font_normal"])
    dice_count_entry.insert(0, "1")
    dice_count_entry.grid(row=0, column=0, padx=6)

    ttk.Label(roller_frame, text="d", font=STYLE["font_normal"]).grid(row=0, column=1)
    dice_sides_entry = tk.Entry(roller_frame, width=6, font=STYLE["font_normal"])
    dice_sides_entry.insert(0, "20")
    dice_sides_entry.grid(row=0, column=2, padx=6)

    custom_result_lbl = ttk.Label(roller_frame, text="", font=STYLE["font_normal"])
    custom_result_lbl.grid(row=1, column=0, columnspan=4, pady=6)

    def roll_custom():
        try:
            cnt = int(dice_count_entry.get())
            sides = int(dice_sides_entry.get())
            total = roll(sides, cnt)
            custom_result_lbl.config(text=f"Rolled {cnt}d{sides}: {total}")
        except ValueError:
            custom_result_lbl.config(text="Please enter valid whole numbers")

    ttk.Button(roller_frame, text="Roll!", command=roll_custom, style="Accent.TButton").grid(row=0, column=3, padx=8)

    # ---------- Weapons ----------
    weapons_frame = ttk.LabelFrame(inner, text="Weapons", padding=8)
    weapons_frame.pack(fill="x", padx=6, pady=6)

    for r, (w_name, w_data) in enumerate(character["weapons"].items()):
        ttk.Label(weapons_frame, text=w_name, font=STYLE["font_normal"]).grid(row=r, column=0, padx=6, pady=4, sticky="w")

        hit_lbl = ttk.Label(weapons_frame, text="", font=STYLE["font_normal"])
        hit_lbl.grid(row=r, column=2, padx=6, pady=4)
        ttk.Button(
            weapons_frame,
            text="Roll to Hit",
            command=lambda wd=w_data, lbl=hit_lbl: lbl.config(text=f"Hit: {roll_to_hit(wd)}"),
            style="Accent.TButton"
        ).grid(row=r, column=1, padx=6, pady=4)

        dmg_lbl = ttk.Label(weapons_frame, text="", font=STYLE["font_normal"])
        dmg_lbl.grid(row=r, column=4, padx=6, pady=4)
        ttk.Button(
            weapons_frame,
            text="Roll Damage",
            command=lambda wd=w_data, lbl=dmg_lbl: lbl.config(text=f"Damage: {roll_damage(wd)}"),
            style="Accent.TButton"
        ).grid(row=r, column=3, padx=6, pady=4)

    # ---------- Combat stats (HP / AC / Initiative) ----------
    combat_frame = ttk.LabelFrame(inner, text="Combat Stats", padding=8)
    combat_frame.pack(fill="x", padx=6, pady=6)

    ttk.Label(combat_frame, text="HP:", font=STYLE["font_normal"]).grid(row=0, column=0, sticky="e")
    hp_current_entry = tk.Entry(combat_frame, width=6, font=STYLE["font_normal"])
    hp_current_entry.grid(row=0, column=1, padx=6)
    ttk.Label(combat_frame, text="/", font=STYLE["font_normal"]).grid(row=0, column=2)
    hp_max_entry = tk.Entry(combat_frame, width=6, font=STYLE["font_normal"])
    hp_max_entry.grid(row=0, column=3, padx=6)

    ttk.Label(combat_frame, text="AC:", font=STYLE["font_normal"]).grid(row=1, column=0, sticky="e")
    ac_entry = tk.Entry(combat_frame, width=6, font=STYLE["font_normal"])
    ac_entry.grid(row=1, column=1, padx=6)

    def roll_initiative():
        mods = calc_mods(character["stats"])
        initiative_result_label.config(text=str(roll(20) + mods["DEX"]))

    ttk.Label(combat_frame, text="Initiative:", font=STYLE["font_normal"]).grid(row=2, column=0, sticky="e")
    ttk.Button(combat_frame, text="+DEX", command=roll_initiative, style="Accent.TButton").grid(row=2, column=1, padx=6)
    initiative_result_label = ttk.Label(combat_frame, text="", font=STYLE["font_normal"])
    initiative_result_label.grid(row=2, column=2, padx=6)

    # ---------- Notes and Inventory ----------
    bottom_frame = ttk.Frame(inner)
    bottom_frame.pack(fill="both", expand=True, padx=6, pady=6)

    notes_frame = ttk.LabelFrame(bottom_frame, text="Notes", padding=8)
    notes_frame.pack(side="left", fill="both", expand=True, padx=6, pady=6)
    notes_text = tk.Text(notes_frame, height=10, wrap="word", font=STYLE["font_normal"])
    notes_text.pack(fill="both", expand=True)

    inventory_frame = ttk.LabelFrame(bottom_frame, text="Inventory", padding=8)
    inventory_frame.pack(side="right", fill="both", expand=True, padx=6, pady=6)

    inventory_listbox = tk.Listbox(inventory_frame, height=10, font=STYLE["font_normal"])
    inventory_listbox.pack(fill="both", expand=True, padx=6, pady=6)

    new_item_entry = tk.Entry(inventory_frame, font=STYLE["font_normal"])
    new_item_entry.pack(fill="x", padx=6)

    def add_item():
        it = new_item_entry.get().strip()
        if it:
            character.setdefault("inventory", []).append(it)
            inventory_listbox.insert(tk.END, it)
            new_item_entry.delete(0, tk.END)

    def remove_selected_item():
        sel = inventory_listbox.curselection()
        if sel:
            idx = sel[0]
            inventory_listbox.delete(idx)
            del character["inventory"][idx]

    btn_row = ttk.Frame(inventory_frame)
    btn_row.pack(fill="x", pady=6)
    ttk.Button(btn_row, text="Add", command=add_item, style="Accent.TButton").pack(side="left", padx=6)
    ttk.Button(btn_row, text="Remove Selected", command=remove_selected_item, style="Accent.TButton").pack(side="right", padx=6)

    # ---------- Save / Load controls ----------
    def update_combat_and_notes_from_ui():
        # Safely read numeric fields and update character dict
        try:
            character["hp"]["current"] = int(hp_current_entry.get())
        except Exception:
            pass
        try:
            character["hp"]["max"] = int(hp_max_entry.get())
        except Exception:
            pass
        try:
            character["ac"] = int(ac_entry.get())
        except Exception:
            pass
        character["notes"] = notes_text.get("1.0", tk.END).strip()
        character["name"] = name_entry.get().strip()

    def save_character_action():
        update_combat_and_notes_from_ui()
        save_character_to_file(character)

    def load_character_action():
        try:
            loaded = load_character_from_file()
            # update the existing dictionary in-place so closures keep working
            character.clear()
            character.update(loaded)
            refresh_ui()
        except FileNotFoundError:
            print("No saved character file found.")

    control_frame = ttk.Frame(inner, padding=8)
    control_frame.pack(fill="x", padx=6, pady=6)
    ttk.Button(control_frame, text="Save Character", command=save_character_action, style="Accent.TButton").pack(side="left", padx=6)
    ttk.Button(control_frame, text="Load Character", command=load_character_action, style="Accent.TButton").pack(side="left", padx=6)

    # Final UI sync
    refresh_ui()

    # Start the GUI loop
    root.mainloop()


if __name__ == "__main__":
    gui_app()
