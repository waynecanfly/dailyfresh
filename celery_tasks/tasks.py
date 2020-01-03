# -*- coding: utf-8 -*-
# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 创建一个celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')

# 定义函数任务
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    # 发送激活邮件
    # subject 主题
    subject = '欢迎信息'
    message = ''
    # 发件人
    sender = settings.EMAIL_HOST_USER
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎您成为注册会员</h>请点击下面的链接激活您的账户</br><a href="http://127.0.0.1:8000/user/' \
                   'active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)