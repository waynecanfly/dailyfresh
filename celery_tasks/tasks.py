# -*- coding: utf-8 -*-
# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 在任务处理者一端加入
# import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()


# 创建一个celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://192.168.10.135:6379/8')

# 定义函数任务
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    """发送激活邮件"""
    # 发送邮件
    subject = '天天生鲜激活信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
        username, token, token)

    try:
        send_mail(subject,
                  message,
                  sender,
                  receiver,
                  html_message=html_message, fail_silently=False)
    except Exception as e:
        print(e)
