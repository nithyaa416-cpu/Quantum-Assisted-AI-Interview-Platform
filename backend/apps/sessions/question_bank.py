"""
Question bank for the AI Interviewer.

Organised by: phase → domain → difficulty → list of questions.
Each question has: text, topic, expected_concepts, follow_ups.

This bank is the fallback engine. In Phase 6, this will be replaced
by actual LLM generation. The interface stays identical.
"""
from typing import TypedDict


class QuestionEntry(TypedDict):
    text: str
    topic: str
    expected_concepts: list[str]
    follow_ups: list[str]          # follow-up prompts if answer is weak
    harder_follow_up: str          # follow-up if answer is strong (harder)


# ── WARMUP ────────────────────────────────────────────────────────────────────

WARMUP_QUESTIONS: list[QuestionEntry] = [
    {
        "text": "Tell me about yourself and what brings you to this interview today.",
        "topic": "introduction",
        "expected_concepts": ["background", "skills", "motivation", "goals"],
        "follow_ups": [
            "Can you elaborate on your technical background a bit more?",
            "What specific skills are you most confident about?",
        ],
        "harder_follow_up": "That's a great overview. What makes you stand out from other candidates for this role specifically?",
    },
    {
        "text": "Walk me through your most recent project. What problem did it solve?",
        "topic": "project overview",
        "expected_concepts": ["problem statement", "solution", "impact", "technology"],
        "follow_ups": [
            "What was the main technical challenge you faced?",
            "How did you decide on the technology stack?",
        ],
        "harder_follow_up": "How would you scale that solution to handle 10x the current load?",
    },
    {
        "text": "What are your strongest technical skills, and how have you applied them recently?",
        "topic": "skills",
        "expected_concepts": ["technical skills", "practical application", "recent work"],
        "follow_ups": [
            "Can you give a specific example of using that skill?",
            "How did you learn that skill?",
        ],
        "harder_follow_up": "How do you stay current with advances in that area?",
    },
]

# ── TECHNICAL QUESTIONS BY DOMAIN ─────────────────────────────────────────────

