from __future__ import annotations

from app.analysis.code_analysis_engine import CodeAnalysisEngine
from app.analysis.complexity import ComplexityAnalyzer


def test_complexity_nested_loops_quadratic():
    py_code = """
def twoSum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    report = ComplexityAnalyzer.analyze(py_code, "python", constraints=["1 <= nums.length <= 10^5"])
    assert report.time_complexity in ("O(N²)", "O(N^2)")
    assert report.is_bottleneck is True
    assert "Time Limit Exceeded" in (report.warning or "")


def test_complexity_linear():
    cpp_code = """
int maxSubArray(vector<int>& nums) {
    int max_sum = nums[0];
    int current = 0;
    for (int x : nums) {
        current = max(x, current + x);
        max_sum = max(max_sum, current);
    }
    return max_sum;
}
"""
    report = ComplexityAnalyzer.analyze(cpp_code, "cpp")
    assert report.time_complexity == "O(N)"
    assert report.is_bottleneck is False


def test_code_analysis_detects_unclosed_delimiter():
    bad_code = "def foo():\n    arr = [1, 2, 3\n    return arr"
    result = CodeAnalysisEngine.analyze(code=bad_code, language="python")
    assert result.syntax_valid is False
    assert len(result.syntax_errors) >= 1
    assert any("unclosed" in str(e["message"]).lower() or "syntax" in str(e["message"]).lower() for e in result.syntax_errors)


def test_code_analysis_cpp_array_bounds():
    cpp_code = """
#include <iostream>
using namespace std;
int main() {
    int arr[5] = {1,2,3,4,5};
    for(int i = 0; i <= 5; i++) {
        cout << arr[i] << endl;
    }
    return 0;
}
"""
    result = CodeAnalysisEngine.analyze(code=cpp_code, language="cpp")
    assert result.language == "cpp"
    assert result.primary_finding is not None
    assert "array" in result.primary_finding.summary.lower() or "bounds" in result.primary_finding.summary.lower() or "off-by-one" in result.primary_finding.summary.lower()
