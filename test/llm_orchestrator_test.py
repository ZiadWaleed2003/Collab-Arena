"""
Test script for the LLM-powered LangGraph Coordination Engine

This script demonstrates how the orchestrator agent intelligently analyzes
tasks and designs multi-agent architectures using LLM reasoning.
"""
from src.OrchestrationLayer.coordination_engine import LangGraphCoordinationEngine

def test_orchestrator_analysis():
    """Test the LLM-powered orchestrator agent"""
    
    print("🚀 Testing LLM-Powered Orchestration Engine\n")
    
    # Create test configurations
    test_cases = [
        {
            "name": "Web Development Task",
            "config": {
                "task_description": "Build a modern e-commerce website with user authentication, product catalog, shopping cart, payment processing, and admin dashboard. The site should be responsive and include real-time notifications.",
                "user_preferences": {
                    "memory_mode": "shared",
                    "communication_mode": "blackboard"
                },
                "environment_config": {
                    "available_tools": ["web_development", "database", "payment_apis"],
                    "constraints": {"timeline": "6 weeks", "team_size": "flexible"},
                    "success_criteria": "Fully functional e-commerce platform"
                }
            }
        },
        {
            "name": "Data Science Research",
            "config": {
                "task_description": "Analyze customer behavior patterns from e-commerce data to predict churn. Need to clean data, perform exploratory analysis, build ML models, validate results, and create executive summary with actionable insights.",
                "user_preferences": {
                    "preferred_agent_count": 3
                },
                "environment_config": {
                    "available_tools": ["python", "sql", "ml_libraries"],
                    "constraints": {"data_sensitivity": "high"},
                    "success_criteria": "Accurate churn prediction model with business recommendations"
                }
            }
        }
    ]
    
    # Initialize the coordination engine
    engine = LangGraphCoordinationEngine()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{'='*60}")
        print(f"TEST CASE {i}: {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            # Test just the orchestrator analysis (without full workflow)
            orchestrator_agent = engine._create_orchestrator_agent()
            analysis_prompt = engine._create_task_analysis_prompt(
                test_case["config"],
                test_case["config"]["user_preferences"],
                []
            )
            
            print("\n📋 ANALYSIS PROMPT:")
            print("-" * 40)
            print(analysis_prompt[:500] + "..." if len(analysis_prompt) > 500 else analysis_prompt)
            
            print("\n🤖 LLM ORCHESTRATOR ANALYSIS:")
            print("-" * 40)
            
            # Get orchestrator response
            orchestrator_response = orchestrator_agent.generate_response(
                problem=analysis_prompt,
                recent_messages=[]
            )
            
            print(orchestrator_response)
            
            # Parse the response
            task_analysis, agent_plan = engine._parse_orchestrator_response(orchestrator_response)
            
            print("\n📊 PARSED RESULTS:")
            print("-" * 40)
            print(f"Task Type: {task_analysis.get('task_type', 'Unknown')}")
            print(f"Complexity: {task_analysis.get('complexity_level', 'Unknown')}")
            print(f"Confidence: {task_analysis.get('confidence_score', 'Unknown')}")
            print(f"Agent Count: {len(agent_plan)}")
            
            print("\n👥 PLANNED AGENT TEAM:")
            for j, agent in enumerate(agent_plan, 1):
                print(f"{j}. {agent.get('role', 'Unknown')} ({agent.get('agent_id', 'unknown')})")
                print(f"   Capabilities: {', '.join(agent.get('capabilities', []))}")
                print(f"   Reasoning: {agent.get('reasoning', 'N/A')[:100]}...")
                print()
            
        except Exception as e:
            print(f"❌ Error in test case {i}: {e}")
        
        print("\n")

def test_full_orchestration_workflow():
    """Test the complete orchestration workflow"""
    print("🔄 Testing Full Orchestration Workflow\n")
    
    simple_config = {
        "task_description": "Create a simple blog website with user registration and post creation features",
        "user_preferences": {
            "preferred_agent_count": 2,
            "memory_mode": "shared"
        },
        "environment_config": {
            "available_tools": ["web_development"],
            "constraints": {"timeline": "2 weeks"},
            "success_criteria": "Working blog platform"
        }
    }
    
    engine = LangGraphCoordinationEngine()
    
    try:
        result = engine.run_orchestration(
            task_config=simple_config,
            user_preferences=simple_config["user_preferences"],
            thread_id="test_workflow_001"
        )
        
        print("✅ Orchestration completed successfully!")
        print(f"Final step: {result.get('current_step', 'unknown')}")
        print(f"Agents created: {len(result.get('created_agents', []))}")
        print(f"Orchestration decisions: {len(result.get('orchestration_decisions', []))}")
        
        if result.get('error_message'):
            print(f"⚠️ Errors encountered: {result['error_message']}")
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")

if __name__ == "__main__":
    try:
        # Test orchestrator analysis
        test_orchestrator_analysis()
        
        # Test full workflow  
        test_full_orchestration_workflow()
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
