"""Scenario generation for AWS migration simulations."""

import random
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ScenarioPacket:
    """Complete scenario information."""
    aws_code: str
    business_context: str
    base_constraints: List[str]
    module_name: str
    services: List[str]


# AWS service combinations
SERVICE_COMBINATIONS = [
    {
        "services": ["S3", "SNS"],
        "code_template": """import boto3

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

def upload_and_notify(bucket_name: str, key: str, file_content: bytes, topic_arn: str):
    \"\"\"Upload file to S3 and send notification via SNS.\"\"\"
    # Upload to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=file_content,
        ContentType='application/octet-stream'
    )
    
    # Send notification
    sns_client.publish(
        TopicArn=topic_arn,
        Message=f'File {key} uploaded to {bucket_name}',
        Subject='S3 Upload Notification'
    )
    
    return {'status': 'success', 'bucket': bucket_name, 'key': key}""",
        "module_name": "file_processor"
    },
    {
        "services": ["Lambda", "SQS"],
        "code_template": """import json
import boto3

sqs = boto3.client('sqs')
lambda_client = boto3.client('lambda')

def process_queue(queue_url: str, function_name: str):
    \"\"\"Process messages from SQS queue using Lambda.\"\"\"
    # Receive messages
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20
    )
    
    messages = response.get('Messages', [])
    results = []
    
    for message in messages:
        # Invoke Lambda function
        lambda_response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(message['Body'])
        )
        
        result = json.loads(lambda_response['Payload'].read())
        results.append(result)
        
        # Delete message after processing
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
    
    return results""",
        "module_name": "message_processor"
    },
    {
        "services": ["DynamoDB", "IAM"],
        "code_template": """import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
iam = boto3.client('iam')

def query_user_data(table_name: str, user_id: str, role_name: str):
    \"\"\"Query DynamoDB with IAM role-based access.\"\"\"
    # Check IAM role permissions
    try:
        role = iam.get_role(RoleName=role_name)
        if not role:
            raise ValueError(f'Role {role_name} not found')
    except Exception as e:
        raise PermissionError(f'Cannot access role: {e}')
    
    # Query DynamoDB table
    table = dynamodb.Table(table_name)
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        ConsistentRead=True
    )
    
    return response.get('Items', [])""",
        "module_name": "user_data_service"
    },
    {
        "services": ["EC2", "CloudWatch"],
        "code_template": """import boto3
from datetime import datetime, timedelta

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')

def monitor_instance(instance_id: str, metric_name: str = 'CPUUtilization'):
    \"\"\"Monitor EC2 instance metrics via CloudWatch.\"\"\"
    # Get instance status
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = instances['Reservations'][0]['Instances'][0]
    
    # Get CloudWatch metrics
    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName=metric_name,
        Dimensions=[
            {'Name': 'InstanceId', 'Value': instance_id}
        ],
        StartTime=datetime.utcnow() - timedelta(hours=1),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Average']
    )
    
    return {
        'instance_id': instance_id,
        'state': instance['State']['Name'],
        'metrics': metrics['Datapoints']
    }""",
        "module_name": "instance_monitor"
    }
]

# Business context templates
BUSINESS_CONTEXTS = [
    {
        "context": "You've joined a mid-size startup (50 engineers) that's been running on AWS for 3 years. The CTO just announced a strategic partnership requiring migration to Azure within 6 months. Your team has partial documentation - some services are well-documented, others have only legacy code.",
        "constraints": ["time", "partial_docs"]
    },
    {
        "context": "Your company is being acquired, and the acquiring company uses GCP exclusively. You have 3 months to migrate critical services. Budget is tight, and you need to minimize downtime for existing customers.",
        "constraints": ["time", "cost", "downtime"]
    },
    {
        "context": "Regulatory requirements mandate moving sensitive data to a different cloud provider. Security and compliance are paramount. You have 4 months but must pass security audits during the process.",
        "constraints": ["security", "time"]
    },
    {
        "context": "Cost optimization initiative: migrate to a cheaper cloud provider. The service handles high traffic (millions of requests/day) and must maintain current performance levels.",
        "constraints": ["cost", "perf"]
    },
    {
        "context": "Multi-cloud strategy: migrate some services to reduce vendor lock-in. The migration should be gradual with zero downtime. Some services are customer-facing and critical.",
        "constraints": ["downtime", "time"]
    }
]

# Constraint pool
ALL_CONSTRAINTS = ["time", "cost", "security", "perf", "downtime", "partial_docs"]


def randomize_variant() -> Dict[str, Any]:
    """Randomly select a scenario variant."""
    service_combo = random.choice(SERVICE_COMBINATIONS)
    business_context = random.choice(BUSINESS_CONTEXTS)
    
    # Combine base constraints from business context with additional random constraints
    base_constraints = business_context["constraints"].copy()
    remaining_constraints = [c for c in ALL_CONSTRAINTS if c not in base_constraints]
    
    # Add 1-2 additional constraints randomly
    num_additional = random.randint(1, 2)
    additional = random.sample(remaining_constraints, min(num_additional, len(remaining_constraints)))
    all_constraints = base_constraints + additional
    
    return {
        "services": service_combo["services"],
        "code_template": service_combo["code_template"],
        "module_name": service_combo["module_name"],
        "business_context": business_context["context"],
        "constraints": all_constraints
    }


def generate_aws_code(variant: Dict[str, Any]) -> str:
    """Generate AWS code snippet from variant."""
    return variant["code_template"]


def generate_business_context(variant: Dict[str, Any]) -> str:
    """Generate business context from variant."""
    return variant["business_context"]


def pick_constraints(variant: Dict[str, Any]) -> List[str]:
    """Get constraints from variant."""
    return variant["constraints"]


def scenario_generator(state) -> ScenarioPacket:
    """Generate a complete scenario packet."""
    variant = randomize_variant()
    state.scenario_variant = variant
    
    aws_code = generate_aws_code(variant)
    business_context = generate_business_context(variant)
    base_constraints = pick_constraints(variant)
    
    return ScenarioPacket(
        aws_code=aws_code,
        business_context=business_context,
        base_constraints=base_constraints,
        module_name=variant["module_name"],
        services=variant["services"]
    )


def present_context(context_packet: ScenarioPacket) -> str:
    """Format the context packet as an agent message."""
    services_str = ", ".join(context_packet.services)
    return f"""Welcome to the Cloud Migration Simulation! 🌐

You've been tasked with migrating an AWS-based service to an alternative cloud provider.

**Context:**
{context_packet.business_context}

**Current AWS Implementation:**
The service uses: {services_str}
Module name: {context_packet.module_name}

```python
{context_packet.aws_code}
```

**Your Task:**
Plan and discuss your migration strategy. Consider constraints like time, cost, security, performance, and downtime. Different team members (PM, DevOps, CTO) will join the conversation with their perspectives and concerns.

Type your response to begin the simulation..."""
