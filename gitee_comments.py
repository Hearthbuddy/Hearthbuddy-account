import os
import re

import requests

from sqlite_db import SQLiteDB


class GiteeIssueCommentFetcher:
    def __init__(self, access_token=None, validation_func=None):
        self.access_token = access_token
        self.base_url = "https://gitee.com/api/v5/repos"
        self.validation_func = validation_func or self._default_validation

    @staticmethod
    def _default_validation(body):
        """默认验证规则：机器码"""
        cleaned = body.strip()
        return re.match(r"^[A-Z0-9]{4}(-[A-Z0-9]{4}){4}$", cleaned) is not None

    def get_all_comments(self, owner, repo, issue_number):
        """获取原始评论数据"""
        comments = []
        page = 1
        per_page = 100

        while True:
            params = {"page": page, "per_page": per_page}
            if self.access_token:
                params["access_token"] = self.access_token

            url = f"{self.base_url}/{owner}/{repo}/issues/{issue_number}/comments"
            response = requests.get(url, params=params)
            response.raise_for_status()

            page_comments = response.json()
            if not page_comments:
                break

            comments.extend(page_comments)
            if len(page_comments) < per_page:
                break
            page += 1

        return comments

    def get_comments_if_text_in_comments(self, owner, repo, issue_number, text):
        """判断指定text是否在评论中，仅获取前100条"""

        if not self.validation_func(text):
            print("机器码格式不正确")
            return

        params = {"page": 1, "per_page": 100}
        if self.access_token:
            params["access_token"] = self.access_token

        url = f"{self.base_url}/{owner}/{repo}/issues/{issue_number}/comments"
        response = requests.get(url, params=params)
        response.raise_for_status()

        page_comments = response.json()
        with SQLiteDB('gitee.db') as db:
            for comment in page_comments:
                if comment["body"] == text:
                    # 先判断此用户有没有生成过key
                    uid = comment["user"]["id"]
                    user = db.fetch_one("SELECT * FROM USERS WHERE USERID = :uid", {'uid': uid})
                    if user:
                        hid_old = user["HARDWAREID"]
                        if hid_old == text:
                            print("该用户已生成过相同的机器码，请勿重复生成")
                            return
                        hid_old_users = db.fetch_all("SELECT * FROM USERS WHERE HARDWAREID = :hid_old and USERID != :uid", {'hid_old': hid_old, 'uid': uid})
                        if not hid_old_users and os.path.exists(f'accounts/{hid_old}'):
                            # 没有其他账户引用此机器码并且文件存在，移除原有生成的key
                            print(f"移除原先生成的key {hid_old}")
                            os.remove(f'accounts/{hid_old}')
                    return comment
            print("未找到gitee评论，请检查")

    def filter_comments(self, comments):
        """过滤评论并保留每个用户第一条有效评论"""
        valid_comments = []
        users = set()

        for comment in comments:
            user_id = comment["user"]["id"]
            body = comment["body"]

            if user_id in users:
                continue

            if self.validation_func(body):
                valid_comments.append(comment)
                users.add(user_id)

        return valid_comments
