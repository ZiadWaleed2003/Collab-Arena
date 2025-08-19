from typing import Any, Dict
from langchain_core.tools import tool
# from src.EnviromentModule.workspace_manager import WorkspaceManager
from .base_tool import BaseTool
from src.clients import get_search_client

class SearchingTool(BaseTool):


    def __init__(self):
        super().__init__(name="search_tavily",description="Searches the web for information.")
        self.searching_tool = get_search_client()


    

    @tool
    def execute(self, state: dict, params: dict) -> Dict[str, Any]:
        """Search for information using the provided query.
        
        This tool performs web search or knowledge base search to find relevant
        information based on the query. It handles rate limiting and provides
        structured results.
        
        Args:
            state: The current state dictionary
            params: Dictionary containing search parameters including 'query'
            
        Returns:
            Dictionary containing:
            - results: List of search results with title, snippet, and url
            - total_found: Total number of results found
            - query_used: The actual query used for searching
            - success: Boolean indicating if search was successful
            - message: Status message or error description
        """
        try:
            # Extract query from params
            query = params.get('query', '')
            
            # Validate inputs
            if not query or not isinstance(query, str):
                return {
                    "results": [],
                    "total_found": 0,
                    "query_used": query,
                    "success": False,
                    "message": "Invalid query: must be a non-empty string"
                }
                   
            # Clean and prepare query
            cleaned_query = query.strip()[:500]  # Limit query length
            


            response = self.searching_tool.search(cleaned_query)

            results = response['results']

            content = results[0]['content']

            
            return {
                "results": content,
                "total_found": len(content),
                "query_used": cleaned_query,
                "success": True,
                "message": f"Found {len(results)} results for query: {cleaned_query}"
            }
            
        except Exception as e:
            return {
                "results": [],
                "total_found": 0,
                "query_used": params.get('query', '') if isinstance(params.get('query'), str) else "",
                "success": False,
                "message": f"Search error: {str(e)}"
            }



