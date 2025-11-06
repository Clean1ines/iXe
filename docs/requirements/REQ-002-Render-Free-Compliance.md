# REQ-002: Render Free Tier Compliance

## Description
The web API component of the system SHALL be deployable and function correctly within the resource constraints of Render's Free tier, specifically the memory limit.

## Rationale
To utilize free hosting resources for the web API service.

## Acceptance Criteria
- The web API service image, when built using `requirements_web.txt`, MUST fit within the Render Free tier memory limits.
- The web API service MUST start and run without Out of Memory errors on Render's Free tier.
- The web API service MUST maintain its core functionality while adhering to the memory constraint.

