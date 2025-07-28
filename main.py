import time
import json
import os
from typing import Dict, List
from dataclasses import dataclass, field

from src.CommunicationModule import create_communication
from src.agent import Agent

from input_data.data import load_sample_datasets

class Simulation:
    """
    Main simulation class that orchestrates the multi-agent collaboration
    """
    def __init__(self):
        self.communication_module = create_communication("pubsub")
        self.agents: List[Agent] = []
        self.datasets = load_sample_datasets()
    
    
    def setup_agents(self) -> None:
        """Initialize the agent team with different roles"""
        agent_configs = [
            {
                "id": "analyst_01",
                "role": "Problem Analyst",
                "system_prompt": "You are a Problem Analyst. Your role is to break down complex problems, identify key components, and provide structured analysis. Be methodical and thorough."
            },
            {
                "id": "coordinator_01", 
                "role": "Team Coordinator",
                "system_prompt": "You are a Team Coordinator. Your role is to synthesize team input, facilitate collaboration, and guide the problem-solving process. Focus on organizing ideas and next steps."
            },
            {
                "id": "specialist_01",
                "role": "Domain Specialist", 
                "system_prompt": "You are a Domain Specialist with deep expertise. Your role is to provide specialized insights, identify domain-specific approaches, and suggest advanced techniques."
            },
            {
                "id": "implementer_01",
                "role": "Solution Implementer",
                "system_prompt": "You are a Solution Implementer. Your role is to focus on practical implementation, identify potential issues, and propose concrete next steps."
            }
        ]
        
        self.agents = [
            Agent(config["id"], config["role"], config["system_prompt"])
            for config in agent_configs
        ]
        
                # Setup pubsub topics and subscriptions
        self._setup_pubsub_topics()
    
    def _setup_pubsub_topics(self) -> None:
        """Setup pubsub topics and agent subscriptions based on roles"""
        # Register all agents
        for agent in self.agents:
            self.communication_module.register_agent(agent.agent_id)
        
        # Define topic-based communication structure
        # All agents subscribe to general topics
        general_topics = ["problem_statements", "coordination", "final_solutions"]
        for agent in self.agents:
            for topic in general_topics:
                self.communication_module.subscribe(agent.agent_id, topic)
        
        # Role-specific topic subscriptions
        role_topics = {
            "Problem Analyst": ["analysis_requests", "problem_breakdown"],
            "Team Coordinator": ["coordination", "status_updates", "team_sync"],
            "Domain Specialist": ["technical_insights", "expert_consultation"],
            "Solution Implementer": ["implementation_plans", "technical_details"]
        }
        
        for agent in self.agents:
            if agent.role in role_topics:
                for topic in role_topics[agent.role]:
                    self.communication_module.subscribe(agent.agent_id, topic)
        
        print("📡 Pubsub Communication Setup:")
        print(f"   Topics created: {self.communication_module.get_all_topics()}")
        for agent in self.agents:
            subscriptions = self.communication_module.get_subscriptions(agent.agent_id)
            print(f"   {agent.role} ({agent.agent_id}): {list(subscriptions)}")
    
    def run_simulation(self, problem_data: Dict, max_steps: int = 2) -> Dict:
        """
        Run a single simulation scenario
        """
        print(f"\n{'='*80}")
        print(f"STARTING SIMULATION: {problem_data['id']}")
        print(f"Domain: {problem_data['domain']} | Difficulty: {problem_data['difficulty']}")
        print(f"{'='*80}")
        print(f"PROBLEM: {problem_data['problem']}")
        print(f"{'='*80}\n")
        
        # Clear communication module for new simulation
        self.communication_module.clear()
        
        # Initialize problem message to problem_statements topic
        self.communication_module.publish_message(
            agent_id="system",
            agent_role="System",
            content=f"PROBLEM TO SOLVE: {problem_data['problem']}",
            topic="problem_statements",
            message_type="problem_statement"
        )
        
        # Run collaboration steps
        for step in range(max_steps):
            print(f"\n--- COLLABORATION STEP {step + 1} ---")
            
            # Each agent takes a turn
            for agent in self.agents:
                print(f"\n🤖 {agent.role} ({agent.agent_id}) is thinking...")
                
                # Agent uses communication module and generates response
                message_id = agent.act(self.communication_module, problem_data['problem'])
                
                # Display the response
                messages = self.communication_module.get_all_messages()
                latest_msg = messages[-1]
                print(f"💬 Response: {latest_msg.content}")
                
                # Add small delay for readability
                time.sleep(0.5)
            
            print(f"\n--- END OF STEP {step + 1} ---")
        
        # Return simulation results
        return {
            "problem_id": problem_data['id'],
            "total_messages": len(self.communication_module.get_all_messages()),
            "final_state": self.communication_module.get_conversation_history(),
            "agents_participated": len(self.agents)
        }
    
    def save_results_to_json(self, results: List[Dict]) -> None:
        """
        Save simulation results to JSON files in results folder
        Each problem gets its own JSON file with problem ID and solution
        """
        # Create results directory if it doesn't exist
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        for result in results:
            # Extract solution from the final conversation state
            solution = self._extract_solution_from_conversation(result['final_state'])
            
            # Create result data structure
            result_data = {
                "problem_id": result['problem_id'],
                "solution": solution,
                "metadata": {
                    "total_messages": result['total_messages'],
                    "agents_participated": result['agents_participated'],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            # Save to JSON file
            filename = f"{result['problem_id']}_solution.json"
            filepath = os.path.join(results_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved solution for {result['problem_id']} to {filepath}")
    
    def _extract_solution_from_conversation(self, conversation_history: str) -> str:
        """
        Extract the collaborative solution from the conversation history
        """
        # For now, we just gonna return the full conversation as the solution
        return conversation_history
    
    def run_all_simulations(self) -> List[Dict]:
        """
        Run simulations for all problems in the dataset
        """
        print("🚀 STARTING COLLAB ARENA SIMULATION")
        print("Testing Pub-Sub Communication Protocol with LLM-Powered Agents")
        print(f"Dataset Size: {len(self.datasets)} problems")
        print(f"Agent Team Size: {len(self.agents)} agents")
        
        results = []
        
        for i, problem in enumerate(self.datasets):
            print(f"\n\n📊 SIMULATION {i+1}/{len(self.datasets)}")
            result = self.run_simulation(problem)
            results.append(result)
            
            # Brief pause between simulations
            if i < len(self.datasets) - 1:
                print(f"\n⏳ Preparing next simulation...")
                time.sleep(2)
        
        return results
    
    def print_final_summary(self, results: List[Dict]) -> None:
        """Print summary of all simulation results"""
        print(f"\n\n{'='*80}")
        print("🎯 SIMULATION SUMMARY")
        print(f"{'='*80}")
        
        total_messages = sum(r['total_messages'] for r in results)
        avg_messages = total_messages / len(results) if results else 0
        
        print(f"✅ Completed Simulations: {len(results)}")
        print(f"📝 Total Messages Generated: {total_messages}")
        print(f"📊 Average Messages per Problem: {avg_messages:.1f}")
        print(f"🤖 Agents in Team: {results[0]['agents_participated'] if results else 0}")
        
        print(f"\n📋 Problem Breakdown:")
        for result in results:
            print(f"  • {result['problem_id']}: {result['total_messages']} messages")
        
        print(f"\n🏆 Simulation completed successfully!")
        print("The Pub-Sub Communication protocol is working correctly.")

def main():
    """
    Main function to run the CollaB Arena simulation
    """
    # Create simulation instance
    simulation = Simulation()
    
    # Setup agent team
    simulation.setup_agents()
    
    # Run all simulations
    results = simulation.run_all_simulations()
    
    # Save results to JSON files
    simulation.save_results_to_json(results)
    
    # Print final summary
    simulation.print_final_summary(results)

if __name__ == "__main__":
    main()