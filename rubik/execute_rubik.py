import requests
import time
import logging
from typing import Optional, Dict, Any, List


class ExecuteRubik:
    """
        只需传入必要参数即可提取字段值
        外部使用请看代码底部示例
    """

    def __init__(self,
                 base_url: str = "http://10.114.30.106:8899",
                 rubik_token: str = "8ea220d3-308f-4b29-bc29-b6beee2cff30"):
        """
        初始化客户端

        Args:
            base_url: 基础URL，默认 "http://10.114.30.106:8899"
            rubik_token: 认证token，默认 "8ea220d3-308f-4b29-bc29-b6beee2cff30"
        """
        # 确保尾部只有一个斜杠
        self.base_url = base_url.rstrip('/')
        # 请求头 "*/*"表示接收任何类型的响应
        self.headers = {
            "rubik-token": rubik_token,
            "Accept": "*/*",
        }

        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def extract_multiple_fields(self,
                                element_id: str,
                                env: str,
                                operator_account: str,
                                target_fields: List[str],
                                max_wait_time: int = 300) -> Dict[str, Optional[str]]:
        """
        一次性提取多个字段的值

        Args:
            element_id: 组件ID
            env: 环境名称
            operator_account: 操作者
            target_fields: 要提取的字段名列表
            max_wait_time: 最大等待时间

        Returns:
            字段名到值的映射字典
        """
        self.logger.info(f"开始提取字段: {target_fields}")

        # 1. 执行组件
        execution_id = self._execute_element(element_id, env, operator_account)
        if not execution_id:
            return {field: None for field in target_fields}

        # 2. 等待执行完成
        self._wait_for_execution_completion(execution_id, max_wait_time)

        # 3. 获取执行详情
        detail_data = self._get_execution_detail(execution_id)
        if not detail_data:
            return {field: None for field in target_fields}

        # 4. 批量提取字段
        results = {}
        for field in target_fields:
            results[field] = self._extract_field_value(detail_data, field)

        # 5. 打印结果摘要
        success_count = sum(1 for value in results.values() if value is not None)
        self.logger.info(f"批量提取完成: 成功 {success_count}/{len(target_fields)} 个字段")

        return results

    # 内部方法
    def _execute_element(self, element_id: str, env: str, operator_account: str) -> Optional[str]:
        """执行组件并返回执行ID"""
        url = f"{self.base_url}/external/execution/element_executor"
        params = {
            "element_id": element_id,
            "env": env,
            "operator_account": operator_account
        }

        try:
            self.logger.info(f"执行组件: {element_id}")
            response = requests.post(url=url, params=params, headers=self.headers, data="", timeout=60)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0 and "data" in result:
                    execution_id = str(result["data"])
                    self.logger.info(f"✅ 执行成功，ID: {execution_id}")
                    return execution_id
                else:
                    self.logger.error(f"执行失败，返回码: {result.get('code')}")
            else:
                self.logger.error(f"HTTP请求失败: {response.status_code}")
            return None
        except Exception as e:
            self.logger.error(f"执行元素异常: {e}")
            return None

    def _get_execution_detail(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行详情"""
        url = f"{self.base_url}/external/execution/trace/{execution_id}/detail"

        try:
            response = requests.get(url=url, headers=self.headers, timeout=60)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"获取详情失败: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"获取详情异常: {e}")
            return None

    def _extract_field_value(self, detail_data: Dict[str, Any], target_field: str) -> Optional[str]:
        """从详情数据中提取指定字段的值"""

        def deep_find_field(obj, field_name):
            """递归搜索字段"""
            if isinstance(obj, dict):
                if field_name in obj:
                    field_data = obj[field_name]
                    if isinstance(field_data, dict) and "value" in field_data:
                        return field_data["value"]
                    return str(field_data)

                for value in obj.values():
                    result = deep_find_field(value, field_name)
                    if result is not None:
                        return result

            elif isinstance(obj, list):
                for item in obj:
                    result = deep_find_field(item, field_name)
                    if result is not None:
                        return result
            return None

        try:
            return deep_find_field(detail_data, target_field)
        except Exception as e:
            self.logger.error(f"提取字段 {target_field} 异常: {e}")
            return None

    def _wait_for_execution_completion(self, execution_id: str, max_wait_time: int = 300) -> bool:
        """等待执行完成"""
        self.logger.info(f"等待执行完成: {execution_id}")

        start_time = time.time()
        check_interval = 5

        while time.time() - start_time < max_wait_time:
            detail_data = self._get_execution_detail(execution_id)
            if not detail_data:
                time.sleep(check_interval)
                continue

            status = self._get_execution_status(detail_data)
            if status in ["pass", "fail", "completed", "success"]:
                self.logger.info(f"✅ 执行完成，状态: {status}")
                # 断言是否执行通过
                assert status == "pass"
                return True

            self.logger.info(f"⏳ 执行中，状态: {status}")
            time.sleep(check_interval)

        self.logger.warning("⏰ 等待超时")
        return False

    def _get_execution_status(self, detail_data: Dict[str, Any]) -> str:
        """提取执行状态"""
        try:
            # 直接访问确定的路径
            status = detail_data["data"]["status"]
            if isinstance(status, str):
                return status
            else:
                return "unknown"
        except (KeyError, TypeError):
            return "unknown"


"""
    使用示例：
    # 先在test_mex代码包创建一个和helpers同级的代码包，在这个代码包下建一个test_rubik.py文件，将下面的代码复制进去即可
    from test_mex.helpers.execute_rubik import ExecuteRubik

    def test_rubik():
        # 创建客户端（使用默认的URL和token）
        client = ExecuteRubik()

        # 提取字段
        print("\n=== 提取字段 ===")
        field_values = client.extract_multiple_fields(
            element_id="2055498",
            env="env-3474",
            operator_account="zhangsan",
            target_fields=["channelUserId","channelCreditApplyId","channelLoanApplyId"]
        )

        # 拆分key-value
        for field, value in field_values.items():
            print(f"{field}: {value}")
"""