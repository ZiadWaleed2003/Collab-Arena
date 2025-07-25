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
                "id": "analysis_003",
                "problem": "A data scientist has a dataset with 10,000 samples and 50 features. The target variable is continuous. They want to build a predictive model but are concerned about overfitting. What approach should they take?",
                "domain": "machine_learning", 
                "difficulty": "medium"
            }
        ]