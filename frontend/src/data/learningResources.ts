/**
 * Universal Learning Resource Catalogue for the QAOA Preparation Planner.
 *
 * Design:
 * - Each entry has a `subject` key, a human-readable `label`, a list of `matchKeywords`
 *   used for fuzzy topic → resource matching, and a `resources` array.
 * - Matching is purely client-side keyword intersection — no LLM or API calls.
 * - A topic card passes its `activity_id`, `topic` name, `category`, and `sub_topics`
 *   through `getResourcesForTopic()` to receive 2–3 relevant resources.
 * - Unknown or unmapped topics receive a curated search-link fallback.
 *
 * Adding a new subject: append a new entry to RESOURCE_CATALOGUE.
 * Adding a new topic within an existing subject: add keywords to matchKeywords.
 */

export interface LearningResource {
  title: string
  platform: string
  type: 'Video' | 'Tutorial' | 'Documentation' | 'Practice' | 'Course'
  description: string
  url: string
}

interface CatalogueEntry {
  subject: string
  label: string
  matchKeywords: string[]
  resources: LearningResource[]
}

// ─────────────────────────────────────────────────────────────────────────────
// CATALOGUE — covers DSA, DBMS, OS, CN, OOP, AI/ML, SE, Cloud, System Design,
// other technical subjects, and interview preparation.
// ─────────────────────────────────────────────────────────────────────────────

