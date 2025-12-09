from dataclasses import dataclass
from tkinter import DISABLED, END, NORMAL, StringVar, Tk, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Tuple

from openai import OpenAI


PROMPT_TEMPLATE = """
You are an expert educator creating classroom-ready quizzes.
Generate exactly {num_questions} questions for a {subject} course about "{topic}" at {difficulty} difficulty.
Preferred question type: {question_type}.

Use the following strict format so it can be parsed:

QUIZ:
1. <question 1> (type: Multiple Choice/Fill in the Blank/Short Answer)
   - If Multiple Choice, provide options A-D on separate lines using the pattern "A) ...".
2. <question 2>
...
{num_questions}. <question N>

ANSWERS:
1. <answer to question 1 with brief justification>
2. <answer to question 2>
...
{num_questions}. <answer to question N>

Rules:
- Provide clear, concise questions and answers.
- For numeric answers, keep values simple enough for classroom use.
- Do not include any text before "QUIZ:" or after the last answer line.
- Do not wrap content in code fences or add extra commentary.
"""


@dataclass
class QuizRequest:
    subject: str
    topic: str
    num_questions: int
    difficulty: str
    question_type: str


class QuizGenerator:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model

    def build_prompt(self, request: QuizRequest) -> str:
        difficulty_text = request.difficulty or "a mix of beginner and intermediate"
        question_type = request.question_type or "Mixed"
        return PROMPT_TEMPLATE.format(
            num_questions=request.num_questions,
            subject=request.subject,
            topic=request.topic,
            difficulty=difficulty_text,
            question_type=question_type,
        )

    def generate(self, request: QuizRequest, api_key: str) -> Tuple[str, str]:
        prompt = self.build_prompt(request)
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        content = response.choices[0].message.content or ""
        return self._split_sections(content)

    def _split_sections(self, content: str) -> Tuple[str, str]:
        quiz_marker = "QUIZ:"
        answers_marker = "ANSWERS:"

        quiz_index = content.find(quiz_marker)
        answers_index = content.find(answers_marker)

        if quiz_index == -1 or answers_index == -1 or answers_index <= quiz_index:
            raise ValueError(
                "Unexpected LLM format. Expected 'QUIZ:' followed by 'ANSWERS:' markers."
            )

        quiz_section = content[quiz_index + len(quiz_marker) : answers_index].strip()
        answers_section = content[answers_index + len(answers_marker) :].strip()

        return quiz_section, answers_section


class QuizApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Classroom AI: Quiz Generator")
        self.generator = QuizGenerator()

        self.api_key_var = StringVar()
        self.subject_var = StringVar()
        self.topic_var = StringVar()
        self.num_questions_var = StringVar(value="5")
        self.difficulty_var = StringVar(value="Mixed")
        self.question_type_var = StringVar(value="Mixed")

        self._build_form()

    def _build_form(self) -> None:
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.grid(column=0, row=0, sticky="NSEW")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(main_frame, text="OpenAI API Key").grid(column=0, row=0, sticky="W", pady=(0, 4))
        ttk.Entry(main_frame, textvariable=self.api_key_var, width=40, show="*").grid(
            column=0, row=1, sticky="WE", pady=(0, 12)
        )

        # Inputs
        ttk.Label(main_frame, text="Subject").grid(column=0, row=2, sticky="W", pady=(0, 4))
        ttk.Entry(main_frame, textvariable=self.subject_var, width=40).grid(
            column=0, row=3, sticky="WE", pady=(0, 8)
        )

        ttk.Label(main_frame, text="Topic").grid(column=0, row=4, sticky="W", pady=(0, 4))
        ttk.Entry(main_frame, textvariable=self.topic_var, width=40).grid(
            column=0, row=5, sticky="WE", pady=(0, 8)
        )

        input_row = ttk.Frame(main_frame)
        input_row.grid(column=0, row=6, sticky="WE", pady=(0, 8))
        input_row.columnconfigure(0, weight=1)
        input_row.columnconfigure(1, weight=1)
        input_row.columnconfigure(2, weight=1)

        ttk.Label(input_row, text="# Questions").grid(column=0, row=0, sticky="W")
        ttk.Entry(input_row, textvariable=self.num_questions_var, width=10).grid(
            column=0, row=1, sticky="WE", padx=(0, 6)
        )

        ttk.Label(input_row, text="Difficulty").grid(column=1, row=0, sticky="W")
        ttk.Combobox(
            input_row,
            textvariable=self.difficulty_var,
            values=["Beginner", "Intermediate", "Advanced", "Mixed"],
            state="readonly",
        ).grid(column=1, row=1, sticky="WE", padx=6)

        ttk.Label(input_row, text="Question Type").grid(column=2, row=0, sticky="W")
        ttk.Combobox(
            input_row,
            textvariable=self.question_type_var,
            values=["Mixed", "Multiple Choice", "Fill in the Blank", "Short Answer"],
            state="readonly",
        ).grid(column=2, row=1, sticky="WE", padx=(6, 0))

        # Actions
        self.status_label = ttk.Label(main_frame, text="Enter your API key and quiz details to begin.")
        self.status_label.grid(column=0, row=7, sticky="W", pady=(4, 8))

        button_row = ttk.Frame(main_frame)
        button_row.grid(column=0, row=8, sticky="WE", pady=(0, 10))
        button_row.columnconfigure((0, 1), weight=1)

        self.generate_button = ttk.Button(button_row, text="Generate Quiz", command=self.generate_quiz)
        self.generate_button.grid(column=0, row=0, sticky="WE", padx=(0, 6))

        self.save_button = ttk.Button(button_row, text="Save quiz.md & answers.md", command=self.save_files)
        self.save_button.grid(column=1, row=0, sticky="WE", padx=(6, 0))
        self.save_button.state(["disabled"])

        # Output areas
        ttk.Label(main_frame, text="Quiz Preview").grid(column=0, row=9, sticky="W")
        self.quiz_text = ScrolledText(main_frame, height=12, wrap="word")
        self.quiz_text.grid(column=0, row=10, sticky="NSEW", pady=(0, 10))

        ttk.Label(main_frame, text="Answer Key Preview").grid(column=0, row=11, sticky="W")
        self.answers_text = ScrolledText(main_frame, height=10, wrap="word")
        self.answers_text.grid(column=0, row=12, sticky="NSEW")

        main_frame.rowconfigure(10, weight=1)
        main_frame.rowconfigure(12, weight=1)

    def generate_quiz(self) -> None:
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("API key required", "Please paste your OpenAI API key to continue.")
            return

        try:
            request = self._build_request()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self._set_loading_state(True)
        self.status_label.config(text="Generating quiz with OpenAI…")
        self.root.after(50, lambda: self._run_generation(request, api_key))

    def _run_generation(self, request: QuizRequest, api_key: str) -> None:
        try:
            quiz_section, answers_section = self.generator.generate(request, api_key)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Generation failed", f"Could not generate quiz: {exc}")
            self.status_label.config(text="Generation failed. Please try again.")
            self._set_loading_state(False)
            return

        self.quiz_text.config(state=NORMAL)
        self.answers_text.config(state=NORMAL)

        self.quiz_text.delete("1.0", END)
        self.answers_text.delete("1.0", END)

        self.quiz_text.insert(END, quiz_section)
        self.answers_text.insert(END, answers_section)

        self.quiz_text.config(state=DISABLED)
        self.answers_text.config(state=DISABLED)

        self.status_label.config(text="Quiz ready! Review and save below.")
        self.save_button.state(["!disabled"])
        self._set_loading_state(False)

    def _set_loading_state(self, loading: bool) -> None:
        if loading:
            self.generate_button.state(["disabled"])
            self.save_button.state(["disabled"])
        else:
            self.generate_button.state(["!disabled"])
            # Save button re-enabled only after successful generation

    def _build_request(self) -> QuizRequest:
        subject = self.subject_var.get().strip()
        topic = self.topic_var.get().strip()
        difficulty = self.difficulty_var.get().strip() or "Mixed"
        question_type = self.question_type_var.get().strip() or "Mixed"

        if not subject:
            raise ValueError("Subject is required.")
        if not topic:
            raise ValueError("Topic is required.")

        try:
            num_questions = int(self.num_questions_var.get())
            if num_questions <= 0:
                raise ValueError
        except ValueError as exc:  # noqa: PERF203
            raise ValueError("Number of questions must be a positive integer.") from exc

        return QuizRequest(
            subject=subject,
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            question_type=question_type,
        )

    def save_files(self) -> None:
        quiz_content = self.quiz_text.get("1.0", END).strip()
        answers_content = self.answers_text.get("1.0", END).strip()

        if not quiz_content or not answers_content:
            messagebox.showinfo("Nothing to save", "Generate a quiz before saving.")
            return

        write_output(quiz_content, answers_content)
        self.status_label.config(text="Saved quiz.md and answers.md in this folder.")
        messagebox.showinfo("Saved", "Quiz and answers saved as quiz.md and answers.md.")


def write_output(quiz_section: str, answers_section: str) -> None:
    with open("quiz.md", "w", encoding="utf-8") as quiz_file:
        quiz_file.write("# Quiz\n\n")
        quiz_file.write(quiz_section)
        quiz_file.write("\n")

    with open("answers.md", "w", encoding="utf-8") as answers_file:
        answers_file.write("# Answer Key\n\n")
        answers_file.write(answers_section)
        answers_file.write("\n")


def main() -> None:
    root = Tk()
    QuizApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
