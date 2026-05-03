🚀 ArchInsights

Understand any codebase in seconds.

ArchInsights is a code architecture analyzer that converts raw source code into a clear structure, showing how functions and components interact—and what breaks when you change something.

⚡ What It Does
📂 Architecture View → Files, classes, functions
🔗 Function Connections → Who calls what
🔥 Impact Analysis → Change → affected components
📊 Quick Metrics → Complexity & risk signals
🧠 Why It Matters

Developers waste time reading code to understand it.
CodeLens gives instant clarity, improving:

Debugging speed
Refactoring safety
Developer productivity
⚙️ Stack

FastAPI • Python AST • HTML/CSS

▶️ Run
git clone <repo-url>
cd project_analyzer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

Open → http://127.0.0.1:8000

🎯 Positioning

Not just a visualizer — a developer decision tool
