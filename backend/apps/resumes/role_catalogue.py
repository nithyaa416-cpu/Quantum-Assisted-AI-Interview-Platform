"""
Curated catalogue of target roles for the QAIP platform.

Each role entry defines:
  - display_name     : human-readable role name
  - domain           : maps to TargetRole.domain choices
  - aliases          : alternative names students might type
  - required_skills  : skills expected for this role (used for skill-gap analysis)
  - interview_topics : topics covered in AI interviews (used in Phase 5+)
  - coding_topics    : coding problem areas relevant to this role
  - description      : brief role description shown in UI

This catalogue drives the frontend suggestion list AND the skill-gap
analysis engine. It does NOT rank students — it is used solely per-student.
"""
from typing import TypedDict

class RoleEntry(TypedDict):
    display_name: str
    domain: str
    aliases: list[str]
    required_skills: list[str]
    interview_topics: list[str]
    coding_topics: list[str]
    description: str


ROLE_CATALOGUE: list[RoleEntry] = [
    {
        "display_name": "Software Developer",
        "domain": "software_engineering",
        "aliases": ["software engineer", "sde", "swe", "software development engineer"],
        "required_skills": ["Python", "Java", "C++", "Data Structures", "Algorithms",
                            "Git", "SQL", "REST APIs", "OOP"],
        "interview_topics": ["Data Structures", "Algorithms", "System Design",
                             "OOP Principles", "Design Patterns", "Databases",
                             "Version Control", "SDLC", "Testing"],
        "coding_topics": ["Arrays", "Strings", "Linked Lists", "Trees", "Graphs",
                          "Dynamic Programming", "Sorting", "Searching"],
        "description": "Builds software systems across the full stack. Requires strong fundamentals in DSA, OOP, and system design.",
    },
    {
        "display_name": "Python Developer",
        "domain": "backend",
        "aliases": ["python engineer", "python backend developer", "python software engineer"],
        "required_skills": ["Python", "Django", "Flask", "FastAPI", "PostgreSQL",
                            "Redis", "REST APIs", "Docker", "Git", "SQL"],
        "interview_topics": ["Python Internals", "Django/Flask", "REST APIs",
                             "Database Design", "Async Python", "Testing",
                             "OOP in Python", "Decorators & Generators",
                             "Package Management", "Deployment"],
        "coding_topics": ["Python-specific Problems", "File I/O", "Data Manipulation",
                          "OOP", "Functional Programming", "Concurrency"],
        "description": "Specialises in Python-based backend systems using frameworks like Django and FastAPI.",
    },
    {
        "display_name": "Java Developer",
        "domain": "backend",
        "aliases": ["java engineer", "java backend developer", "j2ee developer"],
        "required_skills": ["Java", "Spring Boot", "Hibernate", "Maven", "SQL",
                            "Microservices", "REST APIs", "Docker", "JUnit", "Git"],
        "interview_topics": ["Java OOP", "Spring Framework", "JVM Internals",
                             "Concurrency & Threads", "Collections Framework",
                             "Microservices", "Database Design", "Testing with JUnit",
                             "Design Patterns", "Memory Management"],
        "coding_topics": ["Java Collections", "Streams & Lambda", "Concurrency",
                          "OOP Design Problems", "Spring Boot REST"],
        "description": "Develops enterprise-grade applications using Java and Spring Boot.",
    },
    {
        "display_name": "Data Analyst",
        "domain": "data_science",
        "aliases": ["data analytics", "business analyst", "data analyst engineer"],
        "required_skills": ["Python", "SQL", "Pandas", "NumPy", "Matplotlib",
                            "Seaborn", "Excel", "Power BI", "Tableau",
                            "Statistics", "Data Visualisation"],
        "interview_topics": ["SQL Queries", "Data Cleaning", "Statistical Analysis",
                             "Data Visualisation", "Pandas & NumPy",
                             "Business Intelligence", "A/B Testing",
                             "Probability & Statistics", "Excel/Sheets"],
        "coding_topics": ["SQL Aggregations", "Window Functions", "Pandas Operations",
                          "Data Cleaning Scripts", "Statistical Computations"],
        "description": "Extracts insights from data using SQL, Python, and visualisation tools.",
    },
    {
        "display_name": "Machine Learning Engineer",
        "domain": "machine_learning",
        "aliases": ["ml engineer", "ml developer", "machine learning developer",
                    "ml ops engineer"],
        "required_skills": ["Python", "scikit-learn", "TensorFlow", "PyTorch",
                            "NumPy", "Pandas", "SQL", "Statistics",
                            "Feature Engineering", "Model Deployment", "Docker"],
        "interview_topics": ["ML Algorithms", "Model Evaluation", "Feature Engineering",
                             "Bias & Variance", "Neural Networks", "NLP Basics",
                             "MLOps & Deployment", "Statistics & Probability",
                             "Deep Learning", "Data Preprocessing"],
        "coding_topics": ["Model Implementation", "Data Preprocessing",
                          "Evaluation Metrics", "Loss Functions", "Optimisers"],
        "description": "Designs, trains, and deploys machine learning models for production.",
    },
    {
        "display_name": "AI Engineer",
        "domain": "machine_learning",
        "aliases": ["artificial intelligence engineer", "generative ai engineer",
                    "llm engineer", "ai developer"],
        "required_skills": ["Python", "PyTorch", "TensorFlow", "LLM", "Transformers",
                            "LangChain", "OpenAI APIs", "NLP", "Vector Databases",
                            "Prompt Engineering", "RAG", "Docker"],
        "interview_topics": ["Large Language Models", "Prompt Engineering",
                             "RAG Architecture", "Fine-tuning", "Embeddings",
                             "Neural Networks", "Transformer Architecture",
                             "AI Ethics", "MLOps", "Vector Databases"],
        "coding_topics": ["LLM API Integration", "Embeddings", "Chain of Thought",
                          "RAG Pipeline", "Agent Design"],
        "description": "Builds AI-powered applications using LLMs, RAG pipelines, and generative AI tools.",
    },
    {
        "display_name": "Frontend Developer",
        "domain": "frontend",
        "aliases": ["frontend engineer", "ui developer", "react developer",
                    "vue developer", "web developer"],
        "required_skills": ["JavaScript", "TypeScript", "React", "HTML5", "CSS3",
                            "Tailwind CSS", "REST APIs", "Git", "Responsive Design",
                            "State Management"],
        "interview_topics": ["JavaScript Fundamentals", "React Lifecycle",
                             "CSS & Responsive Design", "Browser APIs",
                             "State Management", "Performance Optimisation",
                             "Accessibility", "TypeScript", "Testing",
                             "Web Security Basics"],
        "coding_topics": ["DOM Manipulation", "Async JS", "React Components",
                          "CSS Layout", "TypeScript Types"],
        "description": "Builds responsive, performant user interfaces using modern JavaScript frameworks.",
    },
    {
        "display_name": "Backend Developer",
        "domain": "backend",
        "aliases": ["backend engineer", "server-side developer", "api developer"],
        "required_skills": ["Python", "Node.js", "SQL", "REST APIs", "Docker",
                            "Redis", "PostgreSQL", "Authentication", "Git",
                            "System Design"],
        "interview_topics": ["API Design", "Database Design", "Authentication & Auth",
                             "Caching Strategies", "Message Queues",
                             "Concurrency", "System Design", "Microservices",
                             "Testing", "Deployment"],
        "coding_topics": ["API Design Problems", "Database Queries",
                          "Concurrency Problems", "System Design"],
        "description": "Designs and builds server-side APIs, databases, and backend services.",
    },
    {
        "display_name": "Full Stack Developer",
        "domain": "fullstack",
        "aliases": ["fullstack engineer", "full-stack developer", "mern developer",
                    "mean developer"],
        "required_skills": ["JavaScript", "TypeScript", "React", "Node.js",
                            "SQL", "PostgreSQL", "REST APIs", "Docker",
                            "Git", "HTML5", "CSS3"],
        "interview_topics": ["Frontend + Backend Integration", "API Design",
                             "Database Design", "React", "Node.js",
                             "Authentication", "Deployment", "System Design",
                             "Testing", "Performance"],
        "coding_topics": ["Full Stack Features", "API + UI Integration",
                          "Database Design", "Component Design"],
        "description": "Handles both frontend and backend development across the full application stack.",
    },
    {
        "display_name": "DevOps Engineer",
        "domain": "devops",
        "aliases": ["devops developer", "site reliability engineer", "sre",
                    "cloud engineer", "infrastructure engineer"],
        "required_skills": ["Docker", "Kubernetes", "CI/CD", "Terraform", "AWS",
                            "Linux", "Python", "Bash", "Git", "Monitoring"],
        "interview_topics": ["CI/CD Pipelines", "Container Orchestration",
                             "Infrastructure as Code", "Cloud Platforms",
                             "Linux Administration", "Monitoring & Alerting",
                             "Security Practices", "Networking Basics",
                             "Scripting", "Incident Management"],
        "coding_topics": ["Shell Scripting", "YAML Configs", "Infrastructure Scripts",
                          "Automation Problems"],
        "description": "Manages deployment pipelines, cloud infrastructure, and system reliability.",
    },
    {
        "display_name": "Data Engineer",
        "domain": "data_science",
        "aliases": ["big data engineer", "data pipeline engineer", "etl developer"],
        "required_skills": ["Python", "SQL", "Apache Spark", "Kafka", "Airflow",
                            "PostgreSQL", "Data Warehousing", "ETL", "Docker",
                            "Cloud Storage"],
        "interview_topics": ["ETL Design", "Data Modelling", "SQL Optimisation",
                             "Streaming vs Batch", "Data Quality",
                             "Distributed Computing", "Data Warehousing",
                             "Pipeline Orchestration", "Cloud Data Services"],
        "coding_topics": ["SQL Window Functions", "ETL Scripts", "Data Transformation",
                          "Pipeline Design"],
        "description": "Designs and maintains data pipelines, warehouses, and large-scale data infrastructure.",
    },
    {
        "display_name": "Mobile Developer",
        "domain": "mobile",
        "aliases": ["android developer", "ios developer", "react native developer",
                    "flutter developer", "mobile app developer"],
        "required_skills": ["Kotlin", "Swift", "React Native", "Flutter",
                            "REST APIs", "Git", "Mobile UI Design",
                            "State Management", "Testing"],
        "interview_topics": ["Mobile Architecture", "State Management",
                             "API Integration", "Performance Optimisation",
                             "Platform-specific APIs", "Testing",
                             "App Store Deployment", "Accessibility"],
        "coding_topics": ["UI Components", "State Management", "API Calls",
                          "Platform APIs", "Animations"],
        "description": "Builds native or cross-platform mobile applications for iOS and Android.",
    },
    {
        "display_name": "Cybersecurity Analyst",
        "domain": "cybersecurity",
        "aliases": ["security engineer", "information security analyst",
                    "penetration tester", "security analyst"],
        "required_skills": ["Networking", "Linux", "Python", "SQL",
                            "OWASP", "Cryptography", "Firewalls",
                            "Vulnerability Assessment", "SIEM", "Git"],
        "interview_topics": ["Network Security", "Web Application Security",
                             "Cryptography Basics", "OWASP Top 10",
                             "Incident Response", "Penetration Testing",
                             "Security Policies", "Identity & Access Management"],
        "coding_topics": ["Security Scripts", "Vulnerability Scanning",
                          "Cryptographic Functions", "Log Analysis"],
        "description": "Protects systems from threats through vulnerability analysis, monitoring, and incident response.",
    },
]

# Build lookup dictionaries for fast access
ROLES_BY_DOMAIN: dict[str, list[RoleEntry]] = {}
for role in ROLE_CATALOGUE:
    ROLES_BY_DOMAIN.setdefault(role["domain"], []).append(role)

ROLES_BY_NAME: dict[str, RoleEntry] = {}
for role in ROLE_CATALOGUE:
    ROLES_BY_NAME[role["display_name"].lower()] = role
    for alias in role["aliases"]:
        ROLES_BY_NAME[alias.lower()] = role


def find_role(name: str) -> RoleEntry | None:
    """Find a role entry by name or alias (case-insensitive)."""
    return ROLES_BY_NAME.get(name.strip().lower())


def get_required_skills(role_name: str) -> list[str]:
    """Return required skills for a role name."""
    role = find_role(role_name)
    return role["required_skills"] if role else []


def get_interview_topics(role_name: str) -> list[str]:
    """Return interview topics for a role."""
    role = find_role(role_name)
    return role["interview_topics"] if role else []
