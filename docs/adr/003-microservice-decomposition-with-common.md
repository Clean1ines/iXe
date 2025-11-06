# 003: Microservice Decomposition Leveraging Common Library

## Status
Accepted

## Context
The initial monolithic application faced scalability and resource management challenges, particularly on Render's Free tier (OOM errors). The introduction of the `common` library provided a foundation for sharing models and utilities. The next logical step is to decompose the application into microservices to improve scalability, maintainability, and resource allocation. The `common` library serves as a crucial enabler for this decomposition by providing a consistent data schema and shared logic across services.

## Decision
We decided to decompose the application into the following microservices:
1.  **Web API Service**: Handles user requests, serves frontend, and manages quiz state. Uses `requirements_web.txt`. Depends on `common` for models and potentially `QuizServiceAdapter`.
2.  **Scraping & Checking Service**: Handles FIPI website scraping and answer validation. Uses `requirements_scraping_checking.txt`. Depends on `common` for models and potentially shared utilities.
3.  **Indexing Service**: Handles vector indexing of problems for semantic search. Uses `requirements_indexing.txt`. Depends on `common` for models.
Each service will be containerized and deployed independently. The `common` library will be installed as an editable package (`pip install -e ./common`) in each service that requires it, ensuring consistency and avoiding code duplication.

## Consequences
### Positive:
- **Scalability**: Each service can be scaled independently based on demand.
- **Resource Management**: Heavy dependencies like `playwright` and `qdrant-client` are isolated, allowing the Web API service to run on constrained environments like Render Free tier.
- **Maintainability**: Clear separation of concerns improves code organization and makes it easier to develop and test individual components.
- **Technology Flexibility**: Different services can potentially use different technologies or Python versions if needed (though sharing `common` implies some constraint).
- **Team Development**: Different teams can work on different services with less interference.

### Negative:
- **Complexity**: Microservice architecture introduces complexity in deployment, monitoring, and inter-service communication (e.g., synchronous API calls, message queues).
- **Network Latency**: Communication between services introduces potential latency compared to in-process calls in a monolith.
- **Data Consistency**: Maintaining data consistency across services can be challenging and may require distributed transaction patterns.
- **Common Library Coupling**: Services remain coupled through the `common` library. Changes to `common` may require coordinated updates and testing across multiple services.
- **Operational Overhead**: Requires more sophisticated tooling for deployment, logging, and monitoring compared to a single monolithic application.

