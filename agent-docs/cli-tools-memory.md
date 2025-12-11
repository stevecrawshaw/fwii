# One CLI command > Multiple tool calls

## Essential Commands:

  1. Pattern Search:
    - rg -n "pattern" --glob '!node_modules/*' instead of multiple Grep calls
  2. File Finding:
    - fd filename or fd .ext directory instead of Glob tool
  3. File Preview:
    - bat -n filepath for syntax-highlighted preview with line numbers
  4. Bulk Refactoring:
    - rg -l "pattern" | xargs sed -i 's/old/new/g' for mass replacements
    - RESPECT WHITE SPACE in .py files
  5. Project Structure:
<<<<<<< HEAD:agent-docs/cli-tools-memory.md
    - tree -L 2 directories for quick overview in powershell
    - 'cmd //c tree' from bash
=======
    - 'cmd //c tree' directory tree overview
>>>>>>> 8199cc1e092fbf74f5892423964f56401c3d6536:cli-tools-memory.md
  6. JSON Inspection:
    - jq '.key' file.json for quick JSON parsing
  7. Get help: Use e.g. rg --help

## The Game-Changing Pattern:

  # Find files → Pipe to xargs → Apply sed transformation
  rg -l "find_this" | xargs sed -i 's/replace_this/with_this/g'

  Efficiently replace dozens of Edit tool calls!

  Before reaching for Read/Edit/Glob tools, ask:

  - Can rg find this pattern faster?
  - Can fd locate these files quicker?
  - Can sed fix all instances at once?
  - Can jq extract this JSON data directly?
