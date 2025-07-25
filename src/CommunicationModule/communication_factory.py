from typing import Union, Literal
from .blackboard import Blackboard
from .direct_communication import DirectCommunication

CommunicationType = Literal["blackboard", "direct"]

class CommunicationFactory:
    """
    Factory class to create and swap between different communication modules
    """
    
    @staticmethod
    def create_communication_module(comm_type: CommunicationType) -> Union[Blackboard, DirectCommunication]:
        """
        Create a communication module of the specified type
        
        Args:
            comm_type: Type of communication module ("blackboard" or "direct")
            
        Returns:
            Communication module instance
        """
        if comm_type == "blackboard":
            return Blackboard()
        elif comm_type == "direct":
            return DirectCommunication()
        else:
            raise ValueError(f"Unknown communication type: {comm_type}")
    
    @staticmethod
    def get_available_types() -> list[str]:
        """Get list of available communication types"""
        return ["blackboard", "direct"]


# Convenience function for quick module creation
def create_communication(comm_type: CommunicationType = "blackboard") -> Union[Blackboard, DirectCommunication]:
    """
    Convenience function to create a communication module
    
    Args:
        comm_type: Type of communication module (default: "blackboard")
        
    Returns:
        Communication module instance
    """
    return CommunicationFactory.create_communication_module(comm_type)
