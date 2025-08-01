import json
import os
from datetime import datetime
from typing import List, Dict
from src.CommunicationModule.communication_manager import CommunicationManager, CommunicationMode
from src.agent import Agent
from src.MemoryModule.memory_manager import MemoryManager
from input_data.data import load_sample_datasets






class DateTimeEncoder(json.JSONEncoder):
    """ Custom JSON encoder for datetime objects """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def run_on_pubsub_messenger(problem: str, rounds: int = 3) -> tuple:
    """
    Run agents using PubSub communication protocol
    Returns the CommunicationManager and agents for result extraction
    """
    # Create communication manager with PubSub mode
    comm_manager = CommunicationManager(CommunicationMode.PUBSUB)
    
    # Create shared memory manager for agents
    memory_manager = MemoryManager()
    
    # Create agents with memory integration
    agents = [
        Agent("analyst", "Problem Analyst",
              "You break complex problems into clear, actionable components.", memory_manager),
        Agent("coordinator", "Team Coordinator",
              "You coordinate the team, keep track of progress and next steps.", memory_manager),
        Agent("specialist", "Domain Specialist",
              "You provide deep technical or domain-specific insight.", memory_manager),
        Agent("implementer", "Solution Implementer",
              "You turn ideas into concrete, working solutions.", memory_manager)
    ]
    
    # Register all agents with the communication manager
    for agent in agents:
        comm_manager.register_agent(agent)
    
    # Set up topic subscriptions for PubSub pattern
    pubsub_impl = comm_manager.pubsub_impl
    
    # Define topics based on problem-solving workflow
    topics = ["analysis", "coordination", "technical_insights", "implementation", "status_updates"]
    
    # Subscribe agents to relevant topics using the subscribe_to_topic method
    # Analyst subscribes to coordination and status updates
    agents[0].subscribe_to_topic(comm_manager, "coordination")
    agents[0].subscribe_to_topic(comm_manager, "status_updates")
    
    # Coordinator subscribes to all topics (central hub)
    for topic in topics:
        agents[1].subscribe_to_topic(comm_manager, topic)
    
    # Specialist subscribes to analysis, coordination, and status updates
    agents[2].subscribe_to_topic(comm_manager, "analysis")
    agents[2].subscribe_to_topic(comm_manager, "coordination")
    agents[2].subscribe_to_topic(comm_manager, "status_updates")
    
    # Implementer subscribes to technical insights, coordination, and status updates
    agents[3].subscribe_to_topic(comm_manager, "technical_insights")
    agents[3].subscribe_to_topic(comm_manager, "coordination")
    agents[3].subscribe_to_topic(comm_manager, "status_updates")
    
    print(f"Active topics: {pubsub_impl.get_active_topics()}")
    
    # Run simulation rounds with PubSub messaging pattern
    for round_num in range(rounds):
        print(f"Round {round_num + 1}/{rounds}")
        
        # PubSub workflow: agents act and messages are published to topics based on content
        for agent in agents:
            # Agent processes the problem and publishes to "all" (subscribers will receive based on topics)
            result = agent.act(comm_manager, problem, recipient_id="all")
            
            # # Send additional status updates to specific topics using direct messaging
            # if agent.agent_id == "analyst":
            #     agent.send_direct_message(comm_manager, "all", 
            #                             f"Analysis phase completed", 
            #                             topic="analysis")
                
            # elif agent.agent_id == "coordinator":
            #     agent.send_direct_message(comm_manager, "all", 
            #                             f"Coordination update from {agent.role}", 
            #                             topic="coordination")
                
            # elif agent.agent_id == "specialist":
            #     agent.send_direct_message(comm_manager, "all", 
            #                             f"Technical insights provided", 
            #                             topic="technical_insights")
                
            # elif agent.agent_id == "implementer":
            #     agent.send_direct_message(comm_manager, "all", 
            #                             f"Implementation progress update", 
            #                             topic="implementation")
            
            # # All agents send status updates
            # agent.send_direct_message(comm_manager, "all", 
            #                         f"Status: {agent.role} completed round {round_num + 1}", 
            #                         topic="status_updates")
            
            print(f"  {agent.role} ({agent.agent_id}): {result}")
    
    return comm_manager, agents

