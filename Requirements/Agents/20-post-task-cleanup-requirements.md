# Post Task Cleanup Agent Requirements

## Purpose and Value Proposition
Ensures codebase hygiene after task completion by removing artifacts and validating philosophy compliance.

## Core Functional Requirements
- FR20.1: MUST analyze git status for all changes
- FR20.2: MUST identify and remove temporary artifacts
- FR20.3: MUST check philosophy compliance
- FR20.4: MUST detect unnecessary complexity
- FR20.5: MUST validate modular design principles
- FR20.6: MUST delegate fixes to appropriate agents

## Input Requirements
- IR20.1: Completed task context
- IR20.2: Git repository state
- IR20.3: Philosophy documents
- IR20.4: File change list

## Output Requirements
- OR20.1: Cleanup actions taken
- OR20.2: Philosophy violations found
- OR20.3: Delegation recommendations
- OR20.4: Final cleanliness report
- OR20.5: Prevention suggestions

## Quality Requirements
- QR20.1: Must not break working functionality
- QR20.2: All temporary files must be identified
- QR20.3: Philosophy checks must be comprehensive
- QR20.4: Reports must be actionable