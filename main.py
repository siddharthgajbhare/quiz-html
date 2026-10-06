//aad some new 
import json
import random
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

SCORES_FILE = Path(__file__).with_name("quiz_scores.json")
TIME_PER_QUESTION = 15      # seconds
QUESTIONS_PER_QUIZ = 5
MAX_NAME_LENGTH = 20


@dataclass
class Question:
    text: str
    options: list
    answer: str
    explanation: str = ""


# ----------------------------------------------------------------- data
QUESTION_BANK = {
    "Basics": [
        Question("Which of them is a keyword in Python?", ["range", "def", "Val", "to"], "def",
                 "'def' is used to define a function."),
        Question("Which of the following is a built-in function in Python?",
                 ["factorial()", "print()", "seed()", "sqrt()"], "print()",
                 "factorial, seed and sqrt live in the math/random modules."),
        Question("Which of the following is not a core data type in Python?",
                 ["Tuple", "Dictionary", "Lists", "Class"], "Class",
                 "Tuple, dict and list are built-in types; 'class' is a keyword."),
        Question("Who developed the Python programming language?",
                 ["Wick Van Rossum", "Rasmus Lerdorf", "Guido Van Rossum", "Niene Stom"],
                 "Guido Van Rossum", "Guido van Rossum created Python in 1991."),
        Question("Which of the following is the extension for a Python file?",
                 [".python", ".p", ".pl", ".py"], ".py"),
        Question("Which symbol starts a single-line comment in Python?",
                 ["//", "#", "/*", "--"], "#"),
        Question("What is the output of len('Python')?", ["5", "6", "7", "Error"], "6"),
        Question("Which of these data types is immutable?",
                 ["list", "dict", "set", "tuple"], "tuple",
                 "Tuples cannot be changed after creation."),
    ],
    "Intermediate": [
        Question("What does list(range(3)) return?",
                 ["[1, 2, 3]", "[0, 1, 2]", "[0, 1, 2, 3]", "(0, 1, 2)"], "[0, 1, 2]",
                 "range(3) starts at 0 and stops before 3."),
        Question("Which keyword turns a function into a generator?",
                 ["return", "yield", "lambda", "async"], "yield"),
        Question("What is the value of 3 ** 2?", ["6", "9", "5", "1.5"], "9",
                 "** is the exponent operator."),
        Question("Which list method adds an item to the end?",
                 ["add", "append", "insert", "push"], "append"),
        Question("What does the 'is' operator check?",
                 ["Equality of values", "Identity of objects", "Type of object", "Membership"],
                 "Identity of objects", "Use == for value equality, 'is' for same object."),
        Question("Which statements handle exceptions in Python?",
                 ["try / except", "catch / throw", "error / handle", "do / rescue"], "try / except"),
    ],
}
QUESTION_BANK["Mixed"] = [q for qs in list(QUESTION_BANK.values()) for q in qs]


# --------------------------------------------------------------- engine
class QuizEngine:
    """Pure quiz logic (no GUI) - easy to test."""

    def __init__(self, questions, count=QUESTIONS_PER_QUIZ):
        picked = random.sample(questions, min(count, len(questions)))
        # copy each question so shuffling options never touches the bank
        self.questions = [Question(q.text, random.sample(q.options, len(q.options)),
                                   q.answer, q.explanation) for q in picked]
        self.index = 0
        self.score = 0
        self.wrong = []     # (question, chosen text or None)

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
        return round(100 * self.score / self.total) if self.total else 0

    def submit(self, choice_index):
        """Record an answer (None = timed out). Returns True if correct."""
        q = self.current
        chosen = q.options[choice_index] if choice_index is not None else None
        correct = chosen == q.answer
        if correct:
            self.score += 1
        else:
            self.wrong.append((q, chosen))
        return correct

    def next(self):
        self.index += 1