TECHNICAL_QUESTIONS: dict[str, dict[str, list[QuestionEntry]]] = {
    "software_engineering": {
        "easy": [
            {
                "text": "What is the difference between a stack and a queue? Give a real-world example of each.",
                "topic": "Data Structures",
                "expected_concepts": ["LIFO", "FIFO", "stack example", "queue example"],
                "follow_ups": ["When would you choose a stack over a queue?", "What is a deque?"],
                "harder_follow_up": "Implement a queue using two stacks. What is the time complexity?",
            },
            {
                "text": "Explain what Object-Oriented Programming is and name its four pillars.",
                "topic": "OOP",
                "expected_concepts": ["encapsulation", "inheritance", "polymorphism", "abstraction"],
                "follow_ups": ["Can you give an example of polymorphism?", "What is the difference between abstraction and encapsulation?"],
                "harder_follow_up": "When would you prefer composition over inheritance? Give a design example.",
            },
            {
                "text": "What is version control, and why is it important in software development?",
                "topic": "Version Control",
                "expected_concepts": ["git", "tracking changes", "collaboration", "branching"],
                "follow_ups": ["What is the difference between git merge and git rebase?"],
                "harder_follow_up": "Describe your git branching strategy in a team project.",
            },
        ],
        "medium": [
            {
                "text": "Explain the time and space complexity of binary search. When can it be applied?",
                "topic": "Algorithms",
                "expected_concepts": ["O(log n)", "sorted array", "divide and conquer", "space complexity"],
                "follow_ups": ["What happens if the array is not sorted?", "How would you apply binary search to a rotated sorted array?"],
                "harder_follow_up": "How would you implement binary search on an infinite sorted array?",
            },
            {
                "text": "What is the difference between SQL and NoSQL databases? When would you choose one over the other?",
                "topic": "Databases",
                "expected_concepts": ["structured vs unstructured", "ACID", "scalability", "use cases"],
                "follow_ups": ["What is CAP theorem?", "Give an example of when you'd use MongoDB over PostgreSQL."],
                "harder_follow_up": "Design a database schema for a social media platform. Which type would you choose and why?",
            },
            {
                "text": "Explain REST API design principles. What makes an API truly RESTful?",
                "topic": "APIs",
                "expected_concepts": ["stateless", "HTTP methods", "resources", "status codes", "JSON"],
                "follow_ups": ["What is the difference between PUT and PATCH?", "How do you handle API versioning?"],
                "harder_follow_up": "Design the API endpoints for a hotel booking system following REST principles.",
            },
            {
                "text": "What is a deadlock? How can it be prevented in a multi-threaded application?",
                "topic": "Concurrency",
                "expected_concepts": ["mutual exclusion", "hold and wait", "no preemption", "circular wait", "prevention strategies"],
                "follow_ups": ["What is a race condition?", "How does a mutex differ from a semaphore?"],
                "harder_follow_up": "Design a thread-safe singleton in Python or Java.",
            },
        ],
        "hard": [
            {
                "text": "Design a URL shortening service like bit.ly. Walk me through your high-level architecture.",
                "topic": "System Design",
                "expected_concepts": ["hash function", "database", "caching", "load balancer", "scalability", "redirect"],
                "follow_ups": ["How would you handle 1 million URLs per day?", "How do you prevent hash collisions?"],
                "harder_follow_up": "How would you add analytics (click tracking) to your design without slowing down redirects?",
            },
            {
                "text": "Explain SOLID principles with examples. Which one do you find most difficult to apply consistently?",
                "topic": "Design Principles",
                "expected_concepts": ["single responsibility", "open-closed", "Liskov", "interface segregation", "dependency inversion"],
                "follow_ups": ["Can you show a violation of the Open-Closed principle?"],
                "harder_follow_up": "Refactor this violating code snippet to follow SOLID principles.",
            },
        ],
    },
    "backend": {
        "easy": [
            {
                "text": "What is the difference between synchronous and asynchronous programming? Give a Python example.",
                "topic": "Python",
                "expected_concepts": ["blocking", "non-blocking", "async/await", "event loop"],
                "follow_ups": ["When would you use async in Django?", "What is the GIL in Python?"],
                "harder_follow_up": "How does Python's asyncio event loop work internally?",
            },
            {
                "text": "What is Django's ORM? How does it differ from writing raw SQL?",
                "topic": "Django",
                "expected_concepts": ["model", "queryset", "abstraction", "migration", "performance"],
                "follow_ups": ["When would you use raw SQL over ORM?", "What is an N+1 query problem?"],
                "harder_follow_up": "How would you optimise a Django queryset that has N+1 queries?",
            },
        ],
        "medium": [
            {
                "text": "Explain how JWT authentication works. What are its advantages and limitations?",
                "topic": "Authentication",
                "expected_concepts": ["header", "payload", "signature", "stateless", "expiry", "refresh token"],
                "follow_ups": ["How do you invalidate a JWT token?", "What is the difference between JWT and session-based auth?"],
                "harder_follow_up": "Design a secure JWT authentication flow with refresh token rotation.",
            },
            {
                "text": "What is database indexing and how does it improve query performance?",
                "topic": "Databases",
                "expected_concepts": ["B-tree", "read speed", "write overhead", "composite index", "covering index"],
                "follow_ups": ["When should you NOT add an index?", "What is a covering index?"],
                "harder_follow_up": "EXPLAIN a slow query and describe how you'd optimise it.",
            },
            {
                "text": "What is caching? Describe different caching strategies and when to use each.",
                "topic": "Caching",
                "expected_concepts": ["Redis", "cache-aside", "write-through", "TTL", "cache invalidation"],
                "follow_ups": ["What are the challenges of cache invalidation?", "How does Redis differ from Memcached?"],
                "harder_follow_up": "Design a caching strategy for a news feed that serves 10,000 users simultaneously.",
            },
        ],
        "hard": [
            {
                "text": "Design a rate limiter for an API that allows 100 requests per minute per user.",
                "topic": "System Design",
                "expected_concepts": ["token bucket", "sliding window", "Redis", "distributed", "header response"],
                "follow_ups": ["How would you handle burst traffic?", "What data structure would you use in Redis?"],
                "harder_follow_up": "How would you make this rate limiter work across multiple server instances?",
            },
        ],
    },
    "data_science": {
        "easy": [
            {
                "text": "What is the difference between supervised and unsupervised learning? Give an example of each.",
                "topic": "ML Fundamentals",
                "expected_concepts": ["labelled data", "unlabelled data", "classification", "clustering"],
                "follow_ups": ["What is semi-supervised learning?", "Give an example of an unsupervised algorithm."],
                "harder_follow_up": "How do you decide which type of learning to use for a new problem?",
            },
            {
                "text": "Explain what overfitting is and how you would prevent it in a machine learning model.",
                "topic": "Model Evaluation",
                "expected_concepts": ["training accuracy", "validation accuracy", "regularisation", "dropout", "cross-validation"],
                "follow_ups": ["What is the difference between L1 and L2 regularisation?", "When would you use dropout?"],
                "harder_follow_up": "How do you determine the optimal regularisation hyperparameter?",
            },
        ],
        "medium": [
            {
                "text": "Walk me through how you would approach a classification problem from scratch.",
                "topic": "ML Pipeline",
                "expected_concepts": ["EDA", "feature engineering", "model selection", "evaluation", "deployment"],
                "follow_ups": ["How do you handle imbalanced classes?", "What metrics would you use besides accuracy?"],
                "harder_follow_up": "How would you detect and handle data drift in a production model?",
            },
            {
                "text": "Explain precision, recall, and F1 score. When would you optimise for precision vs recall?",
                "topic": "Evaluation Metrics",
                "expected_concepts": ["true positive", "false positive", "precision formula", "recall formula", "trade-off"],
                "follow_ups": ["What is AUC-ROC?", "When does accuracy fail as a metric?"],
                "harder_follow_up": "Design an evaluation strategy for a medical diagnosis model.",
            },
        ],
        "hard": [
            {
                "text": "Explain the bias-variance tradeoff and how it relates to model complexity.",
                "topic": "Theory",
                "expected_concepts": ["bias", "variance", "underfitting", "overfitting", "complexity curve"],
                "follow_ups": ["How does ensemble learning reduce variance?"],
                "harder_follow_up": "How do you tune hyperparameters to balance bias and variance?",
            },
        ],
    },
    "machine_learning": {
        "easy": [
            {
                "text": "Explain how a neural network learns. What is backpropagation?",
                "topic": "Neural Networks",
                "expected_concepts": ["forward pass", "loss function", "gradient", "weight update", "chain rule"],
                "follow_ups": ["What is the vanishing gradient problem?", "What is an activation function and why is it needed?"],
                "harder_follow_up": "How does batch normalisation help with training deep networks?",
            },
        ],
        "medium": [
            {
                "text": "What is the Transformer architecture? How does attention mechanism work?",
                "topic": "Deep Learning",
                "expected_concepts": ["self-attention", "Q/K/V", "positional encoding", "multi-head attention", "BERT/GPT"],
                "follow_ups": ["What is the difference between encoder and decoder in a Transformer?"],
                "harder_follow_up": "Explain how you would fine-tune a pre-trained LLM for a specific classification task.",
            },
            {
                "text": "What is transfer learning and why has it become so important in modern AI?",
                "topic": "Transfer Learning",
                "expected_concepts": ["pre-trained model", "fine-tuning", "feature extraction", "domain adaptation"],
                "follow_ups": ["When would transfer learning NOT be beneficial?"],
                "harder_follow_up": "How would you fine-tune BERT for sentiment analysis on a small dataset?",
            },
        ],
        "hard": [
            {
                "text": "Explain RAG (Retrieval-Augmented Generation) and how it improves LLM responses.",
                "topic": "LLM Architecture",
                "expected_concepts": ["vector database", "embeddings", "retrieval", "augmentation", "hallucination reduction"],
                "follow_ups": ["What embedding model would you use?", "How do you chunk documents for RAG?"],
                "harder_follow_up": "Design a RAG pipeline for a company's internal knowledge base.",
            },
        ],
    },
    "frontend": {
        "easy": [
            {
                "text": "What is the difference between `let`, `const`, and `var` in JavaScript?",
                "topic": "JavaScript",
                "expected_concepts": ["scope", "hoisting", "reassignment", "block scope", "function scope"],
                "follow_ups": ["What is temporal dead zone?", "When would you still use `var`?"],
                "harder_follow_up": "Explain how JavaScript closures work and give a practical use case.",
            },
            {
                "text": "What is the virtual DOM in React and why does it exist?",
                "topic": "React",
                "expected_concepts": ["reconciliation", "diffing algorithm", "performance", "real DOM manipulation"],
                "follow_ups": ["What triggers a re-render in React?", "What is the difference between state and props?"],
                "harder_follow_up": "When and why would you use `useMemo` and `useCallback` in React?",
            },
        ],
        "medium": [
            {
                "text": "Explain the concept of event bubbling and event delegation in JavaScript.",
                "topic": "DOM",
                "expected_concepts": ["bubbling phase", "capturing phase", "stopPropagation", "delegation pattern"],
                "follow_ups": ["What is event capturing?", "When would you use event delegation?"],
                "harder_follow_up": "Implement an event system from scratch using the observer pattern.",
            },
            {
                "text": "What is CSS specificity and how does it affect styling?",
                "topic": "CSS",
                "expected_concepts": ["specificity score", "inline styles", "ID vs class", "!important", "cascade"],
                "follow_ups": ["How do you avoid specificity wars?", "What is the BEM methodology?"],
                "harder_follow_up": "Explain CSS Grid vs Flexbox and when to use each.",
            },
        ],
        "hard": [
            {
                "text": "Explain React's reconciliation algorithm and how keys affect it.",
                "topic": "React Advanced",
                "expected_concepts": ["fiber", "key prop", "diffing", "component identity", "list rendering"],
                "follow_ups": ["What happens if you use index as key?"],
                "harder_follow_up": "How would you implement virtualised rendering for a list of 10,000 items?",
            },
        ],
    },
    "devops": {
        "easy": [
            {
                "text": "What is Docker and how does it differ from a virtual machine?",
                "topic": "Containers",
                "expected_concepts": ["container", "image", "lightweight", "OS kernel", "isolation"],
                "follow_ups": ["What is a Dockerfile?", "What is the difference between CMD and ENTRYPOINT?"],
                "harder_follow_up": "Design a multi-stage Dockerfile to minimise image size for a Python application.",
            },
        ],
        "medium": [
            {
                "text": "Explain CI/CD pipelines. What are the key stages in a typical pipeline?",
                "topic": "CI/CD",
                "expected_concepts": ["build", "test", "lint", "deploy", "automation", "rollback"],
                "follow_ups": ["What is the difference between continuous delivery and continuous deployment?"],
                "harder_follow_up": "Design a CI/CD pipeline for a microservices application with zero-downtime deployments.",
            },
            {
                "text": "What is Kubernetes and what problems does it solve that Docker alone cannot?",
                "topic": "Orchestration",
                "expected_concepts": ["orchestration", "auto-scaling", "self-healing", "service discovery", "load balancing"],
                "follow_ups": ["What is a Kubernetes Pod?", "What is the difference between a Deployment and a StatefulSet?"],
                "harder_follow_up": "How would you handle secrets management in a Kubernetes cluster?",
            },
        ],
        "hard": [
            {
                "text": "Design the deployment architecture for a high-availability web application that must handle 99.99% uptime.",
                "topic": "System Design",
                "expected_concepts": ["redundancy", "load balancer", "auto-scaling", "health checks", "multi-region", "RTO/RPO"],
                "follow_ups": ["How would you handle database failover?"],
                "harder_follow_up": "How do you perform zero-downtime database migrations in this architecture?",
            },
        ],
    },
}

