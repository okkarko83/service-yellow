#!/usr/bin/env python3
import os
import re
import sys
import subprocess

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.output.decode('utf-8')}")
        sys.exit(1)

def main():
    tag_name = os.environ.get('GITHUB_REF_NAME')
    if not tag_name:
        print("❌ Error: GITHUB_REF_NAME environment variable not set.")
        sys.exit(1)
        
    print(f"Validating tag: {tag_name}")
    
    # Define regexes
    # Release format: vX.Y.Z
    RELEASE_REGEX = r'^v[0-9]+\.[0-9]+\.[0-9]+$'
    # Pre-release format: vX.Y.Z-suffix
    PRERELEASE_REGEX = r'^v[0-9]+\.[0-9]+\.[0-9]+-[a-zA-Z0-9.-]+$'
    
    is_release = bool(re.match(RELEASE_REGEX, tag_name))
    is_prerelease = bool(re.match(PRERELEASE_REGEX, tag_name))
    
    if not is_release and not is_prerelease:
        print(f"❌ Error: Tag '{tag_name}' does not match SemVer format (vX.Y.Z or vX.Y.Z-prerelease).")
        sys.exit(1)
        
    # Fetch all remote branches to know what branches contain this commit
    print("Fetching remote branches...")
    run_cmd(['git', 'fetch', '--prune', 'origin'])
    
    # Get remote branches containing the tag commit
    containing_branches_raw = run_cmd(['git', 'branch', '-r', '--contains', 'HEAD'])
    containing_branches = [b.strip() for b in containing_branches_raw.split('\n') if b.strip()]
    
    print("Remote branches containing this commit:")
    for b in containing_branches:
        print(f" - {b}")
        
    # Check if 'origin/main' or 'origin/master' is in containing branches
    on_main = any(b == 'origin/main' or b == 'origin/master' for b in containing_branches)
    
    if is_release:
        if not on_main:
            print(f"❌ Error: Release tag '{tag_name}' must be pushed from the 'main' branch!")
            print("To release, please merge your changes into 'main' and tag the commit on main.")
            sys.exit(1)
        print(f"✅ Success: Release tag '{tag_name}' is pushed from main branch.")
    else:
        # Pre-release tag is allowed from any branch
        print(f"✅ Success: Pre-release tag '{tag_name}' is allowed from any branch.")

if __name__ == '__main__':
    main()