# ---------------------------------------------------------- leaderboard
def load_scores():
    try:
        return json.loads(SCORES_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def save_score(name, category, engine):
    scores = load_scores()
    scores.append({"name": name, "category": category, "score": engine.score,
                   "total": engine.total, "percent": engine.percent,
                   "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
    scores.sort(key=lambda s: (-s["percent"], s["date"]))
    try:
        SCORES_FILE.write_text(json.dumps(scores[:20], indent=2), encoding="utf-8")
    except OSError:
        pass  # a read-only folder should not crash the quiz


def leaderboard_text(limit=5):
    scores = load_scores()[:limit]
    if not scores:
        return "No scores yet - be the first!"
    return "\n".join(f"{i}. {s['name']:<{MAX_NAME_LENGTH}} {s['score']}/{s['total']} "
                     f"({s['percent']}%)  {s['category']}" for i, s in enumerate(scores, 1))


# ------------------------------------------------------------------ GUI
class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Quiz")
        self.geometry("820x640")
        self.minsize(720, 580)
        self._setup_styles()

        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar(value="Mixed")
        self.engine = None
        self.timer_id = None
        self.time_left = 0
        self.answered = False
        self.option_buttons = []

        self.container = ttk.Frame(self, padding=24)
        self.container.pack(fill="both", expand=True)
        self.show_start()

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Title.TLabel", font=("Arial", 36, "bold"), foreground="#1f3a5f")
        s.configure("Heading.TLabel", font=("Arial", 20, "bold"))
        s.configure("Question.TLabel", font=("Arial", 20))
        s.configure("Info.TLabel", font=("Arial", 13))
        s.configure("Option.TButton", font=("Arial", 15), padding=12)
        s.configure("Main.TButton", font=("Arial", 15, "bold"), padding=10)
        for name, colour in (("Correct", "#2e7d32"), ("Wrong", "#c62828")):
            s.configure(f"{name}.TButton", font=("Arial", 15), padding=12,
                        background=colour, foreground="white")
            s.map(f"{name}.TButton", background=[("disabled", colour)],
                  foreground=[("disabled", "white")])

    def _clear(self):
        self._stop_timer()
        for w in self.container.winfo_children():
            w.destroy()
        for key in ("<Key>", "<Return>"):
            self.unbind(key)

    # ------------------------------------------------------ start screen
    def show_start(self):
        self._clear()
        c = self.container
        ttk.Label(c, text="Python Quiz", style="Title.TLabel").pack(pady=(10, 20))

        form = ttk.Frame(c)
        form.pack(pady=5)
        ttk.Label(form, text="Username", style="Info.TLabel").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        entry = ttk.Entry(form, textvariable=self.name_var, font=("Arial", 15), width=22)
        entry.grid(row=0, column=1, pady=8)
        ttk.Label(form, text="Category", style="Info.TLabel").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        ttk.Combobox(form, textvariable=self.category_var, values=list(QUESTION_BANK),
                     state="readonly", font=("Arial", 14), width=20).grid(row=1, column=1, pady=8)
        entry.focus_set()

        ttk.Label(c, text=f"{QUESTIONS_PER_QUIZ} questions  |  {TIME_PER_QUESTION}s each",
                  style="Info.TLabel").pack(pady=8)
        ttk.Button(c, text="START", style="Main.TButton", command=self.start_quiz).pack(pady=10)

        ttk.Label(c, text="Leaderboard", style="Heading.TLabel").pack(pady=(25, 5))
        ttk.Label(c, text=leaderboard_text(), font=("Courier", 12), justify="left").pack()
        self.bind("<Return>", lambda e: self.start_quiz())

    def start_quiz(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Username required", "Please enter your username.")
            return
        if len(name) > MAX_NAME_LENGTH:
            messagebox.showwarning("Username too long", f"Use at most {MAX_NAME_LENGTH} characters.")
            return
        self.engine = QuizEngine(QUESTION_BANK[self.category_var.get()])
        self.show_question()

    # --------------------------------------------------- question screen
    def show_question(self):
        self._clear()
        e, q, c = self.engine, self.engine.current, self.container
        self.answered = False

        header = ttk.Frame(c)
        header.pack(fill="x")
        ttk.Label(header, text=f"Question {e.index + 1} of {e.total}", style="Heading.TLabel").pack(side="left")
        self.score_lbl = ttk.Label(header, text=f"Score: {e.score}", style="Info.TLabel")
        self.score_lbl.pack(side="right")
        self.timer_lbl = ttk.Label(header, style="Info.TLabel")
        self.timer_lbl.pack(side="right", padx=25)

        ttk.Progressbar(c, maximum=e.total, value=e.index).pack(fill="x", pady=(12, 25))
        ttk.Label(c, text=q.text, style="Question.TLabel", wraplength=720,
                  justify="center").pack(pady=(0, 25))

        grid = ttk.Frame(c)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="opt")
        self.option_buttons = []
        for i, opt in enumerate(q.options):
            b = ttk.Button(grid, text=f"{i + 1}. {opt}", style="Option.TButton",
                           command=lambda i=i: self.choose(i))
            b.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="ew")
            self.option_buttons.append(b)

        self.feedback_lbl = ttk.Label(c, text="", style="Info.TLabel", wraplength=720, justify="center")
        self.feedback_lbl.pack(pady=15)
        last = e.index == e.total - 1
        self.next_btn = ttk.Button(c, text="Finish" if last else "Next", style="Main.TButton",
                                   command=self.next_question)

        self.bind("<Key>", self._on_key)
        self.bind("<Return>", lambda ev: self.next_question() if self.answered else None)
        self.time_left = TIME_PER_QUESTION
        self._tick()

    def _on_key(self, event):
        if event.char in "1234" and event.char and not self.answered:
            idx = int(event.char) - 1
            if idx < len(self.option_buttons):
                self.choose(idx)

    def _tick(self):
        self.timer_lbl.config(text=f"Time: {self.time_left}s",
                              foreground="#c62828" if self.time_left <= 5 else "#333333")
        if self.time_left <= 0:
            self.choose(None)
            return
        self.time_left -= 1
        self.timer_id = self.after(1000, self._tick)

    def _stop_timer(self):
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def choose(self, index):
        if self.answered:
            return
        self.answered = True
        self._stop_timer()
        e, q = self.engine, self.engine.current
        correct = e.submit(index)

        for i, b in enumerate(self.option_buttons):
            if q.options[i] == q.answer:
                b.configure(style="Correct.TButton")
            elif i == index:
                b.configure(style="Wrong.TButton")
            b.state(["disabled"])

        if correct:
            msg = "Correct!"
        elif index is None:
            msg = f"Time's up! The answer is: {q.answer}"
        else:
            msg = f"Wrong! The answer is: {q.answer}"
        if q.explanation:
            msg += f"\n{q.explanation}"
        self.feedback_lbl.config(text=msg, foreground="#2e7d32" if correct else "#c62828")
        self.score_lbl.config(text=f"Score: {e.score}")
        self.next_btn.pack(pady=5)

    def next_question(self):
        if not self.answered:
            return
        self.engine.next()
        self.show_result() if self.engine.finished else self.show_question()

    # ---------------------------------------------------- result screen
    def show_result(self):
        self._clear()
        e, c = self.engine, self.container
        name, category = self.name_var.get().strip(), self.category_var.get()
        save_score(name, category, e)

        verdict = ("Outstanding!" if e.percent >= 90 else "Great job!" if e.percent >= 70
                   else "Good effort!" if e.percent >= 50 else "Keep practising!")
        ttk.Label(c, text="SCORE", style="Title.TLabel").pack(pady=(0, 5))
        ttk.Label(c, text=f"{name}: {e.score} / {e.total}  ({e.percent}%)",
                  style="Heading.TLabel").pack()
        ttk.Label(c, text=verdict, style="Question.TLabel").pack(pady=8)

        ttk.Label(c, text="Review of mistakes" if e.wrong else "Perfect - nothing to review!",
                  style="Info.TLabel").pack(pady=(10, 4))
        if e.wrong:
            box = tk.Text(c, height=8, wrap="word", font=("Arial", 12), relief="flat", bg="#f4f4f4")
            for q, chosen in e.wrong:
                box.insert("end", f"Q: {q.text}\n")
                box.insert("end", f"   Your answer: {chosen or 'No answer (time out)'}\n")
                box.insert("end", f"   Correct answer: {q.answer}\n\n")
            box.config(state="disabled")
            box.pack(fill="x", padx=10)

        ttk.Label(c, text="Leaderboard", style="Heading.TLabel").pack(pady=(15, 3))
        ttk.Label(c, text=leaderboard_text(), font=("Courier", 12), justify="left").pack()

        buttons = ttk.Frame(c)
        buttons.pack(pady=15)
        ttk.Button(buttons, text="Play again", style="Main.TButton", command=self.show_start).pack(side="left", padx=8)
        ttk.Button(buttons, text="Quit", style="Main.TButton", command=self.destroy).pack(side="left", padx=8)


if __name__ == "__main__":
    QuizApp().mainloop()
