import csv
import re
import sys
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


DEFAULT_NOTE_TYPE = "Prettify Unified MCQ Stable"
DEFAULT_DECK = "Socratopia"


def clean(value: str) -> str:
    return (value or "").replace("\r", "").replace("\n", "<br>").replace("\t", " ").strip()


def parse_line(line: str, row_number: int) -> list[str]:
    cols = line.split("\t")
    if len(cols) < 2:
        raise ValueError(f"第 {row_number} 行少于 2 列")

    front = cols[0]
    back = cols[1]
    tags = cols[2] if len(cols) > 2 else ""

    match = re.match(
        r"^([\s\S]*?)<br\s*/?><br\s*/?><b>A\.</b>\s*([\s\S]*?)<br\s*/?><b>B\.</b>\s*([\s\S]*?)<br\s*/?><b>C\.</b>\s*([\s\S]*?)<br\s*/?><b>D\.</b>\s*([\s\S]*)$",
        front,
        flags=re.I,
    )
    correct_match = re.search(r"<b>\s*Correct:\s*([A-D])\.</b>", back, flags=re.I)

    if not match:
        raise ValueError(f"第 {row_number} 行无法解析 A/B/C/D 选项")
    if not correct_match:
        raise ValueError(f"第 {row_number} 行无法解析 Correct: A-D")

    question, a, b, c, d = match.groups()
    correct = correct_match.group(1).upper()
    explanation = re.sub(r"<b>\s*Correct:\s*[A-D]\.</b>\s*", "", back, count=1, flags=re.I)

    return [
        clean(front),
        clean(back),
        "",
        clean(question),
        clean(a),
        clean(b),
        clean(c),
        clean(d),
        correct,
        clean(explanation),
        clean(tags),
    ]


def convert(input_path: Path, output_path: Path, deck_name: str, note_type: str) -> tuple[int, list[str]]:
    lines = input_path.read_text(encoding="utf-8-sig").splitlines()
    rows = []
    errors = []

    for row_number, line in enumerate(lines, start=1):
        if not line.strip() or line.startswith("#"):
            continue
        try:
            rows.append(parse_line(line, row_number))
        except ValueError as exc:
            errors.append(str(exc))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        f.write("#separator:tab\n")
        f.write("#html:true\n")
        f.write(f"#notetype:{note_type.strip() or DEFAULT_NOTE_TYPE}\n")
        f.write(f"#deck:{deck_name.strip() or DEFAULT_DECK}\n")
        f.write("#tags column:11\n")
        writer.writerows(rows)

    return len(rows), errors


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.stem + "_anki_unified.tsv")


class ConverterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Socratopia TXT -> Anki TSV")
        self.root.minsize(720, 430)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.deck_var = tk.StringVar(value=DEFAULT_DECK)
        self.note_type_var = tk.StringVar(value=DEFAULT_NOTE_TYPE)
        self.status_var = tk.StringVar(value="选择原始 txt 文件，然后点击转换。")

        self.build_ui()

    def build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(6, weight=1)

        title = ttk.Label(frame, text="Socratopia TXT 转 Anki 选择题 TSV", font=("", 15, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(frame, text="原始 TXT").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.input_var).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(frame, text="选择文件", command=self.choose_input).grid(row=1, column=2, sticky="ew")

        ttk.Label(frame, text="输出 TSV").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.output_var).grid(row=2, column=1, sticky="ew", padx=8)
        ttk.Button(frame, text="保存为", command=self.choose_output).grid(row=2, column=2, sticky="ew")

        ttk.Label(frame, text="牌组名").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.deck_var).grid(row=3, column=1, sticky="ew", padx=8)

        ttk.Label(frame, text="笔记类型").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.note_type_var).grid(row=4, column=1, sticky="ew", padx=8)

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 8))
        ttk.Button(buttons, text="转换", command=self.run_convert).pack(side=tk.LEFT)
        ttk.Button(buttons, text="打开输出目录", command=self.open_output_folder).pack(side=tk.LEFT, padx=8)
        ttk.Button(buttons, text="清空日志", command=self.clear_log).pack(side=tk.LEFT)

        self.log = tk.Text(frame, height=10, wrap="word")
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew")
        scroll = ttk.Scrollbar(frame, command=self.log.yview)
        scroll.grid(row=6, column=3, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)

        ttk.Label(frame, textvariable=self.status_var).grid(row=7, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.write_log("说明：先导入统一模板 apkg，再把这里生成的 TSV 导入 Anki。")
        self.write_log("输出列顺序：Front, Back, Note, Question, A, B, C, D, Correct, Explanation, Tags。")
        self.write_log("Front 保留在第 1 列，用于让 Anki 匹配旧卡并保留复习记录。")

    def choose_input(self) -> None:
        filename = filedialog.askopenfilename(
            title="选择 Socratopia 原始 txt 文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not filename:
            return
        path = Path(filename)
        self.input_var.set(str(path))
        if not self.output_var.get().strip():
            self.output_var.set(str(default_output_path(path)))

    def choose_output(self) -> None:
        initial = self.output_var.get().strip()
        initial_path = Path(initial) if initial else None
        filename = filedialog.asksaveasfilename(
            title="选择输出 TSV",
            defaultextension=".tsv",
            initialdir=str(initial_path.parent) if initial_path else "",
            initialfile=initial_path.name if initial_path else "socratopia_anki_unified.tsv",
            filetypes=[("TSV files", "*.tsv"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            self.output_var.set(filename)

    def run_convert(self) -> None:
        try:
            input_text = self.input_var.get().strip()
            output_text = self.output_var.get().strip()
            if not input_text:
                messagebox.showwarning("缺少文件", "请先选择原始 txt 文件。")
                return

            input_path = Path(input_text)
            if not input_path.exists():
                messagebox.showerror("文件不存在", f"找不到原始文件：\n{input_path}")
                return

            output_path = Path(output_text) if output_text else default_output_path(input_path)
            self.output_var.set(str(output_path))

            count, errors = convert(
                input_path=input_path,
                output_path=output_path,
                deck_name=self.deck_var.get(),
                note_type=self.note_type_var.get(),
            )

            self.write_log("")
            self.write_log(f"转换完成：{count} 张卡片")
            self.write_log(f"输出文件：{output_path}")
            if errors:
                self.write_log(f"未转换行数：{len(errors)}")
                for error in errors[:30]:
                    self.write_log(" - " + error)
                if len(errors) > 30:
                    self.write_log(" - 其余错误已省略。")
                self.status_var.set(f"完成，但有 {len(errors)} 行未转换。")
                messagebox.showwarning("转换完成但有错误", f"已转换 {count} 张卡片，有 {len(errors)} 行未转换。")
            else:
                self.status_var.set(f"完成：{count} 张卡片。")
                messagebox.showinfo("转换完成", f"已转换 {count} 张卡片。")
        except Exception:
            detail = traceback.format_exc()
            self.write_log("")
            self.write_log(detail)
            self.status_var.set("转换失败，请查看日志。")
            messagebox.showerror("转换失败", detail)

    def open_output_folder(self) -> None:
        output_text = self.output_var.get().strip()
        if output_text:
            folder = Path(output_text).expanduser().resolve().parent
        else:
            input_text = self.input_var.get().strip()
            folder = Path(input_text).expanduser().resolve().parent if input_text else Path.cwd()

        if sys.platform.startswith("win"):
            import os

            os.startfile(folder)
        elif sys.platform == "darwin":
            import subprocess

            subprocess.Popen(["open", str(folder)])
        else:
            import subprocess

            subprocess.Popen(["xdg-open", str(folder)])

    def clear_log(self) -> None:
        self.log.delete("1.0", tk.END)

    def write_log(self, text: str) -> None:
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
