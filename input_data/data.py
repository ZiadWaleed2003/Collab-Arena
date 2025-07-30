from typing import Dict, List


def load_sample_datasets() -> List[Dict]:
        """
        Load sample problems from m500 dataset (simulated for demo)
        In real implementation, this would load actual dataset files
        """
        return [
            {
                "id": "math_001",
                "problem": "A company has 3 factories producing widgets. Factory A produces 100 widgets/day, Factory B produces 150 widgets/day, and Factory C produces 200 widgets/day. If the company needs to produce 10,000 widgets in the minimum number of days, how should they allocate production?",
                "domain": "optimization",
                "difficulty": "medium"
            },
            {
                "id": "logic_002", 
                "problem": "In a tournament, each team plays every other team exactly once. If there are 8 teams total and each game has exactly one winner, what's the minimum number of games needed to determine a clear overall winner?",
                "domain": "combinatorics",
                "difficulty": "hard"
            },
            {
                "id": "algebra_003",
                "domain": "algebra", 
                "difficulty": "medium",
                "problem": "Given the system: x² + y = 7 and 2x - y = 1. Find all solutions (x, y) and substitute back in the formulas to verify your answer."
            }
        ]