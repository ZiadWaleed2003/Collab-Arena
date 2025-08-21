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

        self.system_prompt = self._create_system_prompt()

        # Bind tools with system message
        self.model = self.llm.bind_tools(self.tools).with_config({
                "system": self.system_prompt})
        
        # The compiled graph is stored as an instance variable
        self.graph = self._build_graph()
        
        logger.info(f"Environment Agent initialized with {len(self.tools)} tools: {[tool.name for tool in self.tools if hasattr(tool, 'name')]}")
        print(f"Environment Agent initialized with {len(self.tools)} tools: {[tool.name for tool in self.tools if hasattr(tool, 'name')]}")

    def _create_system_prompt(self) -> str:
        """Create system prompt with tool context"""
        tools_info = "\n".join([
            f"- {tool_info['name']}: {tool_info['description']}\n"
            f"  Parameters: {tool_info['parameters']}\n"
            f"  Use for: {tool_info['category']} tasks"
            for tool_info in tool_utils.TOOL_METADATA.values()
        ])
        
        return "".join([
            "You are an Environment Agent responsible for executing tools and managing environment operations.\n\n",
            "Your responsibilities:\n",
            "1. Execute tool operations as requested by the Action Executor\n",
            "2. Provide accurate and detailed results\n",
            "3. Handle errors gracefully and provide helpful feedback\n",
            "4. Ensure safe execution of all operations\n\n",
            
            "AVAILABLE TOOLS:\n",
            f"{tools_info}\n\n",
            
            "Guidelines:\n",
            "- Always validate parameters before tool execution\n",
            "- Provide clear status messages and results\n",
            "- If a tool fails, explain why and suggest alternatives\n",
            "- Use appropriate tools for each task type\n",
            "- Maintain security and safety in all operations\n\n",
            
            "When you receive a request:\n",
            "1. Understand what needs to be done\n",
            "2. Select the appropriate tool(s)\n",
            "3. Execute with proper parameters\n",
            "4. Return clear results and status\n"
        ])

    def _build_graph(self):
        """
        Builds the LangGraph workflow.
        """
        logger.debug("Building LangGraph workflow...")
        workflow = StateGraph(AgentState)

        # Define the graph nodes 
        workflow.add_node("agent", self._call_model)
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

    def _call_model(self, state: AgentState) -> dict:
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

    def run(self, user_input: str) -> str:
        """
        The public method to run a query through the agent.
        Returns the final result from the LLM.
        """
        logger.info(f"Starting Environment Agent execution for input: '{user_input}'")
        inputs = {"messages": [HumanMessage(content=user_input)]}
        print(f"\n--- Running Agent for: '{user_input}' ---\n")
        
        try:
            # invoke() gets the final state directly
            final_state = self.graph.invoke(inputs)
            
            # The final answer is the last message in the state
            final_answer = final_state["messages"][-1]
            
            logger.info("Environment Agent execution completed successfully")
            print("\n--- FINAL ANSWER ---")
            final_answer.pretty_print()
            
            return final_answer.content

        except Exception as e:
            logger.error(f"Error during Environment Agent execution: {str(e)}")
            raise