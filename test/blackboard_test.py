import json
import os
from typing import List, Dict

from src.CommunicationModule.communication_manager import CommunicationManager, CommunicationMode
from src.agent import Agent
from input_data.data import load_sample_datasets


def run_on_blackboard(problem: str, rounds: int = 3) -> CommunicationManager:
    """
    Run agents using BlackBoard communication protocol
    Returns the CommunicationManager and agents for result extraction
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

    return comm_manager, agents


def extract_conversation_history(comm_manager: CommunicationManager , domain) -> str:
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
        history += f"[{i}] {timestamp} | From: {msg.agent_id}\n"
        history += f"Topic: {domain}\n"
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
            "sender_id": msg.agent_id,
            "recipient_id": msg.recipient_id,
            "topic": msg.message_type,
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
        agent_message_counts[msg.agent_id] = agent_message_counts.get(msg.agent_id, 0) + 1
    
    stats["messages_per_agent"] = agent_message_counts
    
    return stats
def get_token_usage_stats(agents: List[Agent]) -> Dict:
    """
    Get token usage statistics from all agents
    """
    total_tokens = 0
    total_api_calls = 0
    agent_stats = {}
    
    for agent in agents:
        if hasattr(agent, 'get_token_stats'):
            stats = agent.get_token_stats()
            agent_stats[agent.agent_id] = stats
            total_tokens += stats.get("total_tokens", 0)
            total_api_calls += stats.get("api_calls", 0)
    
    return {
        "total_tokens_used": total_tokens,
        "total_api_calls": total_api_calls,
        "average_tokens_per_call": total_tokens / total_api_calls if total_api_calls > 0 else 0,
        "token_usage_per_agent": agent_stats
    }


def get_efficiency_metrics(comm_stats: Dict, token_stats: Dict) -> Dict:
    """
    Calculate efficiency metrics for communication mode comparison
    """
    total_messages = comm_stats.get("total_messages", 0)
    total_tokens = token_stats.get("total_tokens_used", 0)
    
    return {
        "tokens_per_message": total_tokens / total_messages if total_messages > 0 else 0,
        "messages_per_token": total_messages / total_tokens if total_tokens > 0 else 0,
        "communication_efficiency_score": (total_messages * 100) / total_tokens if total_tokens > 0 else 0
    }



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
        comm_manager, agents = run_on_blackboard(problem)

        # Extract results
        conversation_history = extract_conversation_history(comm_manager, case["domain"])
        raw_messages = extract_raw_messages(comm_manager)
        comm_stats = get_communication_stats(comm_manager)
        token_stats = get_token_usage_stats(agents)
        efficiency_metrics = get_efficiency_metrics(comm_stats, token_stats)

        # Combine all statistics
        comprehensive_stats = {
            "communication_stats": comm_stats,
            "token_usage_stats": token_stats,
            "efficiency_metrics": efficiency_metrics
        }

        # Human-readable dump
        with open(f"{out_dir}/case_{cid}.txt", "w", encoding="utf-8") as f:
            f.write(f"CASE ID: {cid}\n")
            f.write(f"DOMAIN: {case['domain']} | DIFFICULTY: {case['difficulty']}\n")
            f.write(f"COMMUNICATION MODE: BLACKBOARD\n")
            f.write("-" * 80 + "\n")
            f.write("PROBLEM:\n" + problem + "\n\n")
            f.write(conversation_history)
            f.write("\n" + "=" * 60 + "\n")
            f.write("COMPREHENSIVE STATISTICS:\n")
            f.write(json.dumps(comprehensive_stats, indent=2))

        # Raw JSON dump
        with open(f"{out_dir}/case_{cid}_raw.json", "w", encoding="utf-8") as f:
            json.dump({
                "case_info": case,
                "messages": raw_messages,
                "statistics": comprehensive_stats
            }, f, indent=2)

        print(f"  Results saved: {comm_stats['total_messages']} messages exchanged")
        print(f"  Token usage: {token_stats['total_tokens_used']} tokens")
        print(f"  Efficiency: {efficiency_metrics['tokens_per_message']:.2f} tokens/message")

    print(f"\nAll done – check {out_dir}")
    print("Blackboard communication tests completed!")
