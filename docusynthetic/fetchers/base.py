"""Base fetcher interface."""

from abc import ABC, abstractmethod
from typing import List

from docusynthetic.models import DocumentContent


class BaseFetcher(ABC):
    """Base class for documentation fetchers."""

    @abstractmethod
    async def fetch(self) -> List[DocumentContent]:
        """Fetch documentation from the source.

        Returns:
            List of DocumentContent objects.
        """
        pass
