from typing import Dict, Any
from datetime import datetime


class Humanfeedback:
    """
    Human Feedback Module for agent configuration approval.
    Presents configuration summary to user and collects approval/modification feedback.
    """

    def __init__(self):
        pass

    def get_feedback(self, config_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Present configuration summary to human and collect feedback.
        
        Args:
            config_summary: Configuration summary from coordination engine
            
        Returns:
            Dict containing feedback, approval status, and any requested modifications
        """
        print("\n" + "="*60)
        print("🤖 AGENT CONFIGURATION REVIEW")
        print("="*60)
        
        # Display configuration summary
        self._display_configuration(config_summary)
        
        # Get user decision
        feedback_response = self._collect_user_feedback()
        
        # Process and return structured feedback
        return self._process_feedback_response(feedback_response)

    def _display_configuration(self, config_summary: Dict[str, Any]) -> None:
        """Display the agent configuration summary in a readable format."""
        
        print(f"\n📋 Task: {config_summary.get('task_description', 'No description')}")
        print(f"🔢 Number of Agents: {config_summary.get('agent_count', 0)}")
        
        # Display agent roles
        roles = config_summary.get('agent_roles', [])
        if roles:
            print(f"\n👥 Configured Agent Roles:")
            for i, role in enumerate(roles, 1):
                print(f"   {i}. {role}")
        
        # Display system configuration
        print(f"\n⚙️  System Configuration:")
        print(f"   • Memory Mode: {config_summary.get('memory_mode', 'shared')}")
        print(f"   • Communication Mode: {config_summary.get('communication_mode', 'blackboard')}")
        print(f"   • Estimated Complexity: {config_summary.get('estimated_complexity', 'Medium')}")
        
        if config_summary.get('approval_iteration', 0) > 1:
            print(f"   • Approval Iteration: {config_summary.get('approval_iteration')}")

    def _collect_user_feedback(self) -> Dict[str, Any]:
        """Collect user feedback through terminal input."""
        
        print("\n" + "-"*60)
        print("Please review the configuration above.")
        print("\nOptions:")
        print("  1. Approve and proceed")
        print("  2. Request modifications")
        print("  3. Get more details")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-3): ").strip()
                
                if choice == "1":
                    return self._handle_approval()
                elif choice == "2":
                    return self._handle_modification_request()
                elif choice == "3":
                    return self._handle_details_request()
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
                    
            except KeyboardInterrupt:
                print("\n\n❌ Operation cancelled by user.")
                return {
                    "approved": False,
                    "cancelled": True,
                    "feedback": "User cancelled the operation",
                    "modifications": []
                }

    def _handle_approval(self) -> Dict[str, Any]:
        """Handle user approval."""
        print("✅ Configuration approved!")
        
        # Optional feedback comment
        comment = input("Any additional comments (optional): ").strip()
        
        return {
            "approved": True,
            "feedback": comment if comment else "Configuration approved",
            "modifications": []
        }

    def _handle_modification_request(self) -> Dict[str, Any]:
        """Handle modification requests."""
        print("\n🔧 What would you like to modify?")
        print("Available modification types:")
        print("  - agent_count: Change number of agents")
        print("  - agent_roles: Modify or add agent roles")
        print("  - memory_mode: Change memory configuration")
        print("  - communication_mode: Change communication method")
        print("  - general: General feedback/changes")
        
        modifications = []
        feedback_text = ""
        
        while True:
            mod_type = input("\nModification type (or 'done' to finish): ").strip().lower()
            
            if mod_type == "done":
                break
            elif mod_type in ["agent_count", "agent_roles", "memory_mode", "communication_mode", "general"]:
                modification = self._get_specific_modification(mod_type)
                if modification:
                    modifications.append(modification)
                    feedback_text += f"{modification['description']}; "
            else:
                print("❌ Invalid modification type. Please use one of the listed types.")
        
        if not modifications:
            general_feedback = input("Please describe what you'd like to change: ").strip()
            feedback_text = general_feedback
            modifications.append({
                "type": "general",
                "description": general_feedback,
                "details": {}
            })
        
        return {
            "approved": False,
            "feedback": feedback_text.rstrip("; "),
            "modifications": modifications
        }

    def _get_specific_modification(self, mod_type: str) -> Dict[str, Any]:
        """Get specific modification details based on type."""
        
        if mod_type == "agent_count":
            try:
                new_count = int(input("Desired number of agents: "))
                return {
                    "type": "agent_count",
                    "description": f"Change agent count to {new_count}",
                    "details": {"new_count": new_count}
                }
            except ValueError:
                print("❌ Invalid number. Skipping this modification.")
                return None
                
        elif mod_type == "agent_roles":
            role_feedback = input("Describe role changes needed: ").strip()
            return {
                "type": "agent_roles",
                "description": f"Role changes: {role_feedback}",
                "details": {"feedback": role_feedback}
            }
            
        elif mod_type == "memory_mode":
            print("Available memory modes: shared, isolated, rbac")
            new_mode = input("Preferred memory mode: ").strip().lower()
            if new_mode in ["shared", "isolated", "rbac"]:
                return {
                    "type": "memory_mode",
                    "description": f"Change memory mode to {new_mode}",
                    "details": {"new_mode": new_mode}
                }
            else:
                print("❌ Invalid memory mode. Skipping this modification.")
                return None
                
        elif mod_type == "communication_mode":
            print("Available communication modes: direct, blackboard, pubsub")
            new_mode = input("Preferred communication mode: ").strip().lower()
            if new_mode in ["direct", "blackboard", "pubsub"]:
                return {
                    "type": "communication_mode",
                    "description": f"Change communication mode to {new_mode}",
                    "details": {"new_mode": new_mode}
                }
            else:
                print("❌ Invalid communication mode. Skipping this modification.")
                return None
                
        elif mod_type == "general":
            description = input("Describe the change needed: ").strip()
            return {
                "type": "general",
                "description": description,
                "details": {"feedback": description}
            }
        
        return None

    def _handle_details_request(self) -> Dict[str, Any]:
        """Handle request for more details - return to feedback loop."""
        print("\n📋 Configuration details displayed above.")
        print("Please review and make your decision.")
        return self._collect_user_feedback()

    def _process_feedback_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure the feedback response."""
        
        # Add timestamp and processing metadata
        processed_response = {
            **response,
            "timestamp": datetime.now().isoformat(),
            "needs_modifications": not response.get("approved", False)
        }
        
        # Log the feedback (optional)
        if response.get("approved"):
            print("\n✅ Feedback recorded: Configuration approved")
        else:
            print("\n📝 Feedback recorded: Modifications requested")
            
        return processed_response


