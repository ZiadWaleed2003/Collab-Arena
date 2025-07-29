import json
import os
from datetime import datetime
from typing import List, Dict

from src.CommunicationModule.communication_manager import CommunicationManager, CommunicationMode
from src.agent import Agent
from input_data.data import load_sample_datasets


def run_on_blackboard(problem: str, rounds: int = 3) -> CommunicationManager:
    """
    Run agents using BlackBoard communication protocol
    Returns the CommunicationManager for result extraction
    """
    # Create communication manager with BlackBoard mode
    comm_manager = CommunicationManager(CommunicationMode.BLACKBOARD)
    
    # Create agents
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
    
    # Register all agents with the communication manager
    for agent in agents:
        comm_manager.register_agent(agent)
    
    # Run simulation rounds
    for round_num in range(rounds):
        print(f"Round {round_num + 1}/{rounds}")
        for agent in agents:
            result = agent.act(comm_manager, problem)
            print(f"  {agent.role} ({agent.agent_id}): {result}")
    
    return comm_manager


def extract_conversation_history(comm_manager: CommunicationManager) -> str:
    """
    Extract conversation history from the communication manager
    """
    # Get messages from the BlackBoard implementation
    blackboard = comm_manager.blackboard_impl
    
    if not blackboard.messages:
        return "No messages exchanged."
    
    history = "=== BLACKBOARD CONVERSATION HISTORY ===\n\n"
    
    for i, msg in enumerate(blackboard.messages, 1):
        timestamp = msg.timestamp.strftime("%H:%M:%S")
        history += f"[{i}] {timestamp} | From: {msg.sender_id}\n"
        history += f"Topic: {msg.topic}\n"
        history += f"Content: {msg.content}\n"
        history += "-" * 60 + "\n"
    
    return history


def extract_raw_messages(comm_manager: CommunicationManager) -> List[Dict]:
    """
    Extract raw message data for JSON serialization
    """
    blackboard = comm_manager.blackboard_impl
    
    raw_messages = []
    for msg in blackboard.messages:
        raw_msg = {
            "sender_id": msg.sender_id,
            "recipient_id": msg.recipient_id,
            "topic": msg.topic,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        }
        raw_messages.append(raw_msg)
    
    return raw_messages


def get_communication_stats(comm_manager: CommunicationManager) -> Dict:
    """
    Get statistics about the communication session
    """
    blackboard = comm_manager.blackboard_impl
    # shared_log = comm_manager.shared_log
    
    stats = {
        "total_messages": len(blackboard.messages),
        # "total_logged_messages": len(shared_log.logs),
        "registered_agents": len(blackboard.agents),
        "communication_mode": "BLACKBOARD",
        "agents": list(blackboard.agents.keys())
    }
    
    # Message count per agent
    agent_message_counts = {}
    for msg in blackboard.messages:
        agent_message_counts[msg.sender_id] = agent_message_counts.get(msg.sender_id, 0) + 1
    
    stats["messages_per_agent"] = agent_message_counts
    
    return stats


# -------------------------------------------------------------
# Main loop
# -------------------------------------------------------------
if __name__ == "__main__":
    datasets = load_sample_datasets()
    out_dir = "./test_results/blackboard"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Starting BlackBoard communication tests...")
    
    for case in datasets:
        cid = case["id"]
        problem = case["problem"]
        
        print(f"\n=== Processing Case {cid} ===")
        print(f"Domain: {case['domain']} | Difficulty: {case['difficulty']}")

        
        # Run the simulation
        comm_manager = run_on_blackboard(problem)
        
        # Extract results
        conversation_history = extract_conversation_history(comm_manager)
        raw_messages = extract_raw_messages(comm_manager)
        stats = get_communication_stats(comm_manager)
        
        # Human-readable dump
        with open(f"{out_dir}/case_{cid}.txt", "w", encoding="utf-8") as f:
            f.write(f"CASE ID: {cid}\n")
            f.write(f"DOMAIN: {case['domain']} | DIFFICULTY: {case['difficulty']}\n")
            f.write(f"COMMUNICATION MODE: BLACKBOARD\n")
            f.write("-" * 80 + "\n")
            f.write("PROBLEM:\n" + problem + "\n\n")
            f.write(conversation_history)
            f.write("\n" + "=" * 60 + "\n")
            f.write("COMMUNICATION STATISTICS:\n")
            f.write(json.dumps(stats, indent=2))
        
        # Raw JSON dump
        with open(f"{out_dir}/case_{cid}_raw.json", "w", encoding="utf-8") as f:
            json.dump({
                "case_info": case,
                "messages": raw_messages,
                "statistics": stats
            }, f, indent=2)
        
        print(f"  Results saved: {stats['total_messages']} messages exchanged")
    
    print(f"\nAll done – check {out_dir}")
    print("BlackBoard communication tests completed!")