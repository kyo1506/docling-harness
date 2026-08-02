## Purpose

Extract structured content from multiple document formats (PDF, DOCX, PPTX, XLSX, HTML, Markdown, images, audio, video) into clean, hierarchical markdown using Docling.

## ADDED Requirements

### Requirement: Multi-format document conversion

The system SHALL accept files in PDF, DOCX, PPTX, XLSX, HTML, Markdown, image (PNG, JPG, TIFF), audio (MP3, WAV), and video (MP4, MOV) formats and convert them to structured markdown using Docling's DocumentConverter.

#### Scenario: PDF with tables is converted
- **WHEN** a PDF containing text and tables is provided as input
- **THEN** the output markdown preserves section hierarchy and includes tables as structured markdown tables

#### Scenario: Image with text is OCR-processed
- **WHEN** an image file containing printed text is provided as input
- **THEN** the output markdown contains the OCR-extracted text

#### Scenario: Video file is transcribed
- **WHEN** a video file with spoken audio is provided as input
- **THEN** the output markdown contains the ASR-transcribed text using the Docling ASR pipeline with Whisper

#### Scenario: URL source is fetched and converted
- **WHEN** a URL pointing to an HTML page or PDF is provided as input
- **THEN** the content is fetched and converted to markdown

### Requirement: Structured output preservation

The system SHALL preserve document structure including section headers, tables (as markdown and exportable DataFrames), image captions, and code blocks during extraction.

#### Scenario: Table is extracted with structure
- **WHEN** a document contains a data table
- **THEN** the output includes the table as markdown with correct row and column structure

#### Scenario: Section hierarchy is preserved
- **WHEN** a document has nested sections (e.g., H1 → H2 → H3)
- **THEN** the output markdown reflects the original heading hierarchy using markdown heading levels

### Requirement: Batch source processing

The system SHALL accept a directory or list of sources and process all supported files within it.

#### Scenario: Directory with mixed formats is processed
- **WHEN** a directory containing a PDF, a DOCX, and an MP3 file is provided
- **THEN** all three files are extracted and their markdown outputs are generated
