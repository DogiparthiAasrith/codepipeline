#!/usr/bin/env python3
"""
Format Terraform plan output into a human-readable table.
"""
import sys
import re
from typing import Dict, List

def parse_terraform_plan(plan_text: str) -> Dict[str, List[Dict]]:
    """Parse terraform plan output and categorize changes."""
    changes = {
        'add': [],
        'change': [],
        'destroy': []
    }
    
    # Extract summary line
    summary_match = re.search(r'Plan: (\d+) to add, (\d+) to change, (\d+) to destroy', plan_text)
    if summary_match:
        changes['summary'] = {
            'add': int(summary_match.group(1)),
            'change': int(summary_match.group(2)),
            'destroy': int(summary_match.group(3))
        }
    
    # Parse resource changes from plan
    resource_pattern = r'#\s+([\w_\.]+)\s+will be (created|destroyed|updated)'
    for match in re.finditer(resource_pattern, plan_text):
        resource_name = match.group(1)
        action = match.group(2)
        
        if action == 'created':
            changes['add'].append({'name': resource_name, 'type': 'resource'})
        elif action == 'destroyed':
            changes['destroy'].append({'name': resource_name, 'type': 'resource'})
        elif action == 'updated':
            changes['change'].append({'name': resource_name, 'type': 'resource'})
    
    # Parse output changes
    output_section = re.search(r'Changes to Outputs:(.*?)(?:\n\n|$)', plan_text, re.DOTALL)
    if output_section:
        output_lines = output_section.group(1).strip().split('\n')
        for line in output_lines:
            # Match output changes: ~ name = "old" -> "new"
            match = re.match(r'[~+-]\s+(\S+)\s+=\s+"([^"]*?)"\s+->\s+"([^"]*?)"', line)
            if match:
                name = match.group(1)
                old_val = match.group(2)
                new_val = match.group(3)
                
                if old_val and not new_val:
                    changes['destroy'].append({'name': name, 'old': old_val, 'new': new_val, 'type': 'output'})
                elif not old_val and new_val:
                    changes['add'].append({'name': name, 'old': old_val, 'new': new_val, 'type': 'output'})
                else:
                    changes['change'].append({'name': name, 'old': old_val, 'new': new_val, 'type': 'output'})
    
    return changes

def format_table(changes: Dict) -> str:
    """Format changes into a readable table."""
    output = []
    
    # Header
    output.append("=" * 120)
    output.append("                              TERRAFORM PLAN SUMMARY")
    output.append("=" * 120)
    output.append("")
    
    # Summary
    if 'summary' in changes:
        s = changes['summary']
        output.append(f"📊 OVERVIEW: {s['add']} resources to ADD | {s['change']} to CHANGE | {s['destroy']} to DESTROY")
        output.append("")
    else:
        output.append("⚠️  No changes detected or plan not yet generated")
        output.append("")
    
    # Resources to ADD
    if changes['add']:
        output.append("✅ RESOURCES TO BE CREATED")
        output.append("-" * 120)
        output.append(f"{'#':<5} {'Resource Type':<30} {'Resource Name':<85}")
        output.append("-" * 120)
        for idx, item in enumerate(changes['add'], 1):
            if item.get('type') == 'output':
                output.append(f"{idx:<5} {'Output':<30} {item['name']:<85}")
            else:
                parts = item['name'].split('.')
                res_type = parts[0] if len(parts) > 0 else 'unknown'
                res_name = '.'.join(parts[1:]) if len(parts) > 1 else item['name']
                output.append(f"{idx:<5} {res_type:<30} {res_name:<85}")
        output.append("")
    
    # Resources to CHANGE
    if changes['change']:
        output.append("🔄 RESOURCES TO BE MODIFIED")
        output.append("-" * 120)
        output.append(f"{'#':<5} {'Resource Type':<30} {'Resource Name':<85}")
        output.append("-" * 120)
        for idx, item in enumerate(changes['change'], 1):
            if item.get('type') == 'output':
                output.append(f"{idx:<5} {'Output':<30} {item['name']:<85}")
            else:
                parts = item['name'].split('.')
                res_type = parts[0] if len(parts) > 0 else 'unknown'
                res_name = '.'.join(parts[1:]) if len(parts) > 1 else item['name']
                output.append(f"{idx:<5} {res_type:<30} {res_name:<85}")
        output.append("")
    
    # Resources to DESTROY
    if changes['destroy']:
        output.append("❌ RESOURCES TO BE DELETED")
        output.append("-" * 120)
        output.append(f"{'#':<5} {'Resource Type':<30} {'Resource Name':<85}")
        output.append("-" * 120)
        for idx, item in enumerate(changes['destroy'], 1):
            if item.get('type') == 'output':
                output.append(f"{idx:<5} {'Output':<30} {item['name']:<85}")
            else:
                parts = item['name'].split('.')
                res_type = parts[0] if len(parts) > 0 else 'unknown'
                res_name = '.'.join(parts[1:]) if len(parts) > 1 else item['name']
                output.append(f"{idx:<5} {res_type:<30} {res_name:<85}")
        output.append("")
    
    output.append("=" * 120)
    
    return "\n".join(output)

if __name__ == "__main__":
    # Read from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            plan_text = f.read()
    else:
        plan_text = sys.stdin.read()
    
    changes = parse_terraform_plan(plan_text)
    formatted_output = format_table(changes)
    print(formatted_output)
