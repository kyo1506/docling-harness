## MODIFIED Requirements

### Requirement: Hierarchical chunking of extracted content

The system SHALL split extracted markdown into section groups before classification, reassembling hierarchical chunk fragments into coherent document sections (e.g., each `7.N RQxx` requirement section) so each group carries its heading path and is classified as a unit. Chunks shorter than 40 characters that match no structured rule pattern SHALL be excluded.

#### Scenario: Document is split into hierarchical chunks
- **WHEN** a markdown document with section headers is processed
- **THEN** chunks are created respecting section boundaries, fragments under the same section header are grouped into a single section group, and each chunk carries its heading path for context

#### Scenario: Noise fragments are excluded
- **WHEN** a fragment contains only a running page header or a few stray characters with no rule or criterion pattern
- **THEN** the fragment is excluded from classification

### Requirement: LLM-based classification into three categories

The system SHALL send each section group to a local LLM with a prompt that classifies content into one or more categories: Spec-Driven Development (requirements, acceptance criteria, data models, business rules), Loop Engineering (automation triggers, verifiable outputs, feedback loops), or Harness Engineering (context rules, validation gates, tool requirements). Classification SHALL be augmented by deterministic extraction of structured business rules and acceptance criteria so that no rule or criterion present in the text is lost.

#### Scenario: Chunk containing a requirement is classified
- **WHEN** a section group contains text describing a functional requirement with acceptance criteria
- **THEN** the section group is classified under specs with extracted requirement items and acceptance criteria

#### Scenario: Chunk containing automation trigger is classified
- **WHEN** a section group describes a CI/CD trigger or scheduled job
- **THEN** the section group is classified under loop_engineering with extracted trigger and verifiable output items

#### Scenario: Chunk containing a coding convention rule is classified
- **WHEN** a section group contains an architecture constraint or coding standard
- **THEN** the section group is classified under harness_engineering with extracted context rule and validation gate items

#### Scenario: Chunk fits no category
- **WHEN** a section group contains generic introductory text or table of contents
- **THEN** the section group produces empty arrays and is excluded from final output

### Requirement: Merge and deduplicate classified results

The system SHALL merge all section group classification results into a single consolidated JSON using a lossless programmatic merge that retains every extracted item. The merge SHALL deduplicate only items with identical text, assign stable identifiers to requirements, acceptance criteria, data models, and business rules (e.g., `REQ-01`, `AC-01`, `BR-01`, `DM-01`), and generate a per-category summary describing the counts of extracted items. The merge SHALL NOT discard, summarize, or semantically consolidate items.

#### Scenario: All classified items survive the merge
- **WHEN** section groups are classified and passed to the merge step
- **THEN** the final output contains every extracted requirement, criterion, rule, and model item across all section groups, each with a source reference

#### Scenario: Duplicate requirements across chunks are merged
- **WHEN** two section groups yield items with identical rule text
- **THEN** the final output contains one item for the duplicated text, with both section sources preserved

#### Scenario: Generated identifiers are assigned
- **WHEN** the merge produces the final JSON
- **THEN** requirements, acceptance criteria, business rules, and data models carry stable generated ids in their category ordering
