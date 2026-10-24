"""
Management command: seed_coding_problems

Seeds the coding problem bank with 20 simple, generic, foundational mock interview questions.
Every problem adheres strictly to:
- Candidate ONLY writes the function (clean starter code, no boilerplate)
- Hidden driver code handles stdin parsing, function invocation, and stdout formatting
- Public and hidden test cases for thorough evaluation
- Multi-language support: Python, Java, C++, JavaScript

Usage:
    python manage.py seed_coding_problems           # Update or create
    python manage.py seed_coding_problems --clear   # Delete all then reseed
"""
from django.core.management.base import BaseCommand
from apps.assessments.models import CodingProblem, CodingTestCase

PROBLEMS = [

    # ─── 1. REMOVE DUPLICATES FROM ARRAY ──────────────────────────────────────
    {
        "title": "Remove Duplicates from Array",
        "slug": "remove-duplicates-from-array",
        "difficulty": "easy",
        "topics": ["arrays", "basic_algorithms"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": "Given an array of integers nums, remove duplicate elements so each element appears only once, preserving original order of appearance.",
        "input_format": "Space-separated integers representing the array.",
        "output_format": "Space-separated unique integers.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [{"input": "1 2 2 3 4 4 5", "output": "1 2 3 4 5", "explanation": "Duplicates removed."}],
        "starter_code": {
            "python": "def remove_duplicates(nums: list[int]) -> list[int]:\n    # Write your solution here\n    pass\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public static int[] removeDuplicates(int[] nums) {\n        // Write your solution here\n        return new int[]{};\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> removeDuplicates(vector<int>& nums) {\n        // Write your solution here\n        return {};\n    }\n};\n",
            "javascript": "function removeDuplicates(nums) {\n    // Write your solution here\n    return [];\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    if raw:\n        nums = list(map(int, raw.split()))\n        res = remove_duplicates(nums)\n        print(' '.join(map(str, res)) if res is not None else '')\n    else:\n        print('')\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (!sc.hasNextLine()) { System.out.println(\"\"); return; }\n        String line = sc.nextLine().trim();\n        if (line.isEmpty()) { System.out.println(\"\"); return; }\n        int[] nums = Arrays.stream(line.split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        int[] res = Solution.removeDuplicates(nums);\n        StringBuilder sb = new StringBuilder();\n        for (int i = 0; i < res.length; i++) { if (i > 0) sb.append(\" \"); sb.append(res[i]); }\n        System.out.println(sb.toString());\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; if (!getline(cin, line) || line.empty()) { cout << endl; return 0; }\n    istringstream iss(line); vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; auto res = sol.removeDuplicates(nums);\n    for (size_t i = 0; i < res.size(); ++i) { if (i > 0) cout << \" \"; cout << res[i]; }\n    cout << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nif (input) {\n    const nums = input.split(/\\s+/).map(Number);\n    const res = removeDuplicates(nums) || [];\n    console.log(Array.isArray(res) ? res.join(' ') : res);\n} else { console.log(''); }\n",
        },
        "public_test_cases": [
            {"input": "1 2 2 3 4 4 5", "expected_output": "1 2 3 4 5"},
            {"input": "1 1 1 1 1", "expected_output": "1"},
        ],
        "hidden_test_cases": [
            {"input": "4 5 1 2 4 5 3", "expected_output": "4 5 1 2 3"},
            {"input": "10", "expected_output": "10"},
            {"input": "-3 -1 -3 0 2 2 -1", "expected_output": "-3 -1 0 2"},
            {"input": "5 4 3 2 1", "expected_output": "5 4 3 2 1"},
        ],
    },

    # ─── 2. SECOND LARGEST ────────────────────────────────────────────────────
    {
        "title": "Second Largest",
        "slug": "second-largest",
        "difficulty": "easy",
        "topics": ["arrays", "basic_algorithms"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given an array of integers nums, return the second largest distinct element. Return -1 if no distinct second largest exists.",
        "input_format": "Space-separated integers representing the array.",
        "output_format": "A single integer.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [{"input": "12 35 1 10 34 1", "output": "34", "explanation": "Largest is 35, second largest is 34."}],
        "starter_code": {
            "python": "def second_largest(nums: list[int]) -> int:\n    # Write your solution here\n    pass\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public static int secondLargest(int[] nums) {\n        // Write your solution here\n        return -1;\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    int secondLargest(vector<int>& nums) {\n        // Write your solution here\n        return -1;\n    }\n};\n",
            "javascript": "function secondLargest(nums) {\n    // Write your solution here\n    return -1;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    if raw:\n        nums = list(map(int, raw.split()))\n        res = second_largest(nums)\n        print(res if res is not None else -1)\n    else:\n        print(-1)\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (!sc.hasNextLine()) { System.out.println(-1); return; }\n        String line = sc.nextLine().trim();\n        if (line.isEmpty()) { System.out.println(-1); return; }\n        int[] nums = Arrays.stream(line.split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(Solution.secondLargest(nums));\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; if (!getline(cin, line) || line.empty()) { cout << -1 << endl; return 0; }\n    istringstream iss(line); vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; cout << sol.secondLargest(nums) << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nif (input) {\n    const nums = input.split(/\\s+/).map(Number);\n    console.log(secondLargest(nums));\n} else { console.log(-1); }\n",
        },
        "public_test_cases": [
            {"input": "12 35 1 10 34 1", "expected_output": "34"},
            {"input": "10 5 10", "expected_output": "5"},
        ],
        "hidden_test_cases": [
            {"input": "10 10 10", "expected_output": "-1"},
            {"input": "7", "expected_output": "-1"},
            {"input": "-5 -2 -1 -10", "expected_output": "-2"},
            {"input": "100 200 50 150", "expected_output": "150"},
            {"input": "-10 -20 -30", "expected_output": "-20"},
        ],
    },

    # ─── 3. REVERSE OF ARRAY ──────────────────────────────────────────────────
    {
        "title": "Reverse of Array",
        "slug": "reverse-of-array",
        "difficulty": "easy",
        "topics": ["arrays", "basic_algorithms"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given an array of integers nums, reverse the array and return the reversed array.",
        "input_format": "Space-separated integers.",
        "output_format": "Space-separated integers in reversed order.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [{"input": "1 2 3 4 5", "output": "5 4 3 2 1", "explanation": "Reversed array."}],
        "starter_code": {
            "python": "def reverse_array(nums: list[int]) -> list[int]:\n    # Write your solution here\n    pass\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public static int[] reverseArray(int[] nums) {\n        // Write your solution here\n        return new int[]{};\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> reverseArray(vector<int>& nums) {\n        // Write your solution here\n        return {};\n    }\n};\n",
            "javascript": "function reverseArray(nums) {\n    // Write your solution here\n    return [];\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    if raw:\n        nums = list(map(int, raw.split()))\n        res = reverse_array(nums)\n        if res is None: res = nums\n        print(' '.join(map(str, res)) if res is not None else '')\n    else: print('')\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (!sc.hasNextLine()) { System.out.println(\"\"); return; }\n        String line = sc.nextLine().trim();\n        if (line.isEmpty()) { System.out.println(\"\"); return; }\n        int[] nums = Arrays.stream(line.split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        int[] res = Solution.reverseArray(nums);\n        if (res == null || (res.length == 0 && nums.length > 0)) res = nums;\n        StringBuilder sb = new StringBuilder();\n        for (int i = 0; i < res.length; i++) { if (i > 0) sb.append(\" \"); sb.append(res[i]); }\n        System.out.println(sb.toString());\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; if (!getline(cin, line) || line.empty()) { cout << endl; return 0; }\n    istringstream iss(line); vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; auto res = sol.reverseArray(nums);\n    if (res.empty() && !nums.empty()) res = nums;\n    for (size_t i = 0; i < res.size(); ++i) { if (i > 0) cout << \" \"; cout << res[i]; }\n    cout << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nif (input) {\n    const nums = input.split(/\\s+/).map(Number);\n    let res = reverseArray(nums);\n    if (!res || (Array.isArray(res) && res.length === 0 && nums.length > 0)) res = nums;\n    console.log(Array.isArray(res) ? res.join(' ') : res);\n} else { console.log(''); }\n",
        },
        "public_test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "5 4 3 2 1"},
            {"input": "4 5 1 2", "expected_output": "2 1 5 4"},
        ],
        "hidden_test_cases": [
            {"input": "42", "expected_output": "42"},
            {"input": "10 20", "expected_output": "20 10"},
            {"input": "-1 0 1 -2 2", "expected_output": "2 -2 1 0 -1"},
            {"input": "9 8 7 6 5 4 3 2 1", "expected_output": "1 2 3 4 5 6 7 8 9"},
        ],
    },

    # ─── 4. FREQUENCY COUNT ───────────────────────────────────────────────────
    {
        "title": "Frequency Count",
        "slug": "frequency-count",
        "difficulty": "easy",
        "topics": ["arrays", "hashing", "basic_algorithms"],
        "required_skills": ["arrays", "hashing"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": "Given an array of integers nums, return the frequency count of each element. The output formats each distinct element as element:count sorted in ascending order of element.",
        "input_format": "Space-separated integers.",
        "output_format": "Space-separated element:count pairs sorted by element.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [{"input": "1 2 2 3 1 4 2", "output": "1:2 2:3 3:1 4:1", "explanation": "Frequencies of elements."}],
        "starter_code": {
            "python": "def frequency_count(nums: list[int]) -> dict[int, int]:\n    # Write your solution here\n    pass\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public static Map<Integer, Integer> frequencyCount(int[] nums) {\n        // Write your solution here\n        return new HashMap<>();\n    }\n}\n",
            "cpp": "#include <vector>\n#include <unordered_map>\nusing namespace std;\n\nclass Solution {\npublic:\n    unordered_map<int, int> frequencyCount(vector<int>& nums) {\n        // Write your solution here\n        return {};\n    }\n};\n",
            "javascript": "function frequencyCount(nums) {\n    // Write your solution here\n    return {};\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    if raw:\n        nums = list(map(int, raw.split()))\n        res = frequency_count(nums)\n        if isinstance(res, dict):\n            items = sorted(res.items())\n            print(' '.join(f\"{k}:{v}\" for k, v in items))\n        elif isinstance(res, (list, tuple)):\n            print(' '.join(f\"{item[0]}:{item[1]}\" for item in res))\n        else: print(res if res is not None else '')\n    else: print('')\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (!sc.hasNextLine()) { System.out.println(\"\"); return; }\n        String line = sc.nextLine().trim();\n        if (line.isEmpty()) { System.out.println(\"\"); return; }\n        int[] nums = Arrays.stream(line.split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        Map<Integer, Integer> res = Solution.frequencyCount(nums);\n        if (res == null) { System.out.println(\"\"); return; }\n        TreeMap<Integer, Integer> sorted = new TreeMap<>(res);\n        StringBuilder sb = new StringBuilder();\n        boolean first = true;\n        for (Map.Entry<Integer, Integer> e : sorted.entrySet()) {\n            if (!first) sb.append(\" \");\n            sb.append(e.getKey()).append(\":\").append(e.getValue());\n            first = false;\n        }\n        System.out.println(sb.toString());\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <map>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; if (!getline(cin, line) || line.empty()) { cout << endl; return 0; }\n    istringstream iss(line); vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; auto res = sol.frequencyCount(nums);\n    map<int, int> sorted(res.begin(), res.end());\n    bool first = true;\n    for (const auto& p : sorted) {\n        if (!first) cout << \" \"; cout << p.first << \":\" << p.second; first = false;\n    }\n    cout << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nif (input) {\n    const nums = input.split(/\\s+/).map(Number);\n    const res = frequencyCount(nums) || {};\n    const keys = Object.keys(res).map(Number).sort((a, b) => a - b);\n    console.log(keys.map(k => `${k}:${res[k]}`).join(' '));\n} else { console.log(''); }\n",
        },
        "public_test_cases": [
            {"input": "1 2 2 3 1 4 2", "expected_output": "1:2 2:3 3:1 4:1"},
            {"input": "10 20 20 10 10 30", "expected_output": "10:3 20:2 30:1"},
        ],
        "hidden_test_cases": [
            {"input": "5 5 5 5", "expected_output": "5:4"},
            {"input": "1 2 3 4", "expected_output": "1:1 2:1 3:1 4:1"},
            {"input": "-1 -1 0 0 0 2", "expected_output": "-1:2 0:3 2:1"},
            {"input": "100", "expected_output": "100:1"},
        ],
    },

    # ─── 5. PALINDROME STRING ─────────────────────────────────────────────────
    {
        "title": "Palindrome String",
        "slug": "palindrome-string",
        "difficulty": "easy",
        "topics": ["strings", "two_pointers"],
        "required_skills": ["strings"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given a string s, determine if it is a palindrome (reads the same forward and backward). The check is case-sensitive.",
        "input_format": "A single string on one line.",
        "output_format": "'true' if palindrome, 'false' otherwise.",
        "constraints": ["1 ≤ s.length ≤ 10^4"],
        "examples": [
            {"input": "racecar", "output": "true", "explanation": "racecar reads the same backwards."},
            {"input": "hello", "output": "false", "explanation": "hello reversed is olleh."},
        ],
        "starter_code": {
            "python": "def is_palindrome(s: str) -> bool:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static boolean isPalindrome(String s) {\n        // Write your solution here\n        return false;\n    }\n}\n",
            "cpp": "#include <string>\nusing namespace std;\n\nclass Solution {\npublic:\n    bool isPalindrome(string s) {\n        // Write your solution here\n        return false;\n    }\n};\n",
            "javascript": "function isPalindrome(s) {\n    // Write your solution here\n    return false;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    s = sys.stdin.read().rstrip('\\r\\n')\n    print('true' if is_palindrome(s) else 'false')\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.hasNextLine() ? sc.nextLine().replaceAll(\"\\r|\\n\", \"\") : \"\";\n        System.out.println(Solution.isPalindrome(s) ? \"true\" : \"false\");\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string s; getline(cin, s);\n    while (!s.empty() && (s.back() == '\\r' || s.back() == '\\n')) s.pop_back();\n    Solution sol; cout << (sol.isPalindrome(s) ? \"true\" : \"false\") << endl;\n    return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').replace(/[\\r\\n]/g, '');\nconsole.log(isPalindrome(s) ? 'true' : 'false');\n",
        },
        "public_test_cases": [
            {"input": "racecar", "expected_output": "true"},
            {"input": "hello", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "madam", "expected_output": "true"},
            {"input": "a", "expected_output": "true"},
            {"input": "ab", "expected_output": "false"},
            {"input": "noon", "expected_output": "true"},
            {"input": "12321", "expected_output": "true"},
        ],
    },

    # ─── 6. REVERSE A STRING ──────────────────────────────────────────────────
    {
        "title": "Reverse a String",
        "slug": "reverse-string",
        "difficulty": "easy",
        "topics": ["strings", "basic_algorithms"],
        "required_skills": ["strings"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": "Given a string s, return the reversed string.",
        "input_format": "A single string on one line.",
        "output_format": "The reversed string.",
        "constraints": ["1 ≤ s.length ≤ 10^4"],
        "examples": [{"input": "interview", "output": "weivretni", "explanation": "String reversed."}],
        "starter_code": {
            "python": "def reverse_string(s: str) -> str:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static String reverseString(String s) {\n        // Write your solution here\n        return \"\";\n    }\n}\n",
            "cpp": "#include <string>\nusing namespace std;\n\nclass Solution {\npublic:\n    string reverseString(string s) {\n        // Write your solution here\n        return \"\";\n    }\n};\n",
            "javascript": "function reverseString(s) {\n    // Write your solution here\n    return \"\";\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    s = sys.stdin.read().rstrip('\\r\\n')\n    print(reverse_string(s))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.hasNextLine() ? sc.nextLine().replaceAll(\"\\r|\\n\", \"\") : \"\";\n        System.out.println(Solution.reverseString(s));\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string s; getline(cin, s);\n    while (!s.empty() && (s.back() == '\\r' || s.back() == '\\n')) s.pop_back();\n    Solution sol; cout << sol.reverseString(s) << endl;\n    return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').replace(/[\\r\\n]/g, '');\nconsole.log(reverseString(s));\n",
        },
        "public_test_cases": [
            {"input": "interview", "expected_output": "weivretni"},
            {"input": "code", "expected_output": "edoc"},
        ],
        "hidden_test_cases": [
            {"input": "a", "expected_output": "a"},
            {"input": "antigravity", "expected_output": "ytivargitna"},
            {"input": "12345", "expected_output": "54321"},
            {"input": "radar", "expected_output": "radar"},
        ],
    },

    # ─── 7. FIND MAXIMUM AND MINIMUM ─────────────────────────────────────────
    {
        "title": "Find Maximum and Minimum",
        "slug": "find-max-min",
        "difficulty": "easy",
        "topics": ["arrays", "basic_algorithms"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given an array of integers nums, find the maximum and minimum elements. Return them as a pair or list [max, min].",
        "input_format": "Space-separated integers representing the array.",
        "output_format": "Two space-separated integers: maximum followed by minimum.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [{"input": "3 1 4 1 5 9 2 6", "output": "9 1", "explanation": "Maximum is 9, minimum is 1."}],
        "starter_code": {
            "python": "def find_max_min(nums: list[int]) -> list[int]:\n    # Write your solution here (return [max_val, min_val])\n    pass\n",
            "java": "class Solution {\n    public static int[] findMaxMin(int[] nums) {\n        // Write your solution here: return new int[]{max, min}\n        return new int[]{0, 0};\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> findMaxMin(vector<int>& nums) {\n        // Return {max_val, min_val}\n        return {};\n    }\n};\n",
            "javascript": "function findMaxMin(nums) {\n    // Return [max, min]\n    return [];\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    if raw:\n        nums = list(map(int, raw.split()))\n        res = find_max_min(nums)\n        print(f\"{res[0]} {res[1]}\")\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        int[] res = Solution.findMaxMin(nums);\n        System.out.println(res[0] + \" \" + res[1]);\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; getline(cin, line); istringstream iss(line);\n    vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; auto res = sol.findMaxMin(nums);\n    cout << res[0] << \" \" << res[1] << endl;\n    return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nconst nums = input.split(/\\s+/).map(Number);\nconst res = findMaxMin(nums);\nconsole.log(`${res[0]} ${res[1]}`);\n",
        },
        "public_test_cases": [
            {"input": "3 1 4 1 5 9 2 6", "expected_output": "9 1"},
            {"input": "-10 0 100 -50 25", "expected_output": "100 -50"},
        ],
        "hidden_test_cases": [
            {"input": "42", "expected_output": "42 42"},
            {"input": "5 5 5 5", "expected_output": "5 5"},
            {"input": "-5 -20 -1 -100", "expected_output": "-1 -100"},
            {"input": "10 20 30 40 50", "expected_output": "50 10"},
        ],
    },

    # ─── 8. SUM OF ARRAY ELEMENTS ─────────────────────────────────────────────
    {
        "title": "Sum of Array Elements",
        "slug": "sum-of-array",
        "difficulty": "easy",
        "topics": ["arrays", "math"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given an array of integers nums, calculate and return the sum of all elements.",
        "input_format": "Space-separated integers.",
        "output_format": "A single integer.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [{"input": "1 2 3 4 5", "output": "15", "explanation": "1+2+3+4+5 = 15."}],
        "starter_code": {
            "python": "def array_sum(nums: list[int]) -> int:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static int arraySum(int[] nums) {\n        // Write your solution here\n        return 0;\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    int arraySum(vector<int>& nums) {\n        // Write your solution here\n        return 0;\n    }\n};\n",
            "javascript": "function arraySum(nums) {\n    // Write your solution here\n    return 0;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    nums = list(map(int, raw.split())) if raw else []\n    print(array_sum(nums))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(Solution.arraySum(nums));\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; getline(cin, line); istringstream iss(line);\n    vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; cout << sol.arraySum(nums) << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nconst nums = input ? input.split(/\\s+/).map(Number) : [];\nconsole.log(arraySum(nums));\n",
        },
        "public_test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "15"},
            {"input": "-1 1 -2 2 0", "expected_output": "0"},
        ],
        "hidden_test_cases": [
            {"input": "100", "expected_output": "100"},
            {"input": "-10 -20 -30", "expected_output": "-60"},
            {"input": "10 20 30 40 50 60", "expected_output": "210"},
        ],
    },

    # ─── 9. COUNT VOWELS AND CONSONANTS ───────────────────────────────────────
    {
        "title": "Count Vowels and Consonants",
        "slug": "count-vowels-and-consonants",
        "difficulty": "easy",
        "topics": ["strings", "basic_algorithms"],
        "required_skills": ["strings"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given a string s containing alphabetic characters and spaces, count the number of vowels (a, e, i, o, u case-insensitive) and consonants. Return [vowel_count, consonant_count].",
        "input_format": "A single string on one line.",
        "output_format": "Two space-separated integers: vowels followed by consonants.",
        "constraints": ["1 ≤ s.length ≤ 10^4"],
        "examples": [{"input": "Hello World", "output": "3 7", "explanation": "Vowels: e, o, o (3). Consonants: H, l, l, W, r, l, d (7)."}],
        "starter_code": {
            "python": "def count_vowels_consonants(s: str) -> list[int]:\n    # Write your solution here: return [vowel_count, consonant_count]\n    pass\n",
            "java": "class Solution {\n    public static int[] countVowelsConsonants(String s) {\n        // Return new int[]{vowels, consonants}\n        return new int[]{0, 0};\n    }\n}\n",
            "cpp": "#include <string>\n#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> countVowelsConsonants(string s) {\n        // Return {vowels, consonants}\n        return {0, 0};\n    }\n};\n",
            "javascript": "function countVowelsConsonants(s) {\n    // Return [vowels, consonants]\n    return [0, 0];\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    s = sys.stdin.read().rstrip('\\r\\n')\n    res = count_vowels_consonants(s)\n    print(f\"{res[0]} {res[1]}\")\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.hasNextLine() ? sc.nextLine().replaceAll(\"\\r|\\n\", \"\") : \"\";\n        int[] res = Solution.countVowelsConsonants(s);\n        System.out.println(res[0] + \" \" + res[1]);\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <string>\n#include <vector>\nusing namespace std;\nint main() {\n    string s; getline(cin, s);\n    while (!s.empty() && (s.back() == '\\r' || s.back() == '\\n')) s.pop_back();\n    Solution sol; auto res = sol.countVowelsConsonants(s);\n    cout << res[0] << \" \" << res[1] << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').replace(/[\\r\\n]/g, '');\nconst res = countVowelsConsonants(s);\nconsole.log(`${res[0]} ${res[1]}`);\n",
        },
        "public_test_cases": [
            {"input": "Hello World", "expected_output": "3 7"},
            {"input": "AEIOU", "expected_output": "5 0"},
        ],
        "hidden_test_cases": [
            {"input": "bcdfgh", "expected_output": "0 6"},
            {"input": "Interview Platform", "expected_output": "6 11"},
            {"input": "a", "expected_output": "1 0"},
            {"input": "z", "expected_output": "0 1"},
        ],
    },

    # ─── 10. CHECK IF ARRAY IS SORTED ─────────────────────────────────────────
    {
        "title": "Check if Array is Sorted",
        "slug": "is-array-sorted",
        "difficulty": "easy",
        "topics": ["arrays", "basic_algorithms"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given an array of integers nums, determine whether the array is sorted in non-decreasing order. Return true or false.",
        "input_format": "Space-separated integers.",
        "output_format": "'true' or 'false'.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [
            {"input": "1 2 3 4 5", "output": "true", "explanation": "Array is sorted."},
            {"input": "1 3 2 4 5", "output": "false", "explanation": "3 is greater than 2."},
        ],
        "starter_code": {
            "python": "def is_sorted(nums: list[int]) -> bool:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static boolean isSorted(int[] nums) {\n        // Write your solution here\n        return false;\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    bool isSorted(vector<int>& nums) {\n        // Write your solution here\n        return false;\n    }\n};\n",
            "javascript": "function isSorted(nums) {\n    // Write your solution here\n    return false;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    nums = list(map(int, raw.split())) if raw else []\n    print('true' if is_sorted(nums) else 'false')\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(Solution.isSorted(nums) ? \"true\" : \"false\");\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; getline(cin, line); istringstream iss(line);\n    vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; cout << (sol.isSorted(nums) ? \"true\" : \"false\") << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nconst nums = input ? input.split(/\\s+/).map(Number) : [];\nconsole.log(isSorted(nums) ? 'true' : 'false');\n",
        },
        "public_test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "true"},
            {"input": "1 3 2 4 5", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "10", "expected_output": "true"},
            {"input": "1 1 1 1", "expected_output": "true"},
            {"input": "5 4 3 2 1", "expected_output": "false"},
            {"input": "-10 -5 0 5 10", "expected_output": "true"},
        ],
    },

    # ─── 11. LINEAR SEARCH INDEX ──────────────────────────────────────────────
    {
        "title": "Linear Search Index",
        "slug": "linear-search-index",
        "difficulty": "easy",
        "topics": ["arrays", "searching"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given an array of integers nums and a target integer, find the first 0-based index of target in nums. Return -1 if not found.",
        "input_format": "Line 1: space-separated integers (array)\nLine 2: target integer",
        "output_format": "A single integer.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i], target ≤ 10^4"],
        "examples": [{"input": "4 2 7 1 9\n7", "output": "2", "explanation": "7 is at index 2."}],
        "starter_code": {
            "python": "def find_index(nums: list[int], target: int) -> int:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static int findIndex(int[] nums, int target) {\n        // Write your solution here\n        return -1;\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    int findIndex(vector<int>& nums, int target) {\n        // Write your solution here\n        return -1;\n    }\n};\n",
            "javascript": "function findIndex(nums, target) {\n    // Write your solution here\n    return -1;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    lines = sys.stdin.read().strip().split('\\n')\n    nums = list(map(int, lines[0].split()))\n    target = int(lines[1].strip())\n    print(find_index(nums, target))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        int target = Integer.parseInt(sc.nextLine().trim());\n        System.out.println(Solution.findIndex(nums, target));\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; getline(cin, line); istringstream iss(line);\n    vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    int target; cin >> target;\n    Solution sol; cout << sol.findIndex(nums, target) << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst lines = fs.readFileSync(0, 'utf-8').trim().split('\\n');\nconst nums = lines[0].split(/\\s+/).map(Number);\nconst target = Number(lines[1].trim());\nconsole.log(findIndex(nums, target));\n",
        },
        "public_test_cases": [
            {"input": "4 2 7 1 9\n7", "expected_output": "2"},
            {"input": "10 20 30\n50", "expected_output": "-1"},
        ],
        "hidden_test_cases": [
            {"input": "5\n5", "expected_output": "0"},
            {"input": "1 2 2 2 3\n2", "expected_output": "1"},
            {"input": "-5 0 5\n-5", "expected_output": "0"},
            {"input": "-5 0 5\n5", "expected_output": "2"},
        ],
    },

    # ─── 12. MOVE ZEROES TO END ───────────────────────────────────────────────
    {
        "title": "Move Zeroes to End",
        "slug": "move-zeroes-to-end",
        "difficulty": "easy",
        "topics": ["arrays", "two_pointers"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given an integer array nums, move all 0's to the end while maintaining the relative order of the non-zero elements.",
        "input_format": "Space-separated integers.",
        "output_format": "Space-separated integers.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [{"input": "0 1 0 3 12", "output": "1 3 12 0 0", "explanation": "Zeroes shifted to end."}],
        "starter_code": {
            "python": "def move_zeroes(nums: list[int]) -> list[int]:\n    # Write your solution here (modify in place or return array)\n    pass\n",
            "java": "class Solution {\n    public static int[] moveZeroes(int[] nums) {\n        // Write your solution here\n        return nums;\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> moveZeroes(vector<int>& nums) {\n        // Write your solution here\n        return nums;\n    }\n};\n",
            "javascript": "function moveZeroes(nums) {\n    // Write your solution here\n    return nums;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    nums = list(map(int, raw.split())) if raw else []\n    res = move_zeroes(nums)\n    if res is None: res = nums\n    print(' '.join(map(str, res)))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        int[] res = Solution.moveZeroes(nums);\n        if (res == null) res = nums;\n        StringBuilder sb = new StringBuilder();\n        for (int i = 0; i < res.length; i++) { if (i > 0) sb.append(\" \"); sb.append(res[i]); }\n        System.out.println(sb.toString());\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; getline(cin, line); istringstream iss(line);\n    vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; auto res = sol.moveZeroes(nums);\n    if (res.empty() && !nums.empty()) res = nums;\n    for (size_t i = 0; i < res.size(); ++i) { if (i > 0) cout << \" \"; cout << res[i]; }\n    cout << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nconst nums = input.split(/\\s+/).map(Number);\nlet res = moveZeroes(nums);\nif (!res) res = nums;\nconsole.log(res.join(' '));\n",
        },
        "public_test_cases": [
            {"input": "0 1 0 3 12", "expected_output": "1 3 12 0 0"},
            {"input": "0", "expected_output": "0"},
        ],
        "hidden_test_cases": [
            {"input": "1 2 3", "expected_output": "1 2 3"},
            {"input": "0 0 0 1", "expected_output": "1 0 0 0"},
            {"input": "4 0 5 0 0 6", "expected_output": "4 5 6 0 0 0"},
        ],
    },

    # ─── 13. VALID ANAGRAM ────────────────────────────────────────────────────
    {
        "title": "Valid Anagram",
        "slug": "valid-anagram",
        "difficulty": "easy",
        "topics": ["strings", "hashing"],
        "required_skills": ["strings"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given two strings s and t, return true if t is an anagram of s (same characters with identical frequencies), and false otherwise.",
        "input_format": "Line 1: first string s\nLine 2: second string t",
        "output_format": "'true' or 'false'.",
        "constraints": ["1 ≤ s.length, t.length ≤ 10^4"],
        "examples": [{"input": "anagram\nnagaram", "output": "true", "explanation": "Both contain same letters."}],
        "starter_code": {
            "python": "def is_anagram(s: str, t: str) -> bool:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static boolean isAnagram(String s, String t) {\n        // Write your solution here\n        return false;\n    }\n}\n",
            "cpp": "#include <string>\nusing namespace std;\n\nclass Solution {\npublic:\n    bool isAnagram(string s, string t) {\n        // Write your solution here\n        return false;\n    }\n};\n",
            "javascript": "function isAnagram(s, t) {\n    // Write your solution here\n    return false;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    lines = sys.stdin.read().strip().split('\\n')\n    s = lines[0].strip()\n    t = lines[1].strip() if len(lines) > 1 else ''\n    print('true' if is_anagram(s, t) else 'false')\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.nextLine().trim();\n        String t = sc.hasNextLine() ? sc.nextLine().trim() : \"\";\n        System.out.println(Solution.isAnagram(s, t) ? \"true\" : \"false\");\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string s, t; getline(cin, s); getline(cin, t);\n    Solution sol; cout << (sol.isAnagram(s, t) ? \"true\" : \"false\") << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst lines = fs.readFileSync(0, 'utf-8').trim().split('\\n');\nconst s = lines[0].trim();\nconst t = lines[1] ? lines[1].trim() : '';\nconsole.log(isAnagram(s, t) ? 'true' : 'false');\n",
        },
        "public_test_cases": [
            {"input": "anagram\nnagaram", "expected_output": "true"},
            {"input": "rat\ncar", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "listen\nsilent", "expected_output": "true"},
            {"input": "a\na", "expected_output": "true"},
            {"input": "ab\na", "expected_output": "false"},
            {"input": "triangle\nintegral", "expected_output": "true"},
        ],
    },

    # ─── 14. FACTORIAL OF A NUMBER ────────────────────────────────────────────
    {
        "title": "Factorial of a Number",
        "slug": "factorial-of-number",
        "difficulty": "easy",
        "topics": ["math", "recursion"],
        "required_skills": ["math"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given a non-negative integer n, compute and return its factorial (n!). For n = 0, factorial is 1.",
        "input_format": "A single integer n.",
        "output_format": "A single integer.",
        "constraints": ["0 ≤ n ≤ 12"],
        "examples": [{"input": "5", "output": "120", "explanation": "5! = 5 * 4 * 3 * 2 * 1 = 120."}],
        "starter_code": {
            "python": "def factorial(n: int) -> int:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static int factorial(int n) {\n        // Write your solution here\n        return 1;\n    }\n}\n",
            "cpp": "class Solution {\npublic:\n    int factorial(int n) {\n        // Write your solution here\n        return 1;\n    }\n};\n",
            "javascript": "function factorial(n) {\n    // Write your solution here\n    return 1;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    n = int(raw) if raw else 0\n    print(factorial(n))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.nextInt();\n        System.out.println(Solution.factorial(n));\n    }\n}\n",
            "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    int n; cin >> n; Solution sol; cout << sol.factorial(n) << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(factorial(n));\n",
        },
        "public_test_cases": [
            {"input": "5", "expected_output": "120"},
            {"input": "0", "expected_output": "1"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected_output": "1"},
            {"input": "3", "expected_output": "6"},
            {"input": "6", "expected_output": "720"},
            {"input": "10", "expected_output": "3628800"},
        ],
    },

    # ─── 15. FIBONACCI NUMBER ─────────────────────────────────────────────────
    {
        "title": "Fibonacci Number",
        "slug": "fibonacci-number",
        "difficulty": "easy",
        "topics": ["math", "dynamic_programming"],
        "required_skills": ["math"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given integer n, calculate the n-th Fibonacci number F(n). The sequence begins: F(0) = 0, F(1) = 1, and F(n) = F(n-1) + F(n-2).",
        "input_format": "A single integer n.",
        "output_format": "A single integer F(n).",
        "constraints": ["0 ≤ n ≤ 30"],
        "examples": [{"input": "4", "output": "3", "explanation": "F(4) = F(3) + F(2) = 2 + 1 = 3."}],
        "starter_code": {
            "python": "def fibonacci(n: int) -> int:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static int fibonacci(int n) {\n        // Write your solution here\n        return 0;\n    }\n}\n",
            "cpp": "class Solution {\npublic:\n    int fibonacci(int n) {\n        // Write your solution here\n        return 0;\n    }\n};\n",
            "javascript": "function fibonacci(n) {\n    // Write your solution here\n    return 0;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    n = int(raw) if raw else 0\n    print(fibonacci(n))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.nextInt();\n        System.out.println(Solution.fibonacci(n));\n    }\n}\n",
            "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    int n; cin >> n; Solution sol; cout << sol.fibonacci(n) << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(fibonacci(n));\n",
        },
        "public_test_cases": [
            {"input": "2", "expected_output": "1"},
            {"input": "4", "expected_output": "3"},
        ],
        "hidden_test_cases": [
            {"input": "0", "expected_output": "0"},
            {"input": "1", "expected_output": "1"},
            {"input": "7", "expected_output": "13"},
            {"input": "10", "expected_output": "55"},
        ],
    },

    # ─── 16. PRIME NUMBER CHECK ───────────────────────────────────────────────
    {
        "title": "Prime Number Check",
        "slug": "check-prime-number",
        "difficulty": "easy",
        "topics": ["math", "basic_algorithms"],
        "required_skills": ["math"],
        "expected_complexity": {"time": "O(sqrt(n))", "space": "O(1)"},
        "description": "Given an integer n, determine whether n is a prime number. Return true or false.",
        "input_format": "A single integer n.",
        "output_format": "'true' or 'false'.",
        "constraints": ["1 ≤ n ≤ 10^6"],
        "examples": [
            {"input": "7", "output": "true", "explanation": "7 has only divisors 1 and 7."},
            {"input": "4", "output": "false", "explanation": "4 is divisible by 2."},
        ],
        "starter_code": {
            "python": "def is_prime(n: int) -> bool:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static boolean isPrime(int n) {\n        // Write your solution here\n        return false;\n    }\n}\n",
            "cpp": "class Solution {\npublic:\n    bool isPrime(int n) {\n        // Write your solution here\n        return false;\n    }\n};\n",
            "javascript": "function isPrime(n) {\n    // Write your solution here\n    return false;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    n = int(raw) if raw else 0\n    print('true' if is_prime(n) else 'false')\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.nextInt();\n        System.out.println(Solution.isPrime(n) ? \"true\" : \"false\");\n    }\n}\n",
            "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    int n; cin >> n; Solution sol; cout << (sol.isPrime(n) ? \"true\" : \"false\") << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(isPrime(n) ? 'true' : 'false');\n",
        },
        "public_test_cases": [
            {"input": "7", "expected_output": "true"},
            {"input": "4", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected_output": "false"},
            {"input": "2", "expected_output": "true"},
            {"input": "17", "expected_output": "true"},
            {"input": "25", "expected_output": "false"},
            {"input": "97", "expected_output": "true"},
        ],
    },

    # ─── 17. FIRST NON-REPEATING CHARACTER ────────────────────────────────────
    {
        "title": "First Non-Repeating Character",
        "slug": "first-non-repeating-char",
        "difficulty": "easy",
        "topics": ["strings", "hashing"],
        "required_skills": ["strings", "hashing"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given a string s of lowercase letters, find the first non-repeating character. Return the character, or '$' if no non-repeating character exists.",
        "input_format": "A single string on one line.",
        "output_format": "A single character.",
        "constraints": ["1 ≤ s.length ≤ 10^4"],
        "examples": [
            {"input": "swiss", "output": "w", "explanation": "'w' is the first unique character."},
            {"input": "aabb", "output": "$", "explanation": "All characters repeat."},
        ],
        "starter_code": {
            "python": "def first_unique_char(s: str) -> str:\n    # Write your solution here (return '$' if none)\n    pass\n",
            "java": "class Solution {\n    public static char firstUniqueChar(String s) {\n        // Return character or '$'\n        return '$';\n    }\n}\n",
            "cpp": "#include <string>\nusing namespace std;\n\nclass Solution {\npublic:\n    char firstUniqueChar(string s) {\n        // Return character or '$'\n        return '$';\n    }\n};\n",
            "javascript": "function firstUniqueChar(s) {\n    // Return character or '$'\n    return '$';\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    s = sys.stdin.read().rstrip('\\r\\n')\n    res = first_unique_char(s)\n    print(res if res else '$')\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.hasNextLine() ? sc.nextLine().replaceAll(\"\\r|\\n\", \"\") : \"\";\n        System.out.println(Solution.firstUniqueChar(s));\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string s; getline(cin, s);\n    while (!s.empty() && (s.back() == '\\r' || s.back() == '\\n')) s.pop_back();\n    Solution sol; cout << sol.firstUniqueChar(s) << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').replace(/[\\r\\n]/g, '');\nconsole.log(firstUniqueChar(s));\n",
        },
        "public_test_cases": [
            {"input": "swiss", "expected_output": "w"},
            {"input": "aabb", "expected_output": "$"},
        ],
        "hidden_test_cases": [
            {"input": "z", "expected_output": "z"},
            {"input": "interview", "expected_output": "n"},
            {"input": "abacabad", "expected_output": "c"},
        ],
    },

    # ─── 18. MISSING NUMBER IN RANGE ──────────────────────────────────────────
    {
        "title": "Missing Number in Range",
        "slug": "missing-number",
        "difficulty": "easy",
        "topics": ["arrays", "math"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": "Given an array nums containing n distinct numbers in the range [0, n], return the only number in the range that is missing from the array.",
        "input_format": "Space-separated integers.",
        "output_format": "A single integer.",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "All elements are unique"],
        "examples": [{"input": "3 0 1", "output": "2", "explanation": "Range is [0,3], 2 is missing."}],
        "starter_code": {
            "python": "def missing_number(nums: list[int]) -> int:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static int missingNumber(int[] nums) {\n        // Write your solution here\n        return 0;\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    int missingNumber(vector<int>& nums) {\n        // Write your solution here\n        return 0;\n    }\n};\n",
            "javascript": "function missingNumber(nums) {\n    // Write your solution here\n    return 0;\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    raw = sys.stdin.read().strip()\n    nums = list(map(int, raw.split())) if raw else []\n    print(missing_number(nums))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(Solution.missingNumber(nums));\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; getline(cin, line); istringstream iss(line);\n    vector<int> nums; int x; while (iss >> x) nums.push_back(x);\n    Solution sol; cout << sol.missingNumber(nums) << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nconst nums = input.split(/\\s+/).map(Number);\nconsole.log(missingNumber(nums));\n",
        },
        "public_test_cases": [
            {"input": "3 0 1", "expected_output": "2"},
            {"input": "0 1", "expected_output": "2"},
        ],
        "hidden_test_cases": [
            {"input": "9 6 4 2 3 5 7 0 1", "expected_output": "8"},
            {"input": "0", "expected_output": "1"},
            {"input": "1", "expected_output": "0"},
        ],
    },

    # ─── 19. MERGE TWO SORTED ARRAYS ──────────────────────────────────────────
    {
        "title": "Merge Two Sorted Arrays",
        "slug": "merge-two-sorted-arrays",
        "difficulty": "easy",
        "topics": ["arrays", "two_pointers"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n + m)", "space": "O(n + m)"},
        "description": "Given two sorted integer arrays arr1 and arr2, merge them into a single sorted array and return it.",
        "input_format": "Line 1: space-separated integers for arr1\nLine 2: space-separated integers for arr2",
        "output_format": "Space-separated integers of merged array.",
        "constraints": ["1 ≤ arr1.length, arr2.length ≤ 10^4"],
        "examples": [{"input": "1 3 5\n2 4 6", "output": "1 2 3 4 5 6", "explanation": "Merged sorted list."}],
        "starter_code": {
            "python": "def merge_sorted(arr1: list[int], arr2: list[int]) -> list[int]:\n    # Write your solution here\n    pass\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public static int[] mergeSorted(int[] arr1, int[] arr2) {\n        // Write your solution here\n        return new int[]{};\n    }\n}\n",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> mergeSorted(vector<int>& arr1, vector<int>& arr2) {\n        // Write your solution here\n        return {};\n    }\n};\n",
            "javascript": "function mergeSorted(arr1, arr2) {\n    // Write your solution here\n    return [];\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    lines = sys.stdin.read().strip().split('\\n')\n    arr1 = list(map(int, lines[0].split())) if len(lines) > 0 and lines[0].strip() else []\n    arr2 = list(map(int, lines[1].split())) if len(lines) > 1 and lines[1].strip() else []\n    res = merge_sorted(arr1, arr2)\n    print(' '.join(map(str, res)))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] a1 = Arrays.stream(sc.nextLine().trim().split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray();\n        int[] a2 = sc.hasNextLine() ? Arrays.stream(sc.nextLine().trim().split(\"\\\\s+\")).mapToInt(Integer::parseInt).toArray() : new int[]{};\n        int[] res = Solution.mergeSorted(a1, a2);\n        StringBuilder sb = new StringBuilder();\n        for (int i = 0; i < res.length; i++) { if (i > 0) sb.append(\" \"); sb.append(res[i]); }\n        System.out.println(sb.toString());\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\nint main() {\n    string l1, l2; getline(cin, l1); getline(cin, l2);\n    vector<int> a1, a2; int x;\n    istringstream i1(l1); while (i1 >> x) a1.push_back(x);\n    istringstream i2(l2); while (i2 >> x) a2.push_back(x);\n    Solution sol; auto res = sol.mergeSorted(a1, a2);\n    for (size_t i = 0; i < res.size(); ++i) { if (i > 0) cout << \" \"; cout << res[i]; }\n    cout << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst lines = fs.readFileSync(0, 'utf-8').trim().split('\\n');\nconst a1 = lines[0] ? lines[0].split(/\\s+/).map(Number) : [];\nconst a2 = lines[1] ? lines[1].split(/\\s+/).map(Number) : [];\nconst res = mergeSorted(a1, a2);\nconsole.log(res.join(' '));\n",
        },
        "public_test_cases": [
            {"input": "1 3 5\n2 4 6", "expected_output": "1 2 3 4 5 6"},
            {"input": "1 2\n3 4", "expected_output": "1 2 3 4"},
        ],
        "hidden_test_cases": [
            {"input": "5\n1", "expected_output": "1 5"},
            {"input": "1 5 9\n2 3 8 10", "expected_output": "1 2 3 5 8 9 10"},
            {"input": "-5 -2 0\n-3 1 4", "expected_output": "-5 -3 -2 0 1 4"},
        ],
    },

    # ─── 20. CAPITALIZE WORDS ─────────────────────────────────────────────────
    {
        "title": "Capitalize Words",
        "slug": "capitalize-words",
        "difficulty": "easy",
        "topics": ["strings", "basic_algorithms"],
        "required_skills": ["strings"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": "Given a sentence string s of space-separated words, capitalize the first letter of every word and return the resulting sentence.",
        "input_format": "A single sentence on one line.",
        "output_format": "The sentence with each word capitalized.",
        "constraints": ["1 ≤ s.length ≤ 10^4"],
        "examples": [{"input": "hello world from ai", "output": "Hello World From Ai", "explanation": "Initial letters capitalized."}],
        "starter_code": {
            "python": "def capitalize_words(s: str) -> str:\n    # Write your solution here\n    pass\n",
            "java": "class Solution {\n    public static String capitalizeWords(String s) {\n        // Write your solution here\n        return \"\";\n    }\n}\n",
            "cpp": "#include <string>\nusing namespace std;\n\nclass Solution {\npublic:\n    string capitalizeWords(string s) {\n        // Write your solution here\n        return \"\";\n    }\n};\n",
            "javascript": "function capitalizeWords(s) {\n    // Write your solution here\n    return \"\";\n}\n",
        },
        "driver_code": {
            "python": "if __name__ == '__main__':\n    import sys\n    s = sys.stdin.read().rstrip('\\r\\n')\n    print(capitalize_words(s))\n",
            "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.hasNextLine() ? sc.nextLine().replaceAll(\"\\r|\\n\", \"\") : \"\";\n        System.out.println(Solution.capitalizeWords(s));\n    }\n}\n",
            "cpp": "#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string s; getline(cin, s);\n    while (!s.empty() && (s.back() == '\\r' || s.back() == '\\n')) s.pop_back();\n    Solution sol; cout << sol.capitalizeWords(s) << endl; return 0;\n}\n",
            "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').replace(/[\\r\\n]/g, '');\nconsole.log(capitalizeWords(s));\n",
        },
        "public_test_cases": [
            {"input": "hello world from ai", "expected_output": "Hello World From Ai"},
            {"input": "python programming", "expected_output": "Python Programming"},
        ],
        "hidden_test_cases": [
            {"input": "interview", "expected_output": "Interview"},
            {"input": "first non repeating char", "expected_output": "First Non Repeating Char"},
            {"input": "a b c", "expected_output": "A B C"},
        ],
    },
]


class Command(BaseCommand):
    help = 'Seeds coding problem bank with 20 simple, generic mock interview questions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing problems and test cases before seeding.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = CodingProblem.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing problems.'))

        created = 0
        updated = 0

        for p in PROBLEMS:
            prob, was_created = CodingProblem.objects.update_or_create(
                slug=p['slug'],
                defaults={
                    'title':               p['title'],
                    'difficulty':          p['difficulty'],
                    'topics':              p.get('topics', []),
                    'required_skills':     p.get('required_skills', []),
                    'expected_complexity': p.get('expected_complexity', {}),
                    'description':         p['description'],
                    'input_format':        p.get('input_format', ''),
                    'output_format':       p.get('output_format', ''),
                    'constraints':         p.get('constraints', []),
                    'examples':            p.get('examples', []),
                    'starter_code':        p.get('starter_code', {}),
                    'driver_code':         p.get('driver_code', {}),
                    'is_active':           True,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1
                # Remove old test cases so we re-seed fresh
                prob.test_cases.all().delete()

            # Seed public test cases
            for i, tc in enumerate(p.get('public_test_cases', []), 1):
                CodingTestCase.objects.create(
                    problem=prob,
                    input_data=tc['input'],
                    expected_output=tc['expected_output'],
                    is_hidden=False,
                    order=i,
                )

            # Seed hidden test cases
            offset = len(p.get('public_test_cases', []))
            for i, tc in enumerate(p.get('hidden_test_cases', []), 1):
                CodingTestCase.objects.create(
                    problem=prob,
                    input_data=tc['input'],
                    expected_output=tc['expected_output'],
                    is_hidden=True,
                    order=offset + i,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'[OK] Seeded {len(PROBLEMS)} problems: {created} created, {updated} updated.'
            )
        )
