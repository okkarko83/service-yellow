#!/usr/bin/env python3
import os
import re
import sys
import subprocess
import json

COMMIT_REGEX = r'^\[(?:!)?(feat|fix|doc|build|chore|ci|style|refactor|test)\] [^\s].*$'
BRANCH_REGEX = r'^(?:main|uat|develop|sandbox|master|(?:feature|hotfix|fix|doc|build|bugfix|chore|ci|style|refactor|test)(?:\/(?:[A-Z]+-\d+-)?[a-z0-9]+(?:-[a-z0-9]+)*)?)$'

def check_branch_name():
    # GITHUB_HEAD_REF is set on pull_request (source branch)
    # GITHUB_REF_NAME is set on push (branch name)
    branch = os.environ.get('GITHUB_HEAD_REF') or os.environ.get('GITHUB_REF_NAME')
    if not branch:
        try:
            branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('utf-8').strip()
        except Exception:
            branch = 'unknown'
            
    print(f"Checking branch name: '{branch}'")
    if not re.match(BRANCH_REGEX, branch):
        print(f"❌ Error: Branch name '{branch}' does not match the compliance pattern.")
        print(f"Allowed pattern: {BRANCH_REGEX}")
        return False
    print("✅ Branch name is compliant.")
    return True

def get_commits_for_pull_request(event_data):
    base_sha = event_data['pull_request']['base']['sha']
    head_sha = event_data['pull_request']['head']['sha']
    print(f"Pull Request base SHA: {base_sha}")
    print(f"Pull Request head SHA: {head_sha}")
    
    # Try using git log between base_sha and head_sha
    try:
        # Fetch base SHA to ensure it's available locally
        subprocess.check_call(['git', 'fetch', 'origin', base_sha, '--depth=100'])
    except Exception as e:
        print(f"⚠️ Warning: failed to fetch base SHA: {e}")
        
    try:
        output = subprocess.check_output(['git', 'log', '--format=%s', f'{base_sha}..{head_sha}']).decode('utf-8')
        commits = [c.strip() for c in output.split('\n') if c.strip()]
        if commits:
            return commits
    except Exception as e:
        print(f"⚠️ Warning: git log failed: {e}")
        
    return []

def get_commits_for_push(event_data):
    commits = []
    # If commits are in the payload:
    if 'commits' in event_data:
        commits = [c['message'] for c in event_data['commits']]
        if commits:
            return commits
            
    before = event_data.get('before')
    after = event_data.get('after')
    if before and after and before != '0000000000000000000000000000000000000000':
        try:
            output = subprocess.check_output(['git', 'log', '--format=%s', f'{before}..{after}']).decode('utf-8')
            commits = [c.strip() for c in output.split('\n') if c.strip()]
            if commits:
                return commits
        except Exception as e:
            print(f"⚠️ Warning: git log failed: {e}")
    return []

def check_commits():
    event_name = os.environ.get('GITHUB_EVENT_NAME')
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    
    commits = []
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path, 'r') as f:
                event_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Failed to parse event payload: {e}")
            event_data = {}
            
        if event_name == 'pull_request':
            commits = get_commits_for_pull_request(event_data)
        elif event_name == 'push':
            commits = get_commits_for_push(event_data)
            
    # Fallback to HEAD commit if we couldn't retrieve commits
    if not commits:
        print("⚠️ Warning: No commits found in payload/history. Falling back to the HEAD commit message.")
        try:
            output = subprocess.check_output(['git', 'log', '-1', '--format=%s']).decode('utf-8')
            commits = [output.strip()]
        except Exception as e:
            print(f"❌ Error: Could not retrieve HEAD commit: {e}")
            return False

    print(f"Checking {len(commits)} commit(s):")
    failed = False
    for commit in commits:
        subject = commit.split('\n')[0].strip()
        if not re.match(COMMIT_REGEX, subject):
            print(f"❌ Error: Commit message '{subject}' does not match the compliance pattern.")
            print(f"Allowed pattern: {COMMIT_REGEX}")
            failed = True
        else:
            print(f"✅ Commit message compliant: '{subject}'")
            
    return not failed

def main():
    branch_ok = check_branch_name()
    print("-" * 40)
    commits_ok = check_commits()
    print("-" * 40)
    
    if not branch_ok or not commits_ok:
        sys.exit(1)
        
    print("🎉 All checks passed successfully!")

if __name__ == '__main__':
    main()
