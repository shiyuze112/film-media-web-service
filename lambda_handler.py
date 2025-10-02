import json
import asyncio
from mangum import Mangum
from app import app

# 包装Flask应用为Lambda处理函数
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """
    AWS Lambda 处理函数
    """
    try:
        # 调用Mangum处理函数
        response = handler(event, context)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
