#!/usr/bin/env bash

# Update agent context files with information from plan.md
#
# This script maintains AI agent context files by parsing feature specifications 
# and updating agent-specific configuration files with project information.
#
# MAIN FUNCTIONS:
# 1. Environment Validation
#    - Verifies git repository structure and branch information
#    - Checks for required plan.md files and templates
#    - Validates file permissions and accessibility
#
# 2. Plan Data Extraction
#    - Parses plan.md files to extract project metadata
#    - Identifies language/version, frameworks, databases, and project types
#    - Handles missing or incomplete specification data gracefully
#
# 3. Agent File Management
#    - Creates new agent context files from templates when needed
#    - Updates existing agent files with new project information
#    - Preserves manual additions and custom configurations
#    - Supports multiple AI agent formats and directory structures
#
# 4. Content Generation
#    - Generates language-specific build/test commands
#    - Creates appropriate project directory structures
#    - Updates technology stacks and recent changes sections
#    - Maintains consistent formatting and timestamps
#
# 5. Multi-Agent Support
#    - Handles agent-specific file paths and naming conventions
#    - Supports: Claude, Gemini, Copilot, Cursor, Qwen, opencode, Codex, Windsurf, Kilo Code, Auggie CLI, or Amazon Q Developer CLI
#    - Can update single agents or all existing agent files
#    - Creates default Claude file if no agent files exist
#
# Usage: ./update-agent-context.sh [agent_type]
# Agent types: claude|gemini|copilot|cursor-agent|qwen|opencode|codex|windsurf|kilocode|auggie|q
# Leave empty to update all existing agent files

set -e

# Enable strict error handling
set -u
set -o pipefail

#==============================================================================
# Configuration and Global Variables
#==============================================================================

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
eval $(get_feature_paths)

NEW_PLAN="$IMPL_PLAN"  # Alias for compatibility with existing code
AGENT_TYPE="${1:-}"

# Agent-specific file paths  
CLAUDE_FILE="$REPO_ROOT/CLAUDE.md"
GEMINI_FILE="$REPO_ROOT/GEMINI.md"
COPILOT_FILE="$REPO_ROOT/.github/copilot-instructions.md"
CURSOR_FILE="$REPO_ROOT/.cursor/rules/specify-rules.mdc"
QWEN_FILE="$REPO_ROOT/QWEN.md"
AGENTS_FILE="$REPO_ROOT/AGENTS.md"
WINDSURF_FILE="$REPO_ROOT/.windsurf/rules/specify-rules.md"
KILOCODE_FILE="$REPO_ROOT/.kilocode/rules/specify-rules.md"
AUGGIE_FILE="$REPO_ROOT/.augment/rules/specify-rules.md"
ROO_FILE="$REPO_ROOT/.roo/rules/specify-rules.md"
CODEBUDDY_FILE="$REPO_ROOT/CODEBUDDY.md"
Q_FILE="$REPO_ROOT/AGENTS.md"

# Template file
TEMPLATE_FILE="$REPO_ROOT/.specify/templates/agent-file-template.md"

# Global variables for parsed plan data
NEW_LANG=""
NEW_FRAMEWORK=""
NEW_DB=""
NEW_PROJECT_TYPE=""

#==============================================================================
# Utility Functions
#==============================================================================

log_info() {
    echo "INFO: $1"
}

log_success() {
    echo "✓ $1"
}

log_error() {
    echo "ERROR: $1" >&2
}

log_warning() {
    echo "WARNING: $1" >&2
}

