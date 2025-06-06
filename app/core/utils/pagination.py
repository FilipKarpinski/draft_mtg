from typing import Annotated

from fastapi import Query


class PaginationParams:
    def __init__(
        self,
        skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
        limit: Annotated[int, Query(ge=1, le=1000, description="Number of items to return")] = 100,
    ):
        self.skip = skip
        self.limit = limit


def get_pagination_params(
    skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=1000, description="Number of items to return")] = 100,
) -> PaginationParams:
    """
    Common pagination dependency for skip and limit parameters.

    Args:
        skip: Number of items to skip (default: 0, minimum: 0)
        limit: Number of items to return (default: 100, minimum: 1, maximum: 1000)

    Returns:
        PaginationParams: Object containing skip and limit values
    """
    return PaginationParams(skip=skip, limit=limit)
