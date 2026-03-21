import json
import boto3
import urllib3
import os

http = urllib3.PoolManager()
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    """
    Lambda function to create GitHub PR after successful deployment.
    Triggered by CodePipeline after Deploy stage succeeds.
    """
    
    # Get configuration from environment variables
    github_owner = os.environ.get('GITHUB_OWNER', 'DogiparthiAasrith')
    github_repo = os.environ.get('GITHUB_REPO', 'codepipeline')
    target_branch = 'main'  # Always merge to main
    
    # Try to get source branch from multiple sources
    source_branch = None
    
    # 1. Try from CodePipeline user parameters (if passed)
    user_params = event.get('CodePipeline.job', {}).get('data', {}).get('actionConfiguration', {}).get('configuration', {}).get('UserParameters')
    if user_params:
        try:
            params = json.loads(user_params)
            source_branch = params.get('source_branch')
        except:
            pass
    
    # 2. Try from environment variable (set in Lambda config)
    if not source_branch:
        source_branch = os.environ.get('SOURCE_BRANCH')
    
    # 3. Try from event detail (if triggered by EventBridge)
    if not source_branch:
        source_branch = event.get('detail', {}).get('source-branch')
    
    # 4. Fallback - check if we can extract from pipeline execution
    if not source_branch:
        # Try to get from CodePipeline execution variables
        execution_vars = event.get('CodePipeline.job', {}).get('data', {}).get('inputArtifacts', [])
        for artifact in execution_vars:
            revision = artifact.get('revision', {})
            if 'revisionId' in revision:
                # This might contain branch info
                source_branch = revision.get('revisionSummary', 'unknown-branch')
                break
    
    # If still no branch found, use environment variable or default
    if not source_branch:
        source_branch = os.environ.get('SOURCE_BRANCH', 'dev')
        print(f"Warning: Could not detect source branch, using: {source_branch}")
    
    print(f"Source branch: {source_branch}, Target branch: {target_branch}")
    
    # Skip if already on main branch
    if source_branch == target_branch:
        print(f"Already on {target_branch} branch, skipping PR creation")
        return {
            'statusCode': 200,
            'body': json.dumps('Skipped - already on main branch')
        }
    
    # Get GitHub token from Parameter Store
    try:
        response = ssm.get_parameter(
            Name='/codepipeline/github-token',
            WithDecryption=True
        )
        github_token = response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting GitHub token: {str(e)}")
        raise
    
    # Get pipeline execution details from event
    pipeline_name = event.get('detail', {}).get('pipeline', 'Unknown')
    execution_id = event.get('detail', {}).get('execution-id', 'Unknown')
    
    # Create PR body
    pr_body = f"""## Terraform Deployment Successful ✅

This PR was automatically created after successful Terraform deployment.

**Pipeline:** {pipeline_name}
**Execution ID:** {execution_id}
**Source Branch:** {source_branch}
**Target Branch:** {target_branch}

All stages (Build → Approval → Deploy) completed successfully.
"""
    
    # Create PR using GitHub API
    pr_data = {
        "title": f"[Terraform] Merge {source_branch} to {target_branch}",
        "body": pr_body,
        "head": source_branch,
        "base": target_branch
    }
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    url = f'https://api.github.com/repos/{github_owner}/{github_repo}/pulls'
    
    try:
        response = http.request(
            'POST',
            url,
            body=json.dumps(pr_data).encode('utf-8'),
            headers=headers
        )
        
        response_data = json.loads(response.data.decode('utf-8'))
        
        if response.status == 201:
            pr_url = response_data.get('html_url')
            print(f"✅ Pull Request created: {pr_url}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'PR created successfully',
                    'pr_url': pr_url
                })
            }
        else:
            print(f"⚠️ PR creation failed or already exists: {response_data}")
            return {
                'statusCode': response.status,
                'body': json.dumps(response_data)
            }
            
    except Exception as e:
        print(f"Error creating PR: {str(e)}")
        raise

