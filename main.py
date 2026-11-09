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
