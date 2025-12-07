# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from nlp_parser import parse_user_text
from calculator import calculate_for_patch

def do_calc():
    try:
        inp = entry.get().strip()
        parsed = parse_user_text(inp)
        version = parsed.get("version") or version_entry.get().strip()
        player = player_var.get()
        res = calculate_for_patch(version, player_type=player,
                                   include_story=parsed.get("include_story", True),
                                   include_character=parsed.get("include_character", True),
                                   include_map=parsed.get("include_map", False))
        out = f"Patch {res['patch']} ({res['patch_date']})\n\n"
        for k, v in res["details"].items():
            out += f"{k}: {v}\n"
        out += f"\nTOTAL: {res['total']}"
        result_text.config(state="normal")
        result_text.delete("1.0", "end")
        result_text.insert("end", out)
        result_text.config(state="disabled")
    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Genshin Primo AI")

frame = ttk.Frame(root, padding=12)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="Natural command:").grid(row=0, column=0, sticky="w")
entry = ttk.Entry(frame, width=60)
entry.grid(row=0, column=1, columnspan=3)

ttk.Label(frame, text="Patch (fallback):").grid(row=1, column=0, sticky="w")
version_entry = ttk.Entry(frame)
version_entry.grid(row=1, column=1, sticky="w")

player_var = tk.StringVar(value="f2p")
ttk.Radiobutton(frame, text="F2P", variable=player_var, value="f2p").grid(row=2, column=0)
ttk.Radiobutton(frame, text="Welkin", variable=player_var, value="welkin").grid(row=2, column=1)
ttk.Radiobutton(frame, text="Welkin + BP", variable=player_var, value="welkin+bp").grid(row=2, column=2)

calc_btn = ttk.Button(frame, text="Calculate", command=do_calc)
calc_btn.grid(row=3, column=0, pady=8)

result_text = tk.Text(frame, width=60, height=12, state="disabled")
result_text.grid(row=4, column=0, columnspan=4)

root.mainloop()
