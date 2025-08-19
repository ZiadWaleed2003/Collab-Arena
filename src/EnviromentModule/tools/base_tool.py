from abc import ABC, abstractmethod


class BaseTool(ABC):

    "Abstract class for all the tools"

    def __init__(self , name , description):
        
        self.name = name
        self.description = description

    @abstractmethod
    def execute(tool_input: dict):
        "a langraph tool to execute action on the enviroment"
        pass