# Cleanup function for temporary files
cleanup() {
    local exit_code=$?
    rm -f /tmp/agent_update_*_$$
    rm -f /tmp/manual_additions_$$
    exit $exit_code
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

#==============================================================================
# Validation Functions
#==============================================================================

validate_environment() {
    # Check if we have a current branch/feature (git or non-git)
    if [[ -z "$CURRENT_BRANCH" ]]; then
        log_error "Unable to determine current feature"
        if [[ "$HAS_GIT" == "true" ]]; then
            log_info "Make sure you're on a feature branch"
        else
            log_info "Set SPECIFY_FEATURE environment variable or create a feature first"
        fi
        exit 1
    fi
    
    # Check if plan.md exists
    if [[ ! -f "$NEW_PLAN" ]]; then
        log_error "No plan.md found at $NEW_PLAN"
        log_info "Make sure you're working on a feature with a corresponding spec directory"
        if [[ "$HAS_GIT" != "true" ]]; then
            log_info "Use: export SPECIFY_FEATURE=your-feature-name or create a new feature first"
        fi
        exit 1
    fi
    
    # Check if template exists (needed for new files)
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        log_warning "Template file not found at $TEMPLATE_FILE"
        log_warning "Creating new agent files will fail"
    fi
}

#==============================================================================
# Plan Parsing Functions
#==============================================================================

extract_plan_field() {
    local field_pattern="$1"
    local plan_file="$2"
    
    grep "^\*\*${field_pattern}\*\*: " "$plan_file" 2>/dev/null | \
        head -1 | \
        sed "s|^\*\*${field_pattern}\*\*: ||" | \
        sed 's/^[ \t]*//;s/[ \t]*$//' | \
        grep -v "NEEDS CLARIFICATION" | \
        grep -v "^N/A$" || echo ""
}

parse_plan_data() {
    local plan_file="$1"
    
    if [[ ! -f "$plan_file" ]]; then
        log_error "Plan file not found: $plan_file"
        return 1
    fi
    
    if [[ ! -r "$plan_file" ]]; then
        log_error "Plan file is not readable: $plan_file"
        return 1
    fi
    
    log_info "Parsing plan data from $plan_file"
    
    NEW_LANG=$(extract_plan_field "Language/Version" "$plan_file")
    NEW_FRAMEWORK=$(extract_plan_field "Primary Dependencies" "$plan_file")
    NEW_DB=$(extract_plan_field "Storage" "$plan_file")
    NEW_PROJECT_TYPE=$(extract_plan_field "Project Type" "$plan_file")
    
    # Log what we found
    if [[ -n "$NEW_LANG" ]]; then
        log_info "Found language: $NEW_LANG"
    else
        log_warning "No language information found in plan"
    fi
    
    if [[ -n "$NEW_FRAMEWORK" ]]; then
        log_info "Found framework: $NEW_FRAMEWORK"
    fi
    
    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]]; then
        log_info "Found database: $NEW_DB"
    fi
    
    if [[ -n "$NEW_PROJECT_TYPE" ]]; then
        log_info "Found project type: $NEW_PROJECT_TYPE"
    fi
}

