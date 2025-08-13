from abc import ABC, abstractmethod


class BaseTool(ABC):

    "Abstract class for all the tools"

    def __init__(self):
        
        self.name : str

        self.description : str



    @abstractmethod
    def execute(state : dict , params : dict):
        "a langraph tool to execute action on the enviroment"
        pass