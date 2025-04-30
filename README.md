## 登记机器码

1. 登录你自己的gitee账号后，寻找一个公共仓库（或者自己创建一个），创建一个issue，在issue评论你的机器码，用于认证
   ```text
      xxxx-xxxx-xxxx-xxxx
   ```
2. 在[github issue](https://github.com/Hearthbuddy/Hearthbuddy-account/issues/1)发布在第一步评论的gitee认证信息，之后点开[Actions](https://github.com/Hearthbuddy/Hearthbuddy-account/actions)查看结果
   - 假设gitee评论地址为`https://gitee.com/thinkgem/jeesite5/issues/I18ARR` ，github评论格式如下：
   ```text
      thinkgem
      jeesite5
      I18ARR
      机器码
   ```
   - 假设gitee评论地址为`https://gitee.com/A/B/issues/C` ，github评论格式如下：
   ```text
      A
      B
      C
      机器码
   ```

4. gitee评论类似验证码的机制，兄弟账号会以gitee账号id为维度，多次评论会覆盖之前的评论，删除评论不会使已经生效的key失效，若要更换机器吗，重新评论即可

5. 禁止多次反复评论、无效评论、冲击github构建。一经发现删除已生成的key，并永久拉黑