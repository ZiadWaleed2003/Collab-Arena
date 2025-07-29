import json
import os
from datetime import datetime
from typing import List, Dict

from src.CommunicationModule.blackboard import Blackboard
from src.agent import Agent
from input_data.data import load_sample_datasets

def run_on_blackboard(problem: str, rounds: int = 3) -> Blackboard:
    blackboard = Blackboard()

    agents = [
        Agent("analyst", "Problem Analyst",
              "You break complex problems into clear, actionable components."),
        Agent("coordinator", "Team Coordinator",
              "You coordinate the team, keep track of progress and next steps."),
        Agent("specialist", "Domain Specialist",
              "You provide deep technical or domain-specific insight."),
        Agent("implementer", "Solution Implementer",
              "You turn ideas into concrete, working solutions.")
    ]

    for _ in range(rounds):
        for agent in agents:
            agent.act(blackboard, problem)
    return blackboard


# -------------------------------------------------------------
# Main loop
# -------------------------------------------------------------
if __name__ == "__main__":
    datasets = load_sample_datasets()
    out_dir = "./test_results/blackboard"
    os.makedirs(out_dir, exist_ok=True)

    for case in datasets:
        cid = case["id"]
        problem = case["problem"]

        bb = run_on_blackboard(problem)

        # Human-readable dump
        with open(f"{out_dir}/case_{cid}.txt", "w", encoding="utf-8") as f:
            f.write(f"CASE ID: {cid}\n")
            f.write(f"DOMAIN: {case['domain']} | DIFFICULTY: {case['difficulty']}\n")
            f.write("-" * 80 + "\n")
            f.write("PROBLEM:\n" + problem + "\n\n")
            f.write(bb.get_conversation_history())

        # Raw JSON dump
        raw = [m.__dict__.copy() for m in bb.messages]
        for m in raw:
            m["timestamp"] = m["timestamp"].isoformat()
        with open(f"{out_dir}/case_{cid}_raw.json", "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)

    print(f"All done – check {out_dir}")