# ── HR / BEHAVIOURAL QUESTIONS ─────────────────────────────────────────────────

HR_QUESTIONS: list[QuestionEntry] = [
    {
        "text": "Tell me about a time you faced a significant technical challenge. How did you approach it?",
        "topic": "Problem Solving",
        "expected_concepts": ["situation", "action", "result", "learning", "initiative"],
        "follow_ups": ["What would you do differently next time?", "How did this experience change your approach to problems?"],
        "harder_follow_up": "How did that experience influence the way you work on your current projects?",
    },
    {
        "text": "Describe a situation where you had to work under pressure to meet a deadline. What was the outcome?",
        "topic": "Time Management",
        "expected_concepts": ["prioritisation", "communication", "delivery", "stress management"],
        "follow_ups": ["How do you prioritise when everything seems urgent?", "What tools or techniques help you manage deadlines?"],
        "harder_follow_up": "How would you handle a situation where the deadline is genuinely impossible to meet?",
    },
    {
        "text": "Have you ever disagreed with a team member or senior? How did you handle it?",
        "topic": "Conflict Resolution",
        "expected_concepts": ["communication", "respectful disagreement", "compromise", "outcome"],
        "follow_ups": ["What did you learn from that experience?", "How do you ensure your disagreement is heard constructively?"],
        "harder_follow_up": "How do you handle a situation where you disagree with a technical decision made by your manager?",
    },
    {
        "text": "Where do you see yourself in 3–5 years, and how does this role fit into that plan?",
        "topic": "Career Goals",
        "expected_concepts": ["growth", "technical skills", "leadership", "alignment", "motivation"],
        "follow_ups": ["What skills do you want to develop most?", "What kind of work environment do you thrive in?"],
        "harder_follow_up": "What would you do if your growth opportunities in this role are slower than expected?",
    },
    {
        "text": "Tell me about a project you're most proud of. What was your specific contribution?",
        "topic": "Achievement",
        "expected_concepts": ["ownership", "impact", "technical contribution", "collaboration", "outcome"],
        "follow_ups": ["What was the biggest obstacle?", "What would you improve if you redid the project?"],
        "harder_follow_up": "How would you mentor a junior developer working on a similar project?",
    },
    {
        "text": "How do you approach learning a new technology or framework you've never used before?",
        "topic": "Learning Ability",
        "expected_concepts": ["documentation", "hands-on practice", "community", "building projects", "systematic approach"],
        "follow_ups": ["Give an example of a technology you recently learned this way.", "How do you know when you're proficient enough?"],
        "harder_follow_up": "How do you balance learning new technologies with delivering current project work?",
    },
    {
        "text": "Describe a time when you had to give or receive constructive criticism. How did you handle it?",
        "topic": "Feedback",
        "expected_concepts": ["openness", "specific feedback", "action taken", "improvement", "communication"],
        "follow_ups": ["How do you deliver critical feedback to a peer?"],
        "harder_follow_up": "How do you handle feedback that you fundamentally disagree with?",
    },
]

