"""
Python Quiz App - Enhanced Edition

Features:
- Easy / Medium / Hard modes (different timer and negative-marking penalty)
- 10 questions per quiz
- Negative marking for wrong answers (no penalty for timeout)
- Optional sound effects (Windows winsound; Tk bell fallback)
- Light / dark mode toggle
- Progress bar, question counter, score and accuracy tracking
- Leaderboard and review of incorrect answers
- Keyboard shortcuts: 1-4 to answer, Enter for Next
"""

import json
import random
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

SCORES_FILE = Path(__file__).with_name("quiz_scores.json")
QUESTIONS_PER_QUIZ = 10
MAX_NAME_LENGTH = 20

# Difficulty: seconds per question, penalty for a wrong answer.
DIFFICULTY_SETTINGS = {
    "Easy": {"time": 25, "penalty": 0.25},
    "Medium": {"time": 15, "penalty": 0.50},
    "Hard": {"time": 10, "penalty": 1.00},
}


@dataclass
class Question:
    text: str
    options: list
    answer: str
    explanation: str = ""


QUESTION_BANK = {
    "Basics": [
        Question("Which of them is a keyword in Python?", ["range", "def", "Val", "to"], "def",
                 "'def' is used to define a function."),
        Question("Which of the following is a built-in function in Python?",
                 ["factorial()", "print()", "seed()", "sqrt()"], "print()",
                 "print() is a built-in function. factorial(), seed() and sqrt() belong to modules."),
        Question("Which of the following is not a core built-in data type in Python?",
                 ["Tuple", "Dictionary", "List", "Class"], "Class",
                 "Tuple, dictionary and list are built-in data types; class is a keyword."),
        Question("Who developed the Python programming language?",
                 ["Wick van Rossum", "Rasmus Lerdorf", "Guido van Rossum", "Dennis Ritchie"],
                 "Guido van Rossum", "Guido van Rossum created Python."),
        Question("Which is the extension of a Python file?", [".python", ".p", ".pl", ".py"], ".py"),
        Question("Which symbol starts a single-line comment in Python?", ["//", "#", "/*", "--"], "#"),
        Question("What is the output of len('Python')?", ["5", "6", "7", "Error"], "6"),
        Question("Which of these data types is immutable?", ["list", "dict", "set", "tuple"], "tuple",
                 "A tuple cannot be changed after it is created."),
        Question("Which keyword is used to make a decision in Python?",
                 ["if", "for", "def", "import"], "if"),
        Question("Which function is used to get input from the keyboard?",
                 ["scan()", "input()", "read()", "get()"], "input()"),
        Question("Which operator is used for exponentiation in Python?",
                 ["^", "**", "//", "%%"], "**"),
        Question("What does the len() function return?", 
                 ["The number of items", "The data type", "The memory address", "The largest item"],
                 "The number of items"),
    ],
    "Intermediate": [
        Question("What does list(range(3)) return?",
                 ["[1, 2, 3]", "[0, 1, 2]", "[0, 1, 2, 3]", "(0, 1, 2)"], "[0, 1, 2]",
                 "range(3) starts at 0 and stops before 3."),
        Question("Which keyword turns a function into a generator?", ["return", "yield", "lambda", "async"], "yield"),
        Question("What is the value of 3 ** 2?", ["6", "9", "5", "1.5"], "9",
                 "** is the exponent operator."),
        Question("Which list method adds an item to the end?", ["add", "append", "insert", "push"], "append"),
        Question("What does the 'is' operator check?",
                 ["Equality of values", "Identity of objects", "Type of object", "Membership"],
                 "Identity of objects", "Use == for value equality and 'is' for object identity."),
        Question("Which statements are used to handle exceptions in Python?",
                 ["try / except", "catch / throw", "error / handle", "do / rescue"], "try / except"),
        Question("What is the result of 10 // 3?", ["3.33", "3", "1", "4"], "3",
                 "// performs floor division."),
        Question("Which collection stores unique values?", ["List", "Tuple", "Set", "String"], "Set"),
        Question("Which file mode is used to append data to a file?", ["r", "w", "a", "x"], "a"),
        Question("What does the __init__ method do in a class?",
                 ["Deletes an object", "Initializes an object", "Imports a module", "Ends a loop"],
                 "Initializes an object"),
        Question("Which keyword is used to import a module?", ["include", "using", "import", "require"], "import"),
        Question("What is a lambda function?", 
                 ["An anonymous function", "A loop", "A class variable", "A package manager"],
                 "An anonymous function"),
    ],
    "Mixed": [],
}
QUESTION_BANK["Mixed"] = QUESTION_BANK["Basics"] + QUESTION_BANK["Intermediate"]


