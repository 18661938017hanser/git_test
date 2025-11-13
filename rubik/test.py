# 使用示例
from rubik.execute_rubik import ExecuteRubik

def test_rubik():
    """
        外部调用只需要传入必要的参数
    """

    # 创建客户端（使用默认的URL和token）
    client = ExecuteRubik()
    # 使用自定义URL和token
    # custom_client = ExecuteRubik(
    #     base_url="http://10.114.30.106:8899",  # 可自定义
    #     rubik_token="8ea220d3-308f-4b29-bc29-b6beee2cff30"  # 可自定义
    # )

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