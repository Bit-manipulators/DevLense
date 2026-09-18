import { Language } from "@/types/api";

export interface DemoExample {
  title: string;
  language: Language;
  code: string;
  error: string;
  question: string;
}

export const demoExamples: DemoExample[] = [
  {
    title: "C++ array boundary",
    language: "cpp",
    code: "#include <iostream>\nusing namespace std;\n\nint main() {\n  int arr[5] = {1, 2, 3, 4, 5};\n  for (int i = 0; i <= 5; i++) {\n    cout << arr[i] << endl;\n  }\n  return 0;\n}",
    error: "Segmentation fault",
    question: "Why is this causing a segmentation fault?"
  },
  {
    title: "Python list range",
    language: "python",
    code: "numbers = [1, 2, 3]\n\nfor i in range(4):\n    print(numbers[i])",
    error: "IndexError: list index out of range",
    question: "Why does this crash on the last loop?"
  },
  {
    title: "JavaScript null access",
    language: "javascript",
    code: "const user = null;\nconsole.log(user.name);",
    error: "TypeError: Cannot read properties of null",
    question: "How should I guard this value?"
  }
];

