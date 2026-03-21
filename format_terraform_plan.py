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
                    changes['destroy'].append({'name': name, 'old': old_val, 'new': new_val})
                elif not old_val and new_val:
                    changes['add'].append({'name': name, 'old': old_val, 'new': new_val})
                else:
                    changes['change'].append({'name': name, 'old': old_val, 'new': new_val})
    
    return changes

def format_table(changes: Dict) -> str:
    """Format changes into a readable table."""
    output = []
    
    # Header
    output.append("=" * 120)
    output.append("TERRAFORM PLAN SUMMARY")
    output.append("=" * 120)
    output.append("")
    
    # Summary
    if 'summary' in changes:
        s = changes['summary']
        output.append(f"📊 OVERVIEW: {s['add']} resources to ADD | {s['change']} to CHANGE | {s['destroy']} to DESTROY")
        output.append("")
    
    # Resources to ADD
    if changes['add']:
        output.append("✅ RESOURCES TO BE CREATED")
        output.append("-" * 120)
        output.append(f"{'Resource Name':<50} {'New Value':<70}")
        output.append("-" * 120)
        for item in changes['add']:
            output.append(f"{item['name']:<50} {item['new']:<70}")
        output.append("")
    
    # Resources to CHANGE
    if changes['change']:
        output.append("🔄 RESOURCES TO BE MODIFIED")
        output.append("-" * 120)
        output.append(f"{'Resource Name':<50} {'Change':<70}")
        output.append("-" * 120)
        for item in changes['change']:
            change_desc = f"{item['old'][:30]}... → {item['new'][:30]}..."
            output.append(f"{item['name']:<50} {change_desc:<70}")
        output.append("")
    
    # Resources to DESTROY
    if changes['destroy']:
        output.append("❌ RESOURCES TO BE DELETED")
        output.append("-" * 120)
        output.append(f"{'Resource Name':<50} {'Current Value (will be removed)':<70}")
        output.append("-" * 120)
        for item in changes['destroy']:
            output.append(f"{item['name']:<50} {item['old']:<70}")
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
