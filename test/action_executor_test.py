#!/usr/bin/env python3
"""
Test Action Executor workflow that uses Environment Agent for weather query
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.OrchestrationLayer.action_executor import ActionExecutor
from src.agent import Agent
from src.MemoryModule.memory_manager import MemoryManager

def test_action_executor_weather_scenario():
    """Test Action Executor full workflow for weather query"""
    
    print("🚀 Testing Action Executor Weather Scenario")
    print("=" * 60)
    
    # Create Action Executor
    action_executor = ActionExecutor()
    
    # Create example agents
    example_agents = [
        Agent(
            agent_id="search_specialist", 
            role="Information Search Specialist",
            system_prompt="You are an information search specialist. You search for and retrieve current information from various sources.",
            memory_manager=MemoryManager(memory_type="shared")
        )
    ]
    
    # Task configuration for weather query
    task_config = {
        "task_description": "Get current weather information for Egypt",
        "success_criteria": "Provide current weather data including temperature and conditions",
        "constraints": {"time_limit": "5 minutes", "resources": "search_tools"}
    }
    
    # Problem statement
    problem_statement = "I need to get today's weather information for Egypt including temperature, conditions"
    
    # Environment configuration
    environment_config = {
        "available_tools": ["search_tool", "code_writer_tool", "file_manager_tool"],
        "safety_constraints": ["read_only_mode", "no_external_modifications"]
    }
    
    print("\n📋 Test Configuration:")
    print(f"Task: {task_config['task_description']}")
    print(f"Problem: {problem_statement}")
    print(f"Available Agents: {[agent.agent_id for agent in example_agents]}")
    
    try:
        print("\n🎯 Starting Action Executor workflow...")
        
        # Execute the full workflow
        result = action_executor.execute_with_agents(
            agents=example_agents,
            task_config=task_config,
            problem_statement=problem_statement,
            environment_config=environment_config
        )
        
        print("\n📊 Execution Results:")
        print(f"Final step: {result.get('current_step', 'unknown')}")
        print(f"Execution phase: {result.get('execution_phase', 'unknown')}")
        print(f"Selected agent: {result.get('selected_agent_id', 'none')}")
        print(f"Execution complete: {result.get('execution_complete', False)}")
        print(f"Total decisions: {len(result.get('execution_decisions', []))}")
        
        if result.get('execution_result'):
            print(f"\n🌤️ Weather Query Result:")
            print(f"Success: {result['execution_result'].get('success', False)}")
            print(f"Message: {result['execution_result'].get('message', 'No message')}")
            if result['execution_result'].get('tool_result'):
                print(f"Tool Result: {result['execution_result']['tool_result'][:200]}...")
        
        if result.get('error_message'):
            print(f"\n⚠️ Errors encountered: {result['error_message']}")
        else:
            print(f"\n✅ Action Executor test completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_action_executor_weather_scenario()
