"""
AI服务
用于调用AI模型进行分析，支持流式输出
"""
import json
from typing import Optional, Generator
from sqlmodel import Session, select
import httpx

from ..models import AIModel


def get_default_ai_model(session: Session) -> Optional[AIModel]:
    """获取默认的AI模型"""
    model = session.exec(
        select(AIModel).where(AIModel.is_default == True)  # noqa: E712
    ).first()
    
    if not model:
        # 如果没有默认模型，获取第一个模型
        model = session.exec(select(AIModel)).first()
    
    return model


def stream_ai_analysis(session: Session, prompt: str) -> Generator[str, None, None]:
    """
    流式调用AI模型进行分析
    
    Args:
        session: 数据库会话
        prompt: 提示词
    
    Yields:
        SSE格式的数据流
    """
    # 获取AI模型配置
    model = get_default_ai_model(session)
    
    if not model:
        yield f"data: {json.dumps({'error': '未配置AI模型，请在系统设置中配置AI模型'}, ensure_ascii=False)}\n\n"
        return
    
    if not model.api_key:
        yield f"data: {json.dumps({'error': 'AI模型未配置API Key'}, ensure_ascii=False)}\n\n"
        return
    
    # 根据provider选择不同的调用方式
    if model.provider in ["DeepSeek", "deepseek"]:
        yield from _stream_deepseek(model, prompt)
    elif model.provider in ["火山引擎", "volcano", "Volcano"]:
        yield from _stream_volcano(model, prompt)
    else:
        # 默认使用OpenAI兼容的API
        yield from _stream_openai_compatible(model, prompt)


def _stream_deepseek(model: AIModel, prompt: str) -> Generator[str, None, None]:
    """流式调用DeepSeek API"""
    base_url = model.base_url or "https://api.deepseek.com"
    api_key = model.api_key
    model_name = model.model or "deepseek-chat"
    
    url = f"{base_url}/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    data = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "你是一位专业的SLO分析专家，擅长分析服务级别目标、识别问题、提出改进建议。请用专业、清晰、结构化的方式回答问题。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True,
        "temperature": 0.7,
    }
    
    try:
        with httpx.stream("POST", url, headers=headers, json=data, timeout=60.0) as response:
            if response.status_code != 200:
                error_text = f"HTTP {response.status_code}"
                try:
                    # 对于非200状态码，读取错误响应
                    error_chunks = []
                    for chunk in response.iter_bytes():
                        error_chunks.append(chunk)
                    if error_chunks:
                        error_text = b''.join(error_chunks).decode('utf-8', errors='ignore')
                except:
                    pass
                yield f"data: {json.dumps({'error': f'AI API调用失败: {error_text}'}, ensure_ascii=False)}\n\n"
                return
            
            for line in response.iter_lines():
                if not line or line.startswith(":"):
                    continue
                
                if line.startswith("data: "):
                    line = line[6:]  # 移除 "data: " 前缀
                
                if line == "[DONE]":
                    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                    break
                
                try:
                    chunk_data = json.loads(line)
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        delta = chunk_data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        yield f"data: {json.dumps({'error': f'调用AI API时发生错误: {str(e)}'}, ensure_ascii=False)}\n\n"


def _stream_volcano(model: AIModel, prompt: str) -> Generator[str, None, None]:
    """流式调用火山引擎API"""
    base_url = model.base_url or "https://ark.cn-beijing.volces.com/api/v3"
    api_key = model.api_key
    model_name = model.model
    
    url = f"{base_url}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    data = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "你是一位专业的SLO分析专家，擅长分析服务级别目标、识别问题、提出改进建议。请用专业、清晰、结构化的方式回答问题。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True,
        "temperature": 0.7,
    }
    
    try:
        with httpx.stream("POST", url, headers=headers, json=data, timeout=60.0) as response:
            if response.status_code != 200:
                error_text = f"HTTP {response.status_code}"
                try:
                    # 对于非200状态码，读取错误响应
                    error_chunks = []
                    for chunk in response.iter_bytes():
                        error_chunks.append(chunk)
                    if error_chunks:
                        error_text = b''.join(error_chunks).decode('utf-8', errors='ignore')
                except:
                    pass
                yield f"data: {json.dumps({'error': f'AI API调用失败: {error_text}'}, ensure_ascii=False)}\n\n"
                return
            
            for line in response.iter_lines():
                if not line or line.startswith(":"):
                    continue
                
                if line.startswith("data: "):
                    line = line[6:]  # 移除 "data: " 前缀
                
                if line == "[DONE]":
                    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                    break
                
                try:
                    chunk_data = json.loads(line)
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        delta = chunk_data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        yield f"data: {json.dumps({'error': f'调用AI API时发生错误: {str(e)}'}, ensure_ascii=False)}\n\n"


def _stream_openai_compatible(model: AIModel, prompt: str) -> Generator[str, None, None]:
    """流式调用OpenAI兼容的API"""
    base_url = model.base_url or "https://api.openai.com/v1"
    api_key = model.api_key
    model_name = model.model
    
    # 确保base_url以/v1结尾或包含chat/completions
    if not base_url.endswith("/v1") and "/v1" not in base_url:
        if base_url.endswith("/"):
            base_url = base_url + "v1"
        else:
            base_url = base_url + "/v1"
    
    url = f"{base_url}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    data = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "你是一位专业的SLO分析专家，擅长分析服务级别目标、识别问题、提出改进建议。请用专业、清晰、结构化的方式回答问题。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True,
        "temperature": 0.7,
    }
    
    try:
        with httpx.stream("POST", url, headers=headers, json=data, timeout=60.0) as response:
            if response.status_code != 200:
                error_text = f"HTTP {response.status_code}"
                try:
                    # 对于非200状态码，读取错误响应
                    error_chunks = []
                    for chunk in response.iter_bytes():
                        error_chunks.append(chunk)
                    if error_chunks:
                        error_text = b''.join(error_chunks).decode('utf-8', errors='ignore')
                except:
                    pass
                yield f"data: {json.dumps({'error': f'AI API调用失败: {error_text}'}, ensure_ascii=False)}\n\n"
                return
            
            for line in response.iter_lines():
                if not line or line.startswith(":"):
                    continue
                
                if line.startswith("data: "):
                    line = line[6:]  # 移除 "data: " 前缀
                
                if line == "[DONE]":
                    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                    break
                
                try:
                    chunk_data = json.loads(line)
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        delta = chunk_data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        yield f"data: {json.dumps({'error': f'调用AI API时发生错误: {str(e)}'}, ensure_ascii=False)}\n\n"

