import requests
import json
import time

# 查询类
class QueryExecutionRecords:
    def __init__(self, base_url, rubik_token):
        self.base_url = base_url
        self.headers = {
            "rubik-token": rubik_token,
            "User-Agent": "PostmanRuntime/7.49.0",
            "Accept": "*/*",
            "Host": base_url.replace("http://", "").split(":")[0]
        }

    def get_trace(self, trace_id, max_retries=3):
        """
        获取执行轨迹详情

        Args:
            trace_id: 轨迹ID
            max_retries: 最大重试次数
        """
        url = f"{self.base_url}/external/execution/trace/{trace_id}/detail"

        for attempt in range(max_retries):
            try:
                print(f"第 {attempt + 1} 次尝试获取轨迹 {trace_id}...")

                response = requests.get(
                    url=url,
                    headers=self.headers,
                    timeout=60
                )

                print(f"状态码: {response.status_code}")

                # 处理响应
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print("✅ 获取执行轨迹成功!")
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

                elif response.status_code == 404:
                    print(f"❌ 轨迹不存在: {trace_id}")
                    return {
                        "success": False,
                        "error": f"轨迹 {trace_id} 不存在",
                        "status_code": response.status_code
                    }

                else:
                    print(f"❌ 请求失败，状态码: {response.status_code}")
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


# 使用示例
if __name__ == "__main__":
    # 初始化客户端
    client = QueryExecutionRecords(
        base_url="http://10.114.30.106:8899",
        rubik_token="8ea220d3-308f-4b29-bc29-b6beee2cff30"
    )

    # 获取执行轨迹
    # 改trace_id就可以查询别的记录
    trace_id = "2500402495"
    result = client.get_trace(trace_id)
    # 处理结果
    if result["success"]:
        print("获取轨迹成功!")
        print(f"返回数据: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")
        data = result["data"]
        status = data['data']['status']
        assert status == "pass"
        # 断言通过再进行后续操作
        # 这边给出一个获取手机号的操作
        context = data['data']['context']
        phone = context['registPhone']['value']
        print(f"用户的电话号码是{phone}")
    else:
        print(f"获取轨迹失败: {result['error']}")