def extract_conversation_history(comm_manager: CommunicationManager, domain: str) -> str:
    """
    Extract conversation history from the PubSub communicator
    """
    # Get messages from the PubSub implementation
    pubsub_communicator = comm_manager.pubsub_impl
    
    # Collect all messages from all agent queues
    all_messages = []
    for agent_id, message_queue in pubsub_communicator.message_queues.items():
        all_messages.extend(message_queue)
    
    # Also get messages from message_log
    all_messages.extend(pubsub_communicator.message_log)
    
    # Remove duplicates and sort by timestamp
    unique_messages = []
    seen_ids = set()
    for msg in all_messages:
        if hasattr(msg, 'id') and msg.id not in seen_ids:
            unique_messages.append(msg)
            seen_ids.add(msg.id)
    
    unique_messages.sort(key=lambda x: x.timestamp)
    
    if not unique_messages:
        return "No messages exchanged."
    
    history = "=== PUBSUB MESSENGER CONVERSATION HISTORY ===\n\n"
    
    for i, msg in enumerate(unique_messages, 1):
        timestamp = msg.timestamp.strftime("%H:%M:%S")
        topic = pubsub_communicator._get_topic_from_message(msg)
        subscribers = pubsub_communicator.get_subscribers(topic)
        history += f"[{i}] {timestamp} | From: {msg.agent_id} → Topic: {topic}\n"
        history += f"Subscribers: {', '.join(subscribers) if subscribers else 'None'}\n"
        history += f"Domain: {domain}\n"
        history += f"Content: {msg.content}\n"
        history += "-" * 60 + "\n"
    
    return history

def extract_raw_messages(comm_manager: CommunicationManager) -> List[Dict]:
    """
    Extract raw message data for JSON serialization
    """
    pubsub_communicator = comm_manager.pubsub_impl
    
    # Collect all messages
    all_messages = []
    for message_queue in pubsub_communicator.message_queues.values():
        all_messages.extend(message_queue)
    all_messages.extend(pubsub_communicator.message_log)
    
    # Remove duplicates
    unique_messages = []
    seen_ids = set()
    for msg in all_messages:
        if hasattr(msg, 'id') and msg.id not in seen_ids:
            unique_messages.append(msg)
            seen_ids.add(msg.id)
    
    raw_messages = []
    for msg in unique_messages:
        topic = pubsub_communicator._get_topic_from_message(msg)
        subscribers = list(pubsub_communicator.get_subscribers(topic))
        
        raw_msg = {
            "sender_id": msg.agent_id,
            "topic": topic,
            "subscribers": subscribers,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "message_type": msg.message_type
        }
        raw_messages.append(raw_msg)
    
    return raw_messages

def get_communication_stats(comm_manager: CommunicationManager) -> Dict:
    """
    Get statistics about the PubSub communication session
    """
    pubsub_communicator = comm_manager.pubsub_impl
    
    # Count unique messages
    all_messages = []
    for message_queue in pubsub_communicator.message_queues.values():
        all_messages.extend(message_queue)
    all_messages.extend(pubsub_communicator.message_log)
    
    unique_messages = []
    seen_ids = set()
    for msg in all_messages:
        if hasattr(msg, 'id') and msg.id not in seen_ids:
            unique_messages.append(msg)
            seen_ids.add(msg.id)
    
    stats = {
        "total_messages": len(unique_messages),
        "registered_agents": len(pubsub_communicator.agents),
        "communication_mode": "PUBSUB_MESSENGER",
        "agents": list(pubsub_communicator.agents.keys()),
        "message_queues": len(pubsub_communicator.message_queues),
        "active_topics": pubsub_communicator.get_active_topics(),
        "total_topics": len(pubsub_communicator.topics)
    }
    
    # Message count per agent (published)
    agent_message_counts = {}
    topic_message_counts = {}
    
    for msg in unique_messages:
        # Count messages published by each agent
        agent_message_counts[msg.agent_id] = agent_message_counts.get(msg.agent_id, 0) + 1
        
        # Count messages per topic
        topic = pubsub_communicator._get_topic_from_message(msg)
        topic_message_counts[topic] = topic_message_counts.get(topic, 0) + 1
    
    stats["messages_published_per_agent"] = agent_message_counts
    stats["messages_per_topic"] = topic_message_counts
    
    # Subscription statistics
    subscription_stats = {}
    for agent_id in pubsub_communicator.agents.keys():
        subscriptions = pubsub_communicator.get_agent_subscriptions(agent_id)
        subscription_stats[agent_id] = subscriptions
    
    stats["agent_subscriptions"] = subscription_stats
    
    # Topic subscriber counts
    topic_subscriber_counts = {}
    for topic in pubsub_communicator.get_active_topics():
        subscriber_count = len(pubsub_communicator.get_subscribers(topic))
        topic_subscriber_counts[topic] = subscriber_count
    
    stats["subscribers_per_topic"] = topic_subscriber_counts
    
    return stats

