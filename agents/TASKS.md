# Task Management

## Rules and Practice
- aim to have the list of `## Unsorted and Raw Tasks` cleaned up one by one by developing them into main Tasks. Ask the user questions about each before detailing each
- when adding a new main task, follow this pattern:
- **IMMEDIATELY after completing a main task**: move it from Main Active Tasks to Completed section using this conversion:
  - Delete the entire detailed task from Main Active Tasks
  - If pitfalls discovered during Main Task completion, update the `## Pitfalls and Issues to Avoid` section in `agents/DOCUMENTATION.md`
  - Add one concise line to Completed: `- [Task Title] (YYYY-MM-DD): [key outcome/result + any critical lessons learned not already documented in ARCHITECTURE.md or DOCUMENTATION.md]`
  - Keep only info relevant for future development that isn't covered elsewhere in agents folder

--- TASK TEMPLATE ---
### [Task Title]
**Status**: [Pending/In Progress/Blocked/Review] | **Labels**: [label1, label2, label3]
**Description**: [Brief description of what needs to be accomplished and why]

**Requirements to Define**:
- [Requirement 1 with acceptance criteria]
- [Requirement 2 with acceptance criteria]
- [Technical specification or constraint]
- [Integration points or dependencies]
- [Quality/testing requirements]

**Success Criteria** (optional):
- [Measurable outcome 1]
- [Specific behavior or functionality that must work]
- [Performance/quality threshold that must be met]

**Sub-tasks**:
- [ ] Research and Identify all needed frameworks, libraries and already developed code documentation that is needed to complete this main task. Start with a check in `agents/DOCUMENTATION.md` if not read in this session already and continue with a check in `agents/DOCUMENTATION.md` (always first sub-task)
- [ ] Obtain the documentation and code references identified in the previous subtask by using tools and mcp servers including context7, mdfetch, websearch and any other way suggested in `agents/DOCUMENTATION.md`. Read that documentation carefully (always second sub-task)
- [ ] [Specific implementation task 1]
- [ ] [Specific implementation task 2]
- [ ] [Specific implementation task 3]
- [ ] Testing and validation (lint, format, compile test, build) (always third last sub-task)
- [ ] User verification. Wait for human to confirm success (always second last sub-task)
- [ ] Update documentation (always last sub-task)
--- END TEMPLATE ---
and ensure that the provided first 2 and the last 3 subtasks are always included.

## Unsorted and Raw Tasks
tasks and ideas yet to be developed in to full proper main tasks:
- [ ] think about next steps in roadmap
- [ ] ensure all needed documentation and architecture is there
- [ ] ensure that github repo and its branches are set up

## Main Active Tasks (backlog)

**P3.1** | Update schema file with explicit FK constraint names | Pending | 2025-11-19 | [→ Details](TASKS/p3_schema_constraint_names.md)

### Add YAML Output Format to manage_db.py
**Status**: Review | **Labels**: enhancement, database-tools, output-formatting
**Description**: Add `--yaml` flag to `scripts/manage_db.py` to provide YAML output format alongside existing text and JSON formats. This will give users a third output option that is both human-readable and machine-parseable.

**Requirements to Define**:
- Add `--yaml` command-line flag that produces YAML formatted output
- Ensure `--yaml` and `--json` flags are mutually exclusive (cannot be used together)
- YAML output should follow the same data structure as JSON output
- All output modes should support YAML: database overview (all servers), single server overview, and SQL query results
- Update help text and docstring to document the new feature
- Maintain backward compatibility (default text output unchanged)

**Success Criteria**:
- `./scripts/manage_db.py --yaml` produces valid YAML output for all servers ✓
- `./scripts/manage_db.py --server vosscloud --yaml` produces valid YAML for single server ✓
- `./scripts/manage_db.py --sql "SHOW DATABASES" --yaml` produces valid YAML for query results ✓
- Using both `--yaml` and `--json` flags together produces an error message ✓
- Help text accurately documents the YAML option ✓

**Sub-tasks**:
- [x] Research and Identify all needed frameworks, libraries and already developed code documentation
- [x] Obtain the documentation and code references (PyYAML already included as dependency)
- [x] Implement `output_yaml()` function similar to `output_json()`
- [x] Add `--yaml` argument to argparse with mutual exclusivity check
- [x] Update all output locations to support YAML formatting
- [x] Update docstring and help text with YAML examples
- [x] Update ARCHITECTURE.md and DOCUMENTATION.md to document YAML output feature
- [x] Testing and validation (test all three output modes with various commands)
- [ ] User verification. Wait for human to confirm success
- [ ] Update documentation (README.md if needed)

## Completed
This section shall include completed tasks in a very concise way with only the information needed for future development
- Constitutional structure setup (2025-11-19): Created complete agents folder structure with all governance files, symlinks, and GitHub integration
