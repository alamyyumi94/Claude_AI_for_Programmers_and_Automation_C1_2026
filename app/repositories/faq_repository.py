# Any is used because the repository receives a database object whose exact
# MongoDB client/database type is not being enforced here.
from typing import Any

# FAQSource is the Pydantic model used to validate and shape FAQ records
# before they leave the repository layer.
from app.schemas.faq import FAQSource


# MongoDB projection defining exactly which FAQ fields are allowed to leave
# the repository and become application/AI context.
#
# _id is excluded because the application uses faq_id instead.
FAQ_SOURCE_PROJECTION = {
    "_id": 0,
    "faq_id": 1,
    "category": 1,
    "question": 1,
    "answer": 1,
}


class FAQRepository:
    # The repository receives the database dependency instead of creating
    # its own database connection.
    def __init__(
        self,
        database: Any,
    ) -> None:
        # Work specifically with the MongoDB "faqs" collection.
        self.collection = database.faqs


    async def get_by_ids(
        self,
        # List of FAQ IDs requested by another part of the application.
        faq_ids: list[str],
        *,
        # Do not return more than three FAQs by default.
        limit: int = 3,
    ) -> list[FAQSource]:

        # Remove duplicate IDs while preserving their original order,
        # then restrict how many records we are prepared to retrieve.
        requested_ids = list(
            dict.fromkeys(faq_ids)
        )[:limit]

        # Avoid making a database query if there are no IDs to search for.
        if not requested_ids:
            return []

        # Query MongoDB for FAQs whose faq_id is in the requested list.
        # Only records marked active=True are considered approved for use.
        cursor = self.collection.find(
            {
                "faq_id": {
                    "$in": requested_ids,
                },
                "active": True,
            },

            # Return only the approved fields defined in our projection.
            FAQ_SOURCE_PROJECTION,
        )

        # Store matched FAQ objects by faq_id so we can restore the caller's
        # requested order after MongoDB returns the records.
        found: dict[
            str,
            FAQSource,
        ] = {}

        # MongoDB returns an asynchronous cursor, so iterate over it with async for.
        async for document in cursor:
            # Validate the raw MongoDB document against our FAQSource schema.
            faq = FAQSource.model_validate(
                document
            )

            # Store the validated FAQ using its ID as the lookup key.
            found[faq.faq_id] = faq

        # Return only FAQs that were actually found, while preserving the same
        # order in which their IDs were originally requested.
        return [
            found[faq_id]
            for faq_id in requested_ids
            if faq_id in found
        ]


    async def search(
        self,
        # Search text supplied by the application.
        query: str,
        *,
        # Keep retrieved FAQ context intentionally small.
        limit: int = 3,
    ) -> list[FAQSource]:

        # Remove unnecessary whitespace before using the text in a search.
        search_query = query.strip()

        # Do not send an empty search to MongoDB.
        if not search_query:
            return []

        # Force the result count into a safe range of 1 to 3 records.
        # Even if a caller asks for 100 results, this repository will return at most 3.
        safe_limit = max(
            1,
            min(limit, 3),
        )

        # MongoDB performs the retrieval and relevance ranking.
        # Claude is not given direct access to browse or query the FAQ collection.
        pipeline = [

            # Stage 1: keep only active FAQs whose indexed text matches the query.
            {
                "$match": {
                    "active": True,
                    "$text": {
                        "$search":
                            search_query,
                    },
                }
            },

            # Stage 2: rank the matched FAQs by MongoDB's text-search relevance score.
            {
                "$sort": {
                    "score": {
                        "$meta":
                            "textScore",
                    }
                }
            },

            # Stage 3: restrict the amount of FAQ context returned downstream.
            {
                "$limit": safe_limit,
            },

            # Stage 4: expose only approved FAQ fields.
            {
                "$project":
                    FAQ_SOURCE_PROJECTION,
            },
        ]

        # Execute the MongoDB aggregation pipeline.
        cursor = (
            await self.collection.aggregate(
                pipeline
            )
        )

        # Final validated FAQ records will be collected here.
        results: list[FAQSource] = []

        # Read each MongoDB result asynchronously.
        async for document in cursor:
            # Validate each database record before adding it to the result list.
            results.append(
                FAQSource.model_validate(
                    document
                )
            )

        # Return clean, validated FAQSource objects to the application layer.
        return results
