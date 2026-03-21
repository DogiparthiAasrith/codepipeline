import json
import boto3
import urllib3
import os

http = urllib3.PoolManager()
ssm = boto3.client('ssm')
s3 = boto3.client('s3')
codepipeline = boto3.client('codepipeline')

def lambda_handler(event, context):
    """
    Lambda function to create GitHub PR after successful deployment.
    Triggered by CodePipeline after Deploy stage succeeds.
    """
    
    # Get configuration from environment variables
    github_owner = os.environ.get('GITHUB_OWNER', 'DogiparthiAasrith')
    github_repo = os.environ.get('GITHUB_REPO', 'codepipeline')
    target_branch = 'main'  # Always merge to main
    
    # Get source branch from CodePipeline artifact
    source_branch = None
    
    try:
        # Get job details from CodePipeline
        job_id = event['CodePipeline.job']['id']
        job_data = event['CodePipeline.job']['data']
        
        # Get input artifacts
        input_artifacts = job_data.get('inputArtifacts', [])
        
        if input_artifacts:
            # Get the first artifact (BuildArtifact)
            artifact = input_artifacts[0]
            artifact_location = artifact['location']['s3Location']
            bucket = artifact_location['bucketName']
            key = artifact_location['objectKey']
            
            print(f"Reading artifact from s3://{bucket}/{key}")
            
            # Download and extract branch_info.json from artifact
            # Note: Artifacts are ZIP files, we need to extract
            import zipfile
            import io
            
            # Download the artifact ZIP
            response = s3.get_object(Bucket=bucket, Key=key)
            zip_content = response['Body'].read()
            
            # Extract branch_info.json
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
                if 'branch_info.json' in zip_file.namelist():
                    branch_data = json.loads(zip_file.read('branch_info.json'))
                    source_branch = branch_data.get('source_branch')
                    print(f"Branch from artifact: {source_branch}")
        
    except Exception as e:
        print(f"Could not read branch from artifact: {str(e)}")
    
    # Fallback to environment variable if artifact reading failed
    if not source_branch:
        source_branch = os.environ.get('SOURCE_BRANCH', 'dev')
        print(f"Using fallback branch: {source_branch}")
    
    print(f"Source branch: {source_branch}, Target branch: {target_branch}")
    
    # Skip if already on main branch
    if source_branch == target_branch:
        print(f"Already on {target_branch} branch, skipping PR creation")
        codepipeline.put_job_success_result(jobId=job_id)
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
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={'message': f'Failed to get GitHub token: {str(e)}', 'type': 'JobFailed'}
        )
        raise
    
    # Get pipeline execution details from event
    pipeline_name = job_data.get('pipelineContext', {}).get('pipelineName', 'Unknown')
    execution_id = job_data.get('pipelineContext', {}).get('pipelineExecutionId', 'Unknown')
    
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
            codepipeline.put_job_success_result(jobId=job_id)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'PR created successfully',
                    'pr_url': pr_url
                })
            }
        else:
            print(f"⚠️ PR creation failed or already exists: {response_data}")
            codepipeline.put_job_success_result(jobId=job_id)
            return {
                'statusCode': response.status,
                'body': json.dumps(response_data)
            }
            
    except Exception as e:
        print(f"Error creating PR: {str(e)}")
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={'message': f'Failed to create PR: {str(e)}', 'type': 'JobFailed'}
        )
        raise