# ── PROJECT-BASED QUESTIONS ────────────────────────────────────────────────────

PROJECT_QUESTIONS: list[QuestionEntry] = [
    {
        "text": "Describe the most complex project you've built. What was the architecture and what were the key design decisions?",
        "topic": "Architecture",
        "expected_concepts": ["design choices", "trade-offs", "scalability", "technology selection"],
        "follow_ups": ["Why did you choose that particular architecture?", "What would you change now?"],
        "harder_follow_up": "How would you scale this project to serve 1 million users?",
    },
    {
        "text": "What was the biggest bug you encountered in a project? How did you debug and fix it?",
        "topic": "Debugging",
        "expected_concepts": ["systematic debugging", "root cause", "fix", "prevention", "logging"],
        "follow_ups": ["What debugging tools do you use?", "How long did it take to find the root cause?"],
        "harder_follow_up": "How do you set up monitoring and alerting to catch such bugs in production?",
    },
    {
        "text": "How did you handle version control and collaboration in your team projects?",
        "topic": "Collaboration",
        "expected_concepts": ["branching strategy", "pull requests", "code review", "merge conflicts", "CI"],
        "follow_ups": ["What was your branching strategy?", "How did you handle merge conflicts?"],
        "harder_follow_up": "How would you establish a code review culture in a new team?",
    },
    {
        "text": "Tell me about a time you improved the performance of a system or application. What did you measure and optimise?",
        "topic": "Performance",
        "expected_concepts": ["profiling", "bottleneck", "measurement", "optimisation", "result"],
        "follow_ups": ["What tools did you use to profile?", "How did you measure the improvement?"],
        "harder_follow_up": "How do you set performance budgets for a web application?",
    },
]

