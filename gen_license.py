import base64
import os
import sys

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from gitee_comments import GiteeIssueCommentFetcher
from sqlite_db import SQLiteDB


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

    licensePart = f'{{"licenseeName": "{id}", "hardwareID": "{hardwareId}", "paidUpTo": "2026-01-01"}}'
    digest = SHA256.new(licensePart.encode('utf-8'))
    signature = pkcs1_15.new(private_key).sign(digest)

    # 编码并保存文件
    sig_results = base64.b64encode(signature)
    licensePartBase64 = base64.b64encode(bytes(licensePart.encode('utf-8')))
    result = licensePartBase64.decode('utf-8') + "-" + sig_results.decode('utf-8')

    # 写入密钥文件
    base_path = "accounts"
    filename = f"{base_path}/{hardwareId}"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    with open(filename, 'w') as f:
        f.write(result)
    # 保存账号信息
    with SQLiteDB('gitee.db') as db:
        db.insert_or_update("USERS", {'USERID': id, 'HARDWAREID': hardwareId}, 'USERID')

def refresh_all_licenses():
    with SQLiteDB('gitee.db') as db:
        all_users = db.fetch_all("SELECT * FROM USERS")
        print(all_users)
        for user in all_users:
            print("开始创建key")
            gen_license(user['USERID'], user['HARDWAREID'])
            print(f"[{user['USERID']}] {user['HARDWAREID']}")
            print(f"生成key成功")

if __name__ == "__main__":
    # 创建实例并获取数据
    fetcher = GiteeIssueCommentFetcher()

    try:
        # 获取评论
        comment = fetcher.get_comments_if_text_in_comments(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        if not comment:
            sys.exit(1)
        print("开始创建key")
        gen_license(comment['user']['id'], comment['body'])
        print(f"[{comment['user']['name']}] {comment['body']}")
        print(f"评论创建时间: {comment['created_at']}")
        print(f"生成key成功")
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)
