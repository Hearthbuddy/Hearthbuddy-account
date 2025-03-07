import re

import requests


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