def get_memory_usage_stats(agents: List[Agent]) -> Dict:
    """
    Get memory usage statistics from all agents
    """
    memory_stats = {}
    shared_memory_state = None
    
    for agent in agents:
        agent_memory_info = {
            "short_term_memory_size": agent.get_short_term_memory_size(),
            "short_term_memory_info": agent.get_short_term_memory_info(),
            "recent_events_count": len(agent.get_recent_short_term_events(100)),
            "available_memory_keys": len(agent.get_all_memory_keys())
        }
        memory_stats[agent.agent_id] = agent_memory_info
        
        # Get shared memory state (same for all agents, so we only need it once)
        if shared_memory_state is None:
            shared_memory_state = agent.get_memory_state()
    
    return {
        "agent_memory_stats": memory_stats,
        "shared_memory_state": shared_memory_state,
        "total_shared_memory_keys": len(shared_memory_state) if shared_memory_state else 0
    }

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
    total_topics = comm_stats.get("total_topics", 0)
    
    return {
        "tokens_per_message": total_tokens / total_messages if total_messages > 0 else 0,
        "messages_per_token": total_messages / total_tokens if total_tokens > 0 else 0,
        "messages_per_topic": total_messages / total_topics if total_topics > 0 else 0,
        "communication_efficiency_score": (total_messages * 100) / total_tokens if total_tokens > 0 else 0,
        "topic_utilization_rate": total_topics / len(comm_stats.get("active_topics", [])) if comm_stats.get("active_topics") else 0
    }

def get_pubsub_specific_metrics(comm_stats: Dict) -> Dict:
    """
    Calculate PubSub-specific metrics like fan-out ratios
    """
    subscribers_per_topic = comm_stats.get("subscribers_per_topic", {})
    messages_per_topic = comm_stats.get("messages_per_topic", {})
    
    # Calculate average fan-out (how many subscribers each message reaches)
    total_fanout = 0
    total_messages = 0
    
    for topic, message_count in messages_per_topic.items():
        subscriber_count = subscribers_per_topic.get(topic, 0)
        total_fanout += message_count * subscriber_count
        total_messages += message_count
    
    avg_fanout = total_fanout / total_messages if total_messages > 0 else 0
    
    return {
        "average_fanout_ratio": avg_fanout,
        "total_message_deliveries": total_fanout,
        "broadcast_efficiency": total_fanout / sum(subscribers_per_topic.values()) if sum(subscribers_per_topic.values()) > 0 else 0,
        "topic_coverage": len([t for t in messages_per_topic.values() if t > 0]) / len(subscribers_per_topic) if subscribers_per_topic else 0
    }

# -------------------------------------------------------------
# Main loop
# -------------------------------------------------------------
if __name__ == "__main__":
    datasets = load_sample_datasets()
    out_dir = "./test_results/pubsub_messenger"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Starting PubSub communication tests...")
    
    for case in datasets:
        cid = case["id"]
        problem = case["problem"]
        
        print(f"\n=== Processing Case {cid} ===")
        print(f"Domain: {case['domain']} | Difficulty: {case['difficulty']}")
        
        # Run the simulation
        comm_manager, agents = run_on_pubsub_messenger(problem)
        
        # Extract results
        conversation_history = extract_conversation_history(comm_manager, case["domain"])
        raw_messages = extract_raw_messages(comm_manager)
        comm_stats = get_communication_stats(comm_manager)
        token_stats = get_token_usage_stats(agents)
        memory_stats = get_memory_usage_stats(agents)
        efficiency_metrics = get_efficiency_metrics(comm_stats, token_stats)
        pubsub_metrics = get_pubsub_specific_metrics(comm_stats)
        
        # Combine all statistics
        comprehensive_stats = {
            "communication_stats": comm_stats,
            "token_usage_stats": token_stats,
            "memory_usage_stats": memory_stats,
            "efficiency_metrics": efficiency_metrics,
            "pubsub_specific_metrics": pubsub_metrics
        }
        
        # Human-readable dump
        with open(f"{out_dir}/case_{cid}.txt", "w", encoding="utf-8") as f:
            f.write(f"CASE ID: {cid}\n")
            f.write(f"DOMAIN: {case['domain']} | DIFFICULTY: {case['difficulty']}\n")
            f.write(f"COMMUNICATION MODE: PUBSUB MESSENGER\n")
            f.write("-" * 80 + "\n")
            f.write("PROBLEM:\n" + problem + "\n\n")
            f.write(conversation_history)
            f.write("\n" + "=" * 60 + "\n")
            f.write("COMPREHENSIVE STATISTICS:\n")
            f.write(json.dumps(comprehensive_stats, indent=2, cls=DateTimeEncoder))
        
        # Raw JSON dump
        with open(f"{out_dir}/case_{cid}_raw.json", "w", encoding="utf-8") as f:
            json.dump({
                "case_info": case,
                "messages": raw_messages,
                "statistics": comprehensive_stats
            }, f, indent=2 , cls=DateTimeEncoder)
        
        print(f"  Results saved: {comm_stats['total_messages']} messages exchanged")
        print(f"  Topics used: {len(comm_stats['active_topics'])}")
        print(f"  Token usage: {token_stats['total_tokens_used']} tokens")
        print(f"  Memory usage: {memory_stats['total_shared_memory_keys']} shared memory keys")
        print(f"  Efficiency: {efficiency_metrics['tokens_per_message']:.2f} tokens/message")
        print(f"  Average fanout: {pubsub_metrics['average_fanout_ratio']:.2f} subscribers/message")
    
    print(f"\nAll done – check {out_dir}")
    print("PubSub communication tests completed!")