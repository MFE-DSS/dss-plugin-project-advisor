from enum import Enum, auto

class ProjectCheckCategory(Enum):
    """
    Enumeration representing different categories of project checks.
    """

    FLOW = auto()
    AUTOMATION = auto()
    DOCUMENTATION = auto()
    CODE = auto()
    PERFORMANCE = auto()
    ROBUSTNESS = auto()
    API_SERVICE = auto()
    DEPLOYMENT = auto()

class InstanceCheckCategory(Enum):
    """
    Enumeration representing different categories of instance checks.
    """

    USAGE = auto()
    PLATFORM = auto()
    CONFIGURATION = auto()
    PROCESSES = auto()