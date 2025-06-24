# Development Assistant Prompts

## Project Context Prompt

```markdown
I'm developing Tilecraft, an AI-assisted geospatial CLI tool for generating vector tiles from OpenStreetMap data.

Project architecture:
- CLI: Click-based interface with rich output
- Core: OSM processing (osmium-tool), feature extraction, tile generation (tippecanoe)
- AI: Schema generation, style generation, tag disambiguation
- Models: Pydantic configuration and data models
- Utils: Caching, validation, preview generation

Current task: {current_task}

Context for AI assistance:
- Prioritize memory efficiency for large OSM datasets
- Follow geospatial best practices (projections, spatial indexing)
- Implement comprehensive error handling
- Use professional Python patterns (type hints, docstrings)
- Maintain compatibility with existing codebase patterns
```

## Code Review Prompt

```markdown
Review this geospatial processing code for:

Code: {code_snippet}
Context: {code_context}

Review criteria:
1. **GIS Best Practices**:
   - Proper coordinate system handling
   - Spatial indexing where appropriate
   - Memory-efficient processing for large datasets
   - Geometry validation and error handling

2. **Performance**:
   - Efficient algorithms for geospatial operations
   - Memory usage optimization
   - I/O optimization for large files
   - Caching strategy effectiveness

3. **Code Quality**:
   - Type hints and documentation
   - Error handling comprehensiveness
   - Consistency with project patterns
   - Testing considerations

4. **Geospatial Edge Cases**:
   - Invalid geometries
   - Coordinate system edge cases
   - Large dataset handling
   - Network/API failure scenarios

Provide specific improvement suggestions with code examples.
```

## Debugging Prompt

```markdown
Debug this geospatial processing error:

Error: {error_message}
Stack trace: {stack_trace}
Context: {error_context}

Geospatial debugging checklist:
1. **Data Issues**:
   - Invalid geometries (self-intersections, empty geometries)
   - Coordinate system mismatches
   - Data format corruption
   - Missing required attributes

2. **Memory Issues**:
   - Large dataset processing
   - Memory leaks in processing loops
   - Inefficient data structures
   - Temporary file cleanup

3. **External Tool Issues**:
   - osmium-tool command errors
   - tippecanoe parameter issues
   - API rate limiting/network issues
   - Missing system dependencies

4. **Logic Issues**:
   - Bounding box calculation errors
   - Zoom level logic
   - Feature filtering logic
   - File path handling

Provide:
- Most likely cause analysis
- Step-by-step debugging approach
- Specific fix recommendations
- Prevention strategies
```

## Performance Optimization Prompt

```markdown
Optimize this geospatial processing function:

Function: {function_code}
Performance target: {performance_target}
Dataset characteristics: {dataset_info}

Optimization strategies:
1. **Algorithm Optimization**:
   - Spatial indexing (R-tree, KD-tree)
   - Streaming processing for large datasets
   - Parallel processing where appropriate
   - Efficient geometry operations

2. **Memory Optimization**:
   - Generator patterns for large datasets
   - Chunked processing
   - Memory-mapped files where appropriate
   - Garbage collection optimization

3. **I/O Optimization**:
   - Batch file operations
   - Efficient serialization formats
   - Caching frequently accessed data
   - Asynchronous I/O where beneficial

4. **External Tool Optimization**:
   - Optimal osmium-tool parameters
   - Tippecanoe optimization flags
   - Efficient API usage patterns

Provide optimized implementation with performance notes.
```

## Testing Strategy Prompt

```markdown
Create comprehensive tests for this geospatial function:

Function: {function_name}
Functionality: {function_description}
Input/Output: {io_specification}

Test categories needed:
1. **Unit Tests**:
   - Normal operation with valid inputs
   - Edge cases (empty inputs, boundary conditions)
   - Error conditions and exception handling
   - Performance benchmarks

2. **Integration Tests**:
   - End-to-end pipeline testing
   - External tool integration (osmium, tippecanoe)
   - API integration testing
   - File system operations

3. **Geospatial-Specific Tests**:
   - Invalid geometry handling
   - Coordinate system transformations
   - Large dataset processing
   - Precision/accuracy validation

4. **Property-Based Tests**:
   - Geometry invariants
   - Data consistency checks
   - Idempotency testing
   - Round-trip validation

Generate pytest test cases with appropriate fixtures and mocking.
```

## Documentation Prompt

```markdown
Generate comprehensive documentation for this geospatial function:

Function: {function_code}
Context: {function_context}

Documentation requirements:
1. **Docstring** (Google style):
   - Clear description of functionality
   - Parameter descriptions with types
   - Return value description
   - Raises section for exceptions
   - Example usage

2. **Technical Details**:
   - Coordinate system assumptions
   - Performance characteristics
   - Memory usage notes
   - External dependencies

3. **Usage Examples**:
   - Basic usage example
   - Advanced usage with options
   - Error handling example
   - Integration with other functions

4. **Implementation Notes**:
   - Algorithm choices and rationale
   - Performance considerations
   - Limitations and constraints
   - Future improvement opportunities

Generate complete documentation following project standards.
```

## Refactoring Prompt

```markdown
Refactor this code to improve maintainability:

Code: {code_to_refactor}
Issues identified: {identified_issues}

Refactoring goals:
1. **Separation of Concerns**:
   - Extract single-responsibility functions
   - Separate GIS logic from I/O operations
   - Isolate external tool interactions
   - Clean configuration handling

2. **Code Reusability**:
   - Identify common patterns for extraction
   - Create utility functions for repeated operations
   - Implement consistent error handling patterns
   - Standardize API patterns

3. **Testing Improvements**:
   - Make code more testable
   - Reduce external dependencies in core logic
   - Enable better mocking/stubbing
   - Improve error condition testing

4. **Performance**:
   - Eliminate redundant operations
   - Optimize hot paths
   - Improve resource management
   - Better caching strategies

Provide refactored implementation with migration notes.
```

## Architecture Decision Prompt

```markdown
Help me make an architectural decision for Tilecraft:

Decision needed: {decision_topic}
Options considered: {options_list}
Constraints: {constraints}

Evaluation criteria:
1. **Performance Impact**:
   - Processing speed for large datasets
   - Memory usage characteristics
   - Scalability considerations
   - I/O performance implications

2. **Maintainability**:
   - Code complexity
   - Testing ease
   - Future extensibility
   - Team familiarity

3. **Geospatial Considerations**:
   - Standard compliance (OGC, etc.)
   - Tool ecosystem compatibility
   - Data format support
   - Precision/accuracy requirements

4. **User Experience**:
   - CLI usability
   - Error messaging quality
   - Performance predictability
   - Documentation clarity

Provide recommendation with detailed rationale and implementation guidance.
``` 