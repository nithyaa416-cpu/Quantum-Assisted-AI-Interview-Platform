"""
Management command: seed_coding_problems

Seeds the coding problem bank with 40+ problems across all major DSA topics.
Each problem has:
- Title, slug, description, difficulty
- Input/output format, constraints, examples
- Python, Java, and C++ starter code
- Public and hidden test cases
- Topics and expected complexity

Usage:
    python manage.py seed_coding_problems           # Skip existing
    python manage.py seed_coding_problems --clear   # Delete all then reseed
"""
import json
from django.core.management.base import BaseCommand
from apps.assessments.models import CodingProblem, CodingTestCase

# ── Problem bank ──────────────────────────────────────────────────────────────

PROBLEMS = [

    # ─── ARRAYS ──────────────────────────────────────────────────────────────
    {
        "title": "Two Sum",
        "slug": "two-sum",
        "difficulty": "easy",
        "topics": ["arrays", "hashing"],
        "required_skills": ["python", "data_structures"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": (
            "Given an array of integers `nums` and an integer `target`, return indices of the two numbers "
            "such that they add up to `target`.\n\n"
            "You may assume that each input has **exactly one** solution, and you may not use the same element twice."
        ),
        "input_format": "Line 1: space-separated integers (the array)\nLine 2: target integer",
        "output_format": "Two space-separated indices (0-indexed)",
        "constraints": ["2 ≤ nums.length ≤ 10^4", "-10^9 ≤ nums[i] ≤ 10^9", "Exactly one valid answer exists"],
        "examples": [
            {"input": "2 7 11 15\n9", "output": "0 1", "explanation": "nums[0] + nums[1] = 2 + 7 = 9"},
            {"input": "3 2 4\n6", "output": "1 2", "explanation": "nums[1] + nums[2] = 2 + 4 = 6"},
        ],
        "starter_code": {
            "python": "def two_sum(nums, target):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split()\nn = len(data) - 1\nnums = list(map(int, data[:n]))\ntarget = int(data[n])\nresult = two_sum(nums, target)\nprint(*result)\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int[] twoSum(int[] nums, int target) {\n        // Write your solution here\n        return new int[]{};\n    }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String[] parts = sc.nextLine().trim().split(\" \");\n        int target = Integer.parseInt(sc.nextLine().trim());\n        int[] nums = Arrays.stream(parts).mapToInt(Integer::parseInt).toArray();\n        int[] res = twoSum(nums, target);\n        System.out.println(res[0] + \" \" + res[1]);\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvector<int> twoSum(vector<int>& nums, int target) {\n    // Write your solution here\n    return {};\n}\nint main() {\n    string line; getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums; int x;\n    while (iss >> x) nums.push_back(x);\n    int target; cin >> target;\n    auto res = twoSum(nums, target);\n    cout << res[0] << \" \" << res[1] << endl;\n    return 0;\n}\n",
        },
        "public_test_cases": [
            {"input": "2 7 11 15\n9", "expected_output": "0 1"},
            {"input": "3 2 4\n6", "expected_output": "1 2"},
        ],
        "hidden_test_cases": [
            {"input": "1 2 3 4 5\n9", "expected_output": "3 4"},
            {"input": "0 4 3 0\n0", "expected_output": "0 3"},
        ],
    },
    {
        "title": "Maximum Subarray",
        "slug": "maximum-subarray",
        "difficulty": "easy",
        "topics": ["arrays", "dynamic_programming"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "Given an integer array `nums`, find the contiguous subarray (containing at least one number) "
            "which has the largest sum and return its sum."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "A single integer — the maximum subarray sum",
        "constraints": ["1 ≤ nums.length ≤ 10^5", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [
            {"input": "-2 1 -3 4 -1 2 1 -5 4", "output": "6", "explanation": "Subarray [4,-1,2,1] has the largest sum = 6"},
        ],
        "starter_code": {
            "python": "def max_subarray(nums):\n    # Write your solution here\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.read().split()))\nprint(max_subarray(nums))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int maxSubArray(int[] nums) {\n        // Write your solution here\n        return 0;\n    }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(maxSubArray(nums));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint maxSubArray(vector<int>& nums) {\n    // Write your solution here\n    return 0;\n}\nint main() {\n    vector<int> nums;\n    int x;\n    while (cin >> x) nums.push_back(x);\n    cout << maxSubArray(nums) << endl;\n    return 0;\n}\n",
        },
        "public_test_cases": [
            {"input": "-2 1 -3 4 -1 2 1 -5 4", "expected_output": "6"},
            {"input": "1", "expected_output": "1"},
        ],
        "hidden_test_cases": [
            {"input": "5 4 -1 7 8", "expected_output": "23"},
            {"input": "-1", "expected_output": "-1"},
        ],
    },
    {
        "title": "Best Time to Buy and Sell Stock",
        "slug": "best-time-buy-sell-stock",
        "difficulty": "easy",
        "topics": ["arrays", "greedy"],
        "required_skills": ["arrays"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "You are given an array `prices` where `prices[i]` is the price of a given stock on the ith day.\n\n"
            "Find the maximum profit you can achieve. Return 0 if no profit is possible."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "A single integer — maximum profit",
        "constraints": ["1 ≤ prices.length ≤ 10^5", "0 ≤ prices[i] ≤ 10^4"],
        "examples": [
            {"input": "7 1 5 3 6 4", "output": "5", "explanation": "Buy on day 2 (price=1), sell on day 5 (price=6). Profit = 5."},
        ],
        "starter_code": {
            "python": "def max_profit(prices):\n    # Write your solution here\n    pass\n\nimport sys\nprices = list(map(int, sys.stdin.read().split()))\nprint(max_profit(prices))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int maxProfit(int[] prices) {\n        // Write your solution here\n        return 0;\n    }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] prices = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(maxProfit(prices));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint maxProfit(vector<int>& prices) {\n    // Write your solution here\n    return 0;\n}\nint main() {\n    vector<int> p; int x;\n    while (cin >> x) p.push_back(x);\n    cout << maxProfit(p) << endl;\n    return 0;\n}\n",
        },
        "public_test_cases": [
            {"input": "7 1 5 3 6 4", "expected_output": "5"},
            {"input": "7 6 4 3 1", "expected_output": "0"},
        ],
        "hidden_test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "4"},
            {"input": "3 3 3", "expected_output": "0"},
        ],
    },
    {
        "title": "Product of Array Except Self",
        "slug": "product-except-self",
        "difficulty": "medium",
        "topics": ["arrays"],
        "required_skills": ["arrays", "prefix_products"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": (
            "Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to "
            "the product of all elements of `nums` except `nums[i]`.\n\n"
            "You must solve without using division and in O(n) time."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "Space-separated integers representing the result array",
        "constraints": ["2 ≤ nums.length ≤ 10^5", "-30 ≤ nums[i] ≤ 30", "Guaranteed non-zero result"],
        "examples": [
            {"input": "1 2 3 4", "output": "24 12 8 6"},
        ],
        "starter_code": {
            "python": "def product_except_self(nums):\n    # Write your solution here\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.read().split()))\nprint(*product_except_self(nums))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int[] productExceptSelf(int[] nums) {\n        return new int[]{};\n    }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(Arrays.toString(productExceptSelf(nums)).replaceAll(\"[\\\\[\\\\],]\", \"\").trim());\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvector<int> productExceptSelf(vector<int>& nums) { return {}; }\nint main() {\n    vector<int> n; int x;\n    while (cin >> x) n.push_back(x);\n    auto r = productExceptSelf(n);\n    for (int i=0;i<r.size();i++) cout << r[i] << (i+1<r.size()?' ':'\\n');\n}\n",
        },
        "public_test_cases": [
            {"input": "1 2 3 4", "expected_output": "24 12 8 6"},
            {"input": "-1 1 0 -3 3", "expected_output": "0 0 9 0 0"},
        ],
        "hidden_test_cases": [
            {"input": "2 3 4 5", "expected_output": "60 40 30 24"},
        ],
    },
    {
        "title": "Find Peak Element",
        "slug": "find-peak-element",
        "difficulty": "medium",
        "topics": ["arrays", "binary_search"],
        "required_skills": ["binary_search"],
        "expected_complexity": {"time": "O(log n)", "space": "O(1)"},
        "description": (
            "A peak element is an element that is strictly greater than its neighbors.\n\n"
            "Given an integer array `nums`, find a peak element and return its index. "
            "If multiple peaks exist, return any of them. Assume `nums[-1] = nums[n] = -∞`."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "A single integer — the index of a peak element",
        "constraints": ["1 ≤ nums.length ≤ 1000", "-2^31 ≤ nums[i] ≤ 2^31 - 1", "nums[i] ≠ nums[i+1] for all valid i"],
        "examples": [
            {"input": "1 2 3 1", "output": "2"},
            {"input": "1 2 1 3 5 6 4", "output": "5"},
        ],
        "starter_code": {
            "python": "def find_peak_element(nums):\n    # Write your solution here\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.read().split()))\nprint(find_peak_element(nums))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int findPeakElement(int[] nums) { return -1; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(findPeakElement(nums));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint findPeakElement(vector<int>& nums) { return -1; }\nint main() {\n    vector<int> n; int x;\n    while (cin >> x) n.push_back(x);\n    cout << findPeakElement(n) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 2 3 1", "expected_output": "2"},
            {"input": "1 2 1 3 5 6 4", "expected_output": "5"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected_output": "0"},
            {"input": "3 2 1", "expected_output": "0"},
        ],
    },

    # ─── STRINGS ─────────────────────────────────────────────────────────────
    {
        "title": "Valid Anagram",
        "slug": "valid-anagram",
        "difficulty": "easy",
        "topics": ["strings", "hashing"],
        "required_skills": ["strings"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "Given two strings `s` and `t`, return `true` if `t` is an anagram of `s`, and `false` otherwise.\n\n"
            "An anagram is a word formed by rearranging the letters of a different word."
        ),
        "input_format": "Line 1: string s\nLine 2: string t",
        "output_format": "true or false",
        "constraints": ["1 ≤ s.length, t.length ≤ 5 × 10^4", "s and t consist of lowercase English letters"],
        "examples": [
            {"input": "anagram\nnagaram", "output": "true"},
            {"input": "rat\ncar", "output": "false"},
        ],
        "starter_code": {
            "python": "def is_anagram(s, t):\n    # Write your solution here\n    pass\n\nimport sys\nlines = sys.stdin.read().strip().split('\\n')\nprint('true' if is_anagram(lines[0], lines[1]) else 'false')\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static boolean isAnagram(String s, String t) { return false; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(isAnagram(sc.nextLine(), sc.nextLine()) ? \"true\" : \"false\");\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nbool isAnagram(string s, string t) { return false; }\nint main() {\n    string s, t; cin >> s >> t;\n    cout << (isAnagram(s, t) ? \"true\" : \"false\") << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "anagram\nnagaram", "expected_output": "true"},
            {"input": "rat\ncar", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "listen\nsilent", "expected_output": "true"},
            {"input": "a\nab", "expected_output": "false"},
        ],
    },
    {
        "title": "Valid Parentheses",
        "slug": "valid-parentheses",
        "difficulty": "easy",
        "topics": ["strings", "stack"],
        "required_skills": ["stack"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": (
            "Given a string `s` containing only the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, "
            "determine if the input string is valid.\n\n"
            "An input string is valid if:\n"
            "1. Open brackets are closed by the same type of brackets.\n"
            "2. Open brackets are closed in the correct order."
        ),
        "input_format": "A single string of brackets",
        "output_format": "true or false",
        "constraints": ["1 ≤ s.length ≤ 10^4", "s consists of parentheses only"],
        "examples": [
            {"input": "()", "output": "true"},
            {"input": "()[]{}", "output": "true"},
            {"input": "(]", "output": "false"},
        ],
        "starter_code": {
            "python": "def is_valid(s):\n    # Write your solution here\n    pass\n\nimport sys\ns = sys.stdin.read().strip()\nprint('true' if is_valid(s) else 'false')\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static boolean isValid(String s) { return false; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(isValid(sc.nextLine()) ? \"true\" : \"false\");\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nbool isValid(string s) { return false; }\nint main() {\n    string s; cin >> s;\n    cout << (isValid(s) ? \"true\" : \"false\") << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "()", "expected_output": "true"},
            {"input": "()[]{}", "expected_output": "true"},
            {"input": "(]", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "([)]", "expected_output": "false"},
            {"input": "{[]}", "expected_output": "true"},
        ],
    },
    {
        "title": "Reverse Words in a String",
        "slug": "reverse-words-string",
        "difficulty": "easy",
        "topics": ["strings"],
        "required_skills": ["strings"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": (
            "Given an input string `s`, reverse the order of the words.\n\n"
            "A word is defined as a sequence of non-space characters. Words are separated by at least one space.\n\n"
            "Return a string of the words in reverse order concatenated by a single space."
        ),
        "input_format": "A single string with words separated by spaces",
        "output_format": "Words reversed, separated by single spaces",
        "constraints": ["1 ≤ s.length ≤ 10^4", "s may contain leading/trailing spaces and multiple spaces between words"],
        "examples": [
            {"input": "the sky is blue", "output": "blue is sky the"},
            {"input": "  hello world  ", "output": "world hello"},
        ],
        "starter_code": {
            "python": "def reverse_words(s):\n    # Write your solution here\n    pass\n\nimport sys\ns = sys.stdin.readline()\nprint(reverse_words(s))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static String reverseWords(String s) { return \"\"; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(reverseWords(sc.nextLine()));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstring reverseWords(string s) { return \"\"; }\nint main() {\n    string s; getline(cin, s);\n    cout << reverseWords(s) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "the sky is blue", "expected_output": "blue is sky the"},
            {"input": "  hello world  ", "expected_output": "world hello"},
        ],
        "hidden_test_cases": [
            {"input": "a good   example", "expected_output": "example good a"},
        ],
    },
    {
        "title": "Longest Common Prefix",
        "slug": "longest-common-prefix",
        "difficulty": "easy",
        "topics": ["strings"],
        "required_skills": ["strings"],
        "expected_complexity": {"time": "O(n*m)", "space": "O(1)"},
        "description": (
            "Write a function to find the longest common prefix string amongst an array of strings.\n\n"
            "If there is no common prefix, return an empty string `\"\"`."
        ),
        "input_format": "Space-separated words on one line",
        "output_format": "The longest common prefix string (or empty string)",
        "constraints": ["1 ≤ strs.length ≤ 200", "0 ≤ strs[i].length ≤ 200", "strs[i] consists of lowercase English letters"],
        "examples": [
            {"input": "flower flow flight", "output": "fl"},
            {"input": "dog racecar car", "output": ""},
        ],
        "starter_code": {
            "python": "def longest_common_prefix(strs):\n    # Write your solution here\n    pass\n\nimport sys\nstrs = sys.stdin.read().strip().split()\nprint(longest_common_prefix(strs))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static String longestCommonPrefix(String[] strs) { return \"\"; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(longestCommonPrefix(sc.nextLine().trim().split(\" \")));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstring longestCommonPrefix(vector<string>& strs) { return \"\"; }\nint main() {\n    vector<string> strs; string w;\n    while (cin >> w) strs.push_back(w);\n    cout << longestCommonPrefix(strs) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "flower flow flight", "expected_output": "fl"},
            {"input": "dog racecar car", "expected_output": ""},
        ],
        "hidden_test_cases": [
            {"input": "interview inter internal", "expected_output": "inter"},
        ],
    },
    {
        "title": "Longest Substring Without Repeating Characters",
        "slug": "longest-substring-no-repeat",
        "difficulty": "medium",
        "topics": ["strings", "sliding_window", "hashing"],
        "required_skills": ["strings", "sliding_window"],
        "expected_complexity": {"time": "O(n)", "space": "O(min(m,n))"},
        "description": (
            "Given a string `s`, find the length of the **longest substring without repeating characters**."
        ),
        "input_format": "A single string",
        "output_format": "A single integer — the length of the longest substring",
        "constraints": ["0 ≤ s.length ≤ 5 × 10^4", "s consists of English letters, digits, symbols and spaces"],
        "examples": [
            {"input": "abcabcbb", "output": "3", "explanation": "The answer is 'abc', length 3"},
            {"input": "bbbbb", "output": "1"},
        ],
        "starter_code": {
            "python": "def length_of_longest_substring(s):\n    # Write your solution here\n    pass\n\nimport sys\ns = sys.stdin.read().strip()\nprint(length_of_longest_substring(s))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int lengthOfLongestSubstring(String s) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(lengthOfLongestSubstring(sc.nextLine()));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint lengthOfLongestSubstring(string s) { return 0; }\nint main() {\n    string s; getline(cin, s);\n    cout << lengthOfLongestSubstring(s) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "abcabcbb", "expected_output": "3"},
            {"input": "bbbbb", "expected_output": "1"},
        ],
        "hidden_test_cases": [
            {"input": "pwwkew", "expected_output": "3"},
            {"input": "", "expected_output": "0"},
        ],
    },

    # ─── HASHING ─────────────────────────────────────────────────────────────
    {
        "title": "Group Anagrams",
        "slug": "group-anagrams",
        "difficulty": "medium",
        "topics": ["hashing", "strings"],
        "required_skills": ["hashing", "strings"],
        "expected_complexity": {"time": "O(n*k log k)", "space": "O(n*k)"},
        "description": (
            "Given an array of strings `strs`, group the anagrams together.\n\n"
            "You can return the answer in any order."
        ),
        "input_format": "Space-separated strings on one line",
        "output_format": "Each group of anagrams on a separate line, sorted alphabetically within group, groups sorted lexicographically",
        "constraints": ["1 ≤ strs.length ≤ 10^4", "0 ≤ strs[i].length ≤ 100", "strs[i] consists of lowercase English letters"],
        "examples": [
            {"input": "eat tea tan ate nat bat", "output": "ate eat tea\nbat\nnat tan"},
        ],
        "starter_code": {
            "python": "from collections import defaultdict\ndef group_anagrams(strs):\n    # Write your solution here\n    pass\n\nimport sys\nstrs = sys.stdin.read().strip().split()\nresult = group_anagrams(strs)\nfor group in sorted([sorted(g) for g in result]):\n    print(' '.join(group))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static List<List<String>> groupAnagrams(String[] strs) { return new ArrayList<>(); }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String[] strs = sc.nextLine().trim().split(\" \");\n        List<List<String>> res = groupAnagrams(strs);\n        res.forEach(g -> { Collections.sort(g); System.out.println(String.join(\" \", g)); });\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvector<vector<string>> groupAnagrams(vector<string>& strs) { return {}; }\nint main() {\n    vector<string> strs; string w;\n    while (cin >> w) strs.push_back(w);\n    auto res = groupAnagrams(strs);\n    for (auto& g : res) { sort(g.begin(),g.end()); for(int i=0;i<g.size();i++) cout<<g[i]<<(i+1<g.size()?' ':'\\n'); }\n}\n",
        },
        "public_test_cases": [
            {"input": "eat tea tan ate nat bat", "expected_output": "ate eat tea\nbat\nnat tan"},
        ],
        "hidden_test_cases": [
            {"input": "a", "expected_output": "a"},
        ],
    },
    {
        "title": "Top K Frequent Elements",
        "slug": "top-k-frequent",
        "difficulty": "medium",
        "topics": ["hashing", "arrays"],
        "required_skills": ["hashing", "sorting"],
        "expected_complexity": {"time": "O(n log k)", "space": "O(n)"},
        "description": (
            "Given an integer array `nums` and an integer `k`, return the `k` most frequent elements.\n\n"
            "You may return the answer in any order."
        ),
        "input_format": "Line 1: space-separated integers\nLine 2: integer k",
        "output_format": "k most frequent elements, space-separated (sorted ascending)",
        "constraints": ["1 ≤ nums.length ≤ 10^5", "k is in the range [1, the number of unique elements]"],
        "examples": [
            {"input": "1 1 1 2 2 3\n2", "output": "1 2"},
        ],
        "starter_code": {
            "python": "def top_k_frequent(nums, k):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\nnums = list(map(int, data[0].split()))\nk = int(data[1])\nresult = top_k_frequent(nums, k)\nprint(*sorted(result))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int[] topKFrequent(int[] nums, int k) { return new int[]{}; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        int k = Integer.parseInt(sc.nextLine().trim());\n        int[] res = topKFrequent(nums, k);\n        Arrays.sort(res);\n        System.out.println(Arrays.toString(res).replaceAll(\"[\\\\[\\\\],]\",\"\").trim());\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvector<int> topKFrequent(vector<int>& nums, int k) { return {}; }\nint main() {\n    string line; getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums; int x;\n    while (iss >> x) nums.push_back(x);\n    int k; cin >> k;\n    auto r = topKFrequent(nums, k);\n    sort(r.begin(), r.end());\n    for (int i=0;i<r.size();i++) cout<<r[i]<<(i+1<r.size()?' ':'\\n');\n}\n",
        },
        "public_test_cases": [
            {"input": "1 1 1 2 2 3\n2", "expected_output": "1 2"},
            {"input": "1\n1", "expected_output": "1"},
        ],
        "hidden_test_cases": [
            {"input": "4 1 2 3 3 2 2\n2", "expected_output": "2 3"},
        ],
    },
    {
        "title": "Subarray Sum Equals K",
        "slug": "subarray-sum-equals-k",
        "difficulty": "medium",
        "topics": ["hashing", "arrays", "prefix_sum"],
        "required_skills": ["hashing", "prefix_sum"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": (
            "Given an array of integers `nums` and an integer `k`, return the total number of subarrays "
            "whose sum equals to `k`."
        ),
        "input_format": "Line 1: space-separated integers\nLine 2: integer k",
        "output_format": "Count of subarrays",
        "constraints": ["1 ≤ nums.length ≤ 2 × 10^4", "-1000 ≤ nums[i] ≤ 1000", "-10^7 ≤ k ≤ 10^7"],
        "examples": [
            {"input": "1 1 1\n2", "output": "2"},
        ],
        "starter_code": {
            "python": "def subarray_sum(nums, k):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\nnums = list(map(int, data[0].split()))\nk = int(data[1])\nprint(subarray_sum(nums, k))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int subarraySum(int[] nums, int k) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(subarraySum(nums, Integer.parseInt(sc.nextLine().trim())));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint subarraySum(vector<int>& nums, int k) { return 0; }\nint main() {\n    string line; getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums; int x;\n    while (iss >> x) nums.push_back(x);\n    int k; cin >> k;\n    cout << subarraySum(nums, k) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 1 1\n2", "expected_output": "2"},
            {"input": "1 2 3\n3", "expected_output": "2"},
        ],
        "hidden_test_cases": [
            {"input": "1 -1 0\n0", "expected_output": "3"},
        ],
    },

    # ─── TWO POINTERS ─────────────────────────────────────────────────────────
    {
        "title": "Three Sum",
        "slug": "three-sum",
        "difficulty": "medium",
        "topics": ["arrays", "two_pointers", "sorting"],
        "required_skills": ["two_pointers"],
        "expected_complexity": {"time": "O(n^2)", "space": "O(1)"},
        "description": (
            "Given an integer array `nums`, return all the triplets `[nums[i], nums[j], nums[k]]` "
            "such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.\n\n"
            "The solution set must not contain duplicate triplets."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "Each triplet on a separate line, sorted ascending, triplets sorted lexicographically",
        "constraints": ["3 ≤ nums.length ≤ 3000", "-10^5 ≤ nums[i] ≤ 10^5"],
        "examples": [
            {"input": "-1 0 1 2 -1 -4", "output": "-1 -1 2\n-1 0 1"},
        ],
        "starter_code": {
            "python": "def three_sum(nums):\n    # Write your solution here\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.read().split()))\nresult = three_sum(nums)\nfor t in sorted([sorted(x) for x in result]):\n    print(*t)\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static List<List<Integer>> threeSum(int[] nums) { return new ArrayList<>(); }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        List<List<Integer>> res = threeSum(nums);\n        res.forEach(t -> System.out.println(t.get(0)+\" \"+t.get(1)+\" \"+t.get(2)));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvector<vector<int>> threeSum(vector<int>& nums) { return {}; }\nint main() {\n    vector<int> n; int x;\n    while (cin >> x) n.push_back(x);\n    auto r = threeSum(n);\n    for (auto& t : r) cout<<t[0]<<\" \"<<t[1]<<\" \"<<t[2]<<\"\\n\";\n}\n",
        },
        "public_test_cases": [
            {"input": "-1 0 1 2 -1 -4", "expected_output": "-1 -1 2\n-1 0 1"},
            {"input": "0 1 1", "expected_output": ""},
        ],
        "hidden_test_cases": [
            {"input": "0 0 0", "expected_output": "0 0 0"},
        ],
    },
    {
        "title": "Container With Most Water",
        "slug": "container-with-most-water",
        "difficulty": "medium",
        "topics": ["arrays", "two_pointers"],
        "required_skills": ["two_pointers"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "You are given an integer array `height` of length `n`. There are `n` vertical lines drawn such that "
            "the two endpoints of the ith line are `(i, 0)` and `(i, height[i])`.\n\n"
            "Find two lines that together with the x-axis form a container that holds the most water."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "A single integer — maximum water",
        "constraints": ["n >= 2", "0 ≤ height[i] ≤ 10^4"],
        "examples": [
            {"input": "1 8 6 2 5 4 8 3 7", "output": "49"},
        ],
        "starter_code": {
            "python": "def max_area(height):\n    # Write your solution here\n    pass\n\nimport sys\nheight = list(map(int, sys.stdin.read().split()))\nprint(max_area(height))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int maxArea(int[] height) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] h = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(maxArea(h));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint maxArea(vector<int>& h) { return 0; }\nint main() {\n    vector<int> h; int x;\n    while (cin >> x) h.push_back(x);\n    cout << maxArea(h) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 8 6 2 5 4 8 3 7", "expected_output": "49"},
            {"input": "1 1", "expected_output": "1"},
        ],
        "hidden_test_cases": [
            {"input": "4 3 2 1 4", "expected_output": "16"},
        ],
    },
    {
        "title": "Move Zeroes",
        "slug": "move-zeroes",
        "difficulty": "easy",
        "topics": ["arrays", "two_pointers"],
        "required_skills": ["two_pointers"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "Given an integer array `nums`, move all 0's to the end of it while maintaining the relative "
            "order of the non-zero elements.\n\nNote: You must do this in-place without making a copy."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "Space-separated integers after moving zeroes",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-2^31 ≤ nums[i] ≤ 2^31 - 1"],
        "examples": [
            {"input": "0 1 0 3 12", "output": "1 3 12 0 0"},
        ],
        "starter_code": {
            "python": "def move_zeroes(nums):\n    # Modify nums in place\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.read().split()))\nmove_zeroes(nums)\nprint(*nums)\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static void moveZeroes(int[] nums) {}\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        moveZeroes(nums);\n        System.out.println(Arrays.toString(nums).replaceAll(\"[\\\\[\\\\],]\",\"\").trim());\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvoid moveZeroes(vector<int>& nums) {}\nint main() {\n    vector<int> n; int x;\n    while (cin >> x) n.push_back(x);\n    moveZeroes(n);\n    for (int i=0;i<n.size();i++) cout<<n[i]<<(i+1<n.size()?' ':'\\n');\n}\n",
        },
        "public_test_cases": [
            {"input": "0 1 0 3 12", "expected_output": "1 3 12 0 0"},
            {"input": "0", "expected_output": "0"},
        ],
        "hidden_test_cases": [
            {"input": "1 0 0 0 2", "expected_output": "1 2 0 0 0"},
        ],
    },

    # ─── SLIDING WINDOW ────────────────────────────────────────────────────────
    {
        "title": "Maximum Average Subarray I",
        "slug": "max-avg-subarray",
        "difficulty": "easy",
        "topics": ["sliding_window", "arrays"],
        "required_skills": ["sliding_window"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "You are given an integer array `nums` consisting of `n` elements, and an integer `k`.\n\n"
            "Find a contiguous subarray whose length is equal to `k` that has the maximum average value "
            "and return this value."
        ),
        "input_format": "Line 1: space-separated integers\nLine 2: integer k",
        "output_format": "The maximum average (print as decimal with 5 decimal places)",
        "constraints": ["n == nums.length", "1 ≤ k ≤ n ≤ 10^5", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [
            {"input": "1 12 -5 -6 50 3\n4", "output": "12.75000"},
        ],
        "starter_code": {
            "python": "def find_max_average(nums, k):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\nnums = list(map(int, data[0].split()))\nk = int(data[1])\nprint(f'{find_max_average(nums, k):.5f}')\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static double findMaxAverage(int[] nums, int k) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        int k = Integer.parseInt(sc.nextLine().trim());\n        System.out.printf(\"%.5f%n\", findMaxAverage(nums, k));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\ndouble findMaxAverage(vector<int>& nums, int k) { return 0; }\nint main() {\n    string line; getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums; int x;\n    while (iss >> x) nums.push_back(x);\n    int k; cin >> k;\n    cout << fixed << setprecision(5) << findMaxAverage(nums, k) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 12 -5 -6 50 3\n4", "expected_output": "12.75000"},
        ],
        "hidden_test_cases": [
            {"input": "5 5 5 5 5\n3", "expected_output": "5.00000"},
        ],
    },
    {
        "title": "Minimum Size Subarray Sum",
        "slug": "minimum-size-subarray-sum",
        "difficulty": "medium",
        "topics": ["sliding_window", "arrays"],
        "required_skills": ["sliding_window"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "Given an array of positive integers `nums` and a positive integer `target`, return the minimal "
            "length of a contiguous subarray of which the sum is greater than or equal to `target`. "
            "If there is no such subarray, return 0."
        ),
        "input_format": "Line 1: target integer\nLine 2: space-separated integers",
        "output_format": "Minimal subarray length (0 if none)",
        "constraints": ["1 ≤ target ≤ 10^9", "1 ≤ nums.length ≤ 10^5", "1 ≤ nums[i] ≤ 10^4"],
        "examples": [
            {"input": "7\n2 3 1 2 4 3", "output": "2"},
        ],
        "starter_code": {
            "python": "def min_subarray_len(target, nums):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\ntarget = int(data[0])\nnums = list(map(int, data[1].split()))\nprint(min_subarray_len(target, nums))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int minSubArrayLen(int target, int[] nums) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int target = Integer.parseInt(sc.nextLine().trim());\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(minSubArrayLen(target, nums));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint minSubArrayLen(int target, vector<int>& nums) { return 0; }\nint main() {\n    int target; cin >> target;\n    vector<int> nums; int x;\n    while (cin >> x) nums.push_back(x);\n    cout << minSubArrayLen(target, nums) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "7\n2 3 1 2 4 3", "expected_output": "2"},
            {"input": "4\n1 4 4", "expected_output": "1"},
        ],
        "hidden_test_cases": [
            {"input": "11\n1 1 1 1 1 1 1 1", "expected_output": "0"},
        ],
    },
    {
        "title": "Fruit Into Baskets",
        "slug": "fruit-into-baskets",
        "difficulty": "medium",
        "topics": ["sliding_window", "hashing"],
        "required_skills": ["sliding_window"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "You are visiting a farm with a row of fruit trees. Each tree produces one type of fruit.\n\n"
            "You have two baskets, and each basket can only hold a single type of fruit.\n\n"
            "Given the integer array `fruits`, return the maximum number of fruits you can pick "
            "(pick from a contiguous subarray of at most 2 distinct types)."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "A single integer — maximum fruits picked",
        "constraints": ["1 ≤ fruits.length ≤ 10^5", "0 ≤ fruits[i] < fruits.length"],
        "examples": [
            {"input": "1 2 1", "output": "3"},
            {"input": "0 1 2 2", "output": "3"},
        ],
        "starter_code": {
            "python": "def total_fruit(fruits):\n    # Write your solution here\n    pass\n\nimport sys\nfruits = list(map(int, sys.stdin.read().split()))\nprint(total_fruit(fruits))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int totalFruit(int[] fruits) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] fruits = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(totalFruit(fruits));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint totalFruit(vector<int>& fruits) { return 0; }\nint main() {\n    vector<int> f; int x;\n    while (cin >> x) f.push_back(x);\n    cout << totalFruit(f) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 2 1", "expected_output": "3"},
            {"input": "0 1 2 2", "expected_output": "3"},
        ],
        "hidden_test_cases": [
            {"input": "1 2 3 2 2", "expected_output": "4"},
        ],
    },

    # ─── STACK ────────────────────────────────────────────────────────────────
    {
        "title": "Min Stack",
        "slug": "min-stack",
        "difficulty": "medium",
        "topics": ["stack"],
        "required_skills": ["stack"],
        "expected_complexity": {"time": "O(1) per op", "space": "O(n)"},
        "description": (
            "Design a stack that supports push, pop, top, and retrieving the minimum element in constant time.\n\n"
            "Given operations as lines: push X / pop / top / getMin\n"
            "Output the result of top and getMin operations."
        ),
        "input_format": "Each line: push X | pop | top | getMin",
        "output_format": "Result of each top/getMin operation on a new line",
        "constraints": ["-2^31 ≤ val ≤ 2^31 - 1", "Methods pop, top and getMin will always be called on non-empty stacks"],
        "examples": [
            {"input": "push -2\npush 0\npush -3\ngetMin\npop\ntop\ngetMin", "output": "-3\n0\n-2"},
        ],
        "starter_code": {
            "python": "class MinStack:\n    def __init__(self):\n        pass\n    def push(self, val):\n        pass\n    def pop(self):\n        pass\n    def top(self):\n        pass\n    def get_min(self):\n        pass\n\nimport sys\nstack = MinStack()\nfor line in sys.stdin:\n    line = line.strip()\n    if not line: continue\n    if line.startswith('push'):\n        stack.push(int(line.split()[1]))\n    elif line == 'pop':\n        stack.pop()\n    elif line == 'top':\n        print(stack.top())\n    elif line == 'getMin':\n        print(stack.get_min())\n",
            "java": "import java.util.*;\npublic class Solution {\n    static int[] data = new int[10000];\n    static int[] mins = new int[10000];\n    static int top = 0;\n    static void push(int v) { data[top] = v; mins[top] = top == 0 ? v : Math.min(mins[top-1], v); top++; }\n    static void pop() { top--; }\n    static int top() { return data[top-1]; }\n    static int getMin() { return mins[top-1]; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        while (sc.hasNextLine()) {\n            String line = sc.nextLine().trim();\n            if (line.isEmpty()) continue;\n            if (line.startsWith(\"push\")) push(Integer.parseInt(line.split(\" \")[1]));\n            else if (line.equals(\"pop\")) pop();\n            else if (line.equals(\"top\")) System.out.println(top());\n            else if (line.equals(\"getMin\")) System.out.println(getMin());\n        }\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstruct MinStack {\n    stack<int> s, mn;\n    void push(int v) { s.push(v); mn.push(mn.empty() ? v : min(mn.top(), v)); }\n    void pop() { s.pop(); mn.pop(); }\n    int top() { return s.top(); }\n    int getMin() { return mn.top(); }\n} ms;\nint main() {\n    string line;\n    while (getline(cin, line)) {\n        if (line.empty()) continue;\n        if (line.substr(0,4)==\"push\") ms.push(stoi(line.substr(5)));\n        else if (line==\"pop\") ms.pop();\n        else if (line==\"top\") cout<<ms.top()<<\"\\n\";\n        else if (line==\"getMin\") cout<<ms.getMin()<<\"\\n\";\n    }\n}\n",
        },
        "public_test_cases": [
            {"input": "push -2\npush 0\npush -3\ngetMin\npop\ntop\ngetMin", "expected_output": "-3\n0\n-2"},
        ],
        "hidden_test_cases": [
            {"input": "push 1\npush 2\ngetMin\npop\ngetMin", "expected_output": "1\n1"},
        ],
    },
    {
        "title": "Daily Temperatures",
        "slug": "daily-temperatures",
        "difficulty": "medium",
        "topics": ["stack", "arrays"],
        "required_skills": ["stack", "monotonic_stack"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": (
            "Given an array of integers `temperatures`, return an array `answer` such that `answer[i]` is "
            "the number of days you have to wait after the ith day to get a warmer temperature.\n\n"
            "If there is no future day for which this is possible, keep `answer[i] == 0` instead."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "Space-separated integers",
        "constraints": ["1 ≤ temperatures.length ≤ 10^5", "30 ≤ temperatures[i] ≤ 100"],
        "examples": [
            {"input": "73 74 75 71 69 72 76 73", "output": "1 1 4 2 1 1 0 0"},
        ],
        "starter_code": {
            "python": "def daily_temperatures(temps):\n    # Write your solution here\n    pass\n\nimport sys\ntemps = list(map(int, sys.stdin.read().split()))\nprint(*daily_temperatures(temps))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int[] dailyTemperatures(int[] t) { return new int[]{}; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] t = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(Arrays.toString(dailyTemperatures(t)).replaceAll(\"[\\\\[\\\\],]\",\"\").trim());\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvector<int> dailyTemperatures(vector<int>& t) { return {}; }\nint main() {\n    vector<int> t; int x;\n    while (cin >> x) t.push_back(x);\n    auto r = dailyTemperatures(t);\n    for (int i=0;i<r.size();i++) cout<<r[i]<<(i+1<r.size()?' ':'\\n');\n}\n",
        },
        "public_test_cases": [
            {"input": "73 74 75 71 69 72 76 73", "expected_output": "1 1 4 2 1 1 0 0"},
        ],
        "hidden_test_cases": [
            {"input": "30 40 50 60", "expected_output": "1 1 1 0"},
        ],
    },
    {
        "title": "Evaluate Reverse Polish Notation",
        "slug": "evaluate-rpn",
        "difficulty": "medium",
        "topics": ["stack"],
        "required_skills": ["stack"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": (
            "Evaluate the value of an arithmetic expression in Reverse Polish Notation.\n\n"
            "Valid operators are `+`, `-`, `*`, and `/`. Division truncates toward zero."
        ),
        "input_format": "Tokens space-separated on one line",
        "output_format": "The evaluated integer result",
        "constraints": ["1 ≤ tokens.length ≤ 10^4", "Each token is an integer or one of +, -, *, /"],
        "examples": [
            {"input": "2 1 + 3 *", "output": "9"},
            {"input": "4 13 5 / +", "output": "6"},
        ],
        "starter_code": {
            "python": "def eval_rpn(tokens):\n    # Write your solution here\n    pass\n\nimport sys\ntokens = sys.stdin.read().split()\nprint(eval_rpn(tokens))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int evalRPN(String[] tokens) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(evalRPN(sc.nextLine().trim().split(\" \")));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint evalRPN(vector<string>& t) { return 0; }\nint main() {\n    vector<string> t; string s;\n    while (cin >> s) t.push_back(s);\n    cout << evalRPN(t) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "2 1 + 3 *", "expected_output": "9"},
            {"input": "4 13 5 / +", "expected_output": "6"},
        ],
        "hidden_test_cases": [
            {"input": "10 6 9 3 + -11 * / * 17 + 5 +", "expected_output": "22"},
        ],
    },

    # ─── QUEUE ────────────────────────────────────────────────────────────────
    {
        "title": "Number of Recent Calls",
        "slug": "number-of-recent-calls",
        "difficulty": "easy",
        "topics": ["queue"],
        "required_skills": ["queue"],
        "expected_complexity": {"time": "O(1) amortized", "space": "O(1)"},
        "description": (
            "You have a `RecentCounter` class which counts recent requests within a certain time frame.\n\n"
            "Implement `ping(t)` which adds a new request at time `t` and returns the number of requests "
            "with timestamps in the inclusive range `[t - 3000, t]`."
        ),
        "input_format": "Space-separated timestamps on one line (given in strictly increasing order)",
        "output_format": "Space-separated results of each ping",
        "constraints": ["1 ≤ t ≤ 10^9", "At most 10^4 calls to ping", "t is strictly increasing"],
        "examples": [
            {"input": "1 100 3001 3002", "output": "1 2 3 3"},
        ],
        "starter_code": {
            "python": "from collections import deque\nclass RecentCounter:\n    def __init__(self):\n        pass\n    def ping(self, t):\n        # Return count of requests in [t-3000, t]\n        pass\n\nimport sys\ntimes = list(map(int, sys.stdin.read().split()))\nrc = RecentCounter()\nprint(*[rc.ping(t) for t in times])\n",
            "java": "import java.util.*;\npublic class Solution {\n    static Deque<Integer> q = new ArrayDeque<>();\n    static int ping(int t) { q.add(t); while (q.peek() < t-3000) q.poll(); return q.size(); }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        StringBuilder sb = new StringBuilder();\n        for (String s : sc.nextLine().trim().split(\" \")) { if (sb.length()>0) sb.append(' '); sb.append(ping(Integer.parseInt(s))); }\n        System.out.println(sb);\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nqueue<int> q;\nint ping(int t) { q.push(t); while(q.front()<t-3000) q.pop(); return q.size(); }\nint main() { int x; vector<int> r; while(cin>>x) r.push_back(ping(x)); for(int i=0;i<r.size();i++) cout<<r[i]<<(i+1<r.size()?' ':'\\n'); }\n",
        },
        "public_test_cases": [
            {"input": "1 100 3001 3002", "expected_output": "1 2 3 3"},
        ],
        "hidden_test_cases": [
            {"input": "1 2 3 4 5 6 3001 3002 3003", "expected_output": "1 2 3 4 5 6 6 6 6"},
        ],
    },
    {
        "title": "Sliding Window Maximum",
        "slug": "sliding-window-maximum",
        "difficulty": "hard",
        "topics": ["queue", "sliding_window", "arrays"],
        "required_skills": ["deque", "sliding_window"],
        "expected_complexity": {"time": "O(n)", "space": "O(k)"},
        "description": (
            "Given an integer array `nums` and an integer `k`, there is a sliding window of size `k` "
            "moving from the left to the right. You can only see the `k` numbers in the window. "
            "Return the max of each window position."
        ),
        "input_format": "Line 1: space-separated integers\nLine 2: integer k",
        "output_format": "Space-separated maximums",
        "constraints": ["1 ≤ nums.length ≤ 10^5", "-10^4 ≤ nums[i] ≤ 10^4", "1 ≤ k ≤ nums.length"],
        "examples": [
            {"input": "1 3 -1 -3 5 3 6 7\n3", "output": "3 3 5 5 6 7"},
        ],
        "starter_code": {
            "python": "from collections import deque\ndef max_sliding_window(nums, k):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\nnums = list(map(int, data[0].split()))\nk = int(data[1])\nprint(*max_sliding_window(nums, k))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int[] maxSlidingWindow(int[] nums, int k) { return new int[]{}; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        int k = Integer.parseInt(sc.nextLine().trim());\n        System.out.println(Arrays.toString(maxSlidingWindow(nums,k)).replaceAll(\"[\\\\[\\\\],]\",\"\").trim());\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvector<int> maxSlidingWindow(vector<int>& nums, int k) { return {}; }\nint main() {\n    string line; getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums; int x;\n    while (iss >> x) nums.push_back(x);\n    cin >> x;\n    auto r = maxSlidingWindow(nums, x);\n    for (int i=0;i<r.size();i++) cout<<r[i]<<(i+1<r.size()?' ':'\\n');\n}\n",
        },
        "public_test_cases": [
            {"input": "1 3 -1 -3 5 3 6 7\n3", "expected_output": "3 3 5 5 6 7"},
        ],
        "hidden_test_cases": [
            {"input": "1\n1", "expected_output": "1"},
        ],
    },

    # ─── BINARY SEARCH ────────────────────────────────────────────────────────
    {
        "title": "Binary Search",
        "slug": "binary-search",
        "difficulty": "easy",
        "topics": ["binary_search", "arrays"],
        "required_skills": ["binary_search"],
        "expected_complexity": {"time": "O(log n)", "space": "O(1)"},
        "description": (
            "Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, "
            "write a function to search `target` in `nums`. If `target` exists, return its index. "
            "Otherwise, return -1."
        ),
        "input_format": "Line 1: space-separated sorted integers\nLine 2: target integer",
        "output_format": "Index of target or -1",
        "constraints": ["1 ≤ nums.length ≤ 10^4", "-10^4 < nums[i], target < 10^4", "All elements are unique and sorted ascending"],
        "examples": [
            {"input": "-1 0 3 5 9 12\n9", "output": "4"},
            {"input": "-1 0 3 5 9 12\n2", "output": "-1"},
        ],
        "starter_code": {
            "python": "def binary_search(nums, target):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\nnums = list(map(int, data[0].split()))\ntarget = int(data[1])\nprint(binary_search(nums, target))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int search(int[] nums, int target) { return -1; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(search(nums, Integer.parseInt(sc.nextLine().trim())));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint search(vector<int>& nums, int target) { return -1; }\nint main() {\n    string line; getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums; int x;\n    while (iss >> x) nums.push_back(x);\n    cin >> x;\n    cout << search(nums, x) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "-1 0 3 5 9 12\n9", "expected_output": "4"},
            {"input": "-1 0 3 5 9 12\n2", "expected_output": "-1"},
        ],
        "hidden_test_cases": [
            {"input": "5\n5", "expected_output": "0"},
            {"input": "1 3 5 7 9\n7", "expected_output": "3"},
        ],
    },
    {
        "title": "Search in Rotated Sorted Array",
        "slug": "search-rotated-sorted-array",
        "difficulty": "medium",
        "topics": ["binary_search", "arrays"],
        "required_skills": ["binary_search"],
        "expected_complexity": {"time": "O(log n)", "space": "O(1)"},
        "description": (
            "There is an integer array `nums` sorted in ascending order (with distinct values) which is "
            "possibly rotated at an unknown pivot.\n\n"
            "Given the array `nums` after the possible rotation and an integer `target`, return the index "
            "of `target` if it is in `nums`, or -1 if it is not."
        ),
        "input_format": "Line 1: space-separated integers\nLine 2: target integer",
        "output_format": "Index of target or -1",
        "constraints": ["1 ≤ nums.length ≤ 5000", "-10^4 ≤ nums[i] ≤ 10^4", "All values are unique"],
        "examples": [
            {"input": "4 5 6 7 0 1 2\n0", "output": "4"},
            {"input": "4 5 6 7 0 1 2\n3", "output": "-1"},
        ],
        "starter_code": {
            "python": "def search_rotated(nums, target):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\nnums = list(map(int, data[0].split()))\ntarget = int(data[1])\nprint(search_rotated(nums, target))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int search(int[] nums, int target) { return -1; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(search(nums, Integer.parseInt(sc.nextLine().trim())));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint search(vector<int>& nums, int target) { return -1; }\nint main() {\n    string line; getline(cin, line);\n    istringstream iss(line); vector<int> n; int x;\n    while (iss >> x) n.push_back(x); cin >> x;\n    cout << search(n, x) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "4 5 6 7 0 1 2\n0", "expected_output": "4"},
            {"input": "4 5 6 7 0 1 2\n3", "expected_output": "-1"},
        ],
        "hidden_test_cases": [
            {"input": "1\n0", "expected_output": "-1"},
            {"input": "1 3\n3", "expected_output": "1"},
        ],
    },
    {
        "title": "Koko Eating Bananas",
        "slug": "koko-eating-bananas",
        "difficulty": "medium",
        "topics": ["binary_search", "arrays"],
        "required_skills": ["binary_search"],
        "expected_complexity": {"time": "O(n log m)", "space": "O(1)"},
        "description": (
            "Koko loves to eat bananas. There are `n` piles of bananas. "
            "Koko can eat at most `k` bananas per hour. The guards will come back in `h` hours.\n\n"
            "Return the minimum integer `k` such that she can eat all the bananas within `h` hours."
        ),
        "input_format": "Line 1: space-separated integers (pile sizes)\nLine 2: integer h",
        "output_format": "Minimum eating speed k",
        "constraints": ["1 ≤ piles.length ≤ 10^4", "piles.length ≤ h ≤ 10^9", "1 ≤ piles[i] ≤ 10^9"],
        "examples": [
            {"input": "3 6 7 11\n8", "output": "4"},
        ],
        "starter_code": {
            "python": "import math\ndef min_eating_speed(piles, h):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\npiles = list(map(int, data[0].split()))\nh = int(data[1])\nprint(min_eating_speed(piles, h))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int minEatingSpeed(int[] piles, int h) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] piles = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(minEatingSpeed(piles, Integer.parseInt(sc.nextLine().trim())));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint minEatingSpeed(vector<int>& piles, int h) { return 0; }\nint main() {\n    string line; getline(cin, line);\n    istringstream iss(line); vector<int> p; int x;\n    while (iss >> x) p.push_back(x); cin >> x;\n    cout << minEatingSpeed(p, x) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "3 6 7 11\n8", "expected_output": "4"},
            {"input": "30 11 23 4 20\n5", "expected_output": "30"},
        ],
        "hidden_test_cases": [
            {"input": "30 11 23 4 20\n6", "expected_output": "23"},
        ],
    },
    {
        "title": "Median of Two Sorted Arrays",
        "slug": "median-two-sorted-arrays",
        "difficulty": "hard",
        "topics": ["binary_search", "arrays"],
        "required_skills": ["binary_search", "divide_conquer"],
        "expected_complexity": {"time": "O(log(min(m,n)))", "space": "O(1)"},
        "description": (
            "Given two sorted arrays `nums1` and `nums2` of size `m` and `n` respectively, return the "
            "median of the two sorted arrays.\n\nThe overall run time complexity should be O(log (m+n))."
        ),
        "input_format": "Line 1: space-separated integers (nums1)\nLine 2: space-separated integers (nums2)",
        "output_format": "Median as decimal with 5 decimal places",
        "constraints": ["0 ≤ m, n ≤ 1000", "1 ≤ m + n", "-10^6 ≤ nums1[i], nums2[i] ≤ 10^6"],
        "examples": [
            {"input": "1 3\n2", "output": "2.00000"},
            {"input": "1 2\n3 4", "output": "2.50000"},
        ],
        "starter_code": {
            "python": "def find_median_sorted_arrays(nums1, nums2):\n    # Write your solution here\n    pass\n\nimport sys\nlines = sys.stdin.read().strip().split('\\n')\nnums1 = list(map(int, lines[0].split()))\nnums2 = list(map(int, lines[1].split()))\nprint(f'{find_median_sorted_arrays(nums1, nums2):.5f}')\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static double findMedianSortedArrays(int[] nums1, int[] nums2) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] a = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        int[] b = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.printf(\"%.5f%n\", findMedianSortedArrays(a, b));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\ndouble findMedianSortedArrays(vector<int>& a, vector<int>& b) { return 0; }\nint main() {\n    string l1, l2; getline(cin,l1); getline(cin,l2);\n    istringstream i1(l1), i2(l2);\n    vector<int> a, b; int x;\n    while(i1>>x) a.push_back(x);\n    while(i2>>x) b.push_back(x);\n    cout << fixed << setprecision(5) << findMedianSortedArrays(a,b) << endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 3\n2", "expected_output": "2.00000"},
            {"input": "1 2\n3 4", "expected_output": "2.50000"},
        ],
        "hidden_test_cases": [
            {"input": "0 0\n0 0", "expected_output": "0.00000"},
        ],
    },

    # ─── LINKED LIST ──────────────────────────────────────────────────────────
    {
        "title": "Reverse Linked List",
        "slug": "reverse-linked-list",
        "difficulty": "easy",
        "topics": ["linked_list"],
        "required_skills": ["linked_list"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "Given the head of a singly linked list, reverse the list, and return the reversed list.\n\n"
            "Input/output the list as space-separated values."
        ),
        "input_format": "Space-separated integers (linked list values)",
        "output_format": "Reversed list as space-separated integers",
        "constraints": ["0 ≤ n ≤ 5000", "-5000 ≤ Node.val ≤ 5000"],
        "examples": [
            {"input": "1 2 3 4 5", "output": "5 4 3 2 1"},
        ],
        "starter_code": {
            "python": "class ListNode:\n    def __init__(self, val=0, nxt=None):\n        self.val = val\n        self.next = nxt\n\ndef reverse_list(head):\n    # Write your solution here\n    pass\n\nimport sys\nvals = list(map(int, sys.stdin.read().split()))\ndummy = ListNode()\ncurr = dummy\nfor v in vals:\n    curr.next = ListNode(v)\n    curr = curr.next\nresult = reverse_list(dummy.next)\nout = []\nwhile result:\n    out.append(str(result.val))\n    result = result.next\nprint(' '.join(out))\n",
            "java": "import java.util.*;\npublic class Solution {\n    static class ListNode { int val; ListNode next; ListNode(int v) { val=v; } }\n    public static ListNode reverseList(ListNode head) { return null; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String[] parts = sc.nextLine().trim().split(\" \");\n        ListNode dummy = new ListNode(0), curr = dummy;\n        for (String p : parts) { curr.next = new ListNode(Integer.parseInt(p)); curr = curr.next; }\n        ListNode res = reverseList(dummy.next);\n        StringBuilder sb = new StringBuilder();\n        while (res != null) { if(sb.length()>0) sb.append(' '); sb.append(res.val); res=res.next; }\n        System.out.println(sb);\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstruct ListNode { int val; ListNode* next; ListNode(int v):val(v),next(nullptr){} };\nListNode* reverseList(ListNode* head) { return nullptr; }\nint main() {\n    vector<int> vals; int x;\n    while(cin>>x) vals.push_back(x);\n    ListNode* dummy=new ListNode(0); ListNode* curr=dummy;\n    for(int v:vals){curr->next=new ListNode(v);curr=curr->next;}\n    ListNode* res=reverseList(dummy->next);\n    bool first=true;\n    while(res){if(!first)cout<<' ';cout<<res->val;res=res->next;first=false;}\n    cout<<endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "5 4 3 2 1"},
            {"input": "1 2", "expected_output": "2 1"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected_output": "1"},
        ],
    },
    {
        "title": "Linked List Cycle",
        "slug": "linked-list-cycle",
        "difficulty": "easy",
        "topics": ["linked_list", "two_pointers"],
        "required_skills": ["linked_list", "two_pointers"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "Given a sequence of operations on a linked list, detect if a cycle is present.\n\n"
            "For this problem: you're given a list of integers and a 'pos' value. "
            "pos = -1 means no cycle. Otherwise, pos is the index where the tail connects.\n\n"
            "Return true if cycle, false if not."
        ),
        "input_format": "Line 1: space-separated integers\nLine 2: pos (-1 for no cycle)",
        "output_format": "true or false",
        "constraints": ["0 ≤ list length ≤ 10^4", "pos is -1 or a valid index"],
        "examples": [
            {"input": "3 2 0 -4\n1", "output": "true"},
            {"input": "1 2\n-1", "output": "false"},
        ],
        "starter_code": {
            "python": "class ListNode:\n    def __init__(self, val=0, nxt=None):\n        self.val = val\n        self.next = nxt\n\ndef has_cycle(head):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\nvals = list(map(int, data[0].split()))\npos = int(data[1])\nnodes = [ListNode(v) for v in vals]\nfor i in range(len(nodes)-1): nodes[i].next = nodes[i+1]\nif pos >= 0: nodes[-1].next = nodes[pos]\nprint('true' if has_cycle(nodes[0] if nodes else None) else 'false')\n",
            "java": "import java.util.*;\npublic class Solution {\n    static class ListNode { int val; ListNode next; ListNode(int v){val=v;} }\n    public static boolean hasCycle(ListNode head) { return false; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] vals = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        int pos = Integer.parseInt(sc.nextLine().trim());\n        ListNode[] nodes = new ListNode[vals.length];\n        for(int i=0;i<vals.length;i++) nodes[i]=new ListNode(vals[i]);\n        for(int i=0;i<vals.length-1;i++) nodes[i].next=nodes[i+1];\n        if(pos>=0) nodes[vals.length-1].next=nodes[pos];\n        System.out.println(hasCycle(vals.length>0?nodes[0]:null)?\"true\":\"false\");\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstruct ListNode{int val;ListNode*next;ListNode(int v):val(v),next(nullptr){}};\nbool hasCycle(ListNode*head){return false;}\nint main(){\n    string line; getline(cin,line);\n    istringstream iss(line);\n    vector<int>vals; int x;\n    while(iss>>x) vals.push_back(x);\n    int pos; cin>>pos;\n    vector<ListNode*>nodes;\n    for(int v:vals) nodes.push_back(new ListNode(v));\n    for(int i=0;i+1<nodes.size();i++) nodes[i]->next=nodes[i+1];\n    if(pos>=0&&!nodes.empty()) nodes.back()->next=nodes[pos];\n    cout<<(hasCycle(nodes.empty()?nullptr:nodes[0])?\"true\":\"false\")<<endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "3 2 0 -4\n1", "expected_output": "true"},
            {"input": "1 2\n-1", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "1\n-1", "expected_output": "false"},
        ],
    },
    {
        "title": "Merge Two Sorted Lists",
        "slug": "merge-two-sorted-lists",
        "difficulty": "easy",
        "topics": ["linked_list"],
        "required_skills": ["linked_list"],
        "expected_complexity": {"time": "O(m+n)", "space": "O(1)"},
        "description": (
            "You are given the heads of two sorted linked lists `list1` and `list2`.\n\n"
            "Merge the two lists in a sorted order and return the merged list."
        ),
        "input_format": "Line 1: space-separated integers (list1)\nLine 2: space-separated integers (list2)",
        "output_format": "Merged sorted list as space-separated integers",
        "constraints": ["0 ≤ n, m ≤ 50", "-100 ≤ Node.val ≤ 100"],
        "examples": [
            {"input": "1 2 4\n1 3 4", "output": "1 1 2 3 4 4"},
        ],
        "starter_code": {
            "python": "class ListNode:\n    def __init__(self, val=0, nxt=None):\n        self.val = val\n        self.next = nxt\n\ndef merge_two_lists(l1, l2):\n    # Write your solution here\n    pass\n\nimport sys\nlines = sys.stdin.read().strip().split('\\n')\ndef build(vals):\n    dummy = ListNode(); curr = dummy\n    for v in vals: curr.next = ListNode(int(v)); curr = curr.next\n    return dummy.next\nl1 = build(lines[0].split()) if lines[0].strip() else None\nl2 = build(lines[1].split()) if len(lines)>1 and lines[1].strip() else None\nres = merge_two_lists(l1, l2)\nout = []\nwhile res: out.append(str(res.val)); res = res.next\nprint(' '.join(out))\n",
            "java": "import java.util.*;\npublic class Solution {\n    static class ListNode{int val;ListNode next;ListNode(int v){val=v;}}\n    public static ListNode mergeTwoLists(ListNode l1,ListNode l2){return null;}\n    static ListNode build(String[] parts){\n        ListNode dummy=new ListNode(0),curr=dummy;\n        for(String p:parts) if(!p.isEmpty()){curr.next=new ListNode(Integer.parseInt(p));curr=curr.next;}\n        return dummy.next;\n    }\n    public static void main(String[] args){\n        Scanner sc=new Scanner(System.in);\n        ListNode l1=build(sc.nextLine().trim().split(\" \"));\n        ListNode l2=build(sc.nextLine().trim().split(\" \"));\n        ListNode res=mergeTwoLists(l1,l2);\n        StringBuilder sb=new StringBuilder();\n        while(res!=null){if(sb.length()>0)sb.append(' ');sb.append(res.val);res=res.next;}\n        System.out.println(sb);\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstruct ListNode{int val;ListNode*next;ListNode(int v):val(v),next(nullptr){}};\nListNode*mergeTwoLists(ListNode*l1,ListNode*l2){return nullptr;}\nListNode*build(istringstream&iss){\n    ListNode*dummy=new ListNode(0),*curr=dummy;int x;\n    while(iss>>x){curr->next=new ListNode(x);curr=curr->next;}\n    return dummy->next;\n}\nint main(){\n    string l1s,l2s;getline(cin,l1s);getline(cin,l2s);\n    istringstream i1(l1s),i2(l2s);\n    ListNode*res=mergeTwoLists(build(i1),build(i2));\n    bool first=true;\n    while(res){if(!first)cout<<' ';cout<<res->val;res=res->next;first=false;}\n    cout<<endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 2 4\n1 3 4", "expected_output": "1 1 2 3 4 4"},
            {"input": "\n", "expected_output": ""},
        ],
        "hidden_test_cases": [
            {"input": "1\n2", "expected_output": "1 2"},
        ],
    },

    # ─── TREES ───────────────────────────────────────────────────────────────
    {
        "title": "Maximum Depth of Binary Tree",
        "slug": "max-depth-binary-tree",
        "difficulty": "easy",
        "topics": ["trees", "recursion", "bfs"],
        "required_skills": ["trees", "recursion"],
        "expected_complexity": {"time": "O(n)", "space": "O(h)"},
        "description": (
            "Given the root of a binary tree, return its maximum depth.\n\n"
            "The maximum depth is the number of nodes along the longest path from the root to the farthest leaf node.\n\n"
            "Input: level-order traversal with 'null' for missing nodes."
        ),
        "input_format": "Level-order traversal: integers and 'null', space-separated",
        "output_format": "A single integer — maximum depth",
        "constraints": ["0 ≤ number of nodes ≤ 10^4", "-100 ≤ Node.val ≤ 100"],
        "examples": [
            {"input": "3 9 20 null null 15 7", "output": "3"},
            {"input": "1 null 2", "output": "2"},
        ],
        "starter_code": {
            "python": "from collections import deque\nclass TreeNode:\n    def __init__(self, val=0, left=None, right=None):\n        self.val=val; self.left=left; self.right=right\n\ndef max_depth(root):\n    # Write your solution here\n    pass\n\nimport sys\ntokens = sys.stdin.read().split()\nif not tokens or tokens[0]=='null':\n    print(0)\nelse:\n    nodes=[TreeNode(int(t)) if t!='null' else None for t in tokens]\n    for i in range(len(nodes)):\n        if nodes[i]:\n            li,ri=2*i+1,2*i+2\n            if li<len(nodes): nodes[i].left=nodes[li]\n            if ri<len(nodes): nodes[i].right=nodes[ri]\n    print(max_depth(nodes[0]))\n",
            "java": "import java.util.*;\npublic class Solution {\n    static class TreeNode{int val;TreeNode left,right;TreeNode(int v){val=v;}}\n    public static int maxDepth(TreeNode root){return 0;}\n    public static void main(String[] args){\n        Scanner sc=new Scanner(System.in);\n        String[] tokens=sc.nextLine().trim().split(\" \");\n        if(tokens[0].equals(\"null\")){System.out.println(0);return;}\n        TreeNode[] nodes=new TreeNode[tokens.length];\n        for(int i=0;i<tokens.length;i++) nodes[i]=tokens[i].equals(\"null\")?null:new TreeNode(Integer.parseInt(tokens[i]));\n        for(int i=0;i<nodes.length;i++) if(nodes[i]!=null){\n            int li=2*i+1,ri=2*i+2;\n            if(li<nodes.length) nodes[i].left=nodes[li];\n            if(ri<nodes.length) nodes[i].right=nodes[ri];\n        }\n        System.out.println(maxDepth(nodes[0]));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstruct TreeNode{int val;TreeNode*left,*right;TreeNode(int v):val(v),left(nullptr),right(nullptr){}};\nint maxDepth(TreeNode*root){return 0;}\nint main(){\n    vector<string> tokens; string s;\n    while(cin>>s) tokens.push_back(s);\n    if(tokens.empty()||tokens[0]==\"null\"){cout<<0<<endl;return 0;}\n    vector<TreeNode*> nodes(tokens.size(),nullptr);\n    for(int i=0;i<tokens.size();i++) if(tokens[i]!=\"null\") nodes[i]=new TreeNode(stoi(tokens[i]));\n    for(int i=0;i<nodes.size();i++) if(nodes[i]){\n        int li=2*i+1,ri=2*i+2;\n        if(li<nodes.size()) nodes[i]->left=nodes[li];\n        if(ri<nodes.size()) nodes[i]->right=nodes[ri];\n    }\n    cout<<maxDepth(nodes[0])<<endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "3 9 20 null null 15 7", "expected_output": "3"},
            {"input": "1 null 2", "expected_output": "2"},
        ],
        "hidden_test_cases": [
            {"input": "null", "expected_output": "0"},
            {"input": "1", "expected_output": "1"},
        ],
    },
    {
        "title": "Lowest Common Ancestor of BST",
        "slug": "lca-bst",
        "difficulty": "medium",
        "topics": ["trees", "binary_search_tree"],
        "required_skills": ["trees"],
        "expected_complexity": {"time": "O(h)", "space": "O(1)"},
        "description": (
            "Given a binary search tree (BST), find the lowest common ancestor (LCA) of two given nodes.\n\n"
            "Input: level-order BST traversal, then two values p and q."
        ),
        "input_format": "Line 1: level-order BST (space-separated integers with 'null')\nLine 2: p q",
        "output_format": "Value of the LCA node",
        "constraints": ["2 ≤ number of nodes ≤ 10^5", "-10^9 ≤ Node.val ≤ 10^9", "All values are unique"],
        "examples": [
            {"input": "6 2 8 0 4 7 9 null null 3 5\n2 8", "output": "6"},
            {"input": "6 2 8 0 4 7 9 null null 3 5\n2 4", "output": "2"},
        ],
        "starter_code": {
            "python": "class TreeNode:\n    def __init__(self, val=0, left=None, right=None):\n        self.val=val;self.left=left;self.right=right\n\ndef lca_bst(root, p, q):\n    # Write your solution here\n    pass\n\nimport sys\nlines=sys.stdin.read().strip().split('\\n')\ntokens=lines[0].split()\npq=list(map(int,lines[1].split()))\nif not tokens or tokens[0]=='null':\n    print(-1)\nelse:\n    nodes=[TreeNode(int(t)) if t!='null' else None for t in tokens]\n    for i in range(len(nodes)):\n        if nodes[i]:\n            li,ri=2*i+1,2*i+2\n            if li<len(nodes):nodes[i].left=nodes[li]\n            if ri<len(nodes):nodes[i].right=nodes[ri]\n    print(lca_bst(nodes[0],pq[0],pq[1]).val)\n",
            "java": "import java.util.*;\npublic class Solution {\n    static class TreeNode{int val;TreeNode left,right;TreeNode(int v){val=v;}}\n    public static TreeNode lowestCommonAncestor(TreeNode root,TreeNode p,TreeNode q){return null;}\n    public static void main(String[] args){\n        Scanner sc=new Scanner(System.in);\n        String[] tokens=sc.nextLine().trim().split(\" \");\n        int[] pq=Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        TreeNode[] nodes=new TreeNode[tokens.length];\n        for(int i=0;i<tokens.length;i++) nodes[i]=tokens[i].equals(\"null\")?null:new TreeNode(Integer.parseInt(tokens[i]));\n        for(int i=0;i<nodes.length;i++) if(nodes[i]!=null){int li=2*i+1,ri=2*i+2;if(li<nodes.length)nodes[i].left=nodes[li];if(ri<nodes.length)nodes[i].right=nodes[ri];}\n        System.out.println(lowestCommonAncestor(nodes[0],new TreeNode(pq[0]),new TreeNode(pq[1])).val);\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstruct TreeNode{int val;TreeNode*left,*right;TreeNode(int v):val(v),left(nullptr),right(nullptr){}};\nTreeNode*lowestCommonAncestor(TreeNode*root,TreeNode*p,TreeNode*q){return nullptr;}\nint main(){\n    string l1,l2;getline(cin,l1);getline(cin,l2);\n    istringstream i1(l1); vector<string> tokens; string s;\n    while(i1>>s) tokens.push_back(s);\n    istringstream i2(l2); int pv,qv; i2>>pv>>qv;\n    vector<TreeNode*>nodes(tokens.size(),nullptr);\n    for(int i=0;i<tokens.size();i++) if(tokens[i]!=\"null\") nodes[i]=new TreeNode(stoi(tokens[i]));\n    for(int i=0;i<nodes.size();i++) if(nodes[i]){int li=2*i+1,ri=2*i+2;if(li<nodes.size())nodes[i]->left=nodes[li];if(ri<nodes.size())nodes[i]->right=nodes[ri];}\n    cout<<lowestCommonAncestor(nodes[0],new TreeNode(pv),new TreeNode(qv))->val<<endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "6 2 8 0 4 7 9 null null 3 5\n2 8", "expected_output": "6"},
            {"input": "6 2 8 0 4 7 9 null null 3 5\n2 4", "expected_output": "2"},
        ],
        "hidden_test_cases": [
            {"input": "2 1\n2 1", "expected_output": "2"},
        ],
    },
    {
        "title": "Level Order Traversal",
        "slug": "level-order-traversal",
        "difficulty": "medium",
        "topics": ["trees", "bfs"],
        "required_skills": ["trees", "bfs"],
        "expected_complexity": {"time": "O(n)", "space": "O(n)"},
        "description": (
            "Given the root of a binary tree, return the level order traversal of its nodes' values "
            "(from left to right, level by level).\n\n"
            "Print each level on a separate line."
        ),
        "input_format": "Level-order traversal: integers and 'null', space-separated",
        "output_format": "Each level's values space-separated, one level per line",
        "constraints": ["0 ≤ number of nodes ≤ 2000", "-1000 ≤ Node.val ≤ 1000"],
        "examples": [
            {"input": "3 9 20 null null 15 7", "output": "3\n9 20\n15 7"},
        ],
        "starter_code": {
            "python": "from collections import deque\nclass TreeNode:\n    def __init__(self, val=0, left=None, right=None):\n        self.val=val;self.left=left;self.right=right\n\ndef level_order(root):\n    # Return list of lists\n    pass\n\nimport sys\ntokens=sys.stdin.read().split()\nif not tokens or tokens[0]=='null':\n    pass\nelse:\n    nodes=[TreeNode(int(t)) if t!='null' else None for t in tokens]\n    for i in range(len(nodes)):\n        if nodes[i]:\n            li,ri=2*i+1,2*i+2\n            if li<len(nodes):nodes[i].left=nodes[li]\n            if ri<len(nodes):nodes[i].right=nodes[ri]\n    for level in level_order(nodes[0]):\n        print(*level)\n",
            "java": "import java.util.*;\npublic class Solution {\n    static class TreeNode{int val;TreeNode left,right;TreeNode(int v){val=v;}}\n    public static List<List<Integer>> levelOrder(TreeNode root){return new ArrayList<>();}\n    public static void main(String[] args){\n        Scanner sc=new Scanner(System.in);\n        String[] tokens=sc.nextLine().trim().split(\" \");\n        if(tokens[0].equals(\"null\")||tokens.length==0)return;\n        TreeNode[] nodes=new TreeNode[tokens.length];\n        for(int i=0;i<tokens.length;i++) nodes[i]=tokens[i].equals(\"null\")?null:new TreeNode(Integer.parseInt(tokens[i]));\n        for(int i=0;i<nodes.length;i++) if(nodes[i]!=null){int li=2*i+1,ri=2*i+2;if(li<nodes.length)nodes[i].left=nodes[li];if(ri<nodes.length)nodes[i].right=nodes[ri];}\n        for(List<Integer> level:levelOrder(nodes[0])){\n            StringBuilder sb=new StringBuilder();\n            for(int v:level){if(sb.length()>0)sb.append(' ');sb.append(v);}\n            System.out.println(sb);\n        }\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nstruct TreeNode{int val;TreeNode*left,*right;TreeNode(int v):val(v),left(nullptr),right(nullptr){}};\nvector<vector<int>>levelOrder(TreeNode*root){return {};}\nint main(){\n    vector<string>tokens;string s;\n    while(cin>>s)tokens.push_back(s);\n    if(tokens.empty()||tokens[0]==\"null\")return 0;\n    vector<TreeNode*>nodes(tokens.size(),nullptr);\n    for(int i=0;i<tokens.size();i++) if(tokens[i]!=\"null\")nodes[i]=new TreeNode(stoi(tokens[i]));\n    for(int i=0;i<nodes.size();i++) if(nodes[i]){int li=2*i+1,ri=2*i+2;if(li<nodes.size())nodes[i]->left=nodes[li];if(ri<nodes.size())nodes[i]->right=nodes[ri];}\n    for(auto&level:levelOrder(nodes[0])){for(int i=0;i<level.size();i++)cout<<level[i]<<(i+1<level.size()?' ':'\\n');}\n}\n",
        },
        "public_test_cases": [
            {"input": "3 9 20 null null 15 7", "expected_output": "3\n9 20\n15 7"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected_output": "1"},
        ],
    },

    # ─── RECURSION ────────────────────────────────────────────────────────────
    {
        "title": "Fibonacci Number",
        "slug": "fibonacci-number",
        "difficulty": "easy",
        "topics": ["recursion", "dynamic_programming"],
        "required_skills": ["recursion"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "The Fibonacci numbers form a sequence, called the Fibonacci sequence, where each number "
            "is the sum of the two preceding ones, starting from 0 and 1.\n\n"
            "F(0) = 0, F(1) = 1\nF(n) = F(n - 1) + F(n - 2), for n > 1\n\n"
            "Given n, calculate F(n)."
        ),
        "input_format": "A single integer n",
        "output_format": "F(n)",
        "constraints": ["0 ≤ n ≤ 30"],
        "examples": [
            {"input": "4", "output": "3"},
            {"input": "10", "output": "55"},
        ],
        "starter_code": {
            "python": "def fib(n):\n    # Write your solution here\n    pass\n\nimport sys\nn = int(sys.stdin.read().strip())\nprint(fib(n))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int fib(int n) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(fib(sc.nextInt()));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint fib(int n) { return 0; }\nint main() { int n; cin >> n; cout << fib(n) << endl; }\n",
        },
        "public_test_cases": [
            {"input": "4", "expected_output": "3"},
            {"input": "10", "expected_output": "55"},
        ],
        "hidden_test_cases": [
            {"input": "0", "expected_output": "0"},
            {"input": "30", "expected_output": "832040"},
        ],
    },
    {
        "title": "Power of Two",
        "slug": "power-of-two",
        "difficulty": "easy",
        "topics": ["recursion", "bit_manipulation"],
        "required_skills": ["recursion"],
        "expected_complexity": {"time": "O(log n)", "space": "O(1)"},
        "description": "Given an integer `n`, return `true` if it is a power of two. Otherwise, return `false`.",
        "input_format": "A single integer n",
        "output_format": "true or false",
        "constraints": ["-2^31 ≤ n ≤ 2^31 - 1"],
        "examples": [
            {"input": "1", "output": "true"},
            {"input": "16", "output": "true"},
            {"input": "3", "output": "false"},
        ],
        "starter_code": {
            "python": "def is_power_of_two(n):\n    # Write your solution here\n    pass\n\nimport sys\nprint('true' if is_power_of_two(int(sys.stdin.read().strip())) else 'false')\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static boolean isPowerOfTwo(int n) { return false; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(isPowerOfTwo(sc.nextInt()) ? \"true\" : \"false\");\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nbool isPowerOfTwo(int n) { return false; }\nint main() { int n; cin>>n; cout<<(isPowerOfTwo(n)?\"true\":\"false\")<<endl; }\n",
        },
        "public_test_cases": [
            {"input": "1", "expected_output": "true"},
            {"input": "16", "expected_output": "true"},
            {"input": "3", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "0", "expected_output": "false"},
            {"input": "-16", "expected_output": "false"},
        ],
    },

    # ─── DYNAMIC PROGRAMMING ──────────────────────────────────────────────────
    {
        "title": "Climbing Stairs",
        "slug": "climbing-stairs",
        "difficulty": "easy",
        "topics": ["dynamic_programming", "recursion"],
        "required_skills": ["dynamic_programming"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "You are climbing a staircase. It takes `n` steps to reach the top.\n\n"
            "Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?"
        ),
        "input_format": "A single integer n",
        "output_format": "Number of distinct ways",
        "constraints": ["1 ≤ n ≤ 45"],
        "examples": [
            {"input": "2", "output": "2"},
            {"input": "3", "output": "3"},
        ],
        "starter_code": {
            "python": "def climb_stairs(n):\n    # Write your solution here\n    pass\n\nimport sys\nprint(climb_stairs(int(sys.stdin.read().strip())))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int climbStairs(int n) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        System.out.println(climbStairs(sc.nextInt()));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint climbStairs(int n){return 0;}\nint main(){int n;cin>>n;cout<<climbStairs(n)<<endl;}\n",
        },
        "public_test_cases": [
            {"input": "2", "expected_output": "2"},
            {"input": "3", "expected_output": "3"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected_output": "1"},
            {"input": "10", "expected_output": "89"},
        ],
    },
    {
        "title": "Coin Change",
        "slug": "coin-change",
        "difficulty": "medium",
        "topics": ["dynamic_programming"],
        "required_skills": ["dynamic_programming"],
        "expected_complexity": {"time": "O(S*n)", "space": "O(S)"},
        "description": (
            "You are given an integer array `coins` representing coins of different denominations "
            "and an integer `amount`.\n\n"
            "Return the fewest number of coins that you need to make up that amount. "
            "If that amount cannot be made up, return -1."
        ),
        "input_format": "Line 1: space-separated coin denominations\nLine 2: target amount",
        "output_format": "Minimum coins needed or -1",
        "constraints": ["1 ≤ coins.length ≤ 12", "1 ≤ coins[i] ≤ 2^31 - 1", "0 ≤ amount ≤ 10^4"],
        "examples": [
            {"input": "1 5 11\n15", "output": "3"},
            {"input": "2\n3", "output": "-1"},
        ],
        "starter_code": {
            "python": "def coin_change(coins, amount):\n    # Write your solution here\n    pass\n\nimport sys\ndata = sys.stdin.read().split('\\n')\ncoins = list(map(int, data[0].split()))\namount = int(data[1])\nprint(coin_change(coins, amount))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int coinChange(int[] coins, int amount) { return -1; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] coins = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(coinChange(coins, Integer.parseInt(sc.nextLine().trim())));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint coinChange(vector<int>&coins,int amount){return -1;}\nint main(){\n    string line;getline(cin,line);\n    istringstream iss(line);vector<int>coins;int x;\n    while(iss>>x)coins.push_back(x);\n    cin>>x;\n    cout<<coinChange(coins,x)<<endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 5 11\n15", "expected_output": "3"},
            {"input": "2\n3", "expected_output": "-1"},
        ],
        "hidden_test_cases": [
            {"input": "1\n0", "expected_output": "0"},
            {"input": "1 2 5\n11", "expected_output": "3"},
        ],
    },
    {
        "title": "Longest Increasing Subsequence",
        "slug": "longest-increasing-subsequence",
        "difficulty": "medium",
        "topics": ["dynamic_programming", "binary_search"],
        "required_skills": ["dynamic_programming"],
        "expected_complexity": {"time": "O(n log n)", "space": "O(n)"},
        "description": (
            "Given an integer array `nums`, return the length of the longest strictly increasing subsequence."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "Length of longest increasing subsequence",
        "constraints": ["1 ≤ nums.length ≤ 2500", "-10^4 ≤ nums[i] ≤ 10^4"],
        "examples": [
            {"input": "10 9 2 5 3 7 101 18", "output": "4"},
            {"input": "0 1 0 3 2 3", "output": "4"},
        ],
        "starter_code": {
            "python": "def length_of_lis(nums):\n    # Write your solution here\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.read().split()))\nprint(length_of_lis(nums))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int lengthOfLIS(int[] nums) { return 0; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(lengthOfLIS(nums));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint lengthOfLIS(vector<int>&nums){return 0;}\nint main(){vector<int>n;int x;while(cin>>x)n.push_back(x);cout<<lengthOfLIS(n)<<endl;}\n",
        },
        "public_test_cases": [
            {"input": "10 9 2 5 3 7 101 18", "expected_output": "4"},
            {"input": "0 1 0 3 2 3", "expected_output": "4"},
        ],
        "hidden_test_cases": [
            {"input": "7 7 7 7 7", "expected_output": "1"},
        ],
    },

    # ─── GREEDY ───────────────────────────────────────────────────────────────
    {
        "title": "Jump Game",
        "slug": "jump-game",
        "difficulty": "medium",
        "topics": ["greedy", "arrays"],
        "required_skills": ["greedy"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "You are given an integer array `nums`. Each element `nums[i]` represents your maximum jump "
            "length at that position. Return `true` if you can reach the last index, else `false`."
        ),
        "input_format": "Space-separated integers on one line",
        "output_format": "true or false",
        "constraints": ["1 ≤ nums.length ≤ 3 × 10^4", "0 ≤ nums[i] ≤ 10^5"],
        "examples": [
            {"input": "2 3 1 1 4", "output": "true"},
            {"input": "3 2 1 0 4", "output": "false"},
        ],
        "starter_code": {
            "python": "def can_jump(nums):\n    # Write your solution here\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.read().split()))\nprint('true' if can_jump(nums) else 'false')\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static boolean canJump(int[] nums) { return false; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(canJump(nums) ? \"true\" : \"false\");\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nbool canJump(vector<int>&nums){return false;}\nint main(){vector<int>n;int x;while(cin>>x)n.push_back(x);cout<<(canJump(n)?\"true\":\"false\")<<endl;}\n",
        },
        "public_test_cases": [
            {"input": "2 3 1 1 4", "expected_output": "true"},
            {"input": "3 2 1 0 4", "expected_output": "false"},
        ],
        "hidden_test_cases": [
            {"input": "0", "expected_output": "true"},
            {"input": "2 0 0", "expected_output": "true"},
        ],
    },
    {
        "title": "Gas Station",
        "slug": "gas-station",
        "difficulty": "medium",
        "topics": ["greedy", "arrays"],
        "required_skills": ["greedy"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "There are `n` gas stations along a circular route. `gas[i]` is the gas at station i. "
            "`cost[i]` is the gas cost to travel from station i to station i+1.\n\n"
            "Return the starting station index if you can travel around the circuit once, or -1 if not."
        ),
        "input_format": "Line 1: gas values (space-separated)\nLine 2: cost values (space-separated)",
        "output_format": "Starting index or -1",
        "constraints": ["n == gas.length == cost.length", "1 ≤ n ≤ 10^5", "0 ≤ gas[i], cost[i] ≤ 10^4"],
        "examples": [
            {"input": "1 2 3 4 5\n3 4 5 1 2", "output": "3"},
            {"input": "2 3 4\n3 4 3", "output": "-1"},
        ],
        "starter_code": {
            "python": "def can_complete_circuit(gas, cost):\n    # Write your solution here\n    pass\n\nimport sys\nlines = sys.stdin.read().strip().split('\\n')\ngas = list(map(int, lines[0].split()))\ncost = list(map(int, lines[1].split()))\nprint(can_complete_circuit(gas, cost))\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int canCompleteCircuit(int[] gas, int[] cost) { return -1; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] gas = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        int[] cost = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        System.out.println(canCompleteCircuit(gas, cost));\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nint canCompleteCircuit(vector<int>&gas,vector<int>&cost){return -1;}\nint main(){\n    string l1,l2;getline(cin,l1);getline(cin,l2);\n    istringstream i1(l1),i2(l2);\n    vector<int>g,c;int x;\n    while(i1>>x)g.push_back(x);\n    while(i2>>x)c.push_back(x);\n    cout<<canCompleteCircuit(g,c)<<endl;\n}\n",
        },
        "public_test_cases": [
            {"input": "1 2 3 4 5\n3 4 5 1 2", "expected_output": "3"},
            {"input": "2 3 4\n3 4 3", "expected_output": "-1"},
        ],
        "hidden_test_cases": [
            {"input": "5\n4", "expected_output": "0"},
        ],
    },

    # ─── SORTING ──────────────────────────────────────────────────────────────
    {
        "title": "Sort Colors",
        "slug": "sort-colors",
        "difficulty": "medium",
        "topics": ["sorting", "arrays", "two_pointers"],
        "required_skills": ["sorting", "two_pointers"],
        "expected_complexity": {"time": "O(n)", "space": "O(1)"},
        "description": (
            "Given an array `nums` with n objects colored red (0), white (1), or blue (2), sort them "
            "in-place so that objects of the same color are adjacent, with colors in the order red, white, and blue.\n\n"
            "You must use only constant extra space."
        ),
        "input_format": "Space-separated integers (0, 1, or 2) on one line",
        "output_format": "Sorted array as space-separated integers",
        "constraints": ["n == nums.length", "1 ≤ n ≤ 300", "nums[i] is 0, 1, or 2"],
        "examples": [
            {"input": "2 0 2 1 1 0", "output": "0 0 1 1 2 2"},
        ],
        "starter_code": {
            "python": "def sort_colors(nums):\n    # Sort in place — Dutch National Flag algorithm\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.read().split()))\nsort_colors(nums)\nprint(*nums)\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static void sortColors(int[] nums) {}\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n        sortColors(nums);\n        System.out.println(Arrays.toString(nums).replaceAll(\"[\\\\[\\\\],]\",\"\").trim());\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvoid sortColors(vector<int>&nums){}\nint main(){vector<int>n;int x;while(cin>>x)n.push_back(x);sortColors(n);for(int i=0;i<n.size();i++)cout<<n[i]<<(i+1<n.size()?' ':'\\n');}\n",
        },
        "public_test_cases": [
            {"input": "2 0 2 1 1 0", "expected_output": "0 0 1 1 2 2"},
            {"input": "2 0 1", "expected_output": "0 1 2"},
        ],
        "hidden_test_cases": [
            {"input": "0", "expected_output": "0"},
        ],
    },
    {
        "title": "Merge Intervals",
        "slug": "merge-intervals",
        "difficulty": "medium",
        "topics": ["sorting", "arrays"],
        "required_skills": ["sorting"],
        "expected_complexity": {"time": "O(n log n)", "space": "O(n)"},
        "description": (
            "Given an array of `intervals` where `intervals[i] = [starti, endi]`, merge all overlapping intervals, "
            "and return an array of the non-overlapping intervals that cover all the intervals in the input."
        ),
        "input_format": "Each line: start end (two integers representing an interval)",
        "output_format": "Each merged interval on a new line: start end",
        "constraints": ["1 ≤ intervals.length ≤ 10^4", "0 ≤ starti ≤ endi ≤ 10^4"],
        "examples": [
            {"input": "1 3\n2 6\n8 10\n15 18", "output": "1 6\n8 10\n15 18"},
        ],
        "starter_code": {
            "python": "def merge(intervals):\n    # Write your solution here\n    pass\n\nimport sys\nlines = sys.stdin.read().strip().split('\\n')\nintervals = [list(map(int, l.split())) for l in lines if l.strip()]\nfor interval in merge(intervals):\n    print(*interval)\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static int[][] merge(int[][] intervals) { return new int[][]{}; }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        List<int[]> list = new ArrayList<>();\n        while(sc.hasNextLine()){String line=sc.nextLine().trim();if(line.isEmpty())break;String[]parts=line.split(\" \");list.add(new int[]{Integer.parseInt(parts[0]),Integer.parseInt(parts[1])});}\n        int[][]res=merge(list.toArray(new int[0][]));\n        for(int[]r:res) System.out.println(r[0]+\" \"+r[1]);\n    }\n}\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\nvector<vector<int>>merge(vector<vector<int>>&i){return {};}\nint main(){\n    vector<vector<int>>intervals;\n    int a,b;\n    while(cin>>a>>b)intervals.push_back({a,b});\n    auto r=merge(intervals);\n    for(auto&x:r)cout<<x[0]<<\" \"<<x[1]<<\"\\n\";\n}\n",
        },
        "public_test_cases": [
            {"input": "1 3\n2 6\n8 10\n15 18", "expected_output": "1 6\n8 10\n15 18"},
            {"input": "1 4\n4 5", "expected_output": "1 5"},
        ],
        "hidden_test_cases": [
            {"input": "1 4\n0 4", "expected_output": "0 4"},
        ],
    },

]


class Command(BaseCommand):
    help = 'Seed the coding problem bank with 40+ problems across all major DSA topics.'

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