format_technology_stack() {
    local lang="$1"
    local framework="$2"
    local parts=()
    
    # Add non-empty parts
    [[ -n "$lang" && "$lang" != "NEEDS CLARIFICATION" ]] && parts+=("$lang")
    [[ -n "$framework" && "$framework" != "NEEDS CLARIFICATION" && "$framework" != "N/A" ]] && parts+=("$framework")
    
    # Join with proper formatting
    if [[ ${#parts[@]} -eq 0 ]]; then
        echo ""
    elif [[ ${#parts[@]} -eq 1 ]]; then
        echo "${parts[0]}"
    else
        # Join multiple parts with " + "
        local result="${parts[0]}"
        for ((i=1; i<${#parts[@]}; i++)); do
            result="$result + ${parts[i]}"
        done
        echo "$result"
    fi
}

#==============================================================================
# Template and Content Generation Functions
#==============================================================================

get_project_structure() {
    local project_type="$1"

    # 1) Tokens entre crases (ex.: `backend/`, `frontend/`)
    local tokens=()
    local bt_matches
    bt_matches=$(printf '%s\n' "$project_type" | grep -oE '`[^`]+`' || true)
    if [[ -n "$bt_matches" ]]; then
        while IFS= read -r match; do
            local token="${match//\`/}"
            [[ "$token" != */ ]] && token="${token}/"
            tokens+=("$token")
        done <<< "$bt_matches"
    else
        # 2) Fallback: palavras terminadas com "/"
        local slash_matches
        slash_matches=$(printf '%s\n' "$project_type" | grep -oE '[A-Za-z0-9_-]+/' | sort -u || true)
        if [[ -n "$slash_matches" ]]; then
            while IFS= read -r token; do
                tokens+=("$token")
            done <<< "$slash_matches"
        fi
    fi

    # 3) Se tokens foram identificados, devolve-os como linhas reais
    if [[ ${#tokens[@]} -gt 0 ]]; then
        printf '%s\n' "${tokens[@]}"
        return 0
    fi

    # 4) Fallback final conforme heurística original
    if [[ "$project_type" == *"web"* ]]; then
        printf 'backend/\nfrontend/\ntests/\n'
    else
        printf 'src/\ntests/\n'
    fi
}


get_commands_for_language() {
    local lang="$1"
    
    case "$lang" in
        *"Python"*)
            echo "cd src && pytest && ruff check ."
            ;;
        *"Rust"*)
            echo "cargo test && cargo clippy"
            ;;
        *"JavaScript"*|*"TypeScript"*)
            echo "npm test && npm run lint"
            ;;
        *)
            echo "# Add commands for $lang"
            ;;
    esac
}

get_language_conventions() {
    local lang="$1"
    echo "$lang: Follow standard conventions"
}

create_new_agent_file() {
    local target_file="$1"
    local temp_file="$2"
    local project_name="$3"
    local current_date="$4"
    
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        log_error "Template not found at $TEMPLATE_FILE"
        return 1
    fi
    
    if [[ ! -r "$TEMPLATE_FILE" ]]; then
        log_error "Template file is not readable: $TEMPLATE_FILE"
        return 1
    fi
    
    log_info "Creating new agent context file from template..."
    
    if ! cp "$TEMPLATE_FILE" "$temp_file"; then
        log_error "Failed to copy template file"
        return 1
    fi
    
    # Replace template placeholders
    local project_structure
    project_structure=$(get_project_structure "$NEW_PROJECT_TYPE")
    
    local commands
    commands=$(get_commands_for_language "$NEW_LANG")
    
    local language_conventions
    language_conventions=$(get_language_conventions "$NEW_LANG")
    
    local tech_stack_base
    tech_stack_base=$(format_technology_stack "$NEW_LANG" "$NEW_FRAMEWORK")
    local tech_entries=()
    if [[ -n "$tech_stack_base" ]]; then
        tech_entries+=("- $tech_stack_base ($CURRENT_BRANCH)")
    fi
    if [[ -n "$NEW_DB" && "$NEW_DB" != "N/A" && "$NEW_DB" != "NEEDS CLARIFICATION" ]]; then
        tech_entries+=("- $NEW_DB ($CURRENT_BRANCH)")
    fi
    local full_tech_stack=""
    if [[ ${#tech_entries[@]} -gt 0 ]]; then
        full_tech_stack=$(printf '%s\n' "${tech_entries[@]}")
        full_tech_stack=${full_tech_stack%$'\n'}
    fi

    local recent_change="- $CURRENT_BRANCH: Added"
    if [[ -n "$tech_stack_base" ]]; then
        recent_change="- $CURRENT_BRANCH: Added $tech_stack_base"
    elif [[ -n "$NEW_DB" && "$NEW_DB" != "N/A" && "$NEW_DB" != "NEEDS CLARIFICATION" ]]; then
        recent_change="- $CURRENT_BRANCH: Added $NEW_DB"
    fi

    local content
    content=$(<"$temp_file")

    content=$(PROJECT_NAME="$project_name" \
        CURRENT_DATE="$current_date" \
        TECH_STACK="$full_tech_stack" \
        PROJECT_STRUCTURE="$project_structure" \
        COMMANDS="$commands" \
        LANGUAGE_CONVENTIONS="$language_conventions" \
        RECENT_CHANGE="$recent_change" \
        CONTENT="$content" \
        python3 - <<'PY'
import os

content = os.environ["CONTENT"]
replacements = {
    "[PROJECT NAME]": os.environ["PROJECT_NAME"],
    "[DATE]": os.environ["CURRENT_DATE"],
    "[EXTRACTED FROM ALL PLAN.MD FILES]": os.environ["TECH_STACK"],
    "[ACTUAL STRUCTURE FROM PLANS]": os.environ["PROJECT_STRUCTURE"],
    "[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]": os.environ["COMMANDS"],
    "[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]": os.environ["LANGUAGE_CONVENTIONS"],
    "[LAST 3 FEATURES AND WHAT THEY ADDED]": os.environ["RECENT_CHANGE"],
}
for key, value in replacements.items():
    content = content.replace(key, value)
print(content, end="")
PY
)

    printf '%s' "$content" > "$temp_file"
    
    return 0
}





update_existing_agent_file() {
    local target_file="$1"
    local current_date="$2"

    log_info "Updating existing agent context file..."

    local manual_additions=""
    manual_additions=$(sed -n '/<!-- MANUAL ADDITIONS START -->/,/<!-- MANUAL ADDITIONS END -->/{/<!--/!p;}' "$target_file" 2>/dev/null || true)

    local old_tech_lines=()
    local old_change_lines=()
    if [[ -f "$target_file" ]]; then
        mapfile -t old_tech_lines < <(sed -n '/## Active Technologies/,/##/{/##/!p;}' "$target_file" | grep '^- ' || true)
        mapfile -t old_change_lines < <(awk '
            BEGIN { in_changes=0 }
            /^## Recent Changes$/ { in_changes=1; next }
            {
                if (in_changes) {
                    if ($0 ~ /^##[[:space:]]/ || $0 ~ /^<!--/) { in_changes=0; next }
                    if ($0 ~ /^- /) { print }
                }
            }
        ' "$target_file" || true)
    fi

    local temp_file
    temp_file=$(mktemp) || {
        log_error "Failed to create temporary file"
        return 1
    }

    local project_name
    project_name=$(basename "$REPO_ROOT")

    if ! create_new_agent_file "$target_file" "$temp_file" "$project_name" "$current_date"; then
        log_error "Failed to regenerate agent file content."
        rm -f "$temp_file"
        return 1
    fi

    local tech_stack_base
    tech_stack_base=$(format_technology_stack "$NEW_LANG" "$NEW_FRAMEWORK")

    local new_tech_entries=()
    if [[ -n "$tech_stack_base" ]]; then
        new_tech_entries+=("- $tech_stack_base ($CURRENT_BRANCH)")
    fi
    if [[ -n "$NEW_DB" && "$NEW_DB" != "N/A" && "$NEW_DB" != "NEEDS CLARIFICATION" ]]; then
        new_tech_entries+=("- $NEW_DB ($CURRENT_BRANCH)")
    fi

    declare -A seen_tech=()
    local final_tech_lines=()
    local entry
    for entry in "${new_tech_entries[@]}"; do
        [[ -z "$entry" ]] && continue
        if [[ -z "${seen_tech[$entry]+_}" ]]; then
            seen_tech["$entry"]=1
            final_tech_lines+=("$entry")
        fi
    done
    for entry in "${old_tech_lines[@]}"; do
        [[ -z "$entry" ]] && continue
        entry=$(printf '%s' "$entry" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        [[ -z "$entry" ]] && continue
        if [[ -z "${seen_tech[$entry]+_}" ]]; then
            seen_tech["$entry"]=1
            final_tech_lines+=("$entry")
        fi
    done

    local new_change_entry=""
    if [[ -n "$tech_stack_base" ]]; then
        new_change_entry="- $CURRENT_BRANCH: Added $tech_stack_base"
    elif [[ -n "$NEW_DB" && "$NEW_DB" != "N/A" && "$NEW_DB" != "NEEDS CLARIFICATION" ]]; then
        new_change_entry="- $CURRENT_BRANCH: Added $NEW_DB"
    fi

    declare -A seen_changes=()
    local final_change_lines=()
    if [[ -n "$new_change_entry" ]]; then
        seen_changes["$new_change_entry"]=1
        final_change_lines+=("$new_change_entry")
    fi
    for entry in "${old_change_lines[@]}"; do
        entry=$(printf '%s' "$entry" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        [[ -z "$entry" ]] && continue
        if [[ -z "${seen_changes[$entry]+_}" ]]; then
            seen_changes["$entry"]=1
            final_change_lines+=("$entry")
        fi
        if (( ${#final_change_lines[@]} >= 3 )); then
            break
        fi
    done

    local tech_lines_str=""
    if (( ${#final_tech_lines[@]} > 0 )); then
        printf -v tech_lines_str '%s\n' "${final_tech_lines[@]}"
        tech_lines_str=${tech_lines_str%$'\n'}
    fi

    local change_lines_str=""
    if (( ${#final_change_lines[@]} > 0 )); then
        printf -v change_lines_str '%s\n' "${final_change_lines[@]}"
        change_lines_str=${change_lines_str%$'\n'}
    fi

    local rewritten_file
    rewritten_file=$(mktemp) || {
        log_error "Failed to create temporary file"
        rm -f "$temp_file"
        return 1
    }

    awk -v tech="$tech_lines_str" -v changes="$change_lines_str" '
        BEGIN {
            tech_len = split(tech, tech_arr, "\n");
            change_len = split(changes, change_arr, "\n");
        }
        {
            if ($0 == "## Active Technologies") {
                print $0;
                if (tech_len > 0) {
                    for (i = 1; i <= tech_len; i++) {
                        if (tech_arr[i] != "")
                            print tech_arr[i];
                    }
                }
                print "";
                section = "tech";
                next;
            }
            if (section == "tech") {
                if ($0 ~ /^##[[:space:]]/ ) {
                    section = "";
                    print $0;
                }
                next;
            }
            if ($0 == "## Recent Changes") {
                print $0;
                if (change_len > 0) {
                    for (i = 1; i <= change_len; i++) {
                        if (change_arr[i] != "")
                            print change_arr[i];
                    }
                }
                print "";
                section = "changes";
                next;
            }
            if (section == "changes") {
                if ($0 ~ /^##[[:space:]]/ || $0 ~ /^<!--/) {
                    section = "";
                    print $0;
                }
                next;
            }
            print $0;
        }
    ' "$temp_file" > "$rewritten_file"

    mv "$rewritten_file" "$temp_file"

    if [[ -n "$manual_additions" ]]; then
        local manual_file
        manual_file=$(mktemp) || {
            log_error "Failed to create temporary file"
            rm -f "$temp_file"
            return 1
        }
        printf '%s\n' "$manual_additions" > "$manual_file"
        # Reinjeção segura do bloco MANUAL: a condição deve estar dentro de um bloco de ação
        if ! awk -v file="$manual_file" '
            BEGIN { skip = 0 }
            /<!-- MANUAL ADDITIONS START -->/ {
                print;
                while ((getline line < file) > 0) print line;
                close(file);
                skip = 1;
                next;
            }
            /<!-- MANUAL ADDITIONS END -->/ {
                skip = 0;
                print;
                next;
            }
            {
                if (skip == 1) next;
                print;
            }
        ' "$temp_file" > "$temp_file.updated"; then
            log_error "Failed to re-inject manual additions"
            rm -f "$manual_file" "$temp_file.updated"
            rm -f "$temp_file"
            return 1
        fi
        mv "$temp_file.updated" "$temp_file"
        rm -f "$manual_file"
    fi

    if ! mv "$temp_file" "$target_file"; then
        log_error "Failed to update target file"
        rm -f "$temp_file"
        return 1
    fi

    return 0
}
#==============================================================================
# Main Agent File Update Function
#==============================================================================

update_agent_file() {
    local target_file="$1"
    local agent_name="$2"
    
    if [[ -z "$target_file" ]] || [[ -z "$agent_name" ]]; then
        log_error "update_agent_file requires target_file and agent_name parameters"
        return 1
    fi
    
    log_info "Updating $agent_name context file: $target_file"
    
    local project_name
    project_name=$(basename "$REPO_ROOT")
    local current_date
    current_date=$(date +%Y-%m-%d)
    
    # Create directory if it doesn't exist
    local target_dir
    target_dir=$(dirname "$target_file")
    if [[ ! -d "$target_dir" ]]; then
        if ! mkdir -p "$target_dir"; then
            log_error "Failed to create directory: $target_dir"
            return 1
        fi
    fi
    
    if [[ ! -f "$target_file" ]]; then
        # Create new file from template
        local temp_file
        temp_file=$(mktemp) || {
            log_error "Failed to create temporary file"
            return 1
        }
        
        if create_new_agent_file "$target_file" "$temp_file" "$project_name" "$current_date"; then
            if mv "$temp_file" "$target_file"; then
                log_success "Created new $agent_name context file"
            else
                log_error "Failed to move temporary file to $target_file"
                rm -f "$temp_file"
                return 1
            fi
        else
            log_error "Failed to create new agent file"
            rm -f "$temp_file"
            return 1
        fi
    else
        # Update existing file
        if [[ ! -r "$target_file" ]]; then
            log_error "Cannot read existing file: $target_file"
            return 1
        fi
        
        if [[ ! -w "$target_file" ]]; then
            log_error "Cannot write to existing file: $target_file"
            return 1
        fi
        
        if update_existing_agent_file "$target_file" "$current_date"; then
            log_success "Updated existing $agent_name context file"
        else
            log_error "Failed to update existing agent file"
            return 1
        fi
    fi
    
    return 0
}

#==============================================================================
# Agent Selection and Processing
#==============================================================================

update_specific_agent() {
    local agent_type="$1"
    
    case "$agent_type" in
        claude)
            update_agent_file "$CLAUDE_FILE" "Claude Code"
            ;;
        gemini)
            update_agent_file "$GEMINI_FILE" "Gemini CLI"
            ;;
        copilot)
            update_agent_file "$COPILOT_FILE" "GitHub Copilot"
            ;;
        cursor-agent)
            update_agent_file "$CURSOR_FILE" "Cursor IDE"
            ;;
        qwen)
            update_agent_file "$QWEN_FILE" "Qwen Code"
            ;;
        opencode)
            update_agent_file "$AGENTS_FILE" "opencode"
            ;;
        codex)
            update_agent_file "$AGENTS_FILE" "Codex CLI"
            ;;
        windsurf)
            update_agent_file "$WINDSURF_FILE" "Windsurf"
            ;;
        kilocode)
            update_agent_file "$KILOCODE_FILE" "Kilo Code"
            ;;
        auggie)
            update_agent_file "$AUGGIE_FILE" "Auggie CLI"
            ;;
        roo)
            update_agent_file "$ROO_FILE" "Roo Code"
            ;;
        codebuddy)
            update_agent_file "$CODEBUDDY_FILE" "CodeBuddy CLI"
            ;;
        q)
            update_agent_file "$Q_FILE" "Amazon Q Developer CLI"
            ;;
        *)
            log_error "Unknown agent type '$agent_type'"
            log_error "Expected: claude|gemini|copilot|cursor-agent|qwen|opencode|codex|windsurf|kilocode|auggie|roo|q"
            exit 1
            ;;
    esac
}

update_all_existing_agents() {
    local found_agent=false
    
    # Check each possible agent file and update if it exists
    if [[ -f "$CLAUDE_FILE" ]]; then
        update_agent_file "$CLAUDE_FILE" "Claude Code"
        found_agent=true
    fi
    
    if [[ -f "$GEMINI_FILE" ]]; then
        update_agent_file "$GEMINI_FILE" "Gemini CLI"
        found_agent=true
    fi
    
    if [[ -f "$COPILOT_FILE" ]]; then
        update_agent_file "$COPILOT_FILE" "GitHub Copilot"
        found_agent=true
    fi
    
    if [[ -f "$CURSOR_FILE" ]]; then
        update_agent_file "$CURSOR_FILE" "Cursor IDE"
        found_agent=true
    fi
    
    if [[ -f "$QWEN_FILE" ]]; then
        update_agent_file "$QWEN_FILE" "Qwen Code"
        found_agent=true
    fi
    
    if [[ -f "$AGENTS_FILE" ]]; then
        update_agent_file "$AGENTS_FILE" "Codex/opencode"
        found_agent=true
    fi
    
    if [[ -f "$WINDSURF_FILE" ]]; then
        update_agent_file "$WINDSURF_FILE" "Windsurf"
        found_agent=true
    fi
    
    if [[ -f "$KILOCODE_FILE" ]]; then
        update_agent_file "$KILOCODE_FILE" "Kilo Code"
        found_agent=true
    fi

    if [[ -f "$AUGGIE_FILE" ]]; then
        update_agent_file "$AUGGIE_FILE" "Auggie CLI"
        found_agent=true
    fi
    
    if [[ -f "$ROO_FILE" ]]; then
        update_agent_file "$ROO_FILE" "Roo Code"
        found_agent=true
    fi

    if [[ -f "$CODEBUDDY_FILE" ]]; then
        update_agent_file "$CODEBUDDY_FILE" "CodeBuddy CLI"
        found_agent=true
    fi

    if [[ -f "$Q_FILE" ]]; then
        update_agent_file "$Q_FILE" "Amazon Q Developer CLI"
        found_agent=true
    fi
    
    # If no agent files exist, create a default Claude file
    if [[ "$found_agent" == false ]]; then
        log_info "No existing agent files found, creating default Claude file..."
        update_agent_file "$CLAUDE_FILE" "Claude Code"
    fi
}
print_summary() {
    echo
    log_info "Summary of changes:"
    
    if [[ -n "$NEW_LANG" ]]; then
        echo "  - Added language: $NEW_LANG"
    fi
    
    if [[ -n "$NEW_FRAMEWORK" ]]; then
        echo "  - Added framework: $NEW_FRAMEWORK"
    fi
    
    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]]; then
        echo "  - Added database: $NEW_DB"
    fi
    
    echo

    log_info "Usage: $0 [claude|gemini|copilot|cursor-agent|qwen|opencode|codex|windsurf|kilocode|auggie|codebuddy|q]"
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    # Validate environment before proceeding
    validate_environment
    
    log_info "=== Updating agent context files for feature $CURRENT_BRANCH ==="
    
    # Parse the plan file to extract project information
    if ! parse_plan_data "$NEW_PLAN"; then
        log_error "Failed to parse plan data"
        exit 1
    fi
    
    # Process based on agent type argument
    local success=true
    
    if [[ -z "$AGENT_TYPE" ]]; then
        # No specific agent provided - update all existing agent files
        log_info "No agent specified, updating all existing agent files..."
        if ! update_all_existing_agents; then
            success=false
        fi
    else
        # Specific agent provided - update only that agent
        log_info "Updating specific agent: $AGENT_TYPE"
        if ! update_specific_agent "$AGENT_TYPE"; then
            success=false
        fi
    fi
    
    # Print summary
    print_summary
    
    if [[ "$success" == true ]]; then
        log_success "Agent context update completed successfully"
        exit 0
    else
        log_error "Agent context update completed with errors"
        exit 1
    fi
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
