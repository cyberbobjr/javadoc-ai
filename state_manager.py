"""
State management module for Javadoc automation.
Tracks processed files and commits between runs.
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime


logger = logging.getLogger(__name__)


class StateManager:
    """Manages state persistence between automation runs."""
    
    def __init__(self, state_file: str, enabled: bool = True):
        """
        Initialize state manager.
        
        Args:
            state_file: Path to state file
            enabled: Whether state management is enabled
        """
        self.state_file = Path(state_file)
        self.enabled = enabled
        self.state = {
            'last_run': None,
            'last_commit': None,
            'first_run': True,
            'processed_files': [],
            'total_runs': 0,
            'statistics': {
                'total_files_processed': 0,
                'total_classes_documented': 0,
                'total_methods_documented': 0
            }
        }
        
        if self.enabled:
            self._load_state()
    
    def _load_state(self):
        """Load state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    loaded_state = json.load(f)
                    self.state.update(loaded_state)
                    logger.info(f"Loaded state from {self.state_file}")
            else:
                logger.info("No existing state file, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save state to file."""
        try:
            if not self.enabled:
                return
            
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.info(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def is_first_run(self) -> bool:
        """
        Check if this is the first run.
        
        Returns:
            True if first run, False otherwise
        """
        return self.state.get('first_run', True)
    
    def get_last_commit(self) -> Optional[str]:
        """
        Get the last processed commit SHA.
        
        Returns:
            Last commit SHA or None if first run
        """
        return self.state.get('last_commit')
    
    def update_after_run(self, current_commit: str, processed_files: list, 
                        stats: Dict):
        """
        Update state after a successful run.
        
        Args:
            current_commit: SHA of the current commit
            processed_files: List of processed file paths
            stats: Statistics dictionary
        """
        self.state['last_run'] = datetime.now().isoformat()
        self.state['last_commit'] = current_commit
        self.state['first_run'] = False
        self.state['processed_files'] = processed_files
        self.state['total_runs'] += 1
        
        # Update cumulative statistics
        self.state['statistics']['total_files_processed'] += stats.get('total_files', 0)
        self.state['statistics']['total_classes_documented'] += stats.get('total_classes', 0)
        self.state['statistics']['total_methods_documented'] += stats.get('total_methods', 0)
        
        self._save_state()
    
    def get_statistics(self) -> Dict:
        """
        Get cumulative statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.state.get('statistics', {})
    
    def reset(self):
        """Reset state to initial values."""
        self.state = {
            'last_run': None,
            'last_commit': None,
            'first_run': True,
            'processed_files': [],
            'total_runs': 0,
            'statistics': {
                'total_files_processed': 0,
                'total_classes_documented': 0,
                'total_methods_documented': 0
            }
        }
        self._save_state()
        logger.info("State reset to initial values")
