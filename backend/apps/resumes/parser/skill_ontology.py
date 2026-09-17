"""
Curated skill ontology for resume parsing.
Groups skills by category for normalisation and detection.
"""

SKILL_ONTOLOGY: dict[str, list[str]] = {
    "language": [
        "python", "java", "javascript", "typescript", "c++", "c", "c#", "go", "golang",
        "rust", "kotlin", "swift", "ruby", "php", "scala", "r", "matlab", "perl",
        "bash", "shell", "powershell", "sql", "pl/sql", "dart", "elixir", "haskell",
        "lua", "groovy", "fortran", "cobol", "assembly", "vhdl", "verilog",
    ],
    "frontend": [
        "react", "react.js", "reactjs", "vue", "vue.js", "vuejs", "angular", "angularjs",
        "svelte", "next.js", "nextjs", "nuxt.js", "gatsby", "tailwind", "tailwindcss",
        "bootstrap", "css", "html", "html5", "css3", "sass", "scss", "less",
        "webpack", "vite", "babel", "redux", "zustand", "mobx", "jquery", "d3.js",
        "three.js", "material-ui", "chakra ui", "ant design",
    ],
    "backend": [
        "django", "flask", "fastapi", "express", "express.js", "node.js", "nodejs",
        "spring", "spring boot", "laravel", "rails", "ruby on rails", "asp.net",
        ".net", "nestjs", "hapi", "gin", "fiber", "actix", "rocket", "tornado",
        "celery", "gunicorn", "uvicorn", "graphql", "rest", "grpc", "websocket",
    ],
    "database": [
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "cassandra",
        "dynamodb", "firebase", "supabase", "elasticsearch", "neo4j", "oracle",
        "sql server", "mariadb", "cockroachdb", "influxdb", "prisma", "sqlalchemy",
        "mongoose", "sequelize", "typeorm", "hibernate",
    ],
    "devops_cloud": [
        "docker", "kubernetes", "k8s", "jenkins", "ci/cd", "github actions",
        "gitlab ci", "terraform", "ansible", "chef", "puppet", "vagrant",
        "aws", "azure", "gcp", "google cloud", "heroku", "vercel", "netlify",
        "nginx", "apache", "linux", "ubuntu", "centos", "debian",
        "prometheus", "grafana", "elk stack", "splunk", "datadog",
    ],
    "ml_ai": [
        "machine learning", "deep learning", "neural network", "nlp",
        "natural language processing", "computer vision", "tensorflow", "pytorch",
        "keras", "scikit-learn", "sklearn", "pandas", "numpy", "matplotlib",
        "seaborn", "opencv", "transformers", "hugging face", "langchain",
        "openai", "llm", "bert", "gpt", "xgboost", "lightgbm", "catboost",
        "reinforcement learning", "generative ai", "stable diffusion",
        "mediapipe", "yolo", "spacy", "nltk",
    ],
    "quantum": [
        "qiskit", "quantum computing", "qaoa", "quantum circuit", "pennylane",
        "cirq", "q#", "quantum machine learning", "quantum algorithms",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "trello",
        "figma", "postman", "swagger", "vscode", "intellij", "eclipse",
        "jupyter", "colab", "notion", "slack", "linux", "vim",
        "sonarqube", "selenium", "cypress", "jest", "pytest", "junit",
    ],
    "soft_skill": [
        "communication", "teamwork", "leadership", "problem solving", "analytical",
        "time management", "adaptability", "critical thinking", "collaboration",
        "presentation", "project management", "agile", "scrum", "kanban",
    ],
}

# Flat normalisation map: alias → canonical name
NORMALISATION_MAP: dict[str, str] = {
    "react.js": "React",
    "reactjs": "React",
    "react": "React",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "vue": "Vue.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "spring boot": "Spring Boot",
    "spring": "Spring",
    "k8s": "Kubernetes",
    "sklearn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "golang": "Go",
    "golang ": "Go",
    "c++": "C++",
    "c#": "C#",
    ".net": ".NET",
    "asp.net": "ASP.NET",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "ai": "Artificial Intelligence",
    "nlp": "NLP",
    "cv": "Computer Vision",
    "llm": "LLM",
    "gcp": "Google Cloud",
    "aws": "AWS",
    "ci/cd": "CI/CD",
    "tailwindcss": "Tailwind CSS",
    "tailwind": "Tailwind CSS",
}

# Build flat skill list with category tags for fast lookup
ALL_SKILLS: dict[str, str] = {}   # lowercase_skill → category
for category, skills in SKILL_ONTOLOGY.items():
    for skill in skills:
        ALL_SKILLS[skill.lower()] = category


def normalise_skill(raw: str) -> tuple[str, str]:
    """Return (canonical_name, category) for a raw skill string."""
    lower = raw.strip().lower()
    canonical = NORMALISATION_MAP.get(lower, raw.strip().title())
    category = ALL_SKILLS.get(lower, "tool")
    return canonical, category
