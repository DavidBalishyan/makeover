#!/usr/bin/env python3
import sys
import os
import re
import subprocess
from typing import Dict, List, Tuple

class BuildError(Exception):
    pass

class BuildSystem:
    def __init__(self, buildfile="buildfile"):
        self.buildfile = buildfile
        self.variables: Dict[str, str] = {}
        self.targets: Dict[str, Dict] = {}
        self.first_target = None

    def log(self, message):
        print(f"\033[1;34m[Makeover]\033[0m {message}")

    def parse(self):
        if not os.path.exists(self.buildfile):
            raise BuildError(f"Buildfile '{self.buildfile}' not found.")

        current_target = None
        current_group = "General"
        pending_doc = []
        
        with open(self.buildfile, 'r') as f:
            for line_num, line in enumerate(f, 1):
                raw_line = line.rstrip()
                stripped = line.strip()

                # Group definition
                if stripped.lower().startswith('[group:') and stripped.endswith(']'):
                    current_group = stripped[7:-1].strip()
                    current_target = None
                    pending_doc = []
                    continue

                # Empty lines reset pending doc unless it's a block of comments
                if not stripped:
                    if current_target:
                         # Inside a target, empty lines might be okay but here we treat it as end of non-indented block
                         # But wait, indented lines are commands.
                         pass
                    else:
                        # Outside target, empty line resets doc cache usually? 
                        # Let's say doc comments must be immediately adjacent.
                        pending_doc = []
                    continue

                # Comments
                if stripped.startswith('#'):
                    # If we are inside a target, this is just a comment in the command block (ignored by us as it's not indented command?)
                    # Wait, we skip non-indented lines.
                    # If it's a comment at top level, it might be a doc for the next target.
                    if not current_target:
                        comment_content = stripped[1:].strip()
                        pending_doc.append(comment_content)
                    continue

                # Check for indentation (commands)
                if line.startswith(' ') or line.startswith('\t'):
                    if not current_target:
                        raise BuildError(f"Line {line_num}: Command found outside of target block.")
                    self.targets[current_target]['commands'].append(stripped)
                    # Reset doc after entering target commands
                    pending_doc = [] 
                    continue

                # Variable assignment
                if '=' in stripped and ':' not in stripped: # Simple heuristic
                    parts = stripped.split('=', 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    self.variables[key] = val
                    current_target = None
                    pending_doc = []
                    continue

                # Target definition
                if ':' in stripped:
                    parts = stripped.split(':', 1)
                    target_name = parts[0].strip()
                    deps_str = parts[1].strip()
                    
                    dependencies = [d for d in deps_str.split() if d]
                    
                    # Join pending docs
                    doc_string = " ".join(pending_doc) if pending_doc else ""

                    self.targets[target_name] = {
                        'deps': dependencies,
                        'commands': [],
                        'doc': doc_string,
                        'group': current_group
                    }
                    if self.first_target is None:
                        self.first_target = target_name
                    current_target = target_name
                    pending_doc = []
                    continue
                
                raise BuildError(f"Line {line_num}: Syntax error.")

    def expand_vars(self, text: str) -> str:
        # Simple substitution for $VAR or ${VAR}
        # This is a basic implementation
        for key, val in self.variables.items():
            text = text.replace(f"${key}", val)
            text = text.replace(f"${{{key}}}", val)
        return text

    def needs_rebuild(self, target, deps):
        if not os.path.exists(target):
            return True
        
        target_mtime = os.path.getmtime(target)
        
        for dep in deps:
            if not os.path.exists(dep):
                # If dependency doesn't exist as a file, it might be another target
                # If it's another target, we assume it will be built.
                # If it's a source file that's missing, that's an issue for the command execution mostly.
                # For now, let's just say if dep is newer or missing?
                # If dep is missing, we can't check mtime.
                if dep in self.targets:
                     # It's a target, we should have already built it. 
                     # If the target file actually exists now, check it.
                     pass
                else:
                     # It's a source file. If it's missing, we error later?
                     # Let's assume it exists for timestamp check, or fail.
                     if not os.path.exists(dep):
                         # If a source dependency is missing, we definitely can't build?
                         # Or maybe the command generates it? 
                         # Let's assume we need to rebuild if we can't find the dependency to compare.
                         return True
            
            if os.path.exists(dep):
                dep_mtime = os.path.getmtime(dep)
                if dep_mtime > target_mtime:
                    return True
        
        return False

    def build(self, target_name, visited=None):
        if visited is None:
            visited = set()
        
        if target_name in visited:
            raise BuildError(f"Circular dependency detected involving {target_name}")
        visited.add(target_name)

        if target_name not in self.targets:
            # If it's not a known target, it must be a source file.
            if not os.path.exists(target_name):
                 raise BuildError(f"No rule to make target '{target_name}' and file not found.")
            return

        target_info = self.targets[target_name]
        deps = target_info['deps']

        # Build dependencies first
        for dep in deps:
            self.build(dep, visited.copy())

        # Check if we need to run commands
        # If the target is phony (not a file), we usually run. 
        # But here we don't have explicit .PHONY. 
        # We'll use the needs_rebuild logic: if target file doesn't exist, run.
        should_run = self.needs_rebuild(target_name, deps)

        if should_run:
            self.log(f"Building target: {target_name}")
            for cmd in target_info['commands']:
                expanded_cmd = self.expand_vars(cmd)
                # print(f"  > {expanded_cmd}")
                try:
                   subprocess.run(expanded_cmd, shell=True, check=True)
                except subprocess.CalledProcessError as e:
                   raise BuildError(f"Command failed: {expanded_cmd}")
        else:
            self.log(f"Target '{target_name}' is up to date.")

    def run(self):
        try:
            self.parse()
        except BuildError as e:
            print(f"Error parsing buildfile: {e}")
            sys.exit(1)

        if '--list' in sys.argv or '-l' in sys.argv:
            print("Available targets:")
            
            # Organise targets by group
            grouped = {}
            for t_name, t_info in self.targets.items():
                grp = t_info.get('group', 'General')
                if grp not in grouped:
                    grouped[grp] = []
                grouped[grp].append((t_name, t_info.get('doc', '')))
            
            # Print groups
            for grp_name, targets in grouped.items():
                print(f"\n\033[1;35m{grp_name}\033[0m:")
                # Calculate padding
                max_len = max(len(t[0]) for t in targets) if targets else 0
                for t_name, t_doc in targets:
                    padding = " " * (max_len - len(t_name) + 2)
                    doc_str = f"\033[90m# {t_doc}\033[0m" if t_doc else ""
                    print(f"  \033[1;34m{t_name}\033[0m{padding}{doc_str}")
            return

        targets_to_build = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
        
        if not targets_to_build:
            if self.first_target:
                targets_to_build = [self.first_target]
            else:
                print("No targets found in buildfile.")
                return

        for t in targets_to_build:
            try:
                self.build(t)
            except BuildError as e:
                print(f"Error: {e}")
                sys.exit(1)

if __name__ == '__main__':
    BuildSystem().run()