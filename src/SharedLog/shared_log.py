import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from .audit_event import AuditEvent
from .event_type import EventType

class SharedLog:
    """
    A shared log class to store audit events in JSONL files for each run.
    """
    
    def __init__(self, log_file_path: str):
        """
        Initialize the SharedLog with a specified log file path.
        
        Args:
            log_file_path (str): The name of the log file (will be prefixed with './logs/')
            
        Raises:
            OSError: If the logs directory cannot be created or file cannot be accessed
        """
        self.log_file_path = Path("./logs") / log_file_path
        
        # Create logs directory if it doesn't exist
        try:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            # Clear the file for a new run
            with open(self.log_file_path, 'w') as f:
                pass  # Just create/clear the file
        except OSError as e:
            logging.error(f"Failed to initialize log file {self.log_file_path}: {e}")
            raise


    def record_event(self, source: str, details: dict, event_type: Optional[EventType] = None) -> bool:
        """
        Record an audit event to the log file.
        
        Args:
            source (str): The source of the event (e.g., agent name, system component)
            details (dict): Event details to be logged
            event_type (Optional[EventType]): The type of event being logged
            
        Returns:
            bool: True if the event was successfully logged, False otherwise
            
        Raises:
            ValueError: If required parameters are invalid
        """
        # Validate inputs
        if not source or not source.strip():
            logging.error("Source cannot be empty or None")
            return False
            
        if not isinstance(details, dict):
            logging.error(f"Details must be a dictionary, got {type(details)}")
            return False
            
        if event_type is None:
            logging.warning("Event type not specified, using default")
            
        try:
            # Create the audit event
            event = AuditEvent(
                source=source.strip(),
                event_type=event_type.name if event_type else "UNSPECIFIED",
                details=details
            )

            # Serialize the event object to a JSON string
            log_line = json.dumps(event.__dict__)
            
            # Write to file with proper error handling
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
                f.flush() 
                
            return True
            
        except (TypeError, ValueError) as e:
            logging.error(f"Data serialization error when logging event from {source}: {e}")
            return False
            
        except OSError as e:
            logging.error(f"File I/O error when writing to {self.log_file_path}: {e}")
            return False
            
        except Exception as e:

            logging.error(f"Couldn't log the data error happened{e}")
            return False
        

    
    def get_full_logs(self) -> List[Dict[str, Any]]:
        """
        Reads the entire .jsonl log file and returns all events.
        
        Returns:
            List[Dict[str, Any]]: List of all logged events as dictionaries.
                                 Returns empty list if file doesn't exist or is empty.
        
        Raises:
            OSError: If there are file access issues
            ValueError: If log file contains invalid JSON data
        """
        events = []
        
        # Check if log file exists
        if not self.log_file_path.exists():
            logging.warning(f"Log file {self.log_file_path} does not exist")
            return events
        
        # Check if file is empty
        if self.log_file_path.stat().st_size == 0:
            logging.info(f"Log file {self.log_file_path} is empty")
            return events
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    try:
                        event_data = json.loads(line)
                        events.append(event_data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Invalid JSON on line {line_number} in {self.log_file_path}: {e}")
                        # Continue processing other lines instead of failing completely
                        continue
            
            logging.info(f"Successfully loaded {len(events)} events from {self.log_file_path}")
            return events
        
        except OSError as e:
            logging.error(f"File I/O error while reading from {self.log_file_path}: {e}")
            raise
            
        except Exception as e:
            logging.error(f"Unexpected error while reading logs from {self.log_file_path}: {e}")
            raise