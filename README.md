# Classroom AI: Worksheet & Quiz Generator

A desktop GUI that lets you choose the subject, topic, number of questions, difficulty, and preferred question type, then calls an LLM once to create a classroom-ready quiz and answer key in Markdown.

## Setup
1. Create a virtual environment (optional but recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your OpenAI API key in the environment:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

## Usage
Launch the GUI:
```bash
python quiz_generator.py
```

In the window:
1. Enter a subject and topic.
2. Choose the number of questions, difficulty, and question type.
3. Click **Generate Quiz** to call the LLM and preview the quiz and answers.
4. Click **Save quiz.md & answers.md** to write both files to the current directory.

If the LLM output does not include the expected `QUIZ:` and `ANSWERS:` markers, the app shows an error dialog so you can retry.
