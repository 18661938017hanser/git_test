import requests
import json
import time
from typing import List, Dict

# 执行类
class ExecuteCase:
    def __init__(self, base_url, rubik_token):
        self.base_url = base_url
        self.headers = {
            "rubik-token": rubik_token,
            "User-Agent": "PostmanRuntime/7.49.0",
            "Accept": "*/*",
            "Host": base_url.replace("http://", "").split(":")[0]
        }

    def execute_element(self, element_id, env, operator_account, max_retries=3):
        """
        执行元素

        Args:
            element_id: 元素ID
            env: 环境
            operator_account: 操作者账号
            max_retries: 最大重试次数
        """
        url = f"{self.base_url}/external/execution/element_executor"

        params = {
            "element_id": element_id,
            "env": env,
            "operator_account": operator_account
        }

        for attempt in range(max_retries):
            try:
                print(f"第 {attempt + 1} 次尝试调用接口...")

                response = requests.post(
                    url=url,
                    params=params,
                    headers=self.headers,
                    data="",
                    timeout=60
                )

                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.text}")

                # 处理响应
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print("✅ 接口调用成功!")
                        return {
                            "success": True,
                            "data": result,
                            "status_code": response.status_code
                        }
                    except json.JSONDecodeError:
                        return {
                            "success": True,
                            "data": response.text,
                            "status_code": response.status_code
                        }

                elif response.status_code == 403:
                    error_data = response.json()
                    print(f"❌ 权限错误: {error_data.get('message', '未知错误')}")
                    return {
                        "success": False,
                        "error": error_data.get('message'),
                        "status_code": response.status_code
                    }

                else:
                    print(f"❌ 接口调用失败，状态码: {response.status_code}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 指数退避
                        print(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                    else:
                        return {
                            "success": False,
                            "error": f"请求失败，状态码: {response.status_code}",
                            "status_code": response.status_code
                        }

            except requests.exceptions.Timeout:
                print(f"❌ 请求超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    continue
                else:
                    return {
                        "success": False,
                        "error": "请求超时"
                    }

            except requests.exceptions.RequestException as e:
                print(f"❌ 请求异常: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }

        return {
            "success": False,
            "error": "超过最大重试次数"
        }

# 批量执行函数
def batch_execute_elements(client, tasks: List[Dict]):
    """
    批量执行多个元素
    """
    results = []

    for i, task in enumerate(tasks, 1):
        print(f"\n🚀 执行第 {i}/{len(tasks)} 个任务: {task}")

        result = client.execute_element(
            element_id=task["element_id"],
            env=task["env"],
            operator_account=task["operator_account"]
        )

        results.append({
            "task": task,
            "result": result
        })

        # 任务间延迟，避免请求过于频繁
        time.sleep(1)

    return results


# 批量执行rubik接口
if __name__ == "__main__":
    client = ExecuteCase(
        base_url="http://10.114.30.106:8899",
        rubik_token="8ea220d3-308f-4b29-bc29-b6beee2cff30"
    )

    # 定义批量任务 批量执行rubik接口
    tasks = [
        {"element_id": "1950374", "env": "env-3474", "operator_account": "zhangsan"},
        # 添加更多任务...
    ]

    # 批量执行
    batch_results = batch_execute_elements(client, tasks)

    # 输出汇总结果
    success_count = sum(1 for r in batch_results if r["result"]["success"])
    print(f"\n📊 批量执行完成: 成功 {success_count}/{len(tasks)}")