# ── CLOSING QUESTIONS ──────────────────────────────────────────────────────────

CLOSING_QUESTIONS: list[QuestionEntry] = [
    {
        "text": "Do you have any questions about the role or what we look for in this position?",
        "topic": "closing",
        "expected_concepts": ["curiosity", "engagement", "preparation"],
        "follow_ups": [],
        "harder_follow_up": "",
    },
    {
        "text": "Is there anything important about your experience or skills that we haven't covered today?",
        "topic": "closing",
        "expected_concepts": ["self-advocacy", "communication"],
        "follow_ups": [],
        "harder_follow_up": "",
    },
]


def get_technical_questions(domain: str, difficulty: str) -> list[QuestionEntry]:
    """Get technical questions for a domain and difficulty level."""
    domain_map = {
        'software_engineering': 'software_engineering',
        'backend': 'backend',
        'frontend': 'frontend',
        'fullstack': 'backend',       # fallback to backend
        'data_science': 'data_science',
        'machine_learning': 'machine_learning',
        'devops': 'devops',
        'mobile': 'software_engineering',
        'cybersecurity': 'software_engineering',
        'product_management': 'software_engineering',
        'other': 'software_engineering',
    }
    mapped_domain = domain_map.get(domain, 'software_engineering')
    domain_questions = TECHNICAL_QUESTIONS.get(mapped_domain, TECHNICAL_QUESTIONS['software_engineering'])
    return domain_questions.get(difficulty, domain_questions.get('medium', []))