const RESOURCE_CATALOGUE: CatalogueEntry[] = [
  // ── DSA: Arrays & Hashing ──────────────────────────────────────────────────
  {
    subject: 'arrays_hashing',
    label: 'Arrays & Hashing',
    matchKeywords: ['array', 'hash', 'hashing', 'hash table', 'hash map', 'dictionary', 'frequency', 'prefix sum', 'two-sum', 'contains-duplicate', 'valid-anagram'],
    resources: [
      {
        title: 'Arrays — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'In-depth coverage of array operations, prefix sums, and frequency counting techniques.',
        url: 'https://www.geeksforgeeks.org/array-data-structure/',
      },
      {
        title: 'Hash Tables and Hash Maps Explained',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'Visual walkthrough of hash table internals, collision handling, and real-world use cases.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+hash+table+explained',
      },
      {
        title: 'Arrays & Hashing — Practice Problems',
        platform: 'LeetCode (Free Tier)',
        type: 'Practice',
        description: 'Curated free problems: Two Sum, Contains Duplicate, Valid Anagram, and Group Anagrams.',
        url: 'https://leetcode.com/tag/array/',
      },
    ],
  },

  // ── DSA: Two Pointers & Sliding Window ─────────────────────────────────────
  {
    subject: 'two_pointers_sliding_window',
    label: 'Two Pointers & Sliding Window',
    matchKeywords: ['two pointer', 'two pointers', 'sliding window', 'substring', 'subarray', 'palindrome', 'best-time-to-buy', 'longest-substring'],
    resources: [
      {
        title: 'Sliding Window Technique — Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Fixed and variable-size sliding window patterns with step-by-step examples.',
        url: 'https://www.geeksforgeeks.org/window-sliding-technique/',
      },
      {
        title: 'Two Pointers Algorithm Explained',
        platform: 'TutorialsPoint',
        type: 'Tutorial',
        description: 'Learn the two-pointer approach for sorted arrays, pair sums, and partition problems.',
        url: 'https://www.tutorialspoint.com/data_structures_algorithms/two_pointer_algorithm.htm',
      },
      {
        title: 'Sliding Window Problems — Practice',
        platform: 'LeetCode (Free Tier)',
        type: 'Practice',
        description: 'Practice problems: Longest Substring Without Repeating Characters, Minimum Window Substring.',
        url: 'https://leetcode.com/tag/sliding-window/',
      },
    ],
  },

  // ── DSA: Linked Lists, Stacks & Queues ─────────────────────────────────────
  {
    subject: 'linked_lists_stacks_queues',
    label: 'Linked Lists, Stacks & Queues',
    matchKeywords: ['linked list', 'stack', 'queue', 'lifo', 'fifo', 'singly linked', 'doubly linked', 'monotonic stack', 'deque', 'reverse-linked-list', 'valid-parentheses', 'min-stack'],
    resources: [
      {
        title: 'Linked List — Complete Guide',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Singly, doubly, and circular linked lists with insertion, deletion, and reversal operations.',
        url: 'https://www.geeksforgeeks.org/data-structures/linked-list/',
      },
      {
        title: 'Stacks and Queues — Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'Implementation of stacks, queues, and deques from scratch in Python and JavaScript.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+stacks+queues+data+structures',
      },
      {
        title: 'Stack & Queue Problems — Practice',
        platform: 'LeetCode (Free Tier)',
        type: 'Practice',
        description: 'Practice: Valid Parentheses, Min Stack, Implement Queue Using Stacks.',
        url: 'https://leetcode.com/tag/stack/',
      },
    ],
  },

  // ── DSA: Binary Trees & Traversals ─────────────────────────────────────────
  {
    subject: 'binary_trees_bfs_dfs',
    label: 'Binary Trees & Tree Traversals',
    matchKeywords: ['binary tree', 'tree', 'traversal', 'bfs', 'dfs', 'preorder', 'inorder', 'postorder', 'level order', 'bst', 'binary search tree', 'heap', 'trie'],
    resources: [
      {
        title: 'Binary Tree — Tutorials & Problems',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'All tree traversal patterns, BST operations, and balanced tree concepts.',
        url: 'https://www.geeksforgeeks.org/binary-tree-data-structure/',
      },
      {
        title: 'Tree Traversal (BFS & DFS) Visualized',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'Visual step-by-step traversals — breadth-first, depth-first, pre/in/post order.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+binary+tree+traversal+BFS+DFS',
      },
      {
        title: 'Binary Tree Problems — Practice',
        platform: 'LeetCode (Free Tier)',
        type: 'Practice',
        description: 'Practice: Max Depth, Invert Binary Tree, Level Order Traversal, Validate BST.',
        url: 'https://leetcode.com/tag/tree/',
      },
    ],
  },

  // ── DSA: Graphs & Topological Sort ─────────────────────────────────────────
  {
    subject: 'graphs_topological_sort',
    label: 'Graph Algorithms',
    matchKeywords: ['graph', 'vertex', 'edge', 'adjacency', 'topological', 'cycle', 'shortest path', 'dijkstra', 'bellman', 'connected component', 'bfs graph', 'dfs graph', 'number-of-islands', 'course-schedule', 'clone-graph'],
    resources: [
      {
        title: 'Graph Data Structure — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'BFS, DFS, cycle detection, topological sort, Dijkstra, and Kruskal/Prim MST.',
        url: 'https://www.geeksforgeeks.org/graph-data-structure-and-algorithms/',
      },
      {
        title: 'Graph Algorithms Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'Comprehensive 2+ hour course covering graph representations, traversals, and shortest paths.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+graph+algorithms+full+course',
      },
      {
        title: 'Graph Problems — Practice',
        platform: 'LeetCode (Free Tier)',
        type: 'Practice',
        description: 'Practice: Number of Islands, Course Schedule, Clone Graph, Word Ladder.',
        url: 'https://leetcode.com/tag/graph/',
      },
    ],
  },

  // ── DSA: Dynamic Programming ───────────────────────────────────────────────
  {
    subject: 'dynamic_programming',
    label: 'Dynamic Programming',
    matchKeywords: ['dynamic programming', 'dp', 'memoization', 'tabulation', 'recurrence', 'knapsack', 'longest common subsequence', 'longest increasing subsequence', 'coin-change', 'climbing-stairs', 'fibonacci'],
    resources: [
      {
        title: 'Dynamic Programming — Complete Guide',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Top-down and bottom-up DP patterns, LCS, knapsack, and matrix chain multiplication.',
        url: 'https://www.geeksforgeeks.org/dynamic-programming/',
      },
      {
        title: 'Dynamic Programming for Beginners',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'Beginner-friendly visual explanations of memoization, tabulation, and common DP problems.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+dynamic+programming+beginners',
      },
      {
        title: 'DP Problems — Practice',
        platform: 'LeetCode (Free Tier)',
        type: 'Practice',
        description: 'Practice: Climbing Stairs, Coin Change, House Robber, Longest Increasing Subsequence.',
        url: 'https://leetcode.com/tag/dynamic-programming/',
      },
    ],
  },

  // ── DSA: Sorting & Searching ───────────────────────────────────────────────
  {
    subject: 'sorting_searching',
    label: 'Sorting & Searching',
    matchKeywords: ['sorting', 'searching', 'binary search', 'merge sort', 'quick sort', 'heap sort', 'insertion sort', 'bubble sort', 'selection sort', 'radix sort', 'counting sort'],
    resources: [
      {
        title: 'Sorting Algorithms — Complete Reference',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'All major sorting algorithms with complexity analysis and implementation guides.',
        url: 'https://www.geeksforgeeks.org/sorting-algorithms/',
      },
      {
        title: 'Binary Search — Step-by-Step',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Binary search on sorted arrays, rotated arrays, and search-space reduction.',
        url: 'https://www.geeksforgeeks.org/binary-search/',
      },
      {
        title: 'Sorting Algorithm Visualizations',
        platform: 'VisuAlgo',
        type: 'Practice',
        description: 'Interactive visualizations of merge sort, quicksort, heap sort, and more.',
        url: 'https://visualgo.net/en/sorting',
      },
    ],
  },

  // ── DSA: Recursion & Backtracking ──────────────────────────────────────────
  {
    subject: 'recursion_backtracking',
    label: 'Recursion & Backtracking',
    matchKeywords: ['recursion', 'backtracking', 'n-queens', 'permutation', 'combination', 'subset', 'sudoku solver', 'recursive'],
    resources: [
      {
        title: 'Recursion — Introduction to Problem Solving',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Base cases, recursive thinking, call stack mechanics, and tail recursion.',
        url: 'https://www.geeksforgeeks.org/introduction-to-recursion-2/',
      },
      {
        title: 'Backtracking Algorithms Explained',
        platform: 'Gate Smashers (YouTube)',
        type: 'Video',
        description: 'N-Queens, Sudoku Solver, and subset sum solved with backtracking strategy.',
        url: 'https://www.youtube.com/results?search_query=Gate+Smashers+backtracking+algorithm',
      },
      {
        title: 'Backtracking Problems — Practice',
        platform: 'LeetCode (Free Tier)',
        type: 'Practice',
        description: 'Practice: Subsets, Permutations, N-Queens, Combination Sum.',
        url: 'https://leetcode.com/tag/backtracking/',
      },
    ],
  },

  // ── DSA: Greedy Algorithms ─────────────────────────────────────────────────
  {
    subject: 'greedy_algorithms',
    label: 'Greedy Algorithms',
    matchKeywords: ['greedy', 'greedy algorithm', 'activity selection', 'huffman', 'interval scheduling', 'fractional knapsack', 'job sequencing'],
    resources: [
      {
        title: 'Greedy Algorithms — Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Activity selection, Huffman coding, job sequencing, and fractional knapsack.',
        url: 'https://www.geeksforgeeks.org/greedy-algorithms/',
      },
      {
        title: 'Greedy Algorithm Explained',
        platform: 'Gate Smashers (YouTube)',
        type: 'Video',
        description: 'When and how to apply greedy strategies with optimality proofs.',
        url: 'https://www.youtube.com/results?search_query=Gate+Smashers+greedy+algorithm',
      },
      {
        title: 'Greedy Problems — Practice',
        platform: 'LeetCode (Free Tier)',
        type: 'Practice',
        description: 'Practice: Jump Game, Gas Station, Task Scheduler, Meeting Rooms.',
        url: 'https://leetcode.com/tag/greedy/',
      },
    ],
  },

  // ── DBMS & SQL ─────────────────────────────────────────────────────────────
  {
    subject: 'dbms_sql',
    label: 'DBMS & SQL',
    matchKeywords: ['database', 'dbms', 'sql', 'normalization', 'acid', 'transaction', 'indexing', 'query', 'join', 'relational', 'schema', 'er diagram', 'mysql', 'postgres', 'postgresql', 'foreign key', 'primary key', 'aggregate', 'group by', 'subquery', 'query optimization', 'database design', 'keys'],
    resources: [
      {
        title: 'DBMS — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'ER diagrams, normalization (1NF–BCNF), ACID properties, concurrency control, and indexing.',
        url: 'https://www.geeksforgeeks.org/dbms/',
      },
      {
        title: 'DBMS Full Course (Gate Preparation)',
        platform: 'Gate Smashers (YouTube)',
        type: 'Video',
        description: 'Complete DBMS syllabus covering relational algebra, SQL, transactions, and recovery.',
        url: 'https://www.youtube.com/playlist?list=PLxCzCOWd7aiFAN6I8CuViBuCdJgiOkT2Y',
      },
      {
        title: 'SQL Tutorial — Interactive Practice',
        platform: 'W3Schools',
        type: 'Tutorial',
        description: 'Interactive SQL editor with joins, subqueries, GROUP BY, HAVING, and aggregate functions.',
        url: 'https://www.w3schools.com/sql/',
      },
    ],
  },

  // ── Operating Systems ──────────────────────────────────────────────────────
  {
    subject: 'operating_systems',
    label: 'Operating Systems',
    matchKeywords: ['operating system', 'os', 'process', 'thread', 'cpu scheduling', 'scheduling', 'deadlock', 'synchronization', 'semaphore', 'mutex', 'memory management', 'virtual memory', 'paging', 'segmentation', 'file system', 'page replacement', 'process scheduling', 'fcfs', 'sjf', 'round robin', 'priority scheduling', 'banker'],
    resources: [
      {
        title: 'Operating Systems — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Processes, threads, CPU scheduling, deadlocks, memory management, and file systems.',
        url: 'https://www.geeksforgeeks.org/operating-systems/',
      },
      {
        title: 'Operating System Full Course',
        platform: 'Gate Smashers (YouTube)',
        type: 'Video',
        description: 'Comprehensive video lectures on processes, scheduling, synchronization, and deadlocks.',
        url: 'https://www.youtube.com/playlist?list=PLxCzCOWd7aiGz9donHRrE9I3Mwn6XdP8p',
      },
      {
        title: 'OS Concepts — Textbook Reference',
        platform: 'Neso Academy (YouTube)',
        type: 'Course',
        description: 'University-level OS lectures covering virtual memory, paging, and process life cycle.',
        url: 'https://www.youtube.com/playlist?list=PLBlnK6fEyqRiVhbXDGLXDk_OQAknUkiOA',
      },
    ],
  },

  // ── Computer Networks ──────────────────────────────────────────────────────
  {
    subject: 'computer_networks',
    label: 'Computer Networks',
    matchKeywords: ['computer network', 'network', 'cn', 'osi', 'tcp/ip', 'tcp', 'udp', 'http', 'https', 'dns', 'routing', 'subnet', 'subnetting', 'ip address', 'congestion', 'arp', 'dhcp', 'nat', 'socket', 'application layer', 'transport layer', 'network layer', 'data link', 'physical layer', 'network security', 'firewall', 'ssl', 'tls'],
    resources: [
      {
        title: 'Computer Networks — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'OSI & TCP/IP models, routing, subnetting, TCP vs UDP, DNS, HTTP/HTTPS, and sockets.',
        url: 'https://www.geeksforgeeks.org/computer-network-tutorials/',
      },
      {
        title: 'Computer Networks Full Course',
        platform: 'Gate Smashers (YouTube)',
        type: 'Video',
        description: 'Complete CN syllabus including OSI layers, TCP handshake, IP addressing, and congestion control.',
        url: 'https://www.youtube.com/playlist?list=PLxCzCOWd7aiGFBD2-2joCpWOLUrDLvVV_',
      },
      {
        title: 'Networking Basics — Interactive',
        platform: 'Neso Academy (YouTube)',
        type: 'Course',
        description: 'Detailed networking fundamentals with examples of subnetting, DHCP, NAT, and ARP.',
        url: 'https://www.youtube.com/playlist?list=PLBlnK6fEyqRgMCUAG0XRw78UA8qnv6jEx',
      },
    ],
  },

  // ── OOP & Design Patterns ──────────────────────────────────────────────────
  {
    subject: 'oop_design_patterns',
    label: 'OOP & Design Patterns',
    matchKeywords: ['oop', 'object oriented', 'encapsulation', 'inheritance', 'polymorphism', 'abstraction', 'solid', 'design pattern', 'factory', 'singleton', 'observer', 'strategy', 'decorator', 'dependency injection', 'clean code', 'coupling', 'cohesion', 'interface', 'abstract class'],
    resources: [
      {
        title: 'Object Oriented Programming — Concepts',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Encapsulation, inheritance, polymorphism, abstraction, and SOLID principles with examples.',
        url: 'https://www.geeksforgeeks.org/object-oriented-programming-oops-concept-in-java/',
      },
      {
        title: 'Design Patterns Explained Simply',
        platform: 'Refactoring Guru',
        type: 'Tutorial',
        description: 'All 23 GoF design patterns with visual diagrams, code examples, and use-case guidance.',
        url: 'https://refactoring.guru/design-patterns',
      },
      {
        title: 'OOP Concepts — Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'Comprehensive object-oriented programming course with Java and Python examples.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+OOP+object+oriented+programming+course',
      },
    ],
  },

  // ── Python Programming ─────────────────────────────────────────────────────
  {
    subject: 'python_programming',
    label: 'Python Programming',
    matchKeywords: ['python', 'python programming', 'python3', 'flask', 'django', 'pip', 'virtualenv', 'list comprehension', 'decorator', 'generator', 'lambda', 'pandas', 'numpy'],
    resources: [
      {
        title: 'Python Programming — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Python basics, OOP, data structures, file handling, and advanced features.',
        url: 'https://www.geeksforgeeks.org/python-programming-language/',
      },
      {
        title: 'Python for Everybody — Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Course',
        description: 'Beginner to intermediate Python course covering data structures, web scraping, and databases.',
        url: 'https://www.youtube.com/watch?v=8DvywoWv6fI',
      },
      {
        title: 'Python Official Documentation',
        platform: 'Python.org',
        type: 'Documentation',
        description: 'Official Python 3 documentation — standard library, tutorials, and language reference.',
        url: 'https://docs.python.org/3/tutorial/',
      },
    ],
  },

  // ── Java Programming ───────────────────────────────────────────────────────
  {
    subject: 'java_programming',
    label: 'Java Programming',
    matchKeywords: ['java', 'jdk', 'jvm', 'spring', 'spring boot', 'maven', 'gradle', 'collections framework', 'multithreading java', 'streams api'],
    resources: [
      {
        title: 'Java Programming — Complete Reference',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Java fundamentals, OOP, collections, multithreading, exception handling, and streams.',
        url: 'https://www.geeksforgeeks.org/java/',
      },
      {
        title: 'Java Programming Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Course',
        description: 'Comprehensive Java course from basics to advanced topics like generics and streams.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+java+full+course',
      },
      {
        title: 'Java Tutorials',
        platform: 'W3Schools',
        type: 'Tutorial',
        description: 'Interactive Java tutorials covering syntax, OOP, data structures, and common patterns.',
        url: 'https://www.w3schools.com/java/',
      },
    ],
  },

  // ── C / C++ Programming ────────────────────────────────────────────────────
  {
    subject: 'c_cpp_programming',
    label: 'C / C++ Programming',
    matchKeywords: ['c programming', 'c++', 'cpp', 'c language', 'pointer', 'memory allocation', 'malloc', 'stl', 'standard template library', 'templates', 'competitive programming'],
    resources: [
      {
        title: 'C Programming — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'C fundamentals — pointers, memory management, structures, file I/O, and preprocessor.',
        url: 'https://www.geeksforgeeks.org/c-programming-language/',
      },
      {
        title: 'C++ STL — Complete Reference',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Vectors, maps, sets, priority queues, algorithms, and iterators in C++ STL.',
        url: 'https://www.geeksforgeeks.org/the-c-standard-template-library-stl/',
      },
      {
        title: 'C Programming Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Course',
        description: 'Complete C programming course — variables, control flow, functions, and pointers.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+C+programming+full+course',
      },
    ],
  },

  // ── JavaScript / Frontend ──────────────────────────────────────────────────
  {
    subject: 'javascript_frontend',
    label: 'JavaScript & Frontend',
    matchKeywords: ['javascript', 'js', 'typescript', 'react', 'angular', 'vue', 'dom', 'css', 'html', 'frontend', 'web development', 'node.js', 'next.js', 'tailwind'],
    resources: [
      {
        title: 'JavaScript — Complete Tutorial',
        platform: 'W3Schools',
        type: 'Tutorial',
        description: 'Interactive JavaScript tutorials covering ES6+, DOM, events, async/await, and fetch.',
        url: 'https://www.w3schools.com/js/',
      },
      {
        title: 'Full Stack Web Development Course',
        platform: 'freeCodeCamp',
        type: 'Course',
        description: 'Free certifications covering HTML, CSS, JavaScript, React, Node.js, and APIs.',
        url: 'https://www.freecodecamp.org/learn/',
      },
      {
        title: 'React Official Documentation',
        platform: 'React.dev',
        type: 'Documentation',
        description: 'Official React 18 docs with interactive examples, hooks reference, and best practices.',
        url: 'https://react.dev/learn',
      },
    ],
  },

  // ── AI / ML / Data Science ─────────────────────────────────────────────────
  {
    subject: 'ai_ml_data_science',
    label: 'AI, ML & Data Science',
    matchKeywords: ['machine learning', 'deep learning', 'neural network', 'nlp', 'natural language processing', 'artificial intelligence', 'ai', 'ml', 'data science', 'classification', 'regression', 'clustering', 'cnn', 'rnn', 'transformer', 'sklearn', 'tensorflow', 'pytorch', 'data preprocessing', 'feature engineering', 'model evaluation', 'confusion matrix', 'random forest', 'svm', 'gradient descent'],
    resources: [
      {
        title: 'Machine Learning — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Supervised, unsupervised, and reinforcement learning algorithms with Python implementations.',
        url: 'https://www.geeksforgeeks.org/machine-learning/',
      },
      {
        title: 'Machine Learning Course for Beginners',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Course',
        description: 'Comprehensive ML course covering regression, classification, neural networks, and evaluation.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+machine+learning+full+course',
      },
      {
        title: 'Deep Learning Specialization Lectures',
        platform: 'MIT OpenCourseWare',
        type: 'Course',
        description: 'Free university-level deep learning lectures covering CNNs, RNNs, GANs, and transformers.',
        url: 'https://ocw.mit.edu/courses/6-s191-introduction-to-deep-learning-january-iap-2020/',
      },
    ],
  },

  // ── System Design & Architecture ───────────────────────────────────────────
  {
    subject: 'system_design_architecture',
    label: 'System Design & Scalability',
    matchKeywords: ['system design', 'architecture', 'scalability', 'caching', 'cache', 'load balancer', 'load balancing', 'microservices', 'distributed system', 'database sharding', 'cap theorem', 'cdn', 'reverse proxy', 'rate limiter', 'url shortener', 'message queue', 'event driven', 'redis'],
    resources: [
      {
        title: 'System Design Primer',
        platform: 'GitHub (donnemartin)',
        type: 'Tutorial',
        description: 'Comprehensive open-source system design guide — scalability, databases, caching, and load balancing.',
        url: 'https://github.com/donnemartin/system-design-primer',
      },
      {
        title: 'System Design — Key Concepts',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'CAP theorem, consistent hashing, database replication, sharding, and CDN design.',
        url: 'https://www.geeksforgeeks.org/system-design-tutorial/',
      },
      {
        title: 'System Design Interview Prep',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'Step-by-step system design mock interviews for URL shortener, chat systems, and rate limiters.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+system+design+interview',
      },
    ],
  },

  // ── API Design & Backend Services ──────────────────────────────────────────
  {
    subject: 'api_rest_microservices',
    label: 'API Design & Backend',
    matchKeywords: ['api', 'rest', 'restful', 'http', 'jwt', 'oauth', 'authentication', 'authorization', 'endpoint', 'backend', 'microservices', 'graphql', 'grpc', 'rate limiting', 'middleware', 'flask', 'django', 'express', 'fastapi'],
    resources: [
      {
        title: 'REST API Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'RESTful API design principles, HTTP methods, status codes, authentication, and best practices.',
        url: 'https://www.geeksforgeeks.org/rest-api-introduction/',
      },
      {
        title: 'APIs for Beginners — Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Course',
        description: 'Learn REST APIs, HTTP, JSON, Postman, and API authentication from scratch.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+APIs+beginners+full+course',
      },
      {
        title: 'Django REST Framework Documentation',
        platform: 'DRF Official Docs',
        type: 'Documentation',
        description: 'Official Django REST Framework documentation with serializers, views, and authentication.',
        url: 'https://www.django-rest-framework.org/',
      },
    ],
  },

  // ── Cloud & DevOps ─────────────────────────────────────────────────────────
  {
    subject: 'cloud_devops',
    label: 'Cloud & DevOps',
    matchKeywords: ['cloud', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'ci/cd', 'devops', 'linux', 'deployment', 'terraform', 'ansible', 'jenkins', 'github actions', 'containerization', 'cloud architecture', 'ec2', 's3', 'lambda', 'serverless'],
    resources: [
      {
        title: 'AWS Cloud Practitioner — Free Study Guide',
        platform: 'freeCodeCamp',
        type: 'Course',
        description: 'Complete free AWS Cloud Practitioner preparation covering EC2, S3, Lambda, and IAM.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+AWS+cloud+practitioner+full+course',
      },
      {
        title: 'Docker Tutorial for Beginners',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'Docker containers, images, Dockerfile, Docker Compose, and deployment workflows.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+docker+tutorial+beginners',
      },
      {
        title: 'Linux Command Line — Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Course',
        description: 'Essential Linux commands, shell scripting, file permissions, and system administration.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+linux+command+line+full+course',
      },
    ],
  },

  // ── Software Engineering & SDLC ────────────────────────────────────────────
  {
    subject: 'software_engineering',
    label: 'Software Engineering',
    matchKeywords: ['software engineering', 'sdlc', 'agile', 'scrum', 'waterfall', 'testing', 'unit test', 'integration test', 'git', 'version control', 'code review', 'continuous integration', 'tdd', 'bdd', 'requirement engineering'],
    resources: [
      {
        title: 'Software Engineering — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'SDLC models, requirement analysis, software testing, UML, and project management.',
        url: 'https://www.geeksforgeeks.org/software-engineering/',
      },
      {
        title: 'Git and GitHub — Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Course',
        description: 'Git workflows, branching, merging, pull requests, and collaborative development.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+git+github+full+course',
      },
      {
        title: 'Agile & Scrum Overview',
        platform: 'TutorialsPoint',
        type: 'Tutorial',
        description: 'Agile principles, Scrum ceremonies, sprint planning, user stories, and Kanban boards.',
        url: 'https://www.tutorialspoint.com/agile/index.htm',
      },
    ],
  },

  // ── Computer Organization & Architecture ───────────────────────────────────
  {
    subject: 'computer_organization',
    label: 'Computer Organization & Architecture',
    matchKeywords: ['computer organization', 'coa', 'computer architecture', 'cpu', 'pipeline', 'cache memory', 'instruction set', 'risc', 'cisc', 'alu', 'register', 'addressing mode', 'bus architecture', 'assembly language'],
    resources: [
      {
        title: 'Computer Organization — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'CPU design, pipelining, cache organization, memory hierarchy, and I/O systems.',
        url: 'https://www.geeksforgeeks.org/computer-organization-and-architecture-tutorials/',
      },
      {
        title: 'Computer Organization Full Course',
        platform: 'Gate Smashers (YouTube)',
        type: 'Video',
        description: 'Complete COA lectures — pipeline hazards, cache mapping, addressing modes, and DMA.',
        url: 'https://www.youtube.com/results?search_query=Gate+Smashers+computer+organization+architecture',
      },
      {
        title: 'Computer Architecture — Neso Academy',
        platform: 'Neso Academy (YouTube)',
        type: 'Course',
        description: 'University-level lectures on instruction formats, microprogramming, and memory systems.',
        url: 'https://www.youtube.com/results?search_query=Neso+Academy+computer+organization+architecture',
      },
    ],
  },

  // ── Theory of Computation ──────────────────────────────────────────────────
  {
    subject: 'theory_of_computation',
    label: 'Theory of Computation',
    matchKeywords: ['theory of computation', 'toc', 'automata', 'finite automata', 'pushdown automata', 'turing machine', 'context free grammar', 'regular expression', 'chomsky', 'pumping lemma', 'decidability', 'computability'],
    resources: [
      {
        title: 'Theory of Computation — Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'DFA, NFA, regular expressions, context-free grammars, PDAs, and Turing machines.',
        url: 'https://www.geeksforgeeks.org/theory-of-computation-automata-tutorials/',
      },
      {
        title: 'Theory of Computation Full Course',
        platform: 'Gate Smashers (YouTube)',
        type: 'Video',
        description: 'Complete TOC syllabus — finite automata, CFG, PDA, Turing machine, and decidability.',
        url: 'https://www.youtube.com/playlist?list=PLxCzCOWd7aiFM9Lj5G9G_76adtyb4ef7i',
      },
      {
        title: 'Automata Theory — Neso Academy',
        platform: 'Neso Academy (YouTube)',
        type: 'Course',
        description: 'Detailed lectures on language theory, regular and context-free languages, and closure properties.',
        url: 'https://www.youtube.com/results?search_query=Neso+Academy+automata+theory+of+computation',
      },
    ],
  },

  // ── Compiler Design ────────────────────────────────────────────────────────
  {
    subject: 'compiler_design',
    label: 'Compiler Design',
    matchKeywords: ['compiler', 'compiler design', 'lexical analysis', 'syntax analysis', 'parser', 'code generation', 'code optimization', 'semantic analysis', 'intermediate code', 'lr parser', 'll parser'],
    resources: [
      {
        title: 'Compiler Design — Complete Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Lexical analysis, parsing, semantic analysis, intermediate code, and code optimization.',
        url: 'https://www.geeksforgeeks.org/compiler-design-tutorials/',
      },
      {
        title: 'Compiler Design Full Course',
        platform: 'Gate Smashers (YouTube)',
        type: 'Video',
        description: 'Comprehensive compiler design lectures — phases of compiler, LR/LL parsing, and SDT.',
        url: 'https://www.youtube.com/results?search_query=Gate+Smashers+compiler+design+full+course',
      },
      {
        title: 'Compiler Construction — Neso Academy',
        platform: 'Neso Academy (YouTube)',
        type: 'Course',
        description: 'University-level compiler construction lectures with parsing tables and code generation.',
        url: 'https://www.youtube.com/results?search_query=Neso+Academy+compiler+design',
      },
    ],
  },

  // ── Cybersecurity ──────────────────────────────────────────────────────────
  {
    subject: 'cybersecurity',
    label: 'Cybersecurity',
    matchKeywords: ['cybersecurity', 'security', 'encryption', 'cryptography', 'rsa', 'aes', 'firewall', 'penetration testing', 'vulnerability', 'xss', 'sql injection', 'owasp', 'ethical hacking', 'network security'],
    resources: [
      {
        title: 'Cybersecurity — Complete Guide',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Cryptography, network security, authentication protocols, and common vulnerability types.',
        url: 'https://www.geeksforgeeks.org/cyber-security-tutorial/',
      },
      {
        title: 'Ethical Hacking — Full Course',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Course',
        description: 'Penetration testing, network scanning, exploitation, and security tools explained.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+ethical+hacking+full+course',
      },
      {
        title: 'OWASP Top 10 — Web Security',
        platform: 'OWASP.org',
        type: 'Documentation',
        description: 'Official OWASP Top 10 web application security risks with prevention guidelines.',
        url: 'https://owasp.org/www-project-top-ten/',
      },
    ],
  },

  // ── Mathematics for CS ─────────────────────────────────────────────────────
  {
    subject: 'mathematics_cs',
    label: 'Mathematics for CS',
    matchKeywords: ['mathematics', 'math', 'discrete math', 'linear algebra', 'probability', 'statistics', 'combinatorics', 'number theory', 'graph theory', 'set theory', 'logic', 'boolean algebra', 'calculus'],
    resources: [
      {
        title: 'Discrete Mathematics — Tutorial',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Set theory, combinatorics, graph theory, Boolean algebra, and propositional logic.',
        url: 'https://www.geeksforgeeks.org/discrete-mathematics-tutorial/',
      },
      {
        title: 'Mathematics for Computer Science (MIT)',
        platform: 'MIT OpenCourseWare',
        type: 'Course',
        description: 'Full MIT course covering proofs, number theory, graph theory, and probability.',
        url: 'https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-fall-2010/',
      },
      {
        title: 'Probability & Statistics — Khan Academy',
        platform: 'Khan Academy',
        type: 'Course',
        description: 'Free interactive course covering probability distributions, hypothesis testing, and Bayes theorem.',
        url: 'https://www.khanacademy.org/math/statistics-probability',
      },
    ],
  },

  // ── Behavioral & HR Interview ──────────────────────────────────────────────
  {
    subject: 'behavioral_hr_interview',
    label: 'Behavioral & HR Interview',
    matchKeywords: ['behavioral', 'hr', 'star', 'star method', 'communication', 'leadership', 'teamwork', 'conflict resolution', 'culture fit', 'behavioral interview', 'hr interview', 'tell me about yourself', 'strengths weaknesses', 'why this company', 'resume preparation', 'self introduction'],
    resources: [
      {
        title: 'Top 50 HR Interview Questions',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Common HR and behavioral questions with STAR-format sample answers and tips.',
        url: 'https://www.geeksforgeeks.org/hr-interview-questions/',
      },
      {
        title: 'Behavioral Interview Preparation — STAR Method',
        platform: 'freeCodeCamp (Article)',
        type: 'Tutorial',
        description: 'How to structure behavioral answers using Situation-Task-Action-Result framework.',
        url: 'https://www.freecodecamp.org/news/how-to-answer-behavioral-interview-questions/',
      },
      {
        title: 'HR Interview Tips — Communication Skills',
        platform: 'TutorialsPoint',
        type: 'Tutorial',
        description: 'Body language, active listening, storytelling, and handling stress interview questions.',
        url: 'https://www.tutorialspoint.com/hr_interview_questions/index.htm',
      },
    ],
  },

  // ── Project Deep-Dive & Portfolio ──────────────────────────────────────────
  {
    subject: 'project_deep_dive',
    label: 'Project Architecture & Portfolio',
    matchKeywords: ['project', 'portfolio', 'resume', 'trade-off', 'tradeoff', 'architecture decision', 'whiteboard', 'project explanation', 'technical justification', 'metrics', 'postmortem', 'bottleneck'],
    resources: [
      {
        title: 'How to Explain Projects in Interviews',
        platform: 'GeeksforGeeks',
        type: 'Tutorial',
        description: 'Framework for presenting personal and academic projects — scope, architecture, impact.',
        url: 'https://www.geeksforgeeks.org/how-to-explain-your-project-in-interview/',
      },
      {
        title: 'Build a Developer Portfolio',
        platform: 'freeCodeCamp (YouTube)',
        type: 'Video',
        description: 'How to create a standout developer portfolio showcasing your projects effectively.',
        url: 'https://www.youtube.com/results?search_query=freeCodeCamp+developer+portfolio',
      },
      {
        title: 'Architecture Decision Records',
        platform: 'GitHub (joelparkerhenderson)',
        type: 'Documentation',
        description: 'Open-source guide to writing architecture decision records for technical trade-off documentation.',
        url: 'https://github.com/joelparkerhenderson/architecture-decision-record',
      },
    ],
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Matching Engine
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Normalizes a string for keyword matching: lowercased, trimmed, and with
 * special characters replaced by spaces.
 */
function normalizeText(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim()
}

/**
 * Scores how well a catalogue entry matches a given topic by counting keyword
 * hits across the topic name, activity ID, category, and sub-topics.
 * Returns a value >= 0; higher = better match.
 */
function scoreMatch(
  entry: CatalogueEntry,
  activityId: string,
  topicName: string,
  category: string,
  subTopics: string[]
): number {
  // Build a searchable text blob from all available topic metadata
  const blob = normalizeText(
    [activityId, topicName, category, ...subTopics].join(' ')
  )

  let score = 0

  // Direct activity-ID match (e.g. 'arrays_hashing' === 'arrays_hashing')
  if (normalizeText(entry.subject) === normalizeText(activityId)) {
    score += 100
  }

  // Keyword intersection scoring
  for (const kw of entry.matchKeywords) {
    const normKw = normalizeText(kw)
    if (blob.includes(normKw)) {
      // Longer keywords are more specific = worth more
      score += 2 + normKw.length
    }
  }

  return score
}

/**
 * Returns the best-matched learning resources for a given preparation topic.
 *
 * @param activityId - The machine ID of the topic (e.g. 'arrays_hashing')
 * @param topicName - Human-readable topic name (e.g. 'Arrays & Hashing')
 * @param category  - Topic category (e.g. 'coding', 'technical', 'behavioral')
 * @param subTopics - Sub-topics / recommended activities for the module
 * @returns 2–3 LearningResource objects, or a fallback set for unknown topics
 */
export function getResourcesForTopic(
  activityId: string,
  topicName: string,
  category: string = '',
  subTopics: string[] = []
): LearningResource[] {
  // Score every catalogue entry against this topic
  const scored = RESOURCE_CATALOGUE.map((entry) => ({
    entry,
    score: scoreMatch(entry, activityId, topicName, category, subTopics),
  }))

  // Sort descending by match score
  scored.sort((a, b) => b.score - a.score)

  // Take the best match if its score is meaningful (> 3)
  const best = scored[0]
  if (best && best.score > 3) {
    return best.entry.resources.slice(0, 3)
  }

  // ── Fallback for completely unknown topics ─────────────────────────────
  // Generate a topic-specific GeeksforGeeks search link and a YouTube search
  const safeName = encodeURIComponent(topicName)
  return [
    {
      title: `${topicName} — Tutorials & Articles`,
      platform: 'GeeksforGeeks',
      type: 'Tutorial',
      description: `Search GeeksforGeeks for tutorials, articles, and practice problems on ${topicName}.`,
      url: `https://www.geeksforgeeks.org/search/?q=${safeName}`,
    },
    {
      title: `${topicName} — Video Lectures`,
      platform: 'YouTube',
      type: 'Video',
      description: `Find free video lectures and explanations for ${topicName} from top educators.`,
      url: `https://www.youtube.com/results?search_query=${safeName}+tutorial`,
    },
  ]
}

/**
 * Returns all available subject labels in the catalogue.
 * Useful for debugging or admin views.
 */
export function getAvailableSubjects(): string[] {
  return RESOURCE_CATALOGUE.map((e) => e.label)
}

