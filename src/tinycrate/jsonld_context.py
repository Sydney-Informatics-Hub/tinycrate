"""
JSON-LD Context resolution for RO-Crate
"""

import json
import requests
from pathlib import Path
import logging
from typing import Dict, List, Union, Optional

logger = logging.getLogger(__name__)


class ContextResolutionException(Exception):
    """Exception raised for errors in context resolution"""

    pass


class JSONLDContextResolver:
    """
    Resolves JSON-LD contexts and terms to their fully expanded IRIs

    Handles complex contexts including:
    - Remote contexts (http/https URLs)
    - Context arrays with multiple parts
    - Nested context definitions
    - Prefix mappings
    - Term definitions
    """

    def __init__(self, context: Optional[str] = None):
        """
        Initialize the context resolver

        Args:
            context: The JSON-LD context to resolve. Can be:
                    - A URL string (https://w3id.org/ro/crate/1.1/context)
                    - A path to a local file
                    - A dictionary of context definitions
                    - A list of multiple contexts (URLs, dictionaries, or mixed)
                    - None (defaults to RO-Crate 1.1 context)
        """
        self.raw_context = (
            context if context is not None else "https://w3id.org/ro/crate/1.1/context"
        )
        # The merged, final context mapping
        self.context_map: Dict = {}
        # Cache of downloaded remote contexts
        self._context_cache: Dict = {}

        # Process and resolve the context on initialization
        self._resolve_context()

    def _resolve_context(self) -> None:
        """Process and resolve the context, merging all parts"""
        try:
            # Check if we have a wrapped @context
            if isinstance(self.raw_context, dict) and "@context" in self.raw_context:
                contexts_to_process = self.raw_context["@context"]
                if not isinstance(contexts_to_process, list):
                    contexts_to_process = [contexts_to_process]
            elif isinstance(self.raw_context, list):
                contexts_to_process = self.raw_context
            else:
                contexts_to_process = [self.raw_context]

            # Process each context part in order (later entries override earlier ones)
            for ctx in contexts_to_process:
                if isinstance(ctx, str):
                    # Handle URL or file path
                    if ctx.startswith(("http://", "https://")):
                        # Remote context
                        resolved = self._fetch_remote_context(ctx)
                    else:
                        # Local file
                        resolved = self._load_local_context(ctx)
                elif isinstance(ctx, dict):
                    # Inline context object
                    resolved = ctx
                else:
                    raise ContextResolutionException(
                        f"Unsupported context type: {type(ctx)}"
                    )

                # Merge resolved context into our context map
                self._merge_context(resolved)

        except Exception as e:
            print(f"Error resolving context: {e}")
            raise ContextResolutionException(f"Failed to resolve context: {e}")

    def _fetch_remote_context(self, url: str) -> Dict:
        """Fetch a remote context from a URL"""
        # Check cache first
        if url in self._context_cache:
            return self._context_cache[url]

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Extract @context if it's wrapped
            if "@context" in data:
                context = data["@context"]
            else:
                context = data

            # Cache for future use
            self._context_cache[url] = context
            return context

        except requests.exceptions.RequestException as e:
            raise ContextResolutionException(f"Failed to fetch context from {url}: {e}")
        except json.JSONDecodeError as e:
            raise ContextResolutionException(f"Invalid JSON in context from {url}: {e}")

    def _load_local_context(self, path: str) -> Dict:
        """Load a context from a local file"""
        try:
            filepath = Path(path)
            with filepath.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract @context if it's wrapped
            if "@context" in data:
                return data["@context"]
            return data

        except (json.JSONDecodeError, IOError) as e:
            raise ContextResolutionException(f"Failed to load context from {path}: {e}")

    def _merge_context(self, context: Union[Dict, List, str]):
        """Merge a context into the main context map"""
        if isinstance(context, list):
            # If context is a list, process each item
            for item in context:
                self._merge_context(item)
        elif isinstance(context, str):
            # If it's a string (URL), fetch and process
            resolved = self._fetch_remote_context(context)
            self._merge_context(resolved)
        elif isinstance(context, dict):
            # Add each entry to our context map (overriding existing entries)
            for key, value in context.items():
                self.context_map[key] = value

                # Special handling for @vocab
                if key == "@vocab" and isinstance(value, str):
                    logger.debug(f"Found @vocab: {value}")
        else:
            raise ContextResolutionException(
                f"Unsupported context type: {type(context)}"
            )

    def resolve_term(self, term: str) -> str:
        """
        Resolve a term to its full IRI

        Args:
            term: The term to resolve (e.g., "name", "schema:name", "ldac:corpus")

        Returns:
            The resolved IRI or the original term if not found
        """

        # Skip terms that are already IRIs
        if term.startswith(("http://", "https://")):
            return term

        # Skip JSON-LD keywords
        if term.startswith("@"):
            return term

        # Handle prefixed terms (CURIEs)
        if ":" in term:
            prefix, suffix = term.split(":", 1)
            print(f"Found prefix '{prefix}' and suffix '{suffix}'")
            if prefix in self.context_map:
                print(
                    f"Found prefix '{prefix}' in context map: {self.context_map[prefix]}"
                )
                prefix_value = self.context_map[prefix]
                if isinstance(prefix_value, str):
                    # Simple prefix expansion
                    return f"{prefix_value}{suffix}"
                elif isinstance(prefix_value, dict) and "@id" in prefix_value:
                    # Complex prefix with @id
                    return f"{prefix_value['@id']}{suffix}"
            else:
                print(f"Prefix '{prefix}' not found in context map")

        # Handle direct term lookup
        if term in self.context_map:
            value = self.context_map[term]
            if isinstance(value, str):
                return value
            elif isinstance(value, dict) and "@id" in value:
                return value["@id"]

        # Handle @vocab if present
        if "@vocab" in self.context_map:
            vocab = self.context_map["@vocab"]
            if isinstance(vocab, str):
                return f"{vocab}{term}"

        # If nothing matched, return the original term
        return term

    def get_context_map(self) -> Dict:
        """Get the fully resolved context map"""
        return dict(self.context_map)

    def __str__(self) -> str:
        """String representation showing number of terms in the context"""
        return f"JSONLDContextResolver with {len(self.context_map)} terms"

    def print_context(self) -> None:
        """Print the resolved context for debugging"""
        for key, value in sorted(self.context_map.items()):
            print(f"{key}: {value}")
