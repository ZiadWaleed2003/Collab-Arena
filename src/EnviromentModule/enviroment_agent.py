import operator
import logging
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.clients import get_nvidia_llm
from .tools import utils as tool_utils

# Configure logging
logger = logging.getLogger(__name__)


# Agent State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]



class EnviromentAgent:
    """
    A LangGraph agent for handling environment-related tool operations.
    This agent manages tool execution for the action executor.
    """
    def __init__(self):
        """
        Initializes the agent with a set of tools and a language model.
        """
        logger.info("Initializing Environment Agent...")
        self.tools = tool_utils.AGENT_TOOLS
        self.llm   = get_nvidia_llm()
        self.model = self.llm.bind_tools(self.tools)
        # The compiled graph is stored as an instance variable
        self.graph = self._build_graph()
        
        logger.info(f"Environment Agent initialized with {len(self.tools)} tools: {[tool.name for tool in self.tools if hasattr(tool, 'name')]}")
        print(f"Environment Agent initialized with {len(self.tools)} tools: {[tool.name for tool in self.tools if hasattr(tool, 'name')]}")

    def _build_graph(self):
        """
        Builds the LangGraph workflow.
        """
        logger.debug("Building LangGraph workflow...")
        workflow = StateGraph(AgentState)

        # Define the graph nodes 
        workflow.add_node("agent", self._should_continue)
        workflow.add_node("action", ToolNode(self.tools))

        # Define the edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._decide_next_step
        )
        workflow.add_edge("action", "agent")

        # Compile and return the graph
        compiled_graph = workflow.compile()
        logger.debug("LangGraph workflow compiled successfully")
        return compiled_graph

    def _should_continue(self, state: AgentState) -> dict:
        """
        The 'agent' node. Invokes the model with the current state.
        """
        logger.debug("Executing agent node - invoking model...")
        print("---AGENT NODE---")
        response = self.model.invoke(state["messages"])
        logger.debug("Model response received")
        return {"messages": [response]}

    def _decide_next_step(self, state: AgentState) -> str:
        """
        The conditional edge. Decides whether to call a tool or end.
        """
        logger.debug("Deciding next step...")
        print("---DECIDING NEXT STEP---")
        if state["messages"][-1].tool_calls:
            logger.info("Decision: Continue to action (tool calls detected)")
            print("Decision: Continue to action.")
            return "action"
        else:
            logger.info("Decision: End (no tool calls)")
            print("Decision: End.")
            return END

    def run(self, user_input: str):
        """
        The public method to run a query through the agent.
        Returns the final result for the action executor.
        """
        logger.info(f"Starting Environment Agent execution for input: '{user_input}'")
        inputs = {"messages": [HumanMessage(content=user_input)]}
        print(f"\n--- Running Agent for: '{user_input}' ---\n")
        
        try:
            # Stream the execution to show the steps
            for event in self.graph.stream(inputs, stream_mode="values"):
                logger.debug("Processing graph event...")
                event["messages"][-1].pretty_print()
                print("\n---\n")
            
            logger.info("Environment Agent execution completed successfully")
        except Exception as e:
            logger.error(f"Error during Environment Agent execution: {str(e)}")
            raise


if __name__ == "__main__":
    # Simple test without tool binding to see the agent work
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        agent = EnviromentAgent()
        
        # Test with a simple question that doesn't require tools
        agent.run("What's the weather now in egypt u can use the tool called searching_tool defined for you")
        
    except Exception as e:
        print(f"Test failed: {e}")
        
        # Fallback test - create agent without tools
        print("\n--- Testing without tool binding ---")
        from src.clients import get_nvidia_llm
        
        llm = get_nvidia_llm()
        response = llm.invoke("Hello, can you introduce yourself?")
        print("Direct LLM response:")
        print(response.content)