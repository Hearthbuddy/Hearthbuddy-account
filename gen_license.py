import base64
import os

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from gitee_comments import GiteeIssueCommentFetcher


def get_private_key():
    """
    从环境变量中获取私钥
    """
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        raise ValueError("未找到环境变量 PRIVATE_KEY")
    return private_key


def gen_license(id, hardwareId):
    # 获取私钥
    private_key_content = get_private_key()
    private_key = RSA.import_key(private_key_content)

    licensePart = f'{{"licenseeName": "{id}", "hardwareID": "{hardwareId}", "paidUpTo": "2025-03-27"}}'
    digest = SHA256.new(licensePart.encode('utf-8'))
    signature = pkcs1_15.new(private_key).sign(digest)

    # 编码并保存文件
    sig_results = base64.b64encode(signature)
    licensePartBase64 = base64.b64encode(bytes(licensePart.encode('utf-8')))
    result = licensePartBase64.decode('utf-8') + "-" + sig_results.decode('utf-8')

    # 写入文件
    base_path = "accounts"
    filename = f"{base_path}/{hardwareId}"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    with open(filename, 'w') as f:
        f.write(result)


# 示例调用
if __name__ == "__main__":
    # 配置参数
    REPO_OWNER = "hearthstone-hearthbuddy"
    REPO_NAME = "Hearthbuddy-account"
    ISSUE_NUMBER = "IBRMIH"

    # 创建实例并获取数据
    fetcher = GiteeIssueCommentFetcher()

    try:
        # 获取评论
        raw_comments = fetcher.get_all_comments(
            owner=REPO_OWNER,
            repo=REPO_NAME,
            issue_number=ISSUE_NUMBER
        )

        # 过滤评论
        filtered_comments = fetcher.filter_comments(raw_comments)

        # 打印结果
        print(f"总评论数: {len(raw_comments)}")
        print(f"机器码个数: {len(filtered_comments)}")
        for idx, comment in enumerate(filtered_comments, 1):
            print("-" * 60)
            gen_license(comment['user']['id'], comment['body'])
            print(f"{idx}. [{comment['user']['name']}] {comment['body']}")
            print(f"   评论创建时间: {comment['created_at']}")

    except Exception as e:
        print(f"发生错误: {e}")
