import re

from django.http import HttpResponse
from user.models import User
from django.shortcuts import render, redirect
from django.views.generic import View
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.core.mail import send_mail


# Create your views here.


# /user/register
from django.urls import reverse


def register(request):
    """显示注册页面"""
    return render(request, 'register.html')


def register_handle(request):
    """进行用户注册"""

    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    # 进行数据校验
    if not all([username, password, email]):
        # 数据不完整
        return render(request, 'register.html', {'errmsg': '数据不完整'})


    # 校验邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

    # 进行业务处理：进行用户注册
    user = User.objects.create_user(username, email, password)

    # 返回应答，跳转到首页
    return redirect(reverse('goods:index'))


class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """进行用户注册"""

        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 进行业务处理：进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0 # 默认是未激活状态
        user.save()

        # 发送激活邮件，包含激活链接： 127.0.0.1:8000/user/active/3
        # 使用token对包含用户的身份信息进行加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token.decode()
        # 发送激活邮件
        # subject 主题
        subject = '欢迎信息'
        message = ''
        # 发件人
        sender = settings.EMAIL_HOST_USER
        receiver = [email]
        html_message = '<h1>%s, 欢迎您成为注册会员</h>请点击下面的链接激活您的账户</br><a href="http://127.0.0.1:8000/user/' \
                  'active/%s">http://127.0.0.1:8000/user/active/%s</a>'%(username, token, token)
        send_mail(subject, message, sender, receiver, html_message=html_message)


        # 返回应答，跳转到首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self, request, token):
        # 解密token,获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            user_id = info['confirm']
            user = User.objects.get(user=user_id)
            user.is_active = 1
            user.save()

            # 激活成功，跳转到登陆页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已经过期
            return HttpResponse('激活链接已过期')

# /user/login
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')