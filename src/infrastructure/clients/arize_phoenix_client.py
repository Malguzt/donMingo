from infrastructure.config.arize_config import ArizeConfig
from typing import Optional, Dict, Any, List
import requests


class ArizePhoenixClient:
    """
    Phoenix client for AI observability, evaluation, and prompt management.
    Based on Arize Phoenix documentation: https://arize.com/docs/phoenix
    """
    
    def __init__(self, config: Optional[ArizeConfig] = None):
        self.config = config or ArizeConfig()
        if not self.config.api_url:
            raise ValueError("API URL is required")
        self.base_url = self.config.api_url.rstrip('/')
        self.api_key = self.config.api_key
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def trace_llm_call(self, 
                       prompt: str, 
                       response: str, 
                       model: str,
                       metadata: Optional[Dict[str, Any]] = None,
                       session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Trace an LLM call for observability and debugging.
        
        Args:
            prompt: The input prompt sent to the LLM
            response: The response received from the LLM
            model: The model name/identifier used
            metadata: Additional metadata for the trace
            session_id: Optional session identifier for grouping traces
            
        Returns:
            Trace information from Phoenix
        """
        trace_data = {
            'prompt': prompt,
            'response': response,
            'model': model,
            'metadata': metadata or {},
            'session_id': session_id,
            'timestamp': self._get_timestamp()
        }
        
        endpoint = f"{self.base_url}/api/v1/traces"
        http_response = requests.post(endpoint, json=trace_data, headers=self.headers)
        http_response.raise_for_status()
        return http_response.json()
    
    def create_prompt(self, 
                     name: str, 
                     content: str, 
                     tags: Optional[List[str]] = None,
                     description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create and store a prompt in Phoenix Prompt Management.
        
        Args:
            name: Name identifier for the prompt
            content: The prompt template content
            tags: Optional tags for categorization
            description: Optional description of the prompt's purpose
            
        Returns:
            Created prompt information
        """
        prompt_data = {
            'name': name,
            'content': content,
            'tags': tags or [],
            'description': description,
            'version': '1.0'
        }
        
        endpoint = f"{self.base_url}/api/v1/prompts"
        response = requests.post(endpoint, json=prompt_data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_prompt(self, name: str, version: Optional[str] = None) -> str:
        """
        Retrieve a stored prompt from Phoenix Prompt Management.
        
        Args:
            name: Name of the prompt to retrieve
            version: Optional version (defaults to latest)
            
        Returns:
            The prompt content
        """
        version_param = f"?version={version}" if version else ""
        endpoint = f"{self.base_url}/api/v1/prompts/{name}{version_param}"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()['content']
    
    def run_evaluation(self, 
                      dataset_id: str, 
                      evaluator_type: str,
                      parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run an evaluation on a dataset using Phoenix's evaluation framework.
        
        Args:
            dataset_id: ID of the dataset to evaluate
            evaluator_type: Type of evaluator to use (e.g., 'hallucination', 'toxicity')
            parameters: Optional parameters for the evaluator
            
        Returns:
            Evaluation results
        """
        eval_data = {
            'dataset_id': dataset_id,
            'evaluator_type': evaluator_type,
            'parameters': parameters or {}
        }
        
        endpoint = f"{self.base_url}/api/v1/evaluations"
        response = requests.post(endpoint, json=eval_data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_dataset(self, 
                      name: str, 
                      data: List[Dict[str, Any]],
                      description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a dataset in Phoenix for experiments and evaluation.
        
        Args:
            name: Name of the dataset
            data: List of data items for the dataset
            description: Optional description of the dataset
            
        Returns:
            Created dataset information
        """
        dataset_data = {
            'name': name,
            'data': data,
            'description': description,
            'item_count': len(data)
        }
        
        endpoint = f"{self.base_url}/api/v1/datasets"
        response = requests.post(endpoint, json=dataset_data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def run_experiment(self, 
                      name: str, 
                      dataset_id: str,
                      parameters: Dict[str, Any],
                      description: Optional[str] = None) -> Dict[str, Any]:
        """
        Run an experiment to test different versions of your application.
        
        Args:
            name: Name of the experiment
            dataset_id: ID of the dataset to use
            parameters: Experiment parameters to test
            description: Optional description of the experiment
            
        Returns:
            Experiment results and traces
        """
        experiment_data = {
            'name': name,
            'dataset_id': dataset_id,
            'parameters': parameters,
            'description': description,
            'status': 'running'
        }
        
        endpoint = f"{self.base_url}/api/v1/experiments"
        response = requests.post(endpoint, json=experiment_data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()