def load_scores():
    try:
        data = json.loads(SCORES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def save_score(name, category, difficulty, engine):
    scores = load_scores()
    scores.append({
        "name": name,
        "category": category,
        "difficulty": difficulty,
        "score": round(engine.score, 2),
        "total": engine.total,
        "percent": engine.percent,
        "correct": engine.correct_count,
        "wrong": engine.wrong_count,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    scores.sort(key=lambda item: (-item.get("percent", 0), item.get("date", "")))
    try:
        SCORES_FILE.write_text(json.dumps(scores[:50], indent=2), encoding="utf-8")
    except OSError:
        pass


def leaderboard_text(limit=5):
    scores = load_scores()[:limit]
    if not scores:
        return "No scores yet - be the first!"
    lines = []
    for i, item in enumerate(scores, 1):
        lines.append(
            f"{i}. {item.get('name', 'Player')[:MAX_NAME_LENGTH]:<{MAX_NAME_LENGTH}} "
            f"{item.get('score', 0)}/{item.get('total', 0)} "
            f"({item.get('percent', 0)}%)  {item.get('difficulty', '')}"
        )
    return "\n".join(lines)


class QuizEngine:
    """Quiz logic kept separate from the graphical interface."""

    def __init__(self, questions, count=QUESTIONS_PER_QUIZ, penalty=0.5):
        picked = random.sample(questions, min(count, len(questions)))
        self.questions = [
            Question(q.text, random.sample(q.options, len(q.options)), q.answer, q.explanation)
            for q in picked
        ]
        self.index = 0
        self.score = 0.0
        self.penalty = penalty
        self.correct_count = 0
        self.wrong_count = 0
        self.timeout_count = 0
        self.wrong = []

    @property
    def total(self):
        return len(self.questions)

    @property
    def current(self):
        return self.questions[self.index]

    @property
    def finished(self):
        return self.index >= self.total

    @property
    def percent(self):
        return round(100 * max(0, self.score) / self.total) if self.total else 0

    def submit(self, choice_index):
        """None means timeout. Wrong answers receive negative marks; timeout has no penalty."""
        q = self.current
        chosen = q.options[choice_index] if choice_index is not None else None
        correct = chosen == q.answer
        if correct:
            self.score += 1
            self.correct_count += 1
        elif choice_index is None:
            self.timeout_count += 1
            self.wrong.append((q, None, "Time out"))
        else:
            self.score -= self.penalty
            self.wrong_count += 1
            self.wrong.append((q, chosen, "Wrong answer"))
        return correct


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Quiz - Enhanced Edition")
        self.geometry("900x760")
        self.minsize(760, 650)

        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar(value="Mixed")
        self.difficulty_var = tk.StringVar(value="Medium")
        self.sound_var = tk.BooleanVar(value=True)
        self.dark_mode = False

        self.engine = None
        self.timer_id = None
        self.time_left = 0
        self.answered = False
        self.option_buttons = []

        self.container = ttk.Frame(self, padding=26)
        self.container.pack(fill="both", expand=True)
        self._setup_styles()
        self.show_start()

    def _palette(self):
        if self.dark_mode:
            return {
                "bg": "#171923", "panel": "#242938", "fg": "#edf2f7",
                "muted": "#b7c0d0", "accent": "#79a9ff", "button": "#30394d",
                "input": "#202636", "correct": "#237a50", "wrong": "#a83b46",
            }
        return {
            "bg": "#f3f6fb", "panel": "#ffffff", "fg": "#1d2736",
            "muted": "#526174", "accent": "#2457a6", "button": "#e7edf6",
            "input": "#ffffff", "correct": "#2e7d32", "wrong": "#c62828",
        }

    def _setup_styles(self):
        p = self._palette()
        self.configure(bg=p["bg"])
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=p["bg"], foreground=p["fg"], font=("Segoe UI", 11))
        style.configure("TFrame", background=p["bg"])
        style.configure("Card.TFrame", background=p["panel"])
        style.configure("TLabel", background=p["bg"], foreground=p["fg"])
        style.configure("Title.TLabel", font=("Segoe UI", 30, "bold"), foreground=p["accent"])
        style.configure("Heading.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("Question.TLabel", font=("Segoe UI", 19, "bold"))
        style.configure("Info.TLabel", font=("Segoe UI", 11), foreground=p["muted"])
        style.configure("TButton", font=("Segoe UI", 11), padding=10,
                        background=p["button"], foreground=p["fg"])
        style.map("TButton", background=[("active", p["accent"])])
        style.configure("Main.TButton", font=("Segoe UI", 12, "bold"),
                        padding=11, background=p["accent"], foreground="#ffffff")
        style.map("Main.TButton", background=[("active", p["accent"])])
        style.configure("Option.TButton", font=("Segoe UI", 12), padding=14,
                        background=p["button"], foreground=p["fg"])
        style.configure("Correct.TButton", font=("Segoe UI", 12, "bold"),
                        padding=14, background=p["correct"], foreground="#ffffff")
        style.configure("Wrong.TButton", font=("Segoe UI", 12, "bold"),
                        padding=14, background=p["wrong"], foreground="#ffffff")
        style.configure("TEntry", fieldbackground=p["input"], foreground=p["fg"])
        style.configure("TCombobox", fieldbackground=p["input"], foreground=p["fg"])
        style.configure("Horizontal.TProgressbar", troughcolor=p["button"],
                        background=p["accent"], thickness=12)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._setup_styles()
        if self.engine is None:
            self.show_start()
        elif self.engine.finished:
            self.show_result()
        elif self.answered:
            self.show_question(review=True)
        else:
            self.show_question()

    def toggle_sound(self):
        self.sound_var.set(not self.sound_var.get())
        self.show_start()

    def play_sound(self, kind):
        if not self.sound_var.get():
            return
        try:
            if __import__("sys").platform.startswith("win"):
                import winsound
                tones = {
                    "correct": (880, 120),
                    "wrong": (260, 220),
                    "timeout": (180, 300),
                    "finish": (660, 100),
                }
                freq, duration = tones.get(kind, (500, 100))
                winsound.Beep(freq, duration)
            else:
                self.bell()
        except Exception:
            try:
                self.bell()
            except Exception:
                pass

    def _clear(self):
        self._stop_timer()
        for widget in self.container.winfo_children():
            widget.destroy()
        for key in ("<Key>", "<Return>"):
            self.unbind(key)

    def _toolbar(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 14))
        ttk.Button(bar, text="🌙 Dark mode" if not self.dark_mode else "☀ Light mode",
                   command=self.toggle_theme).pack(side="right", padx=4)
        ttk.Button(bar, text=("🔊 Sound ON" if self.sound_var.get() else "🔇 Sound OFF"),
                   command=self.toggle_sound).pack(side="right", padx=4)

    def show_start(self):
        self._clear()
        c = self.container
        self._toolbar(c)
        ttk.Label(c, text="PYTHON QUIZ", style="Title.TLabel").pack(pady=(12, 4))
        ttk.Label(c, text="Practice • Learn • Improve", style="Info.TLabel").pack(pady=(0, 20))

        card = ttk.Frame(c, style="Card.TFrame", padding=22)
        card.pack(fill="x", padx=45, pady=8)
        ttk.Label(card, text="Set up your quiz", style="Heading.TLabel").pack(pady=(0, 14))

        form = ttk.Frame(card, style="Card.TFrame")
        form.pack()
        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="e", padx=10, pady=9)
        name_entry = ttk.Entry(form, textvariable=self.name_var, width=25, font=("Segoe UI", 12))
        name_entry.grid(row=0, column=1, padx=10, pady=9)
        ttk.Label(form, text="Category").grid(row=1, column=0, sticky="e", padx=10, pady=9)
        ttk.Combobox(form, textvariable=self.category_var, values=list(QUESTION_BANK),
                     state="readonly", width=22).grid(row=1, column=1, padx=10, pady=9)
        ttk.Label(form, text="Difficulty").grid(row=2, column=0, sticky="e", padx=10, pady=9)
        ttk.Combobox(form, textvariable=self.difficulty_var, values=list(DIFFICULTY_SETTINGS),
                     state="readonly", width=22).grid(row=2, column=1, padx=10, pady=9)
        name_entry.focus_set()

        setting = DIFFICULTY_SETTINGS[self.difficulty_var.get()]
        ttk.Label(card, text=(
            f"{QUESTIONS_PER_QUIZ} questions  •  {setting['time']} seconds each  •  "
            f"-{setting['penalty']} mark for a wrong answer  •  No penalty for timeout"
        ), style="Info.TLabel", wraplength=650, justify="center").pack(pady=12)
        ttk.Button(card, text="START QUIZ", style="Main.TButton",
                   command=self.start_quiz).pack(pady=8)

        ttk.Label(c, text="TOP PLAYERS", style="Heading.TLabel").pack(pady=(20, 8))
        board = tk.Text(c, height=6, width=75, font=("Consolas", 11), relief="flat",
                        padx=12, pady=10, wrap="none")
        board.insert("1.0", leaderboard_text())
        board.configure(state="disabled", bg=self._palette()["panel"],
                        fg=self._palette()["fg"], insertbackground=self._palette()["fg"])
        board.pack()
        ttk.Label(c, text="Tip: Press 1, 2, 3 or 4 to select an answer.",
                  style="Info.TLabel").pack(pady=12)

    def start_quiz(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Username required", "Please enter your username.")
            return
        if len(name) > MAX_NAME_LENGTH:
            messagebox.showwarning("Username too long", f"Use at most {MAX_NAME_LENGTH} characters.")
            return

        difficulty = self.difficulty_var.get()
        settings = DIFFICULTY_SETTINGS[difficulty]
        self.engine = QuizEngine(
            QUESTION_BANK[self.category_var.get()],
            count=QUESTIONS_PER_QUIZ,
            penalty=settings["penalty"],
        )
        self.show_question()

    def show_question(self, review=False):
        self._clear()
        e, q, c = self.engine, self.engine.current, self.container
        self.answered = review

        self._toolbar(c)
        header = ttk.Frame(c)
        header.pack(fill="x")
        ttk.Label(header, text=f"QUESTION {e.index + 1} / {e.total}",
                  style="Heading.TLabel").pack(side="left")
        ttk.Label(header, text=f"Score: {e.score:.2f}", style="Heading.TLabel").pack(side="right")

        ttk.Progressbar(c, maximum=e.total, value=e.index + (1 if review else 0)).pack(fill="x", pady=12)
        stats = ttk.Frame(c)
        stats.pack(fill="x", pady=(0, 18))
        ttk.Label(stats, text=f"Correct: {e.correct_count}", style="Info.TLabel").pack(side="left")
        ttk.Label(stats, text=f"Wrong: {e.wrong_count}", style="Info.TLabel").pack(side="left", padx=18)
        ttk.Label(stats, text=f"Time out: {e.timeout_count}", style="Info.TLabel").pack(side="left")
        self.timer_lbl = ttk.Label(stats, text="", style="Info.TLabel")
        self.timer_lbl.pack(side="right")

        card = ttk.Frame(c, style="Card.TFrame", padding=26)
        card.pack(fill="both", expand=True, padx=25, pady=8)
        ttk.Label(card, text=q.text, style="Question.TLabel", wraplength=720,
                  justify="center").pack(pady=(20, 28))

        grid = ttk.Frame(card, style="Card.TFrame")
        grid.pack(fill="x", padx=12)
        grid.columnconfigure((0, 1), weight=1, uniform="opt")
        self.option_buttons = []
        for i, option in enumerate(q.options):
            button = ttk.Button(
                grid, text=f"{i + 1}.  {option}", style="Option.TButton",
                command=lambda i=i: self.choose(i)
            )
            button.grid(row=i // 2, column=i % 2, padx=8, pady=9, sticky="ew")
            self.option_buttons.append(button)

        self.feedback_lbl = ttk.Label(card, text="", style="Info.TLabel",
                                      wraplength=700, justify="center")
        self.feedback_lbl.pack(pady=18)
        self.next_btn = ttk.Button(card, text="NEXT" if e.index < e.total - 1 else "FINISH",
                                   style="Main.TButton", command=self.next_question)

        if review:
            self._show_answer_feedback(q, None)
            for button in self.option_buttons:
                button.state(["disabled"])
            self.next_btn.pack(pady=8)
        else:
            self.bind("<Key>", self._on_key)
            self.bind("<Return>", lambda event: self.next_question() if self.answered else None)
            self.time_left = DIFFICULTY_SETTINGS[self.difficulty_var.get()]["time"]
            self._tick()

    def _on_key(self, event):
        if event.char in "1234" and not self.answered:
            index = int(event.char) - 1
            if index < len(self.option_buttons):
                self.choose(index)

    def _tick(self):
        self.timer_lbl.config(
            text=f"Time left: {self.time_left}s",
            foreground="#e05252" if self.time_left <= 5 else self._palette()["muted"]
        )
        if self.time_left <= 0:
            self.choose(None)
            return
        self.time_left -= 1
        self.timer_id = self.after(1000, self._tick)

    def _stop_timer(self):
        if self.timer_id is not None:
            try:
                self.after_cancel(self.timer_id)
            except tk.TclError:
                pass
            self.timer_id = None

    def _show_answer_feedback(self, q, chosen_index):
        for i, button in enumerate(self.option_buttons):
            if q.options[i] == q.answer:
                button.configure(style="Correct.TButton")
            elif chosen_index is not None and i == chosen_index:
                button.configure(style="Wrong.TButton")
        chosen = q.options[chosen_index] if chosen_index is not None else None
        if chosen == q.answer:
            message = "Correct! +1 mark."
            colour = self._palette()["correct"]
        elif chosen is None:
            message = f"Time is up! Correct answer: {q.answer}. No marks deducted."
            colour = self._palette()["wrong"]
        else:
            message = (
                f"Wrong answer. Correct answer: {q.answer}. "
                f"-{self.engine.penalty:g} mark."
            )
            colour = self._palette()["wrong"]
        if q.explanation:
            message += "\n" + q.explanation
        self.feedback_lbl.config(text=message, foreground=colour)

    def choose(self, index):
        if self.answered:
            return
        self.answered = True
        self._stop_timer()
        q = self.engine.current
        correct = self.engine.submit(index)
        self._show_answer_feedback(q, index)
        for button in self.option_buttons:
            button.state(["disabled"])
        self.play_sound("correct" if correct else ("timeout" if index is None else "wrong"))
        self.next_btn.pack(pady=8)

    def next_question(self):
        if not self.answered:
            return
        self.engine.index += 1
        if self.engine.finished:
            self.show_result()
        else:
            self.show_question()

    def show_result(self):
        self._clear()
        e, c = self.engine, self.container
        name, category = self.name_var.get().strip(), self.category_var.get()
        difficulty = self.difficulty_var.get()
        save_score(name, category, difficulty, e)
        self.play_sound("finish")

        verdict = (
            "Outstanding!" if e.percent >= 90 else
            "Great job!" if e.percent >= 70 else
            "Good effort!" if e.percent >= 50 else "Keep practising!"
        )
        self._toolbar(c)
        ttk.Label(c, text="QUIZ COMPLETED", style="Title.TLabel").pack(pady=(8, 5))
        ttk.Label(c, text=verdict, style="Heading.TLabel").pack(pady=4)

        card = ttk.Frame(c, style="Card.TFrame", padding=22)
        card.pack(fill="x", padx=35, pady=12)
        ttk.Label(card, text=f"{name}  •  {difficulty} mode",
                  style="Heading.TLabel").pack(pady=4)
        ttk.Label(card, text=f"{e.score:.2f} / {e.total} marks",
                  style="Title.TLabel").pack(pady=4)
        ttk.Label(card, text=f"{e.percent}% score", style="Heading.TLabel").pack(pady=4)

        progress = ttk.Progressbar(card, maximum=e.total, value=e.correct_count)
        progress.pack(fill="x", pady=10)
        ttk.Label(card, text=(
            f"Correct: {e.correct_count}    Wrong: {e.wrong_count}    "
            f"Timed out: {e.timeout_count}"
        ), style="Info.TLabel").pack(pady=5)
        ttk.Label(card, text=f"Negative marking: -{e.penalty:g} for each wrong answer",
                  style="Info.TLabel").pack(pady=3)

        ttk.Label(c, text="REVIEW OF MISTAKES", style="Heading.TLabel").pack(pady=(10, 5))
        if e.wrong:
            review = tk.Text(c, height=8, wrap="word", font=("Segoe UI", 10),
                             relief="flat", padx=12, pady=10)
            for question, chosen, reason in e.wrong:
                review.insert("end", f"Q: {question.text}\n")
                review.insert("end", f"Your answer: {chosen if chosen is not None else reason}\n")
                review.insert("end", f"Correct answer: {question.answer}\n\n")
            review.configure(state="disabled", bg=self._palette()["panel"],
                             fg=self._palette()["fg"])
            review.pack(fill="x", padx=35)
        else:
            ttk.Label(c, text="Perfect! No mistakes to review.",
                      style="Info.TLabel").pack()

        buttons = ttk.Frame(c)
        buttons.pack(pady=14)
        ttk.Button(buttons, text="PLAY AGAIN", style="Main.TButton",
                   command=self.show_start).pack(side="left", padx=8)
        ttk.Button(buttons, text="QUIT", command=self.destroy).pack(side="left", padx=8